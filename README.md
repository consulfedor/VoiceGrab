# 🎙️ VoiceGrab

<div align="center">

[**🎥 Watch 15-sec Demo**](#-demo)

[![Windows](https://img.shields.io/badge/Platform-Windows%2010%2F11-0078D6?logo=windows)](https://www.microsoft.com/windows)
[![Groq](https://img.shields.io/badge/API-Groq%20Whisper-FF6B6B?logo=openai)](https://console.groq.com)
[![Telegram](https://img.shields.io/badge/Telegram-Join%20Channel-blue?logo=telegram)](https://t.me/voicegrab_dev)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Free Voice-to-Text for Windows — No Subscription Required**

*Record voice → Get text instantly → Paste anywhere*

[🚀 Quick Start](#-quick-start) • [✨ Features](#-features) • [📥 Download](https://github.com/consulfedor/VoiceGrab/releases)

</div>

---

## ⚡ Why VoiceGrab?

VoiceGrab is a **free, open-source alternative** to Dragon NaturallySpeaking ($300) and Windows Voice Typing. Uses **Groq Whisper API** for professional-grade transcription in **57 languages**.

**Not a browser extension.** Works system-wide: **VS Code, Cursor, Slack, Word, ChatGPT, Telegram** — any Windows app.

### 🔥 Key Benefits

| You get | Why it matters |
|---------|----------------|
| **100% Free Tier** | Groq's free API = ~8 hours/day of dictation |
| **Speak 3x faster** than typing | Voice prompts for ChatGPT, Claude, Copilot |
| **Auto-Translation** | Speak Russian → Type English (DeepL/Groq) |
| **Smart Cleaning** | Removes "um", "uh" and Whisper hallucinations |
| **5 Dev Modes** | Prompts for coding, docs, notes, chat |

> **Note:** Gemini 2.0 integration is experimental (in development). Primary stable engines: Groq (transcription) + DeepL (translation).

---

## 🎥 Demo

**Voice-to-Text with Real-time Translation in action:**

<video src="https://github.com/consulfedor/VoiceGrab/raw/main/assets/demo.mp4" controls width="100%"></video>

*(15 sec: Dictating in Russian → Auto-translates to English → Pastes into MS Word)*

---

## 🚀 Quick Start

### Option A: Download Release
1. [**Download Latest Release**](https://github.com/consulfedor/VoiceGrab/releases) (ZIP)
2. Get **Free API Key** → [console.groq.com/keys](https://console.groq.com/keys)
3. Run **`VoiceGrab.bat`**
4. Enter key → **Install Deps** → **Run**
5. Press **`Right Ctrl`** to dictate! 🎉

### Option B: Clone
```bash
git clone https://github.com/consulfedor/VoiceGrab.git
cd VoiceGrab
```

### Usage

| Action | How |
|--------|-----|
| **Start/Stop Recording** | `Right Ctrl` |
| **Switch Mode** | Click `◀ Mode ▶` on indicator |
| **Settings** | Right-click tray → Settings |

> 💡 **Tip:** Text is always in clipboard! **Ctrl+V** to paste anywhere.

---

## ✨ Features

### Core
- 🎤 **One-Click Recording** — Press `Right Ctrl` (configurable)
- ♾️ **Unlimited Recording** — Auto-segments every 3 min
- 📋 **Auto-Paste** — Text types directly into active window

### Transcription
- ⚡ **Groq Whisper API** — Fast, accurate, FREE tier
- 🧹 **Filler Cleanup** — Removes "um", "uh", "like"
- 👻 **Hallucination Filter** — Removes AI "ghost" phrases

### Translation
- 🌐 **Auto-Translate** — Off / Replace / Append modes
- 🔤 **DeepL Integration** — Quality translation
- 🌍 **Groq AI Translate** — Fast AI translation

### UI
- 🖥️ **System Tray** — Runs in background
- 💡 **Floating Indicator** — Shows mode + recording status
- ⚙️ **Dark Settings Panel** — All options per mode

---

## ⚙️ Configuration

### 5 Modes (fully customizable)

| Mode | Use Case |
|------|----------|
| 🤖 **AI Chat** | ChatGPT prompts, AI conversations |
| 💻 **Code** | Programming, technical terms |
| 📋 **Docs** | Documentation, formal writing |
| 📝 **Notes** | Quick notes, ideas |
| 💬 **Chat** | Casual conversation |

### Per-Mode Settings

- Language (57 options)
- Prompt (context hint for Whisper)
- Filler/Hallucination filters
- Auto-Translate (Off/Replace/Append)
- Translation engine (Groq/DeepL)

---

## 📦 Requirements

- **Windows 10/11**
- **Python 3.10+** — [Download](https://www.python.org/downloads/windows/)
  > ⚠️ Check **"Add Python to PATH"** during installation!
- **Microphone**

---

## 📋 Changelog

### v2.3.2 (2026-01-06)
- 🛡️ **Config Protection** — Prevents saving empty/NULL config

### v2.3.1 (2025-12-31)
- 🛠️ **NULL Eval Fix** — Fixed startup error

### v2.3.0 (2025-12-31)
- 🔧 **Settings Fix** — All fields save correctly
- 📝 **Single Default Config** — `config_default.json`

<details>
<summary><b>Older versions</b></summary>

### v2.0.0 - v2.2.0
- 🏷️ Custom Mode Names
- 💡 Tab Tooltips
- ⚙️ Mode Priority System

### v1.5.0
- 🌐 Auto-Translate (Groq/DeepL)
- 🔤 Translator Tool

### v1.4.0
- 📁 Batch Transcription
- 📄 Document Converter

### v1.3.0
- 🌍 57 Languages support

</details>

---

## ❓ FAQ

<details>
<summary><b>Is it really free?</b></summary>

Yes! Groq offers a generous FREE tier:
- ~10 requests per minute
- ~25,000 audio seconds per day (~8 hours)
- No credit card required

</details>

<details>
<summary><b>Which languages are supported?</b></summary>

57 languages including: Russian, English, Ukrainian, Turkish, Spanish, French, German, Chinese, Japanese.

</details>

<details>
<summary><b>Does it work offline?</b></summary>

No, requires internet. Audio is processed in cloud and deleted immediately.

</details>

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Python not found | Reinstall, check "Add to PATH" |
| No microphone | Check Windows sound settings |
| Rate limit | Wait 1 min, or use Turbo model |

---

## 🛠️ Tech Stack

- **Core:** Python 3.10+
- **UI:** PowerShell + WebView2 (HTML/CSS)
- **APIs:** Groq (Whisper), DeepL, Gemini (dev)

---

## 📄 License

MIT License — free for personal and commercial use.

---

<div align="center">

**⭐ Star this repo if you find it useful!**

[Report Bug](https://github.com/consulfedor/VoiceGrab/issues) • [Join Telegram](https://t.me/voicegrab_dev)

</div>
