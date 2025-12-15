"""
VoiceGrab Floating Indicator - Thread-Safe Version
Uses queue pattern for safe tkinter updates from any thread
"""

import tkinter as tk
import threading
import queue
import time


class FloatingIndicator:
    """Thread-safe floating indicator for recording status"""
    
    def __init__(self, max_duration=180, on_mode_click=None):
        self.max_duration = max_duration
        self.on_mode_click = on_mode_click  # Callback for mode switching
        self.root = None
        self.canvas = None
        self.dot_label = None
        self.label = None
        self.time_label = None
        self.mode_label = None
        
        # Thread-safe command queue
        self._cmd_queue = queue.Queue()
        
        # State
        self.recording = False
        self.start_time = 0
        self.mode_name = ""
        self.is_visible = False
        
        # Dimensions - wide enough for mode name
        self.width = 320
        self.height = 60
    
    def _create_window(self):
        """Create the indicator window"""
        self.root = tk.Tk()
        self.root.title("VoiceGrab")
        
        # Window properties
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.92)
        self.root.overrideredirect(True)
        
        # Position: top-center
        screen_width = self.root.winfo_screenwidth()
        x = (screen_width - self.width) // 2
        y = 25
        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")
        
        # Dark theme
        self.root.configure(bg='#1a1a2e')
        
        # Main frame
        frame = tk.Frame(self.root, bg='#1a1a2e', padx=12, pady=8)
        frame.pack(fill='both', expand=True)
        
        # Status row
        status_frame = tk.Frame(frame, bg='#1a1a2e')
        status_frame.pack(fill='x')
        
        # Separate blinking dot from static text - FIXED WIDTH to prevent shifting
        self.dot_label = tk.Label(
            status_frame,
            text="🎤",
            font=('Segoe UI', 12, 'bold'),
            fg='#ffffff',
            bg='#1a1a2e',
            width=2,  # Fixed width in characters
            anchor='center'
        )
        self.dot_label.pack(side='left')
        
        self.label = tk.Label(
            status_frame,
            text=" Ready",
            font=('Segoe UI', 12, 'bold'),
            fg='#ffffff',
            bg='#1a1a2e'
        )
        self.label.pack(side='left')
        
        self.time_label = tk.Label(
            status_frame,
            text="",
            font=('Segoe UI', 11),
            fg='#888888',
            bg='#1a1a2e'
        )
        self.time_label.pack(side='right')
        
        # Mode label - clickable to switch modes
        self.mode_label = tk.Label(
            frame,
            text="",
            font=('Segoe UI', 9),
            fg='#58a6ff',
            bg='#1a1a2e',
            cursor='hand2'  # Hand cursor to show it's clickable
        )
        self.mode_label.pack(anchor='center')  # Centered below Recording
        self.mode_label.bind('<Button-1>', self._on_mode_click)
        
        # Progress bar canvas - thicker for visibility
        self.canvas = tk.Canvas(
            frame,
            height=10,
            bg='#2d2d44',
            highlightthickness=0
        )
        self.canvas.pack(fill='x', pady=(6, 0))
        
        # Draggable (except mode_label which is for clicking)
        for w in [frame, self.dot_label, self.label, self.time_label]:
            w.bind('<Button-1>', self._start_drag)
            w.bind('<B1-Motion>', self._drag)
        
        # Hide initially
        self.root.withdraw()
        
        # Start command queue processor
        self._process_queue()
    
    def _process_queue(self):
        """Process commands from queue (thread-safe)"""
        try:
            while True:
                cmd, args = self._cmd_queue.get_nowait()
                if cmd == 'show':
                    self._do_show(*args)
                elif cmd == 'hide':
                    self._do_hide()
                elif cmd == 'start_recording':
                    self._do_start_recording(*args)
                elif cmd == 'stop_recording':
                    self._do_stop_recording()
                elif cmd == 'show_processing':
                    self._do_show_processing()
                elif cmd == 'show_result':
                    self._do_show_result(*args)
                elif cmd == 'show_error':
                    self._do_show_error(*args)
                elif cmd == 'update_mode':
                    self._do_update_mode(*args)
                elif cmd == 'update':
                    self._do_update()
        except queue.Empty:
            pass
        
        # Update display if recording
        if self.recording and self.is_visible:
            self._do_update()
        
        # Schedule next check
        if self.root:
            self.root.after(100, self._process_queue)
    
    def _start_drag(self, event):
        self._drag_x = event.x
        self._drag_y = event.y
    
    def _drag(self, event):
        x = self.root.winfo_x() + event.x - self._drag_x
        y = self.root.winfo_y() + event.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")
    
    def _on_mode_click(self, event):
        """Handle click on mode label to switch to next mode"""
        if self.on_mode_click:
            self.on_mode_click()
    
    # === Thread-safe public methods (can be called from any thread) ===
    
    def show(self, mode_name=""):
        self._cmd_queue.put(('show', (mode_name,)))
    
    def hide(self):
        self._cmd_queue.put(('hide', ()))
    
    def start_recording(self, mode_name=""):
        self._cmd_queue.put(('start_recording', (mode_name,)))
    
    def stop_recording(self):
        self._cmd_queue.put(('stop_recording', ()))
    
    def show_processing(self):
        self._cmd_queue.put(('show_processing', ()))
    
    def show_result(self, text, duration):
        self._cmd_queue.put(('show_result', (text, duration)))
    
    def show_error(self, message):
        self._cmd_queue.put(('show_error', (message,)))
    
    def update_mode(self, mode_name):
        """Update mode display (thread-safe)"""
        self.mode_name = mode_name
        self._cmd_queue.put(('update_mode', (mode_name,)))
    
    # === Internal methods (run on main thread) ===
    
    def _do_show(self, mode_name):
        self.mode_name = mode_name
        self.root.deiconify()
        self.is_visible = True
        self._do_update()
    
    def _do_hide(self):
        self.root.withdraw()
        self.is_visible = False
    
    def _do_start_recording(self, mode_name):
        self.recording = True
        self.start_time = time.time()
        self.mode_name = mode_name
        self._do_show(mode_name)
    
    def _do_stop_recording(self):
        self.recording = False
    
    def _do_update_mode(self, mode_name):
        """Update mode display"""
        self.mode_name = mode_name
        self.mode_label.config(text=f"◀ {mode_name} ▶")
    
    def _do_show_processing(self):
        self.label.config(text="⏳ Processing...", fg='#f39c12')
        self.time_label.config(text="")
        self._draw_progress(1.0, '#f39c12')
    
    def _do_show_result(self, text, duration):
        self.label.config(text="✅ Done!", fg='#2ecc71')
        self.time_label.config(text=f"{duration:.1f}s")
        preview = text[:30] + "..." if len(text) > 30 else text
        self.mode_label.config(text=preview)
        self._draw_progress(0, '#2ecc71')
        # Auto-hide after 2s
        self.root.after(2000, self._do_hide)
    
    def _do_show_error(self, message):
        self.label.config(text="❌ Error", fg='#e74c3c')
        self.time_label.config(text="")
        self.mode_label.config(text=message[:40])
        self._draw_progress(0, '#e74c3c')
        self.root.after(3000, self._do_hide)
    
    def _do_update(self):
        """Update display (called from main thread)"""
        if not self.label:
            return
        
        if self.recording:
            elapsed = time.time() - self.start_time
            mins = int(elapsed) // 60
            secs = int(elapsed) % 60
            progress = elapsed / self.max_duration
            
            # Color based on progress (green → yellow → red at 33%/66%)
            if progress < 0.33:
                color = '#00ff88'  # Green
            elif progress < 0.66:
                color = '#ffdd00'  # Yellow
            else:
                color = '#ff4444'  # Red
            
            # Pulse effect - ONLY the dot blinks, text stays static
            pulse = "🔴" if int(elapsed * 2) % 2 == 0 else "⭕"
            
            self.dot_label.config(text=pulse, fg=color)
            self.label.config(text=" Recording", fg=color)
            remaining = max(0, self.max_duration - int(elapsed))
            # Show AutoRec countdown
            self.time_label.config(text=f"{mins}:{secs:02d} • AutoRec in {remaining}s")
            self.mode_label.config(text=f"◀ {self.mode_name} ▶")
            self._draw_progress(progress, color)
        else:
            self.dot_label.config(text="🎤", fg='#ffffff')
            self.label.config(text=" Ready", fg='#ffffff')
            self.time_label.config(text="")
            self._draw_progress(0, '#ffffff')
    
    def _draw_progress(self, progress, color):
        """Draw thick progress bar with rounded ends"""
        if not self.canvas:
            return
        self.canvas.delete('all')
        width = self.canvas.winfo_width()
        if width < 10:
            width = self.width - 24
        
        bar_height = 8  # Thicker bar
        
        # Background (rounded)
        self.canvas.create_rectangle(0, 0, width, bar_height, fill='#2d2d44', outline='')
        
        # Progress fill
        if progress > 0:
            fill_width = int(width * min(progress, 1.0))
            if fill_width > 0:
                self.canvas.create_rectangle(0, 0, fill_width, bar_height, fill=color, outline='')
    
    def run(self):
        """Run the indicator (blocks - call from main thread)"""
        self._create_window()
        self.root.mainloop()
    
    def run_in_thread(self):
        """Run in background thread"""
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        time.sleep(0.2)  # Wait for window creation
        return thread


# Singleton
_indicator = None

def get_indicator() -> FloatingIndicator:
    global _indicator
    if _indicator is None:
        _indicator = FloatingIndicator()
    return _indicator


if __name__ == "__main__":
    # Test
    indicator = FloatingIndicator()
    
    def test():
        time.sleep(1)
        indicator.start_recording("🤖 AI Chat")
        time.sleep(4)
        indicator.show_processing()
        time.sleep(1)
        indicator.show_result("Тестовый результат", 3.5)
    
    threading.Thread(target=test, daemon=True).start()
    indicator.run()
