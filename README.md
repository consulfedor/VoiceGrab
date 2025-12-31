# 🎙️ VoiceGrab

<div align="center">

[![Windows](https://img.shields.io/badge/Platform-Windows%2010%2F11-0078D6?logo=windows)](https://www.microsoft.com/windows)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![Groq](https://img.shields.io/badge/API-Groq%20Whisper-FF6B6B?logo=openai)](https://console.groq.com)
[![Version](https://img.shields.io/badge/Version-2.3.1-blueviolet)](https://github.com/YourUsername/VoiceGrab)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Voice-to-Text Bridge for AI & Any Application**

*Record voice → Get text instantly → Paste anywhere*

[🚀 Quick Start](#-quick-start) • [📖 Features](#-features) • [⚙️ Settings](#%EF%B8%8F-settings) • [❓ FAQ](#-faq)

</div>

---

## 🎯 What is VoiceGrab?

VoiceGrab is a **lightweight Windows utility** that converts your voice to text using cloud APIs. Press a hotkey, speak, and text is automatically typed into any active window — ChatGPT, VS Code, Word, Slack, anywhere!

### Why VoiceGrab?

| Problem | Solution |
|---------|----------|
| Typing is slow | **Speak 3x faster** than typing |
| AI prompts are long | **Voice input** for ChatGPT, Claude, Copilot |
| Coding with voice | **Dictate comments**, docs, commit messages |
| Multilingual | **57 languages** + auto-translation |
| **Gaming chat** | **Voice-to-chat** in CS2, Dota 2, LoL, WoW |

---

## ✨ Features

### Core
- 🎤 **One-Click Recording** — Press `Right Ctrl` (configurable)
- ♾️ **Unlimited Recording** — Auto-segments every 3 min, no interruption
- 📋 **Auto-Paste** — Text goes directly to active window (and clipboard)

### Transcription
- ⚡ **Groq Whisper API** — Fast, accurate transcription (FREE tier available)
- 🧹 **Filler Cleanup** — Remove "um", "uh", "like" automatically
- 👻 **Hallucination Filter** — Remove Whisper AI "ghost" phrases

### Translation (Per Mode)
- 🌐 **Auto-Translate** — 3 modes: Off / Replace / Append
- 🔤 **DeepL Integration** — Quality translation with reverse check
- 🌍 **Groq AI Translate** — Fast AI-powered translation

### Tools
- 🔤 **Translator Tool** — Standalone translation with reverse quality check
- 📁 **Batch Transcription** — via [Google Speech-to-Text](https://cloud.google.com/speech-to-text) (external)
- 📄 **Document Converter** — MD↔DOCX conversion (Pandoc)

### UI
- 🖥️ **System Tray** — Runs silently in background
- 💡 **Floating Indicator** — Shows recording status + current mode
- ⚙️ **Modern Settings** — Dark theme, all settings per mode

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

- First launch: Enter API key → click **Install Deps** → **Run**
- VoiceGrab appears in system tray 🎉

### 4. Use
| Action | How |
|--------|-----|
| **Start/Stop Recording** | Press `Right Ctrl` |
| **Switch Mode** | Click `◀ Mode ▶` on floating indicator |
| **Open Settings** | Right-click tray → Settings |
| **Exit** | Right-click tray → Exit |

### Mode Priority (Simple)

1. **Start Recording** → uses mode from Settings UI
2. **Click mode on Indicator** → switches mode for THIS session only
3. **Next Recording** → reads mode from Settings again

> 💡 **Tip:** Text is always in clipboard! **Ctrl+V** to paste.

---

## ⚙️ Settings

### Configuration Architecture

```
┌─────────────────────┐      ┌─────────────────────┐
│  config_default.json │  →  │     config.json      │
│  (factory defaults)  │      │   (your settings)    │
└─────────────────────┘      └─────────────────────┘
```

- **First launch**: defaults are copied to your config.json
- **Reset Mode**: restores that mode from defaults
- **All changes**: saved to config.json automatically

### Global Settings

| Setting | Default | Description |
|---------|---------|-------------|
| **Hotkey** | Right Ctrl | Global recording trigger |
| **Max Duration** | 180s | Auto-sends at limit |
| **Save Audio** | OFF | Keep audio files in `recordings/` |
| **Default Mode** | Selectable | Mode used at startup |

### Per-Mode Settings (5 Modes)

**Each mode is fully customizable:**

| Setting | Options | Description |
|---------|---------|-------------|
| **Mode Name** | Custom text | Rename tab (e.g., "Ru-TR") |
| **Language** | 57 languages | Primary speech language |
| **Temperature** | 0.0 - 1.0 | 0 = precise, 1 = creative |
| **Input Mode** | Toggle / Hold | Click-click or press-hold |
| **Transcription Model** | Large-v3 / Turbo / Distil | Speed vs accuracy |
| **Filler Cleanup** | ON/OFF | Remove "um", "uh", etc. |
| **Hallucination Filter** | ON/OFF | Remove AI ghost phrases |
| **Phrases to Remove** | Custom list | Add your own hallucinations |
| **Prompt** | Custom text | Context hint for Whisper |
| **Auto-Translate** | Off / Replace / Append | Translation mode |
| **Translate Language** | EN, RU, TR, etc. | Target language |
| **Translate Engine** | Groq / DeepL | Translation service |

### Default Modes

| Mode | Name | Use Case |
|------|------|----------|
| 🤖 **ai** | AI Chat | ChatGPT prompts, coding |
| 💻 **code** | Code | Programming, technical |
| 📋 **docs** | Docs | Documentation |
| 📝 **notes** | Notes | Quick notes, ideas |
| 💬 **chat** | Chat | Casual conversation |

---

## 📦 Installation

### Requirements
- **Windows 10/11**
- **Python 3.10+** — [Download](https://www.python.org/downloads/windows/)
  > ⚠️ Check **"Add Python to PATH"** during installation!
- **Microphone**

### Portable Installation (10 files)

Copy these files to any folder:
```
VoiceGrab.bat           # 🚀 Entry point
VoiceGrab.ps1           # Settings UI
voicegrab.py            # Main service
floating_indicator.py   # Recording indicator
system_tray.py          # Tray icon
config_schema.py        # Config loader
config_default.json     # Factory defaults
config.json             # Your settings (auto-created)
requirements.txt        # Dependencies
recordings/             # Audio (if enabled)
```

---

## 📋 Changelog

### v2.3.1 (2025-12-31)
- 🛠️ **NULL Eval Fix** — Fixed parentWindow.eval NULL error at startup
- 🧹 **Debug Logging Off** — Removed verbose DEBUG output from console

### v2.3.0 (2025-12-31)
- 🔧 **Settings Fix** — Prompt, Phrases to Remove now save correctly
- 📝 **Single Default Config** — `config_default.json` is the only source of defaults

### v2.0.0 - v2.2.0 (2025-12)
- 🏷️ **Custom Mode Names** — Rename tabs
- 💡 **Tab Tooltips** — Hover to see mode config
- ⚙️ **Mode Priority System** — Settings = source of truth
- 🎨 **"Halving Style" UI** — Modern button layout

### v1.5.0 (2025-12)
- 🌐 **Auto-Translate** — Per-mode translation (Groq/DeepL)
- 🔤 **Translator Tool** — Standalone translation with reverse check
- 📋 **Copy All / Clear All** — Translator bulk operations

### v1.4.0 (2024-12)
- 📁 **Batch Transcription** — `batch_transcribe.py`
- 📄 **Document Converter** — MD↔DOCX

### v1.3.0 (2024-12)
- 🌍 **57 Languages** — Expanded language support
- 🐛 **Bug Fixes** — Settings persistence, audio saving

---

## ❓ FAQ

<details>
<summary><b>Is it really free?</b></summary>

Yes! Groq offers a generous FREE tier:
- ~10 requests per minute
- ~25,000 audio seconds per day
- No credit card required

</details>

<details>
<summary><b>Which languages are supported?</b></summary>

Whisper supports 57 languages including:
Russian, English, Ukrainian, Turkish, Spanish, French, German, Chinese, Japanese.
Auto-detection works great for most languages.

</details>

<details>
<summary><b>Does it work offline?</b></summary>

No, VoiceGrab requires internet to send audio to APIs. Audio is processed in cloud and deleted immediately.

</details>

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Python not found | Reinstall Python, check "Add to PATH" |
| No microphone | Check Windows sound settings |
| Hotkey not working | Make sure VoiceGrab is in tray |
| Rate limit exceeded | Wait 1 minute, or use different model |
| Text not pasting | Focus target window before recording |

---

## 🚀 Roadmap

| Phase | Feature | Status |
|-------|---------|--------|
| 6 | **Packaging** — Single .exe installer | 📋 Planned |
| 7 | **Quick Actions** — Translate selected text | 📋 Planned |

---

## 📄 License

MIT License — free for personal and commercial use.

---

<div align="center">

**Made with ❤️ for the AI era**

</div>
