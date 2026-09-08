import threading
from admin.app import run_admin_server
import config
from proxy_module import start_proxy
from dns_module import start_dns
import InfiniDB
from auto_reloader import start_hot_reload

#-------------------------------------------#
# Additional project modules loaded by the main application. #
#-------------------------------------------#
import wpad_module
import dhcp_module

def console_listener():
    print("[*] InfiniNET live operations console is ready. You can enter commands.")
    while True:
        try:
            command = input().strip()
            if not command: continue
            
            #-------------------------------------------#
            # Check the /Forbidden command, validate its argument count, and extract the target IP and site pattern. #
            #-------------------------------------------#
            if command.startswith("/Forbidden "):
                parts = command.split(" ")
                if len(parts) == 3:
                    target_ip = parts[1]
                    target_site = parts[2].strip(".")
                    
                    if InfiniDB.add_db_block_rule(target_ip, target_site):
                        with config.FORBIDDEN_LOCK:
                            if target_ip not in config.ACTIVE_BANNED_SITE_TARGETS:
                                config.ACTIVE_BANNED_SITE_TARGETS[target_ip] = []
                            if target_site not in config.ACTIVE_BANNED_SITE_TARGETS[target_ip]:
                                config.ACTIVE_BANNED_SITE_TARGETS[target_ip].append(target_site)
                        print(f"[+] OPERATION ACTIVE: {target_ip} for '{target_site}' has been registered.")
                else:
                    print("[-] ERROR: Invalid format. Usage: /Forbidden {IP} {Site}")
            
            #-------------------------------------------#
            # List all currently registered blocked-site rules grouped by client IP address. #
            #-------------------------------------------#
            elif command == "/Forbidden_list":
                print("\n=== ACTIVE BLOCKING TARGETS ===")
                with config.FORBIDDEN_LOCK:
                    if not config.ACTIVE_BANNED_SITE_TARGETS:
                        print("No active targets.")
                    for ip, sites in config.ACTIVE_BANNED_SITE_TARGETS.items():
                        print(f"Device: {ip} ➡️ Blocked Sites: {sites}")
                print("========================================\n")

            #-------------------------------------------#
            # Check the /Forbidden_delete command, validate its arguments, and remove the selected rule from persistent and in-memory state. #
            #-------------------------------------------#
            elif command.startswith("/Forbidden_delete "):
                parts = command.split(" ")
                if len(parts) == 3:
                    target_ip = parts[1]
                    target_site = parts[2].strip(".")
                    
                    if InfiniDB.delete_db_block_rule(target_ip, target_site):
                        with config.FORBIDDEN_LOCK:
                            if target_ip in config.ACTIVE_BANNED_SITE_TARGETS and target_site in config.ACTIVE_BANNED_SITE_TARGETS[target_ip]:
                                config.ACTIVE_BANNED_SITE_TARGETS[target_ip].remove(target_site)
                                if not config.ACTIVE_BANNED_SITE_TARGETS[target_ip]:
                                    del config.ACTIVE_BANNED_SITE_TARGETS[target_ip]
                        print(f"[✓] OPERATION CANCELLED: {target_ip} on '{target_site}' has been unblocked.")
                else:
                    print("[-] ERROR: Invalid format. Usage: /Forbidden_delete {IP} {Site}")

            elif command.startswith("/TS_ip "):
                parts = command.split(" ")
                if len(parts) == 3:
                    target_ip = parts[1]
                    try:
                        speed_kb = int(parts[2])
                        with config.SPEED_LOCK:
                            if speed_kb > 0:
                                config.SPECIAL_SPEED_LIMITS[target_ip] = speed_kb
                                print(f"[⚡ SPEED LIMIT] {target_ip} speed set to {speed_kb} KB/s.")
                            else:
                                config.SPECIAL_SPEED_LIMITS.pop(target_ip, None)
                                print(f"[✓ SPEED LIMIT] Custom speed limit for {target_ip} has been removed.")
                    except ValueError:
                        print("[-] ERROR: Speed value must be a number (e.g., 512).")
                else:
                    print("[-] Usage: /TS_ip {IP} {Speed_in_KB} (Reset: /TS_ip IP 0)")

            elif command.startswith("/TS_everyone "):
                parts = command.split(" ")
                if len(parts) == 2:
                    try:
                        speed_kb = int(parts[1])
                        onlines = InfiniDB.load_active_db_sessions()
                        
                        with config.SPEED_LOCK:
                            config.GENERAL_SPEED_LIMIT_KB = speed_kb
                        
                        if speed_kb > 0:
                            print(f"\n[⚡ GLOBAL SPEED LIMIT] Global limit for {len(onlines)} registered IPs in the database: {speed_kb} KB/s")
                            print(f"[🛡️ EXEMPT IP] {config.MY_IP} (Main Server) is not affected by this limit.\n")
                        else:
                            print("[✓ GLOBAL SPEED LIMIT] The global limit has been removed for all registered users.")
                    except ValueError:
                        print("[-] ERROR: Speed value must be a number (e.g., 512).")
                else:
                    print("[-] Usage: /TS_everyone {Speed_in_KB} (Remove: /TS_everyone 0)")
            
            else:
                print("[-] Unknown command. Available commands: /Forbidden, /Forbidden_list, /Forbidden_delete, /TS_ip, /TS_everyone")

        except Exception as e:
            print(f"[-] Console error: {e}")

if __name__ == "__main__":
    InfiniDB.init_db()
    
    config.ACTIVE_SESSIONS = InfiniDB.load_active_db_sessions()
    config.ACTIVE_BANNED_SITE_TARGETS = InfiniDB.load_db_block_rules()
    print(f"[*] Loaded {len(config.ACTIVE_SESSIONS)} active sessions and {len(config.ACTIVE_BANNED_SITE_TARGETS)} blocked targets from the database.")

    start_hot_reload()

    #-------------------------------------------#
# Start the DNS module in a background daemon thread so DNS handling can run independently. #
#-------------------------------------------#
    threading.Thread(target=start_dns, daemon=True).start()
    
    #-------------------------------------------#
# Start the WPAD auto-proxy module on port 80 in a background daemon thread. #
#-------------------------------------------#
    threading.Thread(target=wpad_module.start_wpad, daemon=True).start()

    #-------------------------------------------#
# Start the DHCP server on UDP port 67. This call remains in the main startup flow. #
#-------------------------------------------#
    dhcp_module.start_dhcp()

    #-------------------------------------------#
# Start the interactive console listener in a background daemon thread. #
#-------------------------------------------#
    threading.Thread(target=console_listener, daemon=True).start()

    # 5. Admin Panel (Port 8000'e çekildi, Port 80 WPAD for ayrıldı)
    admin_thread = threading.Thread(target=run_admin_server, kwargs={'host': '0.0.0.0', 'port': 8000}, daemon=True)
    admin_thread.start()
    print("[*] Admin Panel Service Started: http://192.168.1.101:8000/admin")
    
    #-------------------------------------------#
# Start the proxy server on the main thread so the application remains active while the proxy is running. #
#-------------------------------------------#
    start_proxy()