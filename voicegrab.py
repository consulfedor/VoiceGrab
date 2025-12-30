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

# Startup log with timestamp to confirm code version
from datetime import datetime
print(f"[STARTUP] VoiceGrab loaded at {datetime.now().strftime('%H:%M:%S')} - MODE_SYNC v2")

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
indicator_override = False  # True when indicator changes mode during recording

# Mode sync - read active_mode from config.json directly (most reliable)
MODE_SYNC_FILE = SCRIPT_DIR / "mode_sync.txt"  # Keep for backward compat
CONFIG_FILE = SCRIPT_DIR / "config.json"  # Main config file

def debug_log(msg):
    """Log debug message to file (since console is hidden)"""
    try:
        with open(SCRIPT_DIR / "debug.log", "a", encoding="utf-8") as f:
            from datetime import datetime
            f.write(f"{datetime.now().strftime('%H:%M:%S')} {msg}\n")
    except:
        pass

def get_synced_mode():
    """Read active mode from config.json - single source of truth"""
    import json  # Local import to ensure it's available
    try:
        debug_log(f"get_synced_mode() called, CONFIG_FILE={CONFIG_FILE}")
        # Primary: read from config.json active_mode
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as f:
                cfg = json.load(f)
            active = cfg.get('global', {}).get('active_mode')
            debug_log(f"config.json active_mode = {active}")
            if active and active in ['ai', 'code', 'docs', 'notes', 'chat']:
                print(f"[CONFIG] active_mode from config.json: {active}")
                return active
        
        # Fallback: try mode_sync.txt
        if MODE_SYNC_FILE.exists():
            synced = MODE_SYNC_FILE.read_text(encoding='utf-8').strip()
            debug_log(f"mode_sync.txt = {synced}")
            if synced in ['ai', 'code', 'docs', 'notes', 'chat']:
                print(f"[CONFIG] mode from mode_sync.txt fallback: {synced}")
                return synced
    except Exception as e:
        debug_log(f"Error: {e}")
        print(f"[CONFIG] Error reading mode: {e}")
    return None

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


def auto_translate(text, mode_key):
    """Auto-translate text based on mode settings using Groq API"""
    debug_log(f"auto_translate() called, mode_key={mode_key}")
    # Reload config to get fresh settings
    import json
    config_path = SCRIPT_DIR / "config.json"
    try:
        with open(config_path, 'r', encoding='utf-8-sig') as f:
            current_cfg = json.load(f)
    except:
        return text
    
    mode_cfg = current_cfg.get('modes', {}).get(mode_key, {})
    translate_mode = mode_cfg.get('auto_translate', 'off')
    
    if translate_mode == 'off' or not text:
        return text
    
    target_lang = mode_cfg.get('translate_lang', 'EN')
    translate_engine = mode_cfg.get('translate_engine', 'groq')
    lang_names = {'EN': 'English', 'RU': 'Russian', 'DE': 'German', 
                  'FR': 'French', 'ES': 'Spanish', 'ZH': 'Chinese', 
                  'JA': 'Japanese', 'TR': 'Turkish'}
    lang_name = lang_names.get(target_lang, 'English')
    
    print(f"[Auto-Translate] Mode: {translate_mode}, Target: {lang_name}, Engine: {translate_engine}")
    
    translation = None
    
    try:
        if translate_engine == 'groq':
            api_key = current_cfg.get('api', {}).get('key')
            if not api_key:
                print("[Auto-Translate] No Groq API key!")
                return text
            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": f"You are a translation machine. Translate to {lang_name}. Output ONLY the translation, nothing else."},
                    {"role": "user", "content": f"Translate: {text}"}
                ],
                temperature=0.1
            )
            translation = response.choices[0].message.content.strip()
            
        elif translate_engine == 'gemini':
            import requests
            gemini_key = current_cfg.get('gemini', {}).get('key')
            if not gemini_key:
                print("[Auto-Translate] No Gemini API key!")
                return text
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            body = {
                "contents": [{"parts": [{"text": f"Translate to {lang_name}. Output ONLY the translation:\n{text}"}]}]
            }
            resp = requests.post(url, json=body, timeout=30)
            if resp.status_code == 200:
                translation = resp.json()['candidates'][0]['content']['parts'][0]['text'].strip()
            else:
                print(f"[Auto-Translate] Gemini error: {resp.status_code}")
                
        elif translate_engine == 'deepl':
            import requests
            deepl_key = current_cfg.get('deepl', {}).get('key')
            if not deepl_key:
                print("[Auto-Translate] No DeepL API key!")
                return text
            url = "https://api-free.deepl.com/v2/translate"
            body = {"text": [text], "target_lang": target_lang}
            headers = {"Authorization": f"DeepL-Auth-Key {deepl_key}", "Content-Type": "application/json"}
            resp = requests.post(url, json=body, headers=headers, timeout=30)
            if resp.status_code == 200:
                translation = resp.json()['translations'][0]['text']
            else:
                print(f"[Auto-Translate] DeepL error: {resp.status_code}")
        
        if translation:
            print(f"[Auto-Translate] Result: {translation[:50]}...")
            if translate_mode == 'replace':
                return translation
            elif translate_mode == 'append':
                return f"{text} [{target_lang}: {translation}]"
                
    except Exception as e:
        print(f"⚠️ Translation error: {e}")
    
    return text



def callback(indata, frames, time_info, status):
    """Audio callback"""
    if recording:
        audio_queue.put(indata.copy())


def transcribe_groq(filename, mode_cfg, prompt):
    """Transcribe using Groq Whisper API"""
    model = mode_cfg.get('model', 'whisper-large-v3')
    language = mode_cfg.get('language', 'ru')
    temperature = mode_cfg.get('temperature', 0.0)
    
    client = Groq(api_key=API_KEY)
    
    with open(filename, "rb") as f:
        params = {
            'file': (filename, f.read()),
            'model': model,
            'response_format': 'json',
            'prompt': prompt,
            'temperature': temperature
        }
        if language and language != 'auto':
            params['language'] = language
        
        result = client.audio.transcriptions.create(**params)
    
    return result.text


def transcribe_gemini(filename):
    """Transcribe using Gemini API"""
    try:
        from google import genai
    except ImportError:
        return "[Gemini] Error: google-genai not installed"
    
    gemini_key = cfg.get('api', {}).get('gemini_key', '')
    if not gemini_key:
        return "[Gemini] Error: API key not configured"
    
    try:
        client = genai.Client(api_key=gemini_key)
        myfile = client.files.upload(file=filename)
        
        # Get model from config, default to gemini-1.5-flash
        gemini_model = cfg.get('api', {}).get('gemini_model', 'gemini-1.5-flash')
        
        response = client.models.generate_content(
            model=gemini_model,
            contents=['Transcribe this audio accurately. Output only the transcription text, nothing else:', myfile]
        )
        return response.text
    except Exception as e:
        return f"[Gemini] Error: {str(e)[:50]}"


def transcribe(filename):
    """Transcribe audio using configured provider (groq/gemini/both)"""
    global current_mode, cfg
    
    debug_log(f"transcribe() called, current_mode={current_mode}")
    
    # Reload config to get latest provider/model settings
    cfg = config.load()
    
    # Get mode settings from FRESH config (not stale global MODES)
    modes = cfg.get('modes', {})
    mode_cfg = modes.get(current_mode, {})
    prompt = get_prompt(current_mode)
    profanity_filter = mode_cfg.get('profanity_filter', False)
    
    # Get provider from config
    provider = cfg.get('global', {}).get('transcription_provider', 'groq')
    
    try:
        if provider == 'groq':
            text = transcribe_groq(filename, mode_cfg, prompt)
        elif provider == 'gemini':
            text = transcribe_gemini(filename)
        elif provider == 'both':
            # Run both and combine results
            groq_text = transcribe_groq(filename, mode_cfg, prompt)
            gemini_text = transcribe_gemini(filename)
            text = f"[Groq]: {groq_text}\n[Gemini]: {gemini_text}"
        else:
            text = transcribe_groq(filename, mode_cfg, prompt)
        
        if text is None:
            return None
        
        # Apply cleanup if enabled (only for single provider results)
        if provider != 'both' and should_cleanup(current_mode):
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
            print(f'\r⏰ Auto-segment ({MAX_DURATION}s) - continuing...')
            # Show brief feedback in indicator
            if indicator and USE_INDICATOR:
                indicator.show_processing()  # Brief "Sending..." flash
            # Process current segment in background, recording continues
            process_segment()
            # Restore recording display after brief moment
            if indicator and USE_INDICATOR:
                time.sleep(0.3)
                indicator.start_recording(get_mode_name(current_mode))
            # Timer was reset by process_segment, loop continues
            continue
        
        time.sleep(0.5)


def do_start_recording():
    """Start recording"""
    global recording, record_start_time, current_mode, indicator_override
    
    if recording:
        return
    
    # Reset indicator override - new recording reads from Settings
    indicator_override = False
    
    try:
        debug_log(f"do_start_recording() called, current_mode={current_mode}")
        # FORCED SYNC: Read mode from file RIGHT NOW to ensure we use what Settings set
        synced = get_synced_mode()
        debug_log(f"synced={synced}")
        print(f"[SYNC] File={synced}, Before={current_mode}")
        if synced:
            # ALWAYS use mode from file - this is the source of truth
            if synced != current_mode:
                current_mode = synced
                debug_log(f"Mode changed to: {synced}")
                print(f"🔄 Mode changed to: {get_mode_name(synced)}")
                if tray:
                    tray.set_mode(synced)
            # Update indicator with current (possibly updated) mode
        
        # Clear queue
        with audio_queue.mutex:
            audio_queue.queue.clear()
        
        recording = True
        record_start_time = time.time()
        
        print()  # New line
        
        # Show indicator with CURRENT synced mode (ALWAYS use fresh current_mode)
        active_mode = synced if synced else current_mode
        if indicator and USE_INDICATOR:
            try:
                indicator.start_recording(get_mode_name(active_mode))
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


def process_segment():
    """Process current audio segment without stopping recording (for auto-segmentation)"""
    global record_start_time
    
    # Collect audio from queue
    data = []
    while not audio_queue.empty():
        data.append(audio_queue.get())
    
    if not data:
        return
    
    audio = np.concatenate(data, axis=0)
    duration = len(audio) / SAMPLE_RATE
    
    if duration < 0.5:
        return
    
    # Reset timer for next segment
    record_start_time = time.time()
    
    # Process in background
    def _process():
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        recordings_dir = SCRIPT_DIR / "recordings"
        recordings_dir.mkdir(exist_ok=True)
        
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                sf.write(tmp.name, audio, SAMPLE_RATE)
                tmp_path = tmp.name
        except Exception as e:
            print(f"Error creating temp file: {e}")
            return
        
        try:
            text = transcribe(tmp_path)
        except Exception as e:
            print(f"Error in transcribe: {e}")
            text = None
        
        if text:
            try:
                text = cleanup_text(text, current_mode)
            except Exception as e:
                print(f"Error in cleanup_text: {e}")
        
        # Save audio if enabled
        import json
        config_path = SCRIPT_DIR / "config.json"
        try:
            with open(config_path, 'r', encoding='utf-8-sig') as f:
                current_cfg = json.load(f)
            save_audio = current_cfg.get('global', {}).get('save_audio', False)
        except Exception as e:
            save_audio = False
        
        if save_audio:
            import shutil
            saved_path = recordings_dir / f"recording_{timestamp}.wav"
            try:
                shutil.copy(tmp_path, saved_path)
                print(f"💾 Segment saved: {saved_path.name}")
            except Exception as e:
                print(f"❌ Segment save failed: {e}")
        
        os.remove(tmp_path)
        
        if text:
            print(f"📝 Segment: {text[:50]}...")
            
            # Auto-translate if enabled in mode settings
            text = auto_translate(text, current_mode)
            
            pyperclip.copy(text)
            time.sleep(0.1)
            # Use pynput Controller for Ctrl+V (no admin needed)
            kb = pynput_keyboard.Controller()
            kb.press(pynput_keyboard.Key.ctrl)
            kb.press('v')
            kb.release('v')
            kb.release(pynput_keyboard.Key.ctrl)
            
            # Log texts if enabled
            log_texts = cfg.get('global', {}).get('log_texts', True)
            if log_texts:
                date_only = datetime.now().strftime("%Y%m%d")
                log_path = recordings_dir / f"transcription_log_{date_only}.txt"
                with open(log_path, 'a', encoding='utf-8') as f:
                    time_only = datetime.now().strftime("%H:%M:%S")
                    f.write(f"\n[{time_only}] {get_mode_name(current_mode)} (segment)\n{text}\n")
    
    threading.Thread(target=_process, daemon=True).start()


def do_stop_and_process():
    """Stop and process recording"""
    global recording, current_mode
    
    # Check if Settings window has synced a different mode
    # BUT skip if indicator override is active (user changed mode via indicator)
    if not indicator_override:
        synced = get_synced_mode()
        if synced and synced != current_mode:
            print(f"📝 Mode synced from Settings: {synced}")
            current_mode = synced
    else:
        debug_log(f"do_stop_and_process: SKIPPING sync (indicator_override=True, using {current_mode})")
    
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
        # Auto-translate if enabled in mode settings
        text = auto_translate(text, current_mode)
    
    # Check save_audio setting from config (reload to get current value)
    import json
    config_path = SCRIPT_DIR / "config.json"  # FIXED: was CONFIG_PATH (undefined)
    try:
        with open(config_path, 'r', encoding='utf-8-sig') as f:  # utf-8-sig handles BOM
            current_cfg = json.load(f)
        save_audio = current_cfg.get('global', {}).get('save_audio', False)
        print(f"[DEBUG] save_audio = {save_audio}")
    except Exception as e:
        print(f"[DEBUG] save_audio error: {e}")
        save_audio = False
    if save_audio:
        # Copy to recordings folder with timestamp
        import shutil
        saved_path = recordings_dir / f"recording_{timestamp}.wav"
        try:
            shutil.copy(tmp_path, saved_path)
            print(f"💾 Saved: {saved_path.name}")
        except Exception as e:
            print(f"❌ Save failed: {e}")
    
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
    
    # ESC to cancel current recording (not exit!)
    if key == pynput_keyboard.Key.esc:
        if recording:
            recording = False
            # Clear audio queue
            while not audio_queue.empty():
                try:
                    audio_queue.get_nowait()
                except:
                    pass
            print("⏹️ Recording cancelled")
            if indicator:
                indicator.hide()


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
                """Switch to next mode (click on indicator) - TEMPORARY for this session"""
                global current_mode, indicator_override
                idx = MODE_ORDER.index(current_mode) if current_mode in MODE_ORDER else 0
                next_idx = (idx + 1) % len(MODE_ORDER)
                new_mode = MODE_ORDER[next_idx]
                current_mode = new_mode
                indicator_override = True  # Prevent watcher from overwriting this change
                print(f"\n🔄 Mode: {get_mode_name(new_mode)} (session override)")
                debug_log(f"next_mode: switched to {new_mode} (indicator_override=True)")
                
                # NOTE: Do NOT save to config.json - indicator changes are TEMPORARY
                # Next recording will read from Settings tab (config.json active_mode)
                
                # Write to mode_sync.txt for tray sync (temporary)
                try:
                    MODE_SYNC_FILE.write_text(new_mode, encoding='utf-8')
                except:
                    pass
                if indicator:
                    indicator.update_mode(get_mode_name(new_mode))
                if tray:
                    tray.set_mode(new_mode)
            
            indicator = FloatingIndicator(max_duration=MAX_DURATION, on_mode_click=next_mode)
            indicator.run_in_thread()
        except Exception as e:
            print(f"⚠️ Indicator disabled: {e}")
    
    # Start mode sync watcher - polls config.json to sync with Settings
    def mode_sync_watcher():
        """Poll config.json and update all components when Settings changes mode"""
        global current_mode, indicator_override
        # Start with current mode from file if exists
        initial_synced = get_synced_mode()
        if initial_synced:
            current_mode = initial_synced
            print(f"[MODE SYNC] Initial mode from file: {initial_synced}")
        
        last_synced_mode = current_mode
        while True:
            try:
                # Skip syncing if indicator override is active (user changed mode via indicator)
                if indicator_override:
                    debug_log(f"watcher: SKIPPING (indicator_override=True)")
                    time.sleep(0.5)
                    continue
                
                synced = get_synced_mode()
                if synced and synced != last_synced_mode:
                    debug_log(f"watcher: OVERWRITING current_mode from {current_mode} to {synced}")
                    current_mode = synced
                    last_synced_mode = synced
                    mode_display = get_mode_name(synced)
                    print(f"[MODE SYNC] Mode changed to: {mode_display} ({synced})")
                    # Update floating indicator
                    if indicator:
                        indicator.update_mode(mode_display)
                    # Update tray
                    if tray:
                        tray.set_mode(synced)
            except Exception as e:
                print(f"[MODE SYNC] Error: {e}")
            time.sleep(0.5)
    
    sync_thread = threading.Thread(target=mode_sync_watcher, daemon=True)
    sync_thread.start()
    print("🔄 Mode sync watcher started")
    
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

