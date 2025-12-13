"""
VoiceGrab v4.0 — Voice-to-AI Bridge
Main transcription script with config support
"""

import os
import sys
import time
import queue
import tempfile
import threading
import re
from pynput import keyboard as pynput_keyboard
import sounddevice as sd
import soundfile as sf
import numpy as np
import pyperclip
from groq import Groq
from pathlib import Path

# Script directory
SCRIPT_DIR = Path(__file__).parent.absolute()

# === SINGLETON CHECK ===
# Prevent multiple instances from running
LOCK_FILE = SCRIPT_DIR / "voicegrab.lock"

def check_singleton():
    """Check if another instance is running"""
    if LOCK_FILE.exists():
        try:
            # Read PID from lock file
            pid = int(LOCK_FILE.read_text().strip())
            # Check if process is running (Windows)
            import ctypes
            kernel32 = ctypes.windll.kernel32
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if handle:
                kernel32.CloseHandle(handle)
                # Process exists, exit
                print("⚠️ VoiceGrab is already running!")
                print("   Check system tray for the icon.")
                sys.exit(0)
        except (ValueError, OSError):
            pass  # Invalid lock file, continue
    
    # Create lock file with our PID
    LOCK_FILE.write_text(str(os.getpid()))

def cleanup_lock():
    """Remove lock file on exit"""
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except:
        pass

# Run singleton check
check_singleton()
import atexit
atexit.register(cleanup_lock)

# Import config
sys.path.insert(0, str(SCRIPT_DIR))
from config_schema import get_config

# Load config
config = get_config(str(SCRIPT_DIR / "config.json"))
cfg = config.load()

# Also load from .env if API key not in config
if not cfg.get('api', {}).get('key'):
    from dotenv import load_dotenv
    env_path = SCRIPT_DIR / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        cfg['api']['key'] = os.getenv('GROQ_API_KEY', '')

# --- Configuration from config.json ---
API_KEY = cfg.get('api', {}).get('key', '')
INPUT_MODE = cfg.get('input', {}).get('mode', 'toggle')
MAX_DURATION = cfg.get('global', {}).get('max_duration', 180)
SAMPLE_RATE = cfg.get('recording', {}).get('sample_rate', 16000)
CHANNELS = 1

# Modes from new config structure
MODES = cfg.get('modes', {})
DEFAULT_MODE = 'ai'
current_mode = DEFAULT_MODE

def normalize_hotkey(hotkey):
    """Convert config hotkey to pynput key identifier"""
    if not hotkey:
        return 'ctrl_r'
    # Map common variations to pynput key names
    h = hotkey.lower().strip()
    # Right Ctrl variations
    if h in ('ctrl r', 'right ctrl', 'ctrl_r', 'rctrl'):
        return 'ctrl_r'
    # Right Alt variations
    if h in ('alt gr', 'altgr', 'alt_gr', 'right alt', 'alt r', 'alt_r', 'ralt'):
        return 'alt_gr'
    # Left modifiers
    if h in ('ctrl', 'left ctrl', 'ctrl_l'):
        return 'ctrl_l'
    if h in ('alt', 'left alt', 'alt_l'):
        return 'alt_l'
    if h in ('shift', 'left shift', 'shift_l'):
        return 'shift_l'
    # Right shift
    if h in ('right shift', 'shift_r', 'rshift'):
        return 'shift_r'
    return h

def get_pynput_key(hotkey_name):
    """Get pynput Key object from normalized name"""
    key_map = {
        'ctrl_r': pynput_keyboard.Key.ctrl_r,
        'ctrl_l': pynput_keyboard.Key.ctrl_l,
        'alt_gr': pynput_keyboard.Key.alt_gr,
        'alt_r': pynput_keyboard.Key.alt_r,
        'alt_l': pynput_keyboard.Key.alt_l,
        'shift_r': pynput_keyboard.Key.shift_r,
        'shift_l': pynput_keyboard.Key.shift_l,
    }
    return key_map.get(hotkey_name, pynput_keyboard.Key.ctrl_r)

# Single global hotkey for all modes - configurable!
HOTKEY_NAME = normalize_hotkey(cfg.get('global', {}).get('hotkey', cfg.get('input', {}).get('hotkey', 'ctrl r')))
HOTKEY_KEY = get_pynput_key(HOTKEY_NAME)

# UI settings
USE_INDICATOR = cfg.get('ui', {}).get('floating_indicator', True)

# --- Global State ---
recording = False
audio_queue = queue.Queue()
record_start_time = 0
indicator = None

# Mode hotkey mapping
MODE_KEYS = {
    '1': 'ai',
    '2': 'code', 
    '3': 'docs',
    '4': 'notes',
    '5': 'chat'
}


def get_mode_name(mode_key):
    """Get display name for mode"""
    if mode_key in MODES:
        name = MODES[mode_key].get('name', '')
        return name if name else mode_key.capitalize()
    return mode_key.capitalize()


def get_prompt(mode_key):
    """Get prompt for mode"""
    if mode_key in MODES:
        return MODES[mode_key].get('prompt', '')
    return ''


def should_cleanup(mode_key):
    """Check if filler cleanup is enabled for mode"""
    if mode_key in MODES:
        return MODES[mode_key].get('filler_cleanup', False)
    return False


def cleanup_text(text, mode_key):
    """Remove filler words and garbage phrases (Whisper hallucinations)"""
    mode_data = MODES.get(mode_key, {})
    
    # Check if hallucination filter is enabled (default True)
    hallucination_filter = mode_data.get('hallucination_filter', True)
    
    # Remove garbage phrases only if enabled
    if hallucination_filter:
        # Get garbage phrases from config, with defaults
        default_garbage = [
            "Продолжение следует", "продолжение следует",
            "Продолжение следует...", "продолжение следует...",
            "To be continued", "to be continued",
            "Thank you for watching", "Спасибо за просмотр",
            "Подписывайтесь на канал", "Subscribe", "Subtitles by",
            "[Music]", "[Музыка]", "(music)", "(музыка)",
            "Редактор субтитров", "Корректор",
        ]
        
        garbage_phrases = mode_data.get('garbage_phrases', default_garbage)
        
        # Handle comma-separated string from UI
        if isinstance(garbage_phrases, str):
            garbage_phrases = [p.strip() for p in garbage_phrases.split(',') if p.strip()]
        
        for phrase in garbage_phrases:
            # Case-insensitive replacement
            text = re.sub(re.escape(phrase), '', text, flags=re.IGNORECASE)
    
    # Get filler_words from CURRENT mode
    filler_words = mode_data.get('filler_words', [])
    if filler_words:
        # Handle both list and comma-separated string
        if isinstance(filler_words, str):
            filler_words = [w.strip() for w in filler_words.split(',') if w.strip()]
        
        # Remove filler words (as separate words)
        for word in filler_words:
            # Word boundaries for Russian and English
            pattern = r'(?<![а-яА-Яa-zA-Z])' + re.escape(word) + r'(?![а-яА-Яa-zA-Z])'
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s+([.,!?])', r'\1', text)
    
    return text.strip()


def callback(indata, frames, time_info, status):
    """Audio callback"""
    if recording:
        audio_queue.put(indata.copy())


def transcribe(filename):
    """Send to Groq Whisper"""
    global current_mode
    
    # Get mode settings
    mode_cfg = MODES.get(current_mode, {})
    prompt = get_prompt(current_mode)
    model = mode_cfg.get('model', 'whisper-large-v3')
    language = mode_cfg.get('language', 'ru')
    temperature = mode_cfg.get('temperature', 0.0)
    profanity_filter = mode_cfg.get('profanity_filter', False)
    
    client = Groq(api_key=API_KEY)
    
    try:
        with open(filename, "rb") as f:
            # Build API params
            params = {
                'file': (filename, f.read()),
                'model': model,
                'response_format': 'json',
                'prompt': prompt,
                'temperature': temperature
            }
            # Only set language if not 'auto'
            if language and language != 'auto':
                params['language'] = language
            
            result = client.audio.transcriptions.create(**params)
        
        text = result.text
        
        # Apply cleanup if enabled for this mode
        if should_cleanup(current_mode):
            text = cleanup_text(text, current_mode)
        
        # Apply profanity filter if enabled
        if profanity_filter:
            text = filter_profanity(text)
        
        return text
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if indicator:
            indicator.show_error(str(e)[:40])
        return None


def filter_profanity(text):
    """Simple profanity filter - replaces offensive words with ***"""
    # Russian profanity patterns (common roots)
    profanity_patterns = [
        r'\b[хx][уy][йеёия]\w*', r'\b[пp][иiu][зz][дd]\w*', r'\b[бb][лl][яa]\w*',
        r'\b[еe][бb]\w*', r'\b[сc][уy][кk]\w*', r'\bдерьм\w*', r'\bмудак\w*',
        r'\bпидор\w*', r'\bхер\w*', r'\bжоп\w*'
    ]
    for pattern in profanity_patterns:
        text = re.sub(pattern, '***', text, flags=re.IGNORECASE)
    return text


def clear_line():
    sys.stdout.write('\r' + ' ' * 70 + '\r')
    sys.stdout.flush()


def show_timer():
    """Show recording timer"""
    global recording, record_start_time
    while recording:
        elapsed = time.time() - record_start_time
        remaining = MAX_DURATION - elapsed
        
        mins = int(elapsed) // 60
        secs = int(elapsed) % 60
        
        if not USE_INDICATOR:
            clear_line()
            sys.stdout.write(f'\r🔴 REC {mins}:{secs:02d} [{get_mode_name(current_mode)}]')
            sys.stdout.flush()
        
        if remaining <= 0:
            clear_line()
            print(f'\r⏰ Auto-send ({MAX_DURATION}s limit)')
            do_stop_and_process()
            break
        
        time.sleep(0.5)


def do_start_recording():
    """Start recording"""
    global recording, record_start_time
    
    if recording:
        return
    
    try:
        # Clear queue
        with audio_queue.mutex:
            audio_queue.queue.clear()
        
        recording = True
        record_start_time = time.time()
        
        print()  # New line
        
        # Show indicator
        if indicator and USE_INDICATOR:
            try:
                indicator.start_recording(get_mode_name(current_mode))
            except Exception as e:
                print(f"[DEBUG] Indicator error: {e}")
        
        # Start timer thread
        timer_thread = threading.Thread(target=show_timer, daemon=True)
        timer_thread.start()
        
        print("[DEBUG] Recording started successfully!")
    except Exception as e:
        print(f"[ERROR] do_start_recording crashed: {e}")
        import traceback
        traceback.print_exc()


def do_stop_and_process():
    """Stop and process recording"""
    global recording
    
    if not recording:
        return
    
    recording = False
    clear_line()
    
    # Update indicator
    if indicator and USE_INDICATOR:
        indicator.stop_recording()
        indicator.show_processing()
    
    # Collect audio
    data = []
    while not audio_queue.empty():
        data.append(audio_queue.get())
    
    if not data:
        print("⚠️ No audio")
        if indicator:
            indicator.hide()
        return
    
    audio = np.concatenate(data, axis=0)
    duration = len(audio) / SAMPLE_RATE
    
    if duration < 0.5:
        print("⚠️ Too short")
        if indicator:
            indicator.hide()
        return
    
    mins = int(duration) // 60
    secs = int(duration) % 60
    print(f"⏳ Processing {mins}:{secs:02d}...")
    
    # Create recordings folder if needed
    recordings_dir = SCRIPT_DIR / "recordings"
    recordings_dir.mkdir(exist_ok=True)
    
    # Generate timestamp for filenames
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save and transcribe
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        sf.write(tmp.name, audio, SAMPLE_RATE)
        tmp_path = tmp.name
    
    start = time.time()
    text = transcribe(tmp_path)
    elapsed = time.time() - start
    
    # ALWAYS run cleanup to remove garbage phrases (Whisper hallucinations)
    # and filler words (if enabled for this mode)
    if text:
        text = cleanup_text(text, current_mode)
    
    # Check save_audio setting from config (reload to get current value)
    import json
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            current_cfg = json.load(f)
        save_audio = current_cfg.get('global', {}).get('save_audio', False)
    except:
        save_audio = False
    if save_audio:
        # Copy to recordings folder with timestamp
        import shutil
        saved_path = recordings_dir / f"recording_{timestamp}.wav"
        shutil.copy(tmp_path, saved_path)
        print(f"💾 Saved: {saved_path.name}")
    
    # Clean up temp file
    os.remove(tmp_path)
    
    if text:
        preview = text[:100] + '...' if len(text) > 100 else text
        print(f"✅ ({elapsed:.1f}s): {preview}")
        
        # Check log_texts setting and save to log
        log_texts = cfg.get('global', {}).get('log_texts', True)
        if log_texts:
            # Log file per day
            date_only = datetime.now().strftime("%Y%m%d")
            log_path = recordings_dir / f"transcription_log_{date_only}.txt"
            with open(log_path, 'a', encoding='utf-8') as f:
                time_only = datetime.now().strftime("%H:%M:%S")
                mode_name = get_mode_name(current_mode)
                f.write(f"\n[{time_only}] {mode_name} ({elapsed:.1f}s)\n")
                f.write(text + "\n")
            print(f"📝 Logged to: {log_path.name}")
        
        # Show result in indicator
        if indicator and USE_INDICATOR:
            indicator.show_result(text, elapsed)
        
        # Copy and paste
        pyperclip.copy(text)
        time.sleep(0.1)
        # Use pynput Controller for Ctrl+V (no admin needed)
        kb = pynput_keyboard.Controller()
        kb.press(pynput_keyboard.Key.ctrl)
        kb.press('v')
        kb.release('v')
        kb.release(pynput_keyboard.Key.ctrl)
    else:
        print("⚠️ No result")
        if indicator:
            indicator.hide()


def switch_mode(mode_key):
    """Switch transcription mode"""
    global current_mode, HOTKEY
    if mode_key in MODES:
        current_mode = mode_key
        clear_line()
        print(f"🔄 Mode: {get_mode_name(mode_key)}")


def on_press(key):
    """Handle key press events (pynput)"""
    global recording
    
    # Get key name
    try:
        key_name = key.char if hasattr(key, 'char') and key.char else str(key)
    except:
        key_name = str(key)
    
    # Check for configured hotkey (default: Right Ctrl)
    is_hotkey = (key == HOTKEY_KEY or HOTKEY_NAME in key_name.lower())
    
    if is_hotkey:
        # Toggle mode
        if INPUT_MODE == 'toggle':
            if not recording:
                do_start_recording()
            else:
                do_stop_and_process()
        # Hold mode - start on press
        elif not recording:
            do_start_recording()

def on_release(key):
    """Handle key release events (pynput)"""
    global recording
    
    # Check for configured hotkey
    is_hotkey = (key == HOTKEY_KEY)
    
    # Hold mode - stop on release
    if is_hotkey and INPUT_MODE == 'hold' and recording:
        print("[DEBUG] Stopping recording (key released)...")
        do_stop_and_process()
    
    # ESC to exit
    if key == pynput_keyboard.Key.esc:
        print("\n👋 Bye!")
        return False  # Stop listener


def main():
    global indicator, current_mode
    
    print("=" * 50)
    print("🎤 VoiceGrab v4.0")
    print("=" * 50)
    print(f"API: {'✅' if API_KEY else '❌ Missing!'}")
    print(f"Mode: {get_mode_name(current_mode)}")
    print(f"Input: {'Toggle' if INPUT_MODE == 'toggle' else 'Hold'}")
    print(f"Max: {MAX_DURATION}s")
    print()
    print("📌 Controls:")
    hotkey_display = HOTKEY_NAME.replace('ctrl_r', 'Right Ctrl').replace('alt_gr', 'Right Alt')
    print(f"   {hotkey_display} = Start/Stop")
    print("   Right Ctrl + 1-5 = Switch mode")
    print("   ESC = Exit")
    print("   Right-click tray icon = Settings")
    print("=" * 50)
    
    if not API_KEY:
        print("\n⚠️ Run: python voicegrab_launcher.py --settings")
        print("   to configure API key")
        return
    
    # Start system tray
    tray = None
    try:
        from system_tray import SystemTray
        
        def on_mode_change(mode):
            global current_mode
            current_mode = mode
            print(f"\n🔄 Mode: {get_mode_name(mode)}")
        
        def close_settings_windows():
            """Find and close any VoiceGrab Settings windows (PowerShell only)"""
            try:
                import ctypes
                from ctypes import wintypes
                
                user32 = ctypes.windll.user32
                EnumWindows = user32.EnumWindows
                GetWindowTextW = user32.GetWindowTextW
                GetWindowTextLengthW = user32.GetWindowTextLengthW
                GetClassNameW = user32.GetClassNameW
                PostMessageW = user32.PostMessageW
                WM_CLOSE = 0x0010
                
                WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
                
                def callback(hwnd, _):
                    length = GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        GetWindowTextW(hwnd, buff, length + 1)
                        title = buff.value
                        
                        # Get window class name
                        class_buff = ctypes.create_unicode_buffer(256)
                        GetClassNameW(hwnd, class_buff, 256)
                        classname = class_buff.value
                        
                        # Only close PowerShell Forms windows with VoiceGrab title
                        # WindowsForms = PowerShell WebBrowser control
                        is_voicegrab = "VoiceGrab" in title
                        is_forms = "WindowsForms" in classname
                        
                        if is_voicegrab and is_forms:
                            PostMessageW(hwnd, WM_CLOSE, 0, 0)
                    return True
                
                EnumWindows(WNDENUMPROC(callback), 0)
            except Exception as e:
                print(f"[DEBUG] Error closing settings: {e}")
        
        def on_exit():
            close_settings_windows()
            os._exit(0)
        
        tray = SystemTray(on_mode_change=on_mode_change, on_exit=on_exit)
        tray.set_mode(current_mode)
        tray.run_detached()
        print("📌 Tray icon active (right-click for menu)")
    except Exception as e:
        print(f"⚠️ Tray disabled: {e}")
    
    # Start floating indicator if enabled
    if USE_INDICATOR:
        try:
            from floating_indicator import FloatingIndicator
            
            # Mode order for cycling
            MODE_ORDER = ['ai', 'code', 'docs', 'notes', 'chat']
            
            def next_mode():
                """Switch to next mode (click on indicator)"""
                global current_mode
                idx = MODE_ORDER.index(current_mode) if current_mode in MODE_ORDER else 0
                next_idx = (idx + 1) % len(MODE_ORDER)
                new_mode = MODE_ORDER[next_idx]
                current_mode = new_mode
                print(f"\n🔄 Mode: {get_mode_name(new_mode)}")
                if indicator:
                    indicator.update_mode(get_mode_name(new_mode))
                if tray:
                    tray.set_mode(new_mode)
            
            indicator = FloatingIndicator(on_mode_click=next_mode)
            indicator.run_in_thread()
        except Exception as e:
            print(f"⚠️ Indicator disabled: {e}")
    
    # Start audio stream
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, callback=callback):
        print("\n✅ Ready! (Press AltGr to record, ESC to exit)\n")
        
        # Use pynput Listener (no admin rights needed!)
        with pynput_keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            try:
                listener.join()
            except KeyboardInterrupt:
                pass
    
    if tray:
        tray.stop()
    
    print("\n👋 Bye!")


if __name__ == "__main__":
    main()

