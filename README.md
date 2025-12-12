# 🎙️ VoiceGrab

<div align="center">

[![Windows](https://img.shields.io/badge/Platform-Windows%2010%2F11-0078D6?logo=windows)](https://www.microsoft.com/windows)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![Groq](https://img.shields.io/badge/API-Groq%20Whisper-FF6B6B?logo=openai)](https://console.groq.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Voice-to-Text Bridge for AI & Any Application**

*Record voice → Get text instantly → Paste anywhere*

[🚀 Quick Start](#-quick-start) • [📖 Features](#-features) • [⚙️ Settings](#%EF%B8%8F-settings) • [❓ FAQ](#-faq)

</div>

---

## 🎯 What is VoiceGrab?

VoiceGrab is a **lightweight Windows utility** that converts your voice to text using Groq's Whisper API. Press a hotkey, speak, and text is automatically typed into any active window — ChatGPT, VS Code, Word, Slack, anywhere!

### Why VoiceGrab?

| Problem | Solution |
|---------|----------|
| Typing is slow | **Speak 3x faster** than typing |
| AI prompts are long | **Voice input** for ChatGPT, Claude, Copilot |
| Coding with voice | **Dictate comments**, docs, commit messages |
| Multilingual input | **Auto-detect** or set language per mode |

---

## ✨ Features

- 🎤 **One-Click Recording** — Press `Right Alt` to record
- ⚡ **Instant Transcription** — Powered by Groq Whisper (FREE tier!)
- 📋 **Auto-Paste** — Text goes directly to active window
- 🔄 **5 Modes** — AI Chat, Code, Docs, Notes, Custom
- 🛡️ **Profanity Filter** — Optional censorship per mode
- 🧹 **Filler Cleanup** — Remove "um", "uh", "like" automatically
- 🖥️ **System Tray** — Runs silently in background
- ⚙️ **Modern UI** — Beautiful settings panel

---

## 🚀 Quick Start

### 1. Download
```bash
git clone https://github.com/consulfedor/VoiceGrab.git
cd VoiceGrab
```

### 2. Get Free API Key
👉 [console.groq.com/keys](https://console.groq.com/keys) — Create account, generate key

### 3. Run
Double-click **`VoiceGrab.bat`**

- First launch: Enter API key, click **Install Deps**, then **Run**
- That's it! VoiceGrab is now in your system tray 🎉

### 4. Use
| Action | How |
|--------|-----|
| **Start/Stop Recording** | Press `Right Alt` |
| **Change Mode** | Right-click tray → Mode |
| **Open Settings** | Right-click tray → Settings |
| **Exit** | Right-click tray → Exit |

---

## 📦 Installation

### Requirements
- **Windows 10/11**
- **Python 3.10+** — [Download](https://www.python.org/downloads/windows/)
  > ⚠️ Check **"Add Python to PATH"** during installation!
- **Microphone**

### Manual Installation
```powershell
# Clone repository
git clone https://github.com/consulfedor/VoiceGrab.git
cd VoiceGrab

# Install dependencies
pip install -r requirements.txt

# Run
python voicegrab.py
```

### Portable Installation
Just copy these 7 files to any folder:
```
VoiceGrab.bat
VoiceGrab.ps1
voicegrab.py
floating_indicator.py
system_tray.py
config_schema.py
requirements.txt
```

---

## ⚙️ Settings

### Global Settings
| Setting | Default | Description |
|---------|---------|-------------|
| **Hotkey** | Right Alt | Global recording key |
| **Max Duration** | 180s | Auto-sends at limit (no need to stop!) |
| **Save Audio** | OFF | Keep audio files |
| **Log Texts** | ON | Save all transcriptions to log file |

### Per-Mode Settings
Each mode has independent settings:

| Setting | Description |
|---------|-------------|
| **Input Mode** | Toggle (click-click) or Hold (press & hold) |
| **Language** | Auto-detect or force specific language |
| **Temperature** | 0.0 = precise, 1.0 = creative |
| **Profanity Filter** | Replace bad words with *** |
| **Filler Cleanup** | Remove "um", "uh", "like", etc. |
| **Prompt** | Context hint for Whisper |

### 5 Modes
| Mode | Use Case | Profanity | Filler Cleanup |
|------|----------|-----------|----------------|
| 🤖 **AI Chat** | ChatGPT prompts | OFF | ON |
| 💻 **Code** | Programming | ON | ON |
| 📋 **Docs** | Documentation | ON | ON |
| 📝 **Notes** | Quick notes | OFF | ON |
| 💬 **Chat** | Free conversation | OFF | OFF |

---

## 🔧 Configuration

All settings are stored in `config.json`:

```json
{
  "api": { "key": "gsk_..." },
  "global": {
    "hotkey": "alt gr",
    "max_duration": 180,
    "save_audio": false,
    "log_texts": true
  },
  "modes": {
    "ai": { "language": "auto", "temperature": 0.0, ... },
    "code": { "profanity_filter": true, ... }
  }
}
```

---

## ❓ FAQ

<details>
<summary><b>Q: Is it really free?</b></summary>

Yes! Groq offers a generous FREE tier:
- ~10 requests per minute
- ~25,000 audio seconds per day
- No credit card required

</details>

<details>
<summary><b>Q: Which languages are supported?</b></summary>

Whisper supports 50+ languages including:
- English, Russian, Ukrainian, Turkish
- Spanish, French, German, Chinese, Japanese
- Auto-detection works great for most languages

</details>

<details>
<summary><b>Q: Why Right Alt and not another key?</b></summary>

Right Alt (AltGr) is ideal because:
- Rarely used in applications
- Easy to reach with thumb
- Works globally in any window

You can change it in Settings!

</details>

<details>
<summary><b>Q: Does it work offline?</b></summary>

No, VoiceGrab requires internet connection to send audio to Groq API. Audio is processed in cloud and deleted immediately after transcription.

</details>

<details>
<summary><b>Q: Can I use it for coding?</b></summary>

Absolutely! Use **Code** mode:
- Profanity filter ON (clean code comments)
- Filler cleanup ON (no "um" in your code)
- Low temperature (0.0) for precise terms

</details>

---

## 🗂️ File Structure

```
VoiceGrab/
├── VoiceGrab.bat           # 🚀 Entry point (double-click me!)
├── VoiceGrab.ps1           # Settings UI
├── voicegrab.py            # Main service
├── floating_indicator.py   # Recording indicator
├── system_tray.py          # Tray icon
├── config_schema.py        # Default config
├── config.json             # Your settings (auto-created)
├── requirements.txt        # Python dependencies
├── recordings/             # Audio files (if enabled)
└── Doc/                    # Documentation
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Python not found | Reinstall Python, check "Add to PATH" |
| No microphone | Check Windows sound settings |
| Hotkey not working | Make sure VoiceGrab is in tray |
| Rate limit exceeded | Wait 1 minute, or switch Whisper model |
| Text not pasting | Focus target window before recording |

---

## 📄 License

MIT License — free for personal and commercial use.

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

---

## ⭐ Star History

If VoiceGrab helps you, give it a ⭐ on GitHub!

---

<div align="center">

**Made with ❤️ for the AI era**

[Report Bug](https://github.com/consulfedor/VoiceGrab/issues) • [Request Feature](https://github.com/consulfedor/VoiceGrab/issues)

</div>
