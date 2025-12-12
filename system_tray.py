"""
VoiceGrab System Tray
Tray icon with settings access and mode switching
"""

import os
import sys
import webbrowser
import threading
from pathlib import Path

try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    print("⚠️ pystray/pillow not installed. Tray disabled.")


SCRIPT_DIR = Path(__file__).parent.absolute()


def create_icon_image(recording=False, mode="ai"):
    """Create a simple icon image"""
    # 64x64 icon
    size = 64
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Background circle
    if recording:
        # Red when recording
        draw.ellipse([4, 4, size-4, size-4], fill='#e74c3c')
    else:
        # Blue when ready
        draw.ellipse([4, 4, size-4, size-4], fill='#3498db')
    
    # Inner circle (microphone symbol)
    inner = 16
    draw.ellipse([inner, inner, size-inner, size-inner], fill='white')
    
    return image


class SystemTray:
    """System tray icon with menu"""
    
    def __init__(self, on_settings=None, on_mode_change=None, on_exit=None):
        self.on_settings = on_settings
        self.on_mode_change = on_mode_change
        self.on_exit = on_exit
        self.icon = None
        self.recording = False
        self.current_mode = "ai"
        
        if not TRAY_AVAILABLE:
            return
        
        self._create_icon()
    
    def _create_icon(self):
        """Create the tray icon"""
        image = create_icon_image(self.recording, self.current_mode)
        
        menu = pystray.Menu(
            pystray.MenuItem("🎤 VoiceGrab", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("⚙️ Settings", self._open_settings),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Mode:", None, enabled=False),
            pystray.MenuItem("  🤖 AI Chat", lambda icon, item: self._set_mode("ai"), 
                           checked=lambda item: self.current_mode == "ai"),
            pystray.MenuItem("  💻 Code", lambda icon, item: self._set_mode("code"),
                           checked=lambda item: self.current_mode == "code"),
            pystray.MenuItem("  📋 Docs", lambda icon, item: self._set_mode("docs"),
                           checked=lambda item: self.current_mode == "docs"),
            pystray.MenuItem("  📝 Notes", lambda icon, item: self._set_mode("notes"),
                           checked=lambda item: self.current_mode == "notes"),
            pystray.MenuItem("  💬 Chat", lambda icon, item: self._set_mode("chat"),
                           checked=lambda item: self.current_mode == "chat"),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("❌ Exit", self._exit)
        )
        
        self.icon = pystray.Icon("VoiceGrab", image, "VoiceGrab", menu)
    
    def _open_settings(self, icon=None, item=None):
        """Open main settings window (VoiceGrab.ps1) - closes existing first"""
        # Close any existing VoiceGrab Settings windows first
        self._close_settings_windows()
        
        launcher_path = SCRIPT_DIR / "VoiceGrab.ps1"
        if launcher_path.exists():
            # Launch PowerShell with the settings UI
            import subprocess
            subprocess.Popen(
                ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(launcher_path)],
                cwd=str(SCRIPT_DIR)
            )
        else:
            # Fallback: open config.json
            config_path = SCRIPT_DIR / "config.json"
            if config_path.exists():
                os.startfile(str(config_path))
    
    def _close_settings_windows(self):
        """Close any open VoiceGrab PowerShell Settings windows"""
        import ctypes
        from ctypes import wintypes
        
        EnumWindows = ctypes.windll.user32.EnumWindows
        GetWindowTextW = ctypes.windll.user32.GetWindowTextW
        GetClassNameW = ctypes.windll.user32.GetClassNameW
        PostMessageW = ctypes.windll.user32.PostMessageW
        EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        WM_CLOSE = 0x0010
        
        def callback(hwnd, _):
            title = ctypes.create_unicode_buffer(256)
            classname = ctypes.create_unicode_buffer(256)
            GetWindowTextW(hwnd, title, 256)
            GetClassNameW(hwnd, classname, 256)
            
            # Only close windows that are specifically VoiceGrab launcher
            # Check for Windows Forms class (PowerShell WebBrowser control)
            is_voicegrab = 'VoiceGrab' in title.value
            is_forms_window = 'WindowsForms' in classname.value
            
            if is_voicegrab and is_forms_window:
                PostMessageW(hwnd, WM_CLOSE, 0, 0)
            return True
        
        try:
            EnumWindows(EnumWindowsProc(callback), 0)
        except:
            pass
    
    def _set_mode(self, mode):
        """Change mode"""
        self.current_mode = mode
        if self.on_mode_change:
            self.on_mode_change(mode)
        self._update_icon()
    
    def _exit(self, icon=None, item=None):
        """Exit application"""
        if self.on_exit:
            self.on_exit()
        if self.icon:
            self.icon.stop()
    
    def _update_icon(self):
        """Update icon image"""
        if self.icon:
            self.icon.icon = create_icon_image(self.recording, self.current_mode)
    
    def set_recording(self, recording: bool):
        """Update recording state"""
        self.recording = recording
        self._update_icon()
    
    def set_mode(self, mode: str):
        """Update mode externally"""
        self.current_mode = mode
        self._update_icon()
    
    def run(self):
        """Run tray icon (blocking)"""
        if self.icon:
            self.icon.run()
    
    def run_detached(self):
        """Run tray in separate thread"""
        if self.icon:
            thread = threading.Thread(target=self.icon.run, daemon=True)
            thread.start()
            return thread
        return None
    
    def stop(self):
        """Stop tray icon"""
        if self.icon:
            self.icon.stop()


# Singleton
_tray_instance = None

def get_tray() -> SystemTray:
    global _tray_instance
    if _tray_instance is None:
        _tray_instance = SystemTray()
    return _tray_instance


if __name__ == "__main__":
    # Test
    def on_settings():
        print("Opening settings...")
    
    def on_mode(mode):
        print(f"Mode changed to: {mode}")
    
    def on_exit():
        print("Exiting...")
    
    tray = SystemTray(on_settings, on_mode, on_exit)
    print("Tray running. Right-click icon to see menu.")
    tray.run()
