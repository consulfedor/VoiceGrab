# 🎙️ VoiceGrab

<div align="center">

[![Windows](https://img.shields.io/badge/Platform-Windows%2010%2F11-0078D6?logo=windows)](https://www.microsoft.com/windows)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![Groq](https://img.shields.io/badge/API-Groq%20Whisper-FF6B6B?logo=openai)](https://console.groq.com)
[![Version](https://img.shields.io/badge/Version-2.3.0-blueviolet)](https://github.com/YourUsername/VoiceGrab)
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
| Multilingual input | **57 languages** supported |
| **Gaming chat** | **Voice-to-chat** in CS2, Dota 2, LoL, WoW, Valorant, Overwatch 2 |

> 🎮 **Works with:** #CS2 #CounterStrike #Dota2 #LeagueOfLegends #WoW #Valorant #Overwatch2 #PUBG #Fortnite #Apex #R6Siege #Minecraft #Roblox #GTA5 #WoT #Lineage2

---

## ✨ Features

- 🎤 **One-Click Recording** — Press `Right Ctrl` to record
- ♾️ **Unlimited Recording** — Auto-segments every 3 min, no interruption!
- ⚡ **Dual API Support** — Groq Whisper (fast) + Gemini (AI analysis)
- 📁 **Batch Transcription** — Transcribe any audio file (MP3, WAV, OGG, etc.)
- 📋 **Auto-Paste** — Text goes directly to active window
- 🔄 **5 Modes** — AI Chat, Code, Docs, Notes, Custom
- 🛡️ **Profanity Filter** — Optional censorship per mode
- 🧹 **Filler Cleanup** — Remove "um", "uh", "like" automatically
- 👻 **Hallucination Filter** — Remove Whisper "ghost" phrases
- 🌐 **Auto-Translate** — Translate transcription to any language (Groq/Gemini/DeepL)
- 🔤 **Translator Tool** — Standalone translation with reverse quality check
- 📄 **Document Converter** — MD↔DOCX conversion (Pandoc)
- 🖥️ **System Tray** — Runs silently in background
- ⚙️ **Modern UI** — Beautiful dark settings panel, "Halving Style" button layout
- 💾 **Settings Persistence** — All preferences saved to config.json

---

## 🚀 Quick Start

### 1. Download
```bash
git clone https://github.com/YourUsername/VoiceGrab.git
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
| **Start/Stop Recording** | Press `Right Ctrl` |
| **Switch Mode (while recording)** | Click `◀ Mode ▶` on indicator |
| **Open Settings** | Right-click tray → Settings |
| **Exit** | Right-click tray → Exit |

### 🔄 Mode Priority Logic

```
┌─────────────────┐   Read at start   ┌─────────────────┐
│  Settings Tab   │ ───────────────▶  │    Recording    │
│  (config.json)  │   Source of Truth │  (Floating UI)  │
└─────────────────┘                   └─────────────────┘
                                            │ Click
                                            ▼ (temporary)
                                    ┌─────────────────┐
                                    │ Session Override│
                                    │ (memory only)   │
                                    └─────────────────┘
```

- **Settings Tab** = source of truth for NEW recordings
- **Floating Indicator** = temporary override for CURRENT session
- **Next recording** will read from Settings again

> 💡 **Tip:** Text is always in clipboard! **Ctrl+V** to paste.  
> **Win+V** opens emoji picker, clipboard history & special symbols.

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
git clone https://github.com/YourUsername/VoiceGrab.git
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
| **Hotkey** | Right Ctrl | Global recording key |
| **Max Duration** | 180s | Auto-sends at limit (no need to stop!) |
| **Save Audio** | OFF | Keep audio files |
| **Log Texts** | ON | Save all transcriptions to log file |

### Per-Mode Settings
Each mode has independent settings:

| Setting | Description |
|---------|-------------|
| **Input Mode** | Toggle (click-click) or Hold (press & hold) |
| **Language** | 57 languages supported (English default) |
| **Temperature** | 0.0 = precise, 1.0 = creative |
| **Profanity Filter** | Replace bad words with *** |
| **Filler Cleanup** | Remove "um", "uh", "like", etc. |
| **Hallucination Filter** | Remove AI "ghost" phrases (customizable list) |
| **Transcription Provider** | Groq (Whisper) or Gemini per mode |
| **Transcription Model** | whisper-large-v3, distil-v3-en, turbo |
| **Auto-Translate** | Off / Replace / Append |
| **Translate Language** | Target language for auto-translate |
| **Translate Engine** | Groq AI / Gemini / DeepL |
| **Prompt** | Context hint for Whisper |

### 5 Modes
| Mode | Use Case | Profanity | Filler Cleanup |
|------|----------|-----------|----------------|
| 🤖 **AI Chat** | ChatGPT prompts | OFF | ON |
| 💻 **Code** | Programming | ON | ON |
| 📋 **Docs** | Documentation | ON | ON |
| 📝 **Notes** | Quick notes | OFF | ON |
| 💬 **Chat** | Free conversation | OFF | OFF |

### Mode Tab Tooltips
Hover over mode tabs to see settings summary:

| Tooltip | Meaning |
|---------|---------|
| `RU @Groq` | Russian, Groq transcription, no translate |
| `EN @Gemini` | English, Gemini transcription, no translate |
| `RU @Groq \| ON→EN @DeepL` | Russian, Groq transc., translate ON to English via DeepL |
| `RU @Gemini \| Append→EN @Groq` | Russian, Gemini, Append translation to English via Groq |

---

## 🔧 Configuration

All settings are stored in `config.json`:

```json
{
  "api": { "key": "gsk_..." },
  "global": {
    "hotkey": "Right Ctrl",
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
<summary><b>Q: Why Right Ctrl and not another key?</b></summary>

Right Ctrl (AltGr) is ideal because:
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

## 📋 Changelog

### v1.5.0 (2025-12-29)
- 🌐 **Auto-Translate** — Per-mode translation with Groq AI, Gemini, or DeepL
- 🔤 **Translator Tool** — Standalone translation with reverse quality check
- 📋 **Copy All / Clear All** — Translator buttons for bulk operations
- 🏷️ **Custom Mode Names** — Rename tabs with custom short names
- 💡 **Tab Tooltips** — Hover to see mode config (e.g., `RU @Groq | Append→EN @DeepL`)
- 🔧 **Tools Settings Persistence** — Translator language/engine saved
- 💡 **Ctrl+V Tip** — Reminder that text is always in clipboard

### v1.4.0 (2024-12-22)
- 🤖 **Gemini API Support** — AI-powered analysis with speakers, emotions, timestamps
- 📁 **Batch Transcription** — `batch_transcribe.py` for transcribing audio files
- 📄 **Document Converter** — MD↔DOCX conversion with Pandoc (in Tools)
- 🔧 **Dual Provider** — Use Groq (fast) or Gemini (smart) per task

### v1.3.0 (2024-12-15)
- 🌍 **Language Support Expanded** — 57 languages with improved detection
- 🔧 **Bug Fixes:**
  - Fixed settings not persisting (Max Duration, Filler Words, etc.)
  - Fixed audio files not saving to `recordings/` folder
  - Fixed UTF-8 BOM encoding issues in config

---

## 🚀 Roadmap

| Phase | Feature | Status |
|-------|---------|--------|
| 2 | **WebView2 UI** — Modern scroll, ES6+ | 📋 Planned |
| 3 | **TTS (Text-to-Speech)** — Voice output | 📋 Planned |
| 4 | **Screen OCR** — Read text from screen | 📋 Planned |
| 5 | **Realtime Translation** — Live dialog/screen translate | 📋 Planned |
| 6 | **Packaging** — Single .exe installer | 📋 Planned |
| ? | **Story Mode** — Pause recording, single WAV file (optional) | 💡 Idea |

> **Note (v2.3):**
> - **Mode Sync Fix** — Settings → Indicator → Processing chain works correctly
> - **Mode Priority** — Settings = source of truth; Indicator = session override only
> - **Dropdown Sync** — Startup Mode dropdown updates when mode is renamed
> - **Single Default Config** — `config_default.json` is the only source of defaults
> - **Auto-Cache Cleanup** — EXIT button clears `__pycache__` for fresh code
> - **Halving Style UI** — Button layout: Run+Settings → Run+Tray → Transcribe → EXIT

---

## 📁 Project Structure (10 core files)

```
VoiceGrab/
├── VoiceGrab.bat           # 🚀 Entry point (double-click me!)
├── VoiceGrab.ps1           # Settings UI (PowerShell + HTA)
├── voicegrab.py            # Main service
├── floating_indicator.py   # Recording indicator
├── system_tray.py          # Tray icon
├── config_schema.py        # Config loader
├── config_default.json     # Default settings (single source of truth) ← NEW
├── config.json             # Your settings (auto-created)
├── requirements.txt        # Python dependencies
└── recordings/             # Audio files (if enabled)
```

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

[Report Bug](https://github.com/YourUsername/VoiceGrab/issues) • [Request Feature](https://github.com/YourUsername/VoiceGrab/issues)

</div>
