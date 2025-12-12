# VoiceGrab.ps1 - Modern PowerShell Launcher
# Requires: Windows 10/11 with WebView2 Runtime (auto-installed by Microsoft)

# === Single Instance Check for Settings UI ===
$MutexName = "Global\VoiceGrabSettingsUI"
$CreatedNew = $false
$Mutex = New-Object System.Threading.Mutex($true, $MutexName, [ref]$CreatedNew)

if (-not $CreatedNew) {
    # Another Settings UI is running - force bring it to front
    Add-Type @"
    using System;
    using System.Text;
    using System.Runtime.InteropServices;
    using System.Collections.Generic;
    
    public class WinAPI {
        public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
        
        [DllImport("user32.dll")]
        public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
        [DllImport("user32.dll", CharSet = CharSet.Unicode)]
        public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
        [DllImport("user32.dll")]
        public static extern bool IsWindowVisible(IntPtr hWnd);
        [DllImport("user32.dll")]
        public static extern bool SetForegroundWindow(IntPtr hWnd);
        [DllImport("user32.dll")]
        public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
        [DllImport("user32.dll")]
        public static extern bool BringWindowToTop(IntPtr hWnd);
        [DllImport("user32.dll")]
        public static extern void SwitchToThisWindow(IntPtr hWnd, bool fAltTab);
        [DllImport("user32.dll")]
        public static extern bool FlashWindow(IntPtr hWnd, bool bInvert);
        
        private static IntPtr foundHwnd = IntPtr.Zero;
        
        private static bool EnumCallback(IntPtr hWnd, IntPtr lParam) {
            if (!IsWindowVisible(hWnd)) return true;
            StringBuilder sb = new StringBuilder(256);
            GetWindowText(hWnd, sb, 256);
            string title = sb.ToString();
            if (title.StartsWith("VoiceGrab")) {
                foundHwnd = hWnd;
                return false; // Stop enumeration
            }
            return true;
        }
        
        public static IntPtr FindVoiceGrabWindow() {
            foundHwnd = IntPtr.Zero;
            EnumWindows(EnumCallback, IntPtr.Zero);
            return foundHwnd;
        }
        
        public static void ForceForeground(IntPtr hWnd) {
            ShowWindow(hWnd, 9); // SW_RESTORE
            BringWindowToTop(hWnd);
            SetForegroundWindow(hWnd);
            SwitchToThisWindow(hWnd, true);
            // Flash taskbar as backup visual indicator
            FlashWindow(hWnd, true);
        }
    }
"@
    $hwnd = [WinAPI]::FindVoiceGrabWindow()
    if ($hwnd -ne [IntPtr]::Zero) {
        [WinAPI]::ForceForeground($hwnd)
    }
    exit
}

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ConfigPath = Join-Path $ScriptDir "config.json"

# ============ HTML UI ============
$HTML = @'
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>VoiceGrab</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { 
    font-family: 'Segoe UI', sans-serif; 
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
    color: #e0e0e0; 
    padding: 20px;
    min-height: 100vh;
}
h1 { text-align: center; font-size: 28px; color: #fff; margin-bottom: 5px; }
.subtitle { text-align: center; color: #888; margin-bottom: 20px; font-size: 14px; }
.section { 
    background: rgba(255,255,255,0.05); 
    border: 1px solid rgba(255,255,255,0.1); 
    border-radius: 12px; 
    padding: 16px; 
    margin-bottom: 16px;
    backdrop-filter: blur(10px);
}
.section-title { 
    font-size: 14px; 
    font-weight: 600; 
    color: #fff; 
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.btn { 
    padding: 10px 18px; 
    background: linear-gradient(135deg, #4a9eff 0%, #3a7bd5 100%); 
    color: #fff; 
    border: none; 
    border-radius: 8px; 
    font-size: 13px; 
    cursor: pointer; 
    margin: 4px;
    transition: all 0.2s ease;
    box-shadow: 0 2px 8px rgba(74, 158, 255, 0.3);
}
.btn:hover { 
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(74, 158, 255, 0.4);
}
.btn-success { 
    background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%);
    box-shadow: 0 2px 8px rgba(46, 204, 113, 0.3);
}
.btn-success:hover {
    box-shadow: 0 4px 12px rgba(46, 204, 113, 0.4);
}
.btn-large { 
    width: 100%; 
    padding: 16px; 
    font-size: 18px; 
    font-weight: 600;
}
.btn-small { padding: 6px 12px; font-size: 12px; }
.btn-warn { 
    background: linear-gradient(135deg, #f39c12 0%, #d68910 100%);
    box-shadow: 0 2px 8px rgba(243, 156, 18, 0.3);
}
.dep-table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 12px; }
.dep-table td { padding: 10px 12px; border-bottom: 1px solid rgba(255,255,255,0.05); }
.dep-table tr:hover { background: rgba(255,255,255,0.03); }
.dep-table .st { width: 30px; text-align: center; font-size: 16px; }
.dep-table .nm { color: #fff; font-weight: 500; }
.dep-table .vr { color: #888; font-family: 'Consolas', monospace; }
.ok { color: #2ecc71; }
.err { color: #e74c3c; }
.warn { color: #f39c12; }
.cached { color: #9b59b6; }
input[type=text] { 
    padding: 10px 14px; 
    background: rgba(13, 17, 23, 0.8); 
    border: 1px solid rgba(48, 54, 61, 0.8); 
    border-radius: 8px; 
    color: #fff; 
    font-size: 13px; 
    width: 220px;
    transition: border-color 0.2s;
}
input[type=text]:focus {
    outline: none;
    border-color: #4a9eff;
}
.log-area { 
    background: rgba(13, 17, 23, 0.9); 
    border: 1px solid rgba(48, 54, 61, 0.8); 
    border-radius: 8px; 
    padding: 12px; 
    height: 120px; 
    overflow-y: auto; 
    font-family: 'Consolas', monospace; 
    font-size: 11px; 
    color: #8b949e; 
    margin-top: 16px;
}
.quick-actions { display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap; }
.status-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
}
.status-ok { background: rgba(46, 204, 113, 0.2); color: #2ecc71; }
.status-err { background: rgba(231, 76, 60, 0.2); color: #e74c3c; }
.status-warn { background: rgba(243, 156, 18, 0.2); color: #f39c12; }
.collapsible { cursor: pointer; user-select: none; }
.collapsible-content { display: none; overflow: hidden; }
.collapsible-content.expanded { display: block; }
.section-header { display: flex; justify-content: space-between; align-items: center; }
.toggle-icon { font-size: 24px; color: #888; margin-right: 8px; font-weight: 600; }
.deps-summary { font-size: 12px; margin-left: 12px; }
.deps-summary.all-ok { color: #2ecc71; }
.deps-summary.has-errors { color: #e74c3c; }
.radio-group { display: flex; gap: 24px; margin: 12px 0; }
.radio-label { display: flex; align-items: center; gap: 16px; cursor: pointer; padding: 12px 16px; border-radius: 8px; background: rgba(255,255,255,0.03); transition: all 0.2s; min-width: 200px; }
.radio-label:hover { background: rgba(255,255,255,0.08); }
.radio-label input[type=radio] { width: 18px; height: 18px; accent-color: #4a9eff; flex-shrink: 0; }
.radio-label .radio-text { font-size: 14px; font-weight: 600; color: #fff; }
.radio-label .radio-desc { font-size: 11px; color: #888; margin-top: 2px; }
.settings-row { display: flex; align-items: center; justify-content: space-between; margin: 16px 0; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
.settings-row:last-child { border-bottom: none; }
.settings-saved { color: #2ecc71; font-size: 12px; opacity: 0; transition: opacity 0.3s; }
.settings-saved.show { opacity: 1; }
.setting-label { font-size: 13px; color: #fff; }
.setting-desc { font-size: 11px; color: #888; margin-top: 2px; }
.toggle-switch { position: relative; width: 44px; height: 24px; }
.toggle-switch input { opacity: 0; width: 0; height: 0; }
.toggle-slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background: rgba(255,255,255,0.1); border-radius: 24px; transition: 0.3s; }
.toggle-slider:before { content: ''; position: absolute; height: 18px; width: 18px; left: 3px; bottom: 3px; background: #888; border-radius: 50%; transition: 0.3s; }
.toggle-switch input:checked + .toggle-slider { background: #4a9eff; }
.toggle-switch input:checked + .toggle-slider:before { transform: translateX(20px); background: #fff; }
.range-slider { width: 150px; height: 6px; border-radius: 3px; background: rgba(255,255,255,0.1); appearance: none; cursor: pointer; }
.range-slider::-webkit-slider-thumb { appearance: none; width: 16px; height: 16px; border-radius: 50%; background: #4a9eff; cursor: pointer; }
.range-value { font-size: 13px; color: #4a9eff; font-weight: 600; min-width: 50px; text-align: right; }
.settings-divider { border-top: 1px solid rgba(255,255,255,0.1); margin: 16px 0; padding-top: 12px; }
.settings-subtitle { font-size: 12px; color: #888; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px; }
select.model-select { padding: 8px 12px; background: rgba(13, 17, 23, 0.8); border: 1px solid rgba(48, 54, 61, 0.8); border-radius: 8px; color: #fff; font-size: 13px; cursor: pointer; min-width: 180px; }
select.model-select:focus { outline: none; border-color: #4a9eff; }
select.model-select option { background: #1a1a2e; color: #fff; }
.mode-tabs { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
.mode-tab { flex: 1; padding: 8px 12px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; color: #888; cursor: pointer; font-size: 13px; transition: all 0.2s; text-align: center; min-width: 60px; }
.mode-tab:hover { background: rgba(255,255,255,0.1); color: #fff; }
.mode-tab.active { background: #4a9eff; border-color: #4a9eff; color: #fff; }
.mode-form { padding: 12px; background: rgba(255,255,255,0.02); border-radius: 8px; }
textarea.prompt-input { width: 100%; height: 54px; padding: 10px; background: rgba(13, 17, 23, 0.8); border: 1px solid rgba(48, 54, 61, 0.8); border-radius: 8px; color: #fff; font-size: 13px; font-family: inherit; resize: vertical; overflow-y: auto; }
textarea.prompt-input:focus { outline: none; border-color: #4a9eff; }
.hotkey-input { padding: 8px 12px; background: rgba(13, 17, 23, 0.8); border: 1px solid rgba(48, 54, 61, 0.8); border-radius: 8px; color: #4a9eff; font-size: 13px; width: 120px; text-align: center; cursor: pointer; }
.hotkey-input:focus { outline: none; border-color: #4a9eff; }
.temp-slider { width: 120px; }
.btn-reset { padding: 6px 12px; background: rgba(231,76,60,0.2); border: 1px solid #e74c3c; color: #e74c3c; border-radius: 6px; font-size: 11px; cursor: pointer; }
.btn-reset:hover { background: rgba(231,76,60,0.4); }
select.lang-select { padding: 6px 10px; background: rgba(13, 17, 23, 0.8); border: 1px solid rgba(48, 54, 61, 0.8); border-radius: 6px; color: #fff; font-size: 12px; cursor: pointer; }
.filler-input { width: 100%; min-width: 400px; box-sizing: border-box; padding: 10px; background: rgba(13, 17, 23, 0.8); border: 1px solid rgba(48, 54, 61, 0.8); border-radius: 8px; color: #fff; font-size: 13px; }
.filler-input:focus { outline: none; border-color: #4a9eff; }
.help-btn { display: inline-block; width: 16px; height: 16px; line-height: 16px; text-align: center; background: rgba(74,158,255,0.2); color: #4a9eff; border-radius: 50%; font-size: 11px; cursor: help; margin-left: 6px; }
.help-btn:hover { background: rgba(74,158,255,0.4); }
.tooltip { position: relative; display: inline-block; }
.tooltip .tooltip-text { visibility: hidden; width: 280px; background: #1a1a2e; color: #fff; font-size: 11px; line-height: 1.4; padding: 10px; border-radius: 6px; border: 1px solid #4a9eff; position: absolute; z-index: 100; top: 125%; left: 0; opacity: 0; transition: opacity 0.3s; }
.tooltip:hover .tooltip-text { visibility: visible; opacity: 1; }
</style>
</head>
<body>

<h1>VoiceGrab</h1>
<p class="subtitle">Voice-to-AI Bridge</p>

<div class="section">
    <button class="btn btn-success btn-large" onclick="runVoiceGrab()">RUN VOICEGRAB</button>
</div>

<div class="section">
    <div class="section-header collapsible" onclick="toggleApiKey()">
        <span class="section-title" style="margin-bottom:0;">
            <span id="apiToggle" class="toggle-icon">[+]</span>
            <span>API Key</span>
            <span id="apiStatus" class="status-badge status-warn" style="margin-left: 8px;">?</span>
        </span>
    </div>
    <div id="apiContent" class="collapsible-content">
        <p style="color: #888; font-size: 12px; margin-bottom: 12px;">Groq API key for voice transcription. <a href="#" onclick="openLimits(); return false;" style="color: #4a9eff;">View FREE limits</a></p>
        <div style="margin: 12px 0;">
            <input type="text" id="apiKey" placeholder="gsk_...">
            <button class="btn btn-small" onclick="saveApiKey()">Save</button>
            <button class="btn btn-small" onclick="getApiKey()">Get Free Key</button>
        </div>
        <div class="settings-row">
            <div>
                <div class="setting-label">Autostart</div>
                <div class="setting-desc">Run VoiceGrab when Windows starts</div>
            </div>
            <label class="toggle-switch">
                <input type="checkbox" id="autostart" onchange="toggleAutostart(this.checked)">
                <span class="toggle-slider"></span>
            </label>
        </div>
        <div class="settings-row" id="startMinimizedRow" style="display: none; padding-left: 20px;">
            <div>
                <div class="setting-label">Start Minimized</div>
                <div class="setting-desc">Start in system tray (background)</div>
            </div>
            <label class="toggle-switch">
                <input type="checkbox" id="startMinimized" onchange="saveSetting('start_minimized', this.checked)">
                <span class="toggle-slider"></span>
            </label>
        </div>
        <div class="quick-actions">
            <button class="btn btn-small" onclick="openConfig()">config.json</button>
        </div>
    </div>
</div>

<div class="section">
    <div class="section-header collapsible" onclick="toggleDeps()">
        <span class="section-title" style="margin-bottom:0;">
            <span id="depsToggle" class="toggle-icon">[+]</span>
            <span>Dependencies</span>
            <span id="depsSummary" class="deps-summary" style="margin-left: 8px;">checking...</span>
        </span>
        <button class="btn btn-small btn-warn" onclick="event.stopPropagation(); revalidate();">Revalidate</button>
    </div>
    <div id="depsContent" class="collapsible-content">
        <p style="color: #888; font-size: 12px; margin-bottom: 8px;"><b>Python:</b> Download from python.org, run installer (check "Add to PATH")</p>
        <p style="color: #888; font-size: 12px; margin-bottom: 12px;"><b>Packages:</b> Listed in requirements.txt, installed via pip to user site-packages</p>
        <table class="dep-table">
            <tr><td id="s0" class="st warn">?</td><td class="nm">Python</td><td id="v0" class="vr">...</td><td><button class="btn btn-small" onclick="installPython()">Install</button></td></tr>
            <tr><td id="s1" class="st warn">?</td><td class="nm">groq</td><td id="v1" class="vr">...</td><td rowspan="9"><button class="btn btn-small" onclick="installDeps()">Install All</button></td></tr>
            <tr><td id="s2" class="st warn">?</td><td class="nm">pynput</td><td id="v2" class="vr">...</td></tr>
            <tr><td id="s3" class="st warn">?</td><td class="nm">sounddevice</td><td id="v3" class="vr">...</td></tr>
            <tr><td id="s4" class="st warn">?</td><td class="nm">soundfile</td><td id="v4" class="vr">...</td></tr>
            <tr><td id="s5" class="st warn">?</td><td class="nm">numpy</td><td id="v5" class="vr">...</td></tr>
            <tr><td id="s6" class="st warn">?</td><td class="nm">pyperclip</td><td id="v6" class="vr">...</td></tr>
            <tr><td id="s7" class="st warn">?</td><td class="nm">python-dotenv</td><td id="v7" class="vr">...</td></tr>
            <tr><td id="s8" class="st warn">?</td><td class="nm">pystray</td><td id="v8" class="vr">...</td></tr>
            <tr><td id="s9" class="st warn">?</td><td class="nm">pillow</td><td id="v9" class="vr">...</td></tr>
        </table>
    </div>
</div>

<div class="section">
    <div class="section-header collapsible" onclick="toggleSettings()">
        <span class="section-title" style="margin-bottom:0;">
            <span id="settingsToggle" class="toggle-icon">[+]</span>
            Settings
        </span>
        <span id="settingsSaved" class="settings-saved">Saved!</span>
    </div>
    <div id="settingsContent" class="collapsible-content">
        <div class="settings-row">
            <div>
                <div class="setting-label">
                    Global Hotkey
                    <span class="tooltip">
                        <span class="help-btn">?</span>
                        <span class="tooltip-text"><b>Global Hotkey:</b><br>One hotkey for ALL modes!<br>Click and press key combo.<br>Default: Right Alt (AltGr)<br>Mode affects prompt, not hotkey.</span>
                    </span>
                </div>
                <div class="setting-desc">Single hotkey for all modes (click to change)</div>
            </div>
            <input type="text" class="hotkey-input" id="globalHotkey" value="alt gr" readonly onclick="startHotkeyCapture(this)" onkeydown="captureGlobalHotkey(event, this)" onblur="cancelHotkeyCapture(this)" style="min-width: 120px;">
        </div>
        
        <div class="settings-divider"></div>
        
        <div class="settings-row">
            <div>
                <div class="setting-label">
                    Max Duration
                    <span class="tooltip">
                        <span class="help-btn">?</span>
                        <span class="tooltip-text"><b>Auto-Chunking:</b><br>Recording auto-sends at this limit.<br><b>You don't need to stop talking!</b><br>Text is pasted to active window.<br><br><b>Tip:</b> If Log Texts is ON, all transcriptions are saved to recordings/transcription_log.txt</span>
                    </span>
                </div>
                <div class="setting-desc">Max recording time (Groq FREE limit ~3 min)</div>
            </div>
            <div style="display: flex; align-items: center; gap: 12px;">
                <input type="range" class="range-slider" id="maxDuration" min="30" max="300" value="180" oninput="updateDuration(this.value)" onchange="saveDuration(this.value)">
                <span class="range-value" id="durationValue">180s</span>
            </div>
        </div>
        
        <div class="settings-divider"></div>
        <div class="settings-subtitle">Storage</div>
        
        <div class="settings-row">
            <div>
                <div class="setting-label">Save Audio</div>
                <div class="setting-desc">Keep audio files after transcription</div>
            </div>
            <label class="toggle-switch">
                <input type="checkbox" id="saveAudio" onchange="saveSetting('save_audio', this.checked)">
                <span class="toggle-slider"></span>
            </label>
        </div>
        
        <div class="settings-row">
            <div>
                <div class="setting-label">Log Texts</div>
                <div class="setting-desc">Save transcriptions to log file (searchable)</div>
            </div>
            <label class="toggle-switch">
                <input type="checkbox" id="logTexts" checked onchange="saveSetting('log_texts', this.checked)">
                <span class="toggle-slider"></span>
            </label>
        </div>
        
        <div style="display: flex; justify-content: center; gap: 12px; margin-top: 12px;">
            <button class="btn btn-small" onclick="openRecordings()">Recordings Folder</button>
            <button class="btn btn-small" onclick="saveGlobalSettings()" style="background: #27ae60;">Save Settings</button>
        </div>
    </div>
</div>

<div class="section">
    <div class="section-header collapsible" onclick="toggleModes()">
        <span class="section-title" style="margin-bottom:0;">
            <span id="modesToggle" class="toggle-icon">[+]</span>
            Modes
        </span>
    </div>
    <div id="modesContent" class="collapsible-content">
        <p style="color: #888; font-size: 12px; margin-bottom: 12px;">Voice recognition modes with individual settings</p>
        
        <div class="mode-tabs">
            <span class="mode-tab active" onclick="selectMode('ai')">AI Chat</span>
            <span class="mode-tab" onclick="selectMode('code')">Code</span>
            <span class="mode-tab" onclick="selectMode('docs')">Docs</span>
            <span class="mode-tab" onclick="selectMode('notes')">Notes</span>
            <span class="mode-tab" onclick="selectMode('chat')">Chat</span>
        </div>
        
        <div class="mode-form" id="modeForm">
            <!-- Mode Name (only visible for custom mode) -->
            <div class="settings-row" id="modeNameRow" style="display: none;">
                <div>
                    <div class="setting-label">Mode Name</div>
                    <div class="setting-desc">Custom name for this mode</div>
                </div>
                <input type="text" id="modeName" class="input-field" style="width: 120px;" onchange="saveModeField('name', this.value)">
            </div>
            
            <!-- Hotkey is now GLOBAL in Settings section, not per-mode -->
            
            <div class="settings-row">
                <div>
                    <div class="setting-label">
                        Input Mode
                        <span class="tooltip">
                            <span class="help-btn">?</span>
                            <span class="tooltip-text"><b>Input Mode:</b><br>- <b>Toggle:</b> Click once to start, click again to stop<br>- <b>Hold:</b> Hold key to record, release to stop<br>Hold is better for quick phrases, Toggle for long texts</span>
                        </span>
                    </div>
                    <div class="setting-desc">Toggle or hold to record</div>
                </div>
                <div style="display: flex;">
                    <label style="display: flex; align-items: center; margin-right: 40px; cursor: pointer; color: #fff; font-size: 12px;">
                        <input type="radio" name="modeInputMode" value="toggle" id="modeInputToggle" checked onchange="saveModeField('input_mode', 'toggle')" style="margin-right: 6px;"> Toggle
                    </label>
                    <label style="display: flex; align-items: center; cursor: pointer; color: #fff; font-size: 12px;">
                        <input type="radio" name="modeInputMode" value="hold" id="modeInputHold" onchange="saveModeField('input_mode', 'hold')" style="margin-right: 6px;"> Hold
                    </label>
                </div>
            </div>
            
            <div class="settings-row" style="flex-direction: column; align-items: flex-start;">
                <div style="width: 100%; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div class="setting-label">
                            Language
                            <span class="tooltip">
                                <span class="help-btn">?</span>
                                <span class="tooltip-text"><b>Primary Language:</b><br>Whisper uses ONE language at a time!<br>- Select your main spoken language<br>- Auto = Whisper detects language<br>- English terms are recognized in any mode</span>
                            </span>
                        </div>
                        <div class="setting-desc">Select PRIMARY language (Whisper uses one)</div>
                    </div>
                </div>
                <div style="display: flex; flex-wrap: wrap; margin-top: 8px;" id="langRadios">
                    <label style="display: flex; align-items: center; margin-right: 24px; cursor: pointer; color: #fff; font-size: 12px;">
                        <input type="radio" name="modeLang" value="auto" id="langAuto" onchange="saveLang(this.value)" style="margin-right: 4px;"> Auto
                    </label>
                    <label style="display: flex; align-items: center; margin-right: 24px; cursor: pointer; color: #fff; font-size: 12px;">
                        <input type="radio" name="modeLang" value="ru" id="langRu" checked onchange="saveLang(this.value)" style="margin-right: 4px;"> Russian
                    </label>
                    <label style="display: flex; align-items: center; margin-right: 24px; cursor: pointer; color: #fff; font-size: 12px;">
                        <input type="radio" name="modeLang" value="en" id="langEn" onchange="saveLang(this.value)" style="margin-right: 4px;"> English
                    </label>
                    <label style="display: flex; align-items: center; margin-right: 24px; cursor: pointer; color: #fff; font-size: 12px;">
                        <input type="radio" name="modeLang" value="tr" id="langTr" onchange="saveLang(this.value)" style="margin-right: 4px;"> Turkish
                    </label>
                    <label style="display: flex; align-items: center; margin-right: 24px; cursor: pointer; color: #fff; font-size: 12px;">
                        <input type="radio" name="modeLang" value="uk" id="langUk" onchange="saveLang(this.value)" style="margin-right: 4px;"> Ukrainian
                    </label>
                    <label style="display: flex; align-items: center; cursor: pointer; color: #fff; font-size: 12px;">
                        <input type="radio" name="modeLang" value="pl" id="langPl" onchange="saveLang(this.value)" style="margin-right: 4px;"> Polish
                    </label>
                </div>
            </div>
            
            <div class="settings-row">
                <div>
                    <div class="setting-label">
                        Model
                        <span class="tooltip">
                            <span class="help-btn">?</span>
                            <span class="tooltip-text"><b>Whisper Model:</b><br>- <b>Accuracy:</b> whisper-large-v3 (slower, precise)<br>- <b>Speed:</b> whisper-large-v3-turbo (faster)<br><br><b>++ SEPARATE LIMITS!</b> Each model has its own rate limit. If one runs out, switch to other!</span>
                        </span>
                    </div>
                    <div class="setting-desc">Accuracy vs Speed</div>
                </div>
                <select id="modeModel" class="lang-select" onchange="saveModeField('model', this.value)">
                    <option value="whisper-large-v3">Accuracy</option>
                    <option value="whisper-large-v3-turbo">Speed</option>
                </select>
            </div>
            
            <div class="settings-row">
                <div>
                    <div class="setting-label">
                        Temperature
                        <span class="tooltip">
                            <span class="help-btn">?</span>
                            <span class="tooltip-text"><b>Temperature:</b><br>Controls transcription randomness.<br>- <b>0.0:</b> Most accurate (for code, AI prompts)<br>- <b>0.3-0.5:</b> Balanced (notes, docs)<br>- <b>0.8-1.0:</b> Creative (free chat)<br>Lower = more precise, Higher = more natural</span>
                        </span>
                    </div>
                    <div class="setting-desc">0 = accurate, 1 = creative</div>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <input type="range" class="range-slider temp-slider" id="modeTemp" min="0" max="10" value="0" oninput="updateTemp(this.value)" onchange="saveModeField('temperature', this.value/10)">
                    <span class="range-value" id="tempValue" style="min-width: 30px;">0.0</span>
                </div>
            </div>
            
            <div class="settings-row">
                <div>
                    <div class="setting-label">
                        Profanity Filter
                        <span class="tooltip">
                            <span class="help-btn">?</span>
                            <span class="tooltip-text"><b>Profanity Filter:</b><br>Censors offensive words in output.<br>Unique for each mode!</span>
                        </span>
                    </div>
                    <div class="setting-desc">Censor offensive words</div>
                </div>
                <label class="toggle-switch">
                    <input type="checkbox" id="modeProfanity" onchange="saveModeField('profanity_filter', this.checked)">
                    <span class="toggle-slider"></span>
                </label>
            </div>
            
            <div class="settings-divider"></div>
            
            <div style="margin-bottom: 12px;">
                <div class="setting-label">
                    Prompt
                    <span class="tooltip">
                        <span class="help-btn">?</span>
                        <span class="tooltip-text"><b>Prompt - Domain Terms:</b><br>Add terms from YOUR domain!<br>Example for design: Figma, mockup, wireframe, UI kit, prototype<br>Example for dev: Python, DataFrame, API, Docker<br>Helps Whisper recognize specialized vocabulary.</span>
                    </span>
                </div>
                <div class="setting-desc" style="margin-bottom: 8px;">Context hint for Whisper</div>
                <textarea class="prompt-input" id="modePrompt" onchange="saveModeField('prompt', this.value)">AI assistant prompts. Mixed language with technical terms.</textarea>
            </div>
            
            <div class="settings-row">
                <div>
                    <div class="setting-label">
                        Filler Words Cleanup
                        <span class="tooltip">
                            <span class="help-btn">?</span>
                            <span class="tooltip-text"><b>Filler Cleanup:</b><br>Remove um, uh, like after transcription.<br>Unique for each mode!</span>
                        </span>
                    </div>
                    <div class="setting-desc">Remove filler words</div>
                </div>
                <label class="toggle-switch">
                    <input type="checkbox" id="modeFillerCleanup" onchange="saveModeField('filler_cleanup', this.checked)">
                    <span class="toggle-slider"></span>
                </label>
            </div>
            
            <div style="margin-bottom: 12px;" id="fillerWordsContainer">
                <div class="setting-desc" style="margin-bottom: 8px;">Words to remove (comma separated):</div>
                <textarea class="prompt-input" id="modeFillerWords" rows="2" onchange="saveModeField('filler_words', this.value)">um, uh, like, you know</textarea>
            </div>
            
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 12px;">
                <button class="btn btn-small" onclick="saveModeSettings()" style="background: #27ae60;">Save Settings</button>
                <button class="btn-reset" onclick="resetMode()">Reset to Default</button>
            </div>
        </div>
    </div>
</div>

<input type="hidden" id="modeDataJson" value="">
<div class="log-area" id="logArea">Ready to check dependencies...</div>

<script>
// Toggle functions
function toggleDeps() {
    var content = document.getElementById('depsContent');
    var toggle = document.getElementById('depsToggle');
    if (content.className.indexOf('expanded') >= 0) {
        content.className = 'collapsible-content';
        toggle.innerText = '[+]';
    } else {
        content.className = 'collapsible-content expanded';
        toggle.innerText = '[-]';
    }
}

function toggleSettings() {
    var content = document.getElementById('settingsContent');
    var toggle = document.getElementById('settingsToggle');
    if (content.className.indexOf('expanded') >= 0) {
        content.className = 'collapsible-content';
        toggle.innerText = '[+]';
    } else {
        content.className = 'collapsible-content expanded';
        toggle.innerText = '[-]';
    }
}

function toggleApiKey() {
    var content = document.getElementById('apiContent');
    var toggle = document.getElementById('apiToggle');
    if (content.className.indexOf('expanded') >= 0) {
        content.className = 'collapsible-content';
        toggle.innerText = '[+]';
    } else {
        content.className = 'collapsible-content expanded';
        toggle.innerText = '[-]';
    }
}

function log(msg) {
    var el = document.getElementById('logArea');
    el.innerHTML = el.innerHTML + msg + '<br>';
    el.scrollTop = el.scrollHeight;
}

// Button actions - use URL navigation to communicate with PowerShell
function doAction(action) {
    log('Action: ' + action);
    window.location.href = 'action:' + action;
}

function runVoiceGrab() { doAction('run'); }
function saveApiKey() { 
    var key = document.getElementById('apiKey').value;
    doAction('saveKey:' + key); 
}
function getApiKey() { doAction('getKey'); }
function openConfig() { doAction('config'); }
function openRecordings() { doAction('recordings'); }
function openLogs() { doAction('logs'); }
function installPython() { doAction('installPython'); }
function installDeps() { doAction('installDeps'); }
function revalidate() { doAction('revalidate'); }

function saveInputMode(mode) {
    doAction('inputMode:' + mode);
    showSaved();
}

function updateDuration(val) {
    document.getElementById('durationValue').innerText = val + 's';
}

function saveDuration(val) {
    doAction('maxDuration:' + val);
    showSaved();
}

function saveSetting(key, value) {
    doAction('setting:' + key + ':' + (value ? '1' : '0'));
    showSaved();
}

function showSaved() {
    var saved = document.getElementById('settingsSaved');
    saved.className = 'settings-saved show';
    setTimeout(function() { saved.className = 'settings-saved'; }, 1500);
}

function openLimits() {
    doAction('limits');
}

function toggleAutostart(enabled) {
    doAction('autostart:' + (enabled ? '1' : '0'));
    var minRow = document.getElementById('startMinimizedRow');
    if (minRow) { minRow.style.display = enabled ? 'flex' : 'none'; }
    showSaved();
}

function saveModel(model) {
    doAction('model:' + model);
    showSaved();
}

function saveGlobalSettings() {
    var duration = document.getElementById('maxDuration').value;
    var saveAudio = document.getElementById('saveAudio').checked;
    var logTexts = document.getElementById('logTexts').checked;
    
    saveDuration(duration);
    saveSetting('save_audio', saveAudio);
    saveSetting('log_texts', logTexts);
    
    log('Global settings saved');
    showSaved();
}

// ============ Modes Functions ============
var currentMode = 'ai';

function toggleModes() {
    var content = document.getElementById('modesContent');
    var toggle = document.getElementById('modesToggle');
    if (content.className.indexOf('expanded') >= 0) {
        content.className = 'collapsible-content';
        toggle.innerText = '[+]';
    } else {
        content.className = 'collapsible-content expanded';
        toggle.innerText = '[-]';
        // Load all mode checkboxes when opening
        doAction('loadAllModeCheckboxes');
    }
}

function selectMode(mode) {
    currentMode = mode;
    // Update tab styles
    var tabs = document.getElementsByClassName('mode-tab');
    for (var i = 0; i < tabs.length; i++) {
        tabs[i].className = 'mode-tab';
    }
    event.target.className = 'mode-tab active';
    // Load mode data from PowerShell
    doAction('loadMode:' + mode);
    
    // Show/hide Mode Name field (only for 'chat' mode which is customizable)
    var modeNameRow = document.getElementById('modeNameRow');
    if (modeNameRow) {
        modeNameRow.style.display = (mode === 'chat') ? 'flex' : 'none';
    }
    
    // Update checkboxes after loadMode (via hidden data)
    setTimeout(function() {
        var dataEl = document.getElementById('modeDataJson');
        if (dataEl && dataEl.value) {
            try {
                var data = JSON.parse(dataEl.value);
                document.getElementById('modeProfanity').checked = data.profanity_filter === true;
                document.getElementById('modeFillerCleanup').checked = data.filler_cleanup === true;
                // Update mode name for customizable modes
                var nameEl = document.getElementById('modeName');
                if (nameEl && data.name) {
                    nameEl.value = data.name;
                }
            } catch(e) {}
        }
    }, 100);
    log('Mode selected: ' + mode);
}

function updateTemp(val) {
    document.getElementById('tempValue').innerText = (val / 10).toFixed(1);
}

function saveLang(lang) {
    // Whisper only accepts ONE language - save selected radio value
    saveModeField('language', lang);
    log('Language saved: ' + lang);
}

function saveModeField(field, value) {
    var encoded = value;
    if (typeof value === 'string') {
        encoded = encodeURIComponent(value);
    }
    doAction('saveMode:' + currentMode + ':' + field + ':' + encoded);
    showSaved();
}

var previousHotkey = '';

function startHotkeyCapture(input) {
    previousHotkey = input.value;
    input.value = 'Press key combo...';
    input.style.background = '#3a3f47';
    input.focus();
}

function cancelHotkeyCapture(input) {
    // If still in capture mode (showing '...' or partial), restore previous value
    if (input.value.indexOf('...') >= 0 || input.style.background === '#3a3f47' || input.style.background === 'rgb(58, 63, 71)') {
        input.value = previousHotkey || 'alt gr';
        input.style.background = '';
    }
}

function captureHotkey(event, input) {
    event.preventDefault();
    var key = event.key;
    var parts = [];
    
    // Handle AltGr specifically
    if (key === 'AltGraph') {
        input.value = 'alt gr';
        input.style.background = '';
        saveModeField('hotkey', 'alt gr');
        log('Hotkey set: alt gr');
        return;
    }
    
    // Build modifier string
    if (event.ctrlKey) parts.push('ctrl');
    if (event.altKey) parts.push('alt');
    if (event.shiftKey) parts.push('shift');
    
    // Skip if only modifier key pressed - wait for actual key
    if (key === 'Control' || key === 'Alt' || key === 'Shift') {
        input.value = parts.join('+') + '+...';
        return;
    }
    
    // Normalize key names to lowercase
    if (key === ' ') key = 'space';
    else if (key === 'Escape') key = 'esc';
    else if (key === 'Enter') key = 'enter';
    else if (key.length === 1) key = key.toLowerCase();
    else key = key.toLowerCase();
    
    parts.push(key);
    var combo = parts.join('+');
    
    input.value = combo;
    input.style.background = '';
    saveModeField('hotkey', combo);
    log('Hotkey set: ' + combo);
}

function captureGlobalHotkey(event, input) {
    event.preventDefault();
    var key = event.key;
    var parts = [];
    
    // Handle AltGr specifically
    if (key === 'AltGraph') {
        input.value = 'alt gr';
        input.style.background = '';
        saveGlobalHotkey('alt gr');
        return;
    }
    
    // Build modifier string
    if (event.ctrlKey) parts.push('ctrl');
    if (event.altKey) parts.push('alt');
    if (event.shiftKey) parts.push('shift');
    
    // Skip if only modifier key pressed
    if (key === 'Control' || key === 'Alt' || key === 'Shift') {
        input.value = parts.join('+') + '+...';
        return;
    }
    
    // Normalize key names
    if (key === ' ') key = 'space';
    else if (key === 'Escape') key = 'esc';
    else if (key === 'Enter') key = 'enter';
    else if (key.length === 1) key = key.toLowerCase();
    else key = key.toLowerCase();
    
    parts.push(key);
    var combo = parts.join('+');
    
    input.value = combo;
    input.style.background = '';
    saveGlobalHotkey(combo);
}

function saveGlobalHotkey(hotkey) {
    // Save to config.input.hotkey
    window.external.Call('action:saveGlobalHotkey:' + hotkey);
    log('Global hotkey set: ' + hotkey);
}

function saveProfanity(mode, checked) {
    // Save profanity_filter directly to specific mode
    window.external.Call('action:saveProfanityMode:' + mode + ':' + (checked ? 'true' : 'false'));
    log('Profanity filter for ' + mode + ': ' + checked);
}

function saveFillerCleanup(mode, checked) {
    // Save filler_cleanup directly to specific mode
    window.external.Call('action:saveFillerMode:' + mode + ':' + (checked ? 'true' : 'false'));
    log('Filler cleanup for ' + mode + ': ' + checked);
}

function saveModeSettings() {
    // Collect all values and save (hotkey is now GLOBAL, not per-mode)
    var inputMode = document.querySelector('input[name="modeInputMode"]:checked');
    var model = document.getElementById('modeModel').value;
    var lang = document.getElementById('modeLang').value;
    var temp = document.getElementById('modeTemp').value / 10;
    var profanity = document.getElementById('modeProfanity').checked;
    var prompt = document.getElementById('modePrompt').value;
    var fillers = document.getElementById('modeFillerWords').value;
    
    // Save each field (no hotkey - it's global now)
    saveModeField('input_mode', inputMode ? inputMode.value : 'toggle');
    saveModeField('model', model);
    saveModeField('language', lang);
    saveModeField('temperature', temp);
    saveModeField('profanity_filter', profanity);
    saveModeField('prompt', prompt);
    saveModeField('filler_words', fillers);
    
    log('Mode settings saved: ' + currentMode);
    showSaved();
}

function resetMode() {
    if (confirm('Reset ' + currentMode.toUpperCase() + ' mode to defaults?')) {
        doAction('resetMode:' + currentMode);
        // UI will be updated by loadMode action called from PowerShell
    }
}

log('VoiceGrab Launcher loaded');
</script>
</body>
</html>
'@

# ============ Check WebView2 Runtime ============
function Test-WebView2 {
    $regPaths = @(
        "HKLM:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
        "HKCU:\SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
        "HKLM:\SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
    )
    foreach ($path in $regPaths) {
        if (Test-Path $path) {
            $version = (Get-ItemProperty $path -ErrorAction SilentlyContinue).pv
            if ($version) { return $version }
        }
    }
    return $null
}

# ============ Config Functions ============
function Get-DefaultConfig {
    return @{
        api    = @{ key = ""; model = "whisper-large-v3" }
        input  = @{ mode = "toggle" }
        global = @{
            max_duration = 180
            save_audio   = $false
            log_texts    = $true
            cleanup      = $true
        }
        modes  = @{
            ai    = @{
                name             = "AI Chat"
                hotkey           = "alt gr"
                input_mode       = "toggle"
                model            = "whisper-large-v3"
                language         = "ru"
                temperature      = 0.0
                profanity_filter = $false
                prompt           = "AI assistant prompts. Mixed language with technical terms."
                filler_words     = @("um", "uh", "like", "you know")
            }
            code  = @{
                name             = "Code"
                hotkey           = "alt+1"
                input_mode       = "toggle"
                model            = "whisper-large-v3"
                language         = "ru"
                temperature      = 0.0
                profanity_filter = $false
                prompt           = "Programming and technical context. Code-related terminology."
                filler_words     = @("um", "uh", "like")
            }
            docs  = @{
                name             = "Docs"
                hotkey           = "alt+2"
                input_mode       = "toggle"
                model            = "whisper-large-v3"
                language         = "ru"
                temperature      = 0.2
                profanity_filter = $true
                prompt           = "Technical documentation, specifications. Formal style."
                filler_words     = @("um", "uh")
            }
            notes = @{
                name             = "Notes"
                hotkey           = "alt+3"
                input_mode       = "toggle"
                model            = "whisper-large-v3"
                language         = "ru"
                temperature      = 0.3
                profanity_filter = $true
                prompt           = "Notes, thoughts, ideas. Structure into bullet points."
                filler_words     = @("um", "uh", "like")
            }
            chat  = @{
                name             = "Chat"
                hotkey           = "alt+4"
                input_mode       = "hold"
                model            = "whisper-large-v3-turbo"
                language         = "ru"
                temperature      = 0.5
                profanity_filter = $false
                prompt           = "Free conversation. No censorship."
                filler_words     = @()
            }
        }
    }
}

function Get-Config {
    $defaults = Get-DefaultConfig
    if (Test-Path $ConfigPath) {
        $saved = Get-Content $ConfigPath -Raw | ConvertFrom-Json
        # Merge with defaults
        if (-not $saved.global) { $saved | Add-Member -NotePropertyName "global" -NotePropertyValue $defaults.global -Force }
        if (-not $saved.input) { $saved | Add-Member -NotePropertyName "input" -NotePropertyValue $defaults.input -Force }
        if (-not $saved.api) { $saved | Add-Member -NotePropertyName "api" -NotePropertyValue $defaults.api -Force }
        return $saved
    }
    return $defaults
}

function Save-Config($config) {
    $config | ConvertTo-Json -Depth 10 | Set-Content $ConfigPath -Encoding UTF8
}

# ============ Python Detection ============
function Find-Python {
    if (Test-Path "C:\Windows\py.exe") {
        $version = & "C:\Windows\py.exe" --version 2>&1
        if ($version -match "Python") {
            return @{ cmd = "C:\Windows\py.exe"; version = $version.Trim() }
        }
    }
    try {
        $version = & python --version 2>&1
        if ($version -match "Python") {
            return @{ cmd = "python"; version = $version.Trim() }
        }
    }
    catch {}
    return $null
}

function Test-PythonModule($moduleName) {
    $python = Find-Python
    if (-not $python) { return $false }
    try {
        $result = & $python.cmd -c "import $moduleName" 2>&1
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

# ============ WebView2 Window ============
function Show-WebView2Window {
    $webview2Version = Test-WebView2
    if (-not $webview2Version) {
        [System.Windows.Forms.MessageBox]::Show(
            "WebView2 Runtime not found.`n`nPlease install it from:`nhttps://developer.microsoft.com/en-us/microsoft-edge/webview2/",
            "VoiceGrab - WebView2 Required",
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Warning
        )
        Start-Process "https://developer.microsoft.com/en-us/microsoft-edge/webview2/"
        return
    }

    # Load WebView2 assembly
    try {
        Add-Type -Path "$env:ProgramFiles\Microsoft.NET\Primary Interop Assemblies\Microsoft.Web.WebView2.Core.dll" -ErrorAction SilentlyContinue
    }
    catch {}
    
    # For now, use a simple Windows Forms approach with WebBrowser as fallback
    # Full WebView2 requires more complex setup - this is a simplified version
    
    $form = New-Object System.Windows.Forms.Form
    $form.Text = "VoiceGrab"
    $form.Size = New-Object System.Drawing.Size(900, 800)
    $form.StartPosition = "CenterScreen"
    $form.BackColor = [System.Drawing.Color]::FromArgb(26, 26, 46)
    
    $regPath = "HKCU:\SOFTWARE\Microsoft\Internet Explorer\Main\FeatureControl\FEATURE_BROWSER_EMULATION"
    $appName = [System.IO.Path]::GetFileName([System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName)
    if (-not (Test-Path $regPath)) { New-Item -Path $regPath -Force | Out-Null }
    Set-ItemProperty -Path $regPath -Name $appName -Value 11001 -Type DWord -Force
    
    $webBrowser = New-Object System.Windows.Forms.WebBrowser
    $webBrowser.Dock = [System.Windows.Forms.DockStyle]::Fill
    $webBrowser.ScriptErrorsSuppressed = $true
    $webBrowser.DocumentText = $HTML
    
    $form.Controls.Add($webBrowser)
    
    $script:ScriptDir = $ScriptDir
    $script:ConfigPath = $ConfigPath
    
    # Handle navigation to intercept action:* URLs
    $webBrowser.Add_Navigating({
            param($s, $e)
            $url = $e.Url.ToString()
        
            if ($url.StartsWith("action:")) {
                $e.Cancel = $true
                $action = $url.Substring(7)
            
                $doc = $s.Document
                $logEl = $doc.GetElementById("logArea")
            
                switch -Wildcard ($action) {
                    "run" {
                        if ($logEl) { $logEl.InnerHtml += "Starting VoiceGrab...<br>" }
                        Start-Process "cmd" -ArgumentList "/c cd /d `"$script:ScriptDir`" && python voicegrab.py" -WindowStyle Normal
                    }
                    "saveKey:*" {
                        $key = $action.Substring(8)
                        if ($key.Length -gt 5) {
                            $config = Get-Config
                            if (-not $config.api) { $config | Add-Member -NotePropertyName "api" -NotePropertyValue @{} -Force }
                            $config.api.key = $key
                            Save-Config $config
                            if ($logEl) { $logEl.InnerHtml += "API Key saved!<br>" }
                            $statusEl = $doc.GetElementById("apiStatus")
                            if ($statusEl) { 
                                $statusEl.InnerText = "OK"
                                $statusEl.SetAttribute("class", "status-badge status-ok")
                            }
                        }
                    }
                    "getKey" {
                        Start-Process "https://console.groq.com/keys"
                        if ($logEl) { $logEl.InnerHtml += "Opening Groq console...<br>" }
                    }
                    "config" {
                        if (Test-Path $script:ConfigPath) {
                            Start-Process "notepad" -ArgumentList $script:ConfigPath
                        }
                        if ($logEl) { $logEl.InnerHtml += "Opening config.json...<br>" }
                    }
                    "recordings" {
                        $recPath = Join-Path $script:ScriptDir "recordings"
                        if (-not (Test-Path $recPath)) { New-Item -ItemType Directory -Path $recPath -Force | Out-Null }
                        Start-Process "explorer" -ArgumentList $recPath
                        if ($logEl) { $logEl.InnerHtml += "Opening recordings folder...<br>" }
                    }
                    "logs" {
                        if ($logEl) { $logEl.InnerHtml += "Logs are shown in this area.<br>" }
                    }
                    "installPython" {
                        Start-Process "https://www.python.org/downloads/windows/"
                        if ($logEl) { $logEl.InnerHtml += "Opening Python for Windows download page...<br><b>Choose Stable Release, check 'Add to PATH'!</b><br>" }
                    }
                    "installDeps" {
                        $python = Find-Python
                        if ($python) {
                            $reqPath = Join-Path $script:ScriptDir "requirements.txt"
                            if (Test-Path $reqPath) {
                                if ($logEl) { $logEl.InnerHtml += "Installing dependencies (window will open)...<br>" }
                                # Use python -m pip to ensure correct pip, keep window open
                                Start-Process "cmd" -ArgumentList "/k cd /d `"$script:ScriptDir`" && `"$($python.cmd)`" -m pip install -r requirements.txt && echo. && echo === DONE! Close this window ===" -WindowStyle Normal
                            }
                            else {
                                if ($logEl) { $logEl.InnerHtml += "<span class='err'>requirements.txt not found!</span><br>" }
                            }
                        }
                        else {
                            if ($logEl) { $logEl.InnerHtml += "<span class='err'>Python not found! Install Python first.</span><br>" }
                        }
                    }
                    "revalidate" {
                        if ($logEl) { $logEl.InnerHtml += "Revalidating dependencies...<br>" }
                        $s.Refresh()
                    }
                    "inputMode:*" {
                        $mode = $action.Substring(10)
                        $config = Get-Config
                        if (-not $config.input) { 
                            $config | Add-Member -NotePropertyName "input" -NotePropertyValue @{} -Force 
                        }
                        $config.input.mode = $mode
                        Save-Config $config
                        if ($logEl) { $logEl.InnerHtml += "Input mode: $mode<br>" }
                    }
                    "maxDuration:*" {
                        $duration = [int]$action.Substring(12)
                        $config = Get-Config
                        if (-not $config.global) { 
                            $config | Add-Member -NotePropertyName "global" -NotePropertyValue @{} -Force 
                        }
                        $config.global.max_duration = $duration
                        Save-Config $config
                        if ($logEl) { $logEl.InnerHtml += "Max duration: ${duration}s<br>" }
                    }
                    "setting:*" {
                        $parts = $action.Substring(8).Split(":")
                        $key = $parts[0]
                        $value = $parts[1] -eq "1"
                        $config = Get-Config
                        if (-not $config.global) { 
                            $config | Add-Member -NotePropertyName "global" -NotePropertyValue @{} -Force 
                        }
                        $config.global.$key = $value
                        Save-Config $config
                        if ($logEl) { $logEl.InnerHtml += "$key = $value<br>" }
                    }
                    "run" {
                        $python = Find-Python
                        if (-not $python) {
                            if ($logEl) { $logEl.InnerHtml += "<span class='err'><b>ERROR:</b> Python not found!</span><br>Please install Python first (check 'Add to PATH').<br>" }
                            # Expand deps section
                            $depsContent = $doc.GetElementById("depsContent")
                            $depsToggle = $doc.GetElementById("depsToggle")
                            if ($depsContent) { $depsContent.SetAttribute("class", "collapsible-content expanded") }
                            if ($depsToggle) { $depsToggle.InnerText = "[-]" }
                            return
                        }
                        
                        # Check critical dependencies
                        $missingDeps = @()
                        $criticalDeps = @("groq", "pynput", "sounddevice")
                        foreach ($dep in $criticalDeps) {
                            if (-not (Test-PythonModule $dep)) { $missingDeps += $dep }
                        }
                        
                        if ($missingDeps.Count -gt 0) {
                            if ($logEl) { 
                                $logEl.InnerHtml += "<span class='err'><b>ERROR:</b> Missing dependencies:</span><br>"
                                $logEl.InnerHtml += "<b>" + ($missingDeps -join ", ") + "</b><br>"
                                $logEl.InnerHtml += "Click <b>Install All</b> in Dependencies section.<br>"
                            }
                            # Expand deps section
                            $depsContent = $doc.GetElementById("depsContent")
                            $depsToggle = $doc.GetElementById("depsToggle")
                            if ($depsContent) { $depsContent.SetAttribute("class", "collapsible-content expanded") }
                            if ($depsToggle) { $depsToggle.InnerText = "[-]" }
                            return
                        }
                        
                        # Check API key
                        $config = Get-Config
                        $apiKey = $config.api.key
                        if (-not $apiKey -or $apiKey.Length -lt 10) {
                            if ($logEl) { 
                                $logEl.InnerHtml += "<span class='err'><b>ERROR:</b> API Key not set!</span><br>"
                                $logEl.InnerHtml += "Get free key at <a href='action:getKey'>console.groq.com</a><br>"
                            }
                            # Expand API section
                            $apiContent = $doc.GetElementById("apiContent")
                            $apiToggle = $doc.GetElementById("apiToggle")
                            if ($apiContent) { $apiContent.SetAttribute("class", "collapsible-content expanded") }
                            if ($apiToggle) { $apiToggle.InnerText = "[-]" }
                            return
                        }
                        
                        $scriptPath = Join-Path $PSScriptRoot "voicegrab.py"
                        if (Test-Path $scriptPath) {
                            # Get current mode settings for message
                            $inputMode = $config.modes.ai.input_mode
                            if (-not $inputMode) { $inputMode = "toggle" }
                            $hotkeyInstruction = if ($inputMode -eq "hold") { "HOLD Right Alt to record" } else { "Press Right Alt to start/stop" }
                            
                            # pynput works without admin - run hidden
                            Start-Process -FilePath $python.cmd -ArgumentList "`"$scriptPath`"" -WorkingDirectory $PSScriptRoot -WindowStyle Hidden
                            
                            # Show success popup
                            $msg = "VoiceGrab запущен!`n`n"
                            $msg += "Программа свернута в ТРЕЙ`n"
                            $msg += "(правый нижний угол экрана)`n`n"
                            $msg += "Меню: правый клик по иконке`n"
                            $msg += "Настройки / Выход = там же!`n`n"
                            $msg += "$hotkeyInstruction"
                            
                            [System.Windows.Forms.MessageBox]::Show(
                                $msg,
                                "VoiceGrab - Готово!",
                                [System.Windows.Forms.MessageBoxButtons]::OK,
                                [System.Windows.Forms.MessageBoxIcon]::Information
                            ) | Out-Null
                            
                            # Close launcher
                            $form.Close()
                        }
                        else {
                            if ($logEl) { $logEl.InnerHtml += "<span class='err'>ERROR: voicegrab.py not found!</span><br>" }
                        }
                    }
                    "limits" {
                        Start-Process "https://console.groq.com/settings/limits"
                        if ($logEl) { $logEl.InnerHtml += "Opening Groq limits page...<br>" }
                    }
                    "autostart:*" {
                        $enabled = $action.Substring(10) -eq "1"
                        $regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
                        $batPath = Join-Path $script:ScriptDir "VoiceGrab.bat"
                        if ($enabled) {
                            Set-ItemProperty -Path $regPath -Name "VoiceGrab" -Value "`"$batPath`"" -Force
                            if ($logEl) { $logEl.InnerHtml += "Autostart enabled<br>" }
                        }
                        else {
                            Remove-ItemProperty -Path $regPath -Name "VoiceGrab" -ErrorAction SilentlyContinue
                            if ($logEl) { $logEl.InnerHtml += "Autostart disabled<br>" }
                        }
                    }
                    "model:*" {
                        $model = $action.Substring(6)
                        $config = Get-Config
                        if (-not $config.api) { 
                            $config | Add-Member -NotePropertyName "api" -NotePropertyValue @{} -Force 
                        }
                        $config.api.model = $model
                        Save-Config $config
                        if ($logEl) { $logEl.InnerHtml += "Model: $model<br>" }
                    }
                    "saveGlobalHotkey:*" {
                        $hotkey = $action.Substring(16)
                        $config = Get-Config
                        if (-not $config.input) {
                            $config | Add-Member -NotePropertyName "input" -NotePropertyValue @{} -Force
                        }
                        $config.input.hotkey = $hotkey
                        Save-Config $config
                        if ($logEl) { $logEl.InnerHtml += "Global hotkey: $hotkey<br>" }
                    }
                    "saveProfanityMode:*" {
                        $parts = $action.Substring(17).Split(":")
                        $modeName = $parts[0]
                        $value = $parts[1] -eq "true"
                        $config = Get-Config
                        if ($config.modes -and $config.modes.$modeName) {
                            $config.modes.$modeName.profanity_filter = $value
                            Save-Config $config
                            if ($logEl) { $logEl.InnerHtml += "Profanity $modeName : $value<br>" }
                        }
                    }
                    "saveFillerMode:*" {
                        $parts = $action.Substring(15).Split(":")
                        $modeName = $parts[0]
                        $value = $parts[1] -eq "true"
                        $config = Get-Config
                        if ($config.modes -and $config.modes.$modeName) {
                            $config.modes.$modeName.filler_cleanup = $value
                            Save-Config $config
                            if ($logEl) { $logEl.InnerHtml += "Filler $modeName : $value<br>" }
                        }
                    }
                    "loadAllModeCheckboxes" {
                        $config = Get-Config
                        $modes = @('ai', 'code', 'notes', 'docs', 'chat')
                        $jsCode = ""
                        foreach ($m in $modes) {
                            $profanity = "false"
                            $filler = "false"
                            if ($config.modes -and $config.modes.$m) {
                                if ($config.modes.$m.profanity_filter -eq $true) { $profanity = "true" }
                                if ($config.modes.$m.filler_cleanup -eq $true) { $filler = "true" }
                            }
                            $jsCode += "document.getElementById('profanity_$m').checked = $profanity; "
                            $jsCode += "document.getElementById('filler_$m').checked = $filler; "
                        }
                        try { $doc.parentWindow.eval($jsCode) } catch {}
                        if ($logEl) { $logEl.InnerHtml += "Loaded all mode checkboxes<br>" }
                    }
                    "loadMode:*" {
                        $modeName = $action.Substring(9)
                        $config = Get-Config
                        $defaults = Get-DefaultConfig
                        $modeData = $null
                        if ($config.modes -and $config.modes.$modeName) {
                            $modeData = $config.modes.$modeName
                        }
                        elseif ($defaults.modes.$modeName) {
                            $modeData = $defaults.modes.$modeName
                        }
                        if ($modeData) {
                            # Update form fields via DOM
                            $hotkeyEl = $doc.GetElementById("modeHotkey")
                            $modelEl = $doc.GetElementById("modeModel")
                            $langEl = $doc.GetElementById("modeLang")
                            $tempEl = $doc.GetElementById("modeTemp")
                            $tempValEl = $doc.GetElementById("tempValue")
                            $profanityEl = $doc.GetElementById("modeProfanity")
                            $promptEl = $doc.GetElementById("modePrompt")
                            $fillerEl = $doc.GetElementById("modeFillerWords")
                            
                            if ($hotkeyEl) { $hotkeyEl.SetAttribute("value", $modeData.hotkey) }
                            $modelValue = if ($modeData.model) { $modeData.model } else { "whisper-large-v3" }
                            if ($modelEl) { $modelEl.SetAttribute("value", $modelValue) }
                            if ($langEl) { $langEl.SetAttribute("value", $modeData.language) }
                            $tempInt = [int]($modeData.temperature * 10)
                            if ($tempEl) { $tempEl.SetAttribute("value", $tempInt) }
                            if ($tempValEl) { $tempValEl.InnerText = $modeData.temperature.ToString("0.0") }
                            # Profanity filter checkbox - set checked property directly
                            if ($profanityEl) {
                                $profanityEl.checked = $($modeData.profanity_filter -eq $true)
                            }
                            
                            if ($promptEl) { $promptEl.InnerText = $modeData.prompt }
                            if ($fillerEl -and $modeData.filler_words) {
                                $fillerEl.SetAttribute("value", ($modeData.filler_words -join ", "))
                            }
                            # Filler cleanup checkbox - set checked property directly
                            $fillerCleanupEl = $doc.GetElementById("modeFillerCleanup")
                            if ($fillerCleanupEl) {
                                $fillerCleanupEl.checked = $($modeData.filler_cleanup -eq $true)
                            }
                            
                            # Write checkbox and mode data to hidden input for JavaScript to read
                            $modeDataJsonEl = $doc.GetElementById("modeDataJson")
                            if ($modeDataJsonEl) {
                                $profanityVal = if ($modeData.profanity_filter -eq $true) { "true" } else { "false" }
                                $fillerVal = if ($modeData.filler_cleanup -eq $true) { "true" } else { "false" }
                                $nameVal = if ($modeData.name) { $modeData.name } else { $modeName }
                                $jsonData = "{`"profanity_filter`":$profanityVal,`"filler_cleanup`":$fillerVal,`"name`":`"$nameVal`"}"
                                $modeDataJsonEl.SetAttribute("value", $jsonData)
                            }
                            # Input Mode radio buttons
                            $inputToggleEl = $doc.GetElementById("modeInputToggle")
                            $inputHoldEl = $doc.GetElementById("modeInputHold")
                            if ($modeData.input_mode -eq "hold") {
                                if ($inputHoldEl) { $inputHoldEl.SetAttribute("checked", "checked") }
                                if ($inputToggleEl) { $inputToggleEl.RemoveAttribute("checked") }
                            }
                            else {
                                if ($inputToggleEl) { $inputToggleEl.SetAttribute("checked", "checked") }
                                if ($inputHoldEl) { $inputHoldEl.RemoveAttribute("checked") }
                            }
                        }
                        if ($logEl) { $logEl.InnerHtml += "Mode loaded: $modeName<br>" }
                    }
                    "saveMode:*" {
                        $parts = $action.Substring(9).Split(":")
                        $modeName = $parts[0]
                        $field = $parts[1]
                        $value = [System.Web.HttpUtility]::UrlDecode($parts[2])
                        
                        $config = Get-Config
                        if (-not $config.modes) { $config | Add-Member -NotePropertyName "modes" -NotePropertyValue @{} -Force }
                        if (-not $config.modes.$modeName) { 
                            $defaults = Get-DefaultConfig
                            $config.modes | Add-Member -NotePropertyName $modeName -NotePropertyValue $defaults.modes.$modeName -Force
                        }
                        
                        # Handle different field types
                        if ($field -eq "filler_words") {
                            $config.modes.$modeName.$field = $value.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ }
                        }
                        elseif ($field -eq "temperature") {
                            $config.modes.$modeName.$field = [double]$value
                        }
                        elseif ($field -eq "profanity_filter") {
                            $config.modes.$modeName.$field = $value -eq "true"
                        }
                        else {
                            $config.modes.$modeName.$field = $value
                        }
                        
                        Save-Config $config
                        if ($logEl) { $logEl.InnerHtml += "Mode $modeName.$field saved<br>" }
                    }
                    "resetMode:*" {
                        $modeName = $action.Substring(10)
                        $config = Get-Config
                        $defaults = Get-DefaultConfig
                        
                        if (-not $config.modes) { $config | Add-Member -NotePropertyName "modes" -NotePropertyValue @{} -Force }
                        $config.modes | Add-Member -NotePropertyName $modeName -NotePropertyValue $defaults.modes.$modeName -Force
                        
                        Save-Config $config
                        
                        # Update UI directly
                        $modeData = $defaults.modes.$modeName
                        $hotkeyEl = $doc.GetElementById("modeHotkey")
                        $modelEl = $doc.GetElementById("modeModel")
                        $langEl = $doc.GetElementById("modeLang")
                        $tempEl = $doc.GetElementById("modeTemp")
                        $tempValEl = $doc.GetElementById("tempValue")
                        $profanityEl = $doc.GetElementById("modeProfanity")
                        $promptEl = $doc.GetElementById("modePrompt")
                        $fillerEl = $doc.GetElementById("modeFillerWords")
                        
                        if ($hotkeyEl) { $hotkeyEl.SetAttribute("value", $modeData.hotkey) }
                        if ($modelEl -and $modeData.model) { $modelEl.SetAttribute("value", $modeData.model) }
                        if ($langEl) { $langEl.SetAttribute("value", $modeData.language) }
                        $tempInt = [int]($modeData.temperature * 10)
                        if ($tempEl) { $tempEl.SetAttribute("value", $tempInt) }
                        if ($tempValEl) { $tempValEl.InnerText = $modeData.temperature.ToString("0.0") }
                        if ($profanityEl) {
                            if ($modeData.profanity_filter) { $profanityEl.SetAttribute("checked", "checked") }
                            else { $profanityEl.RemoveAttribute("checked") }
                        }
                        if ($promptEl) { $promptEl.InnerText = $modeData.prompt }
                        if ($fillerEl -and $modeData.filler_words) {
                            $fillerEl.SetAttribute("value", ($modeData.filler_words -join ", "))
                        }
                        
                        # Input Mode radio buttons
                        $inputToggleEl = $doc.GetElementById("modeInputToggle")
                        $inputHoldEl = $doc.GetElementById("modeInputHold")
                        if ($modeData.input_mode -eq "hold") {
                            if ($inputHoldEl) { $inputHoldEl.SetAttribute("checked", "checked") }
                            if ($inputToggleEl) { $inputToggleEl.RemoveAttribute("checked") }
                        }
                        else {
                            if ($inputToggleEl) { $inputToggleEl.SetAttribute("checked", "checked") }
                            if ($inputHoldEl) { $inputHoldEl.RemoveAttribute("checked") }
                        }
                        
                        if ($logEl) { $logEl.InnerHtml += "Mode reset: $modeName<br>" }
                    }
                }
            }
        })
    
    # Handle document completion to inject data
    $webBrowser.Add_DocumentCompleted({
            param($s, $e)
        
            try {
                $doc = $s.Document
            
                function Set-Status($id, $text, $className) {
                    $el = $doc.GetElementById($id)
                    if ($el) { 
                        $el.InnerText = $text
                        $el.SetAttribute("class", $className)
                    }
                }
            
                $python = Find-Python
                if ($python) {
                    Set-Status "s0" "OK" "st ok"
                    Set-Status "v0" $python.version "vr"
                
                    $logEl = $doc.GetElementById("logArea")
                    if ($logEl) { $logEl.InnerHtml = "Python found: " + $python.version + "<br>" }
                
                    $deps = @("groq", "pynput", "sounddevice", "soundfile", "numpy", "pyperclip", "dotenv", "pystray", "PIL")
                    $errorCount = 0
                    for ($i = 0; $i -lt $deps.Length; $i++) {
                        $depName = $deps[$i]
                        $ok = Test-PythonModule $depName
                        $idx = $i + 1
                        if ($ok) {
                            Set-Status "s$idx" "OK" "st ok"
                            Set-Status "v$idx" "OK" "vr ok"
                        }
                        else {
                            Set-Status "s$idx" "X" "st err"
                            Set-Status "v$idx" "missing" "vr err"
                            $errorCount++
                        }
                    }
                
                    $summaryEl = $doc.GetElementById("depsSummary")
                    if ($summaryEl) {
                        if ($errorCount -eq 0) {
                            $summaryEl.InnerText = "All OK"
                            $summaryEl.SetAttribute("class", "deps-summary all-ok")
                        }
                        else {
                            $summaryEl.InnerText = "$errorCount errors"
                            $summaryEl.SetAttribute("class", "deps-summary has-errors")
                            $depsContent = $doc.GetElementById("depsContent")
                            $depsToggle = $doc.GetElementById("depsToggle")
                            if ($depsContent) { $depsContent.SetAttribute("class", "collapsible-content expanded") }
                            if ($depsToggle) { $depsToggle.InnerText = "[-]" }
                        }
                    }
            
                    if ($logEl) { $logEl.InnerHtml += "Dependencies checked.<br>Ready!" }
                }
                else {
                    Set-Status "s0" "X" "st err"
                    Set-Status "v0" "Not found" "vr"
                    $logEl = $doc.GetElementById("logArea")
                    if ($logEl) { $logEl.InnerHtml = "Python NOT FOUND. Please install Python first." }
                    $summaryEl = $doc.GetElementById("depsSummary")
                    if ($summaryEl) {
                        $summaryEl.InnerText = "Python missing"
                        $summaryEl.SetAttribute("class", "deps-summary has-errors")
                    }
                    $depsContent = $doc.GetElementById("depsContent")
                    $depsToggle = $doc.GetElementById("depsToggle")
                    if ($depsContent) { $depsContent.SetAttribute("class", "collapsible-content expanded") }
                    if ($depsToggle) { $depsToggle.InnerText = "[-]" }
                }
        
                $config = Get-Config
                if ($config.api -and $config.api.key -and $config.api.key.Length -gt 5) {
                    $apiInput = $doc.GetElementById("apiKey")
                    if ($apiInput) { $apiInput.SetAttribute("value", $config.api.key) }
                    Set-Status "apiStatus" "OK" "status-badge status-ok"
                }
                
                # Load model selector
                if ($config.api -and $config.api.model) {
                    $modelSelect = $doc.GetElementById("modelSelect")
                    if ($modelSelect) { $modelSelect.SetAttribute("value", $config.api.model) }
                }
            
                $inputMode = "toggle"
                if ($config.input -and $config.input.mode) {
                    $inputMode = $config.input.mode
                }
                if ($inputMode -eq "hold") {
                    $holdRadio = $doc.GetElementById("modeHold")
                    if ($holdRadio) { $holdRadio.SetAttribute("checked", "checked") }
                }
                else {
                    $toggleRadio = $doc.GetElementById("modeToggle")
                    if ($toggleRadio) { $toggleRadio.SetAttribute("checked", "checked") }
                }
                
                # Load global settings
                if ($config.global) {
                    # Max Duration
                    if ($config.global.max_duration) {
                        $duration = $config.global.max_duration
                        $durationSlider = $doc.GetElementById("maxDuration")
                        $durationValue = $doc.GetElementById("durationValue")
                        if ($durationSlider) { $durationSlider.SetAttribute("value", $duration) }
                        if ($durationValue) { $durationValue.InnerText = "${duration}s" }
                    }
                    
                    # Save Audio
                    if ($config.global.save_audio -eq $true) {
                        $saveAudioEl = $doc.GetElementById("saveAudio")
                        if ($saveAudioEl) { $saveAudioEl.SetAttribute("checked", "checked") }
                    }
                    
                    # Log Texts (default true, so only uncheck if false)
                    if ($config.global.log_texts -eq $false) {
                        $logTextsEl = $doc.GetElementById("logTexts")
                        if ($logTextsEl) { $logTextsEl.RemoveAttribute("checked") }
                    }
                    
                    # Cleanup (default true, so only uncheck if false)
                    if ($config.global.cleanup -eq $false) {
                        $cleanupEl = $doc.GetElementById("cleanup")
                        if ($cleanupEl) { $cleanupEl.RemoveAttribute("checked") }
                    }
                }
                
                # Check Autostart registry
                $regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
                $autostartValue = Get-ItemProperty -Path $regPath -Name "VoiceGrab" -ErrorAction SilentlyContinue
                if ($autostartValue) {
                    $autostartEl = $doc.GetElementById("autostart")
                    if ($autostartEl) { $autostartEl.SetAttribute("checked", "checked") }
                }
            }
            catch {
                $logEl = $doc.GetElementById("logArea")
                if ($logEl) { $logEl.InnerHtml = "Error: " + $_.Exception.Message }
            }
        })
    
    $form.Add_Shown({ $form.Activate() })
    [System.Windows.Forms.Application]::Run($form)
}

# ============ Main ============
Show-WebView2Window
