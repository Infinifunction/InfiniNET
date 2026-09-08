import socket
import threading
import config
import InfiniDB
import re
from templates import create_html
import time

def extract_sni(data):
    #-------------------------------------------#
    # Parse the raw TLS Client Hello packet and extract the Server Name
    # Indication (SNI) hostname when the packet contains a recognizable
    # TLS handshake structure. Invalid or incomplete packets return None.
    #-------------------------------------------#
    try:
        if len(data) < 5 or data[0] != 0x16 or data[5] != 0x01:
            return None
        
        pos = 43
        if pos + 1 > len(data): return None
        session_id_len = data[pos]
        pos += 1 + session_id_len
        
        if pos + 2 > len(data): return None
        cipher_len = int.from_bytes(data[pos:pos+2], byteorder='big')
        pos += 2 + cipher_len
        
        if pos + 1 > len(data): return None
        comp_len = data[pos]
        pos += 1 + comp_len
        
        if pos + 2 > len(data): return None
        extensions_len = int.from_bytes(data[pos:pos+2], byteorder='big')
        pos += 2
        
        end_pos = pos + extensions_len
        while pos + 4 <= end_pos and pos < len(data):
            ext_type = data[pos:pos+2]
            ext_len = int.from_bytes(data[pos+2:pos+4], byteorder='big')
            pos += 4
            
            if ext_type == b'\x00\x00':
                if pos + 2 > len(data): return None
                pos += 2
                
                if pos + 3 > len(data): return None
                name_type = data[pos]
                name_len = int.from_bytes(data[pos+1:pos+3], byteorder='big')
                pos += 3
                
                if name_type == 0x00 and pos + name_len <= len(data):
                    return data[pos:pos+name_len].decode('utf-8', errors='ignore')
            
            pos += ext_len
    except:
        pass
    return None

def rate_limited_pipe(src, dst, client_ip):
    #-------------------------------------------#
    # Forward data between two sockets while applying the configured
    # per-client or global bandwidth limit. Unrestricted clients use
    # larger receive chunks, while limited clients are throttled according
    # to the calculated transfer time for each received data block.
    #-------------------------------------------#
    try:
        while True:
            active_limit_kb = 0
            if client_ip != config.MY_IP:
                with config.SPEED_LOCK:
                    active_limit_kb = config.SPECIAL_SPEED_LIMITS.get(client_ip, config.GENERAL_SPEED_LIMIT_KB)

            chunk_size = 1048576 if active_limit_kb == 0 else 4096
            start_time = time.time()
            data = src.recv(chunk_size)
            if not data: break
            
            dst.sendall(data)

            if active_limit_kb > 0:
                elapsed_time = time.time() - start_time
                ideal_time = len(data) / (active_limit_kb * 1024)
                if ideal_time > elapsed_time:
                    time.sleep(ideal_time - elapsed_time)
    except: pass
    finally:
        try: src.close()
        except: pass
        try: dst.close()
        except: pass

def secure_sni_tunnel(client_socket, remote_socket, client_ip):
    #-------------------------------------------#
    # Inspect the first packet of an HTTPS CONNECT tunnel to identify the
    # requested SNI hostname. The hostname is checked against the active
    # blocking rules before the remaining traffic is forwarded.
    #-------------------------------------------#
    try:
        first_package = client_socket.recv(8192)
        if not first_package:
            return

        sni_domain = extract_sni(first_package)
        if sni_domain:
            print(f"[🔍 SNI DETECTED] {client_ip} ➡️ Domain: '{sni_domain}'")
            config.add_live_log(client_ip, sni_domain, durum="ALLOWED")
            
            is_banned = False
            with config.FORBIDDEN_LOCK:
                prohibitions = config.ACTIVE_BANNED_SITE_TARGETS.get(client_ip, []) + config.ACTIVE_BANNED_SITE_TARGETS.get("HEPSİ", [])
                for regex_pattern in prohibitions:
                    if re.search(regex_pattern, sni_domain, re.IGNORECASE):
                        is_banned = True
                        break
            
            if is_banned:
                config.add_live_log(client_ip, sni_domain, durum="BLOCKED")
                print(f"[⚠️ SNI BLOCKED] {client_ip} ➡️ '{sni_domain}' was blocked!")
                return

        remote_socket.sendall(first_package)
        
        t1 = threading.Thread(target=rate_limited_pipe, args=(client_socket, remote_socket, client_ip), daemon=True)
        t2 = threading.Thread(target=rate_limited_pipe, args=(remote_socket, client_socket, client_ip), daemon=True)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
    except: pass
    finally:
        try: client_socket.close()
        except: pass
        try: remote_socket.close()
        except: pass

def proxy_handler(client_socket, client_addr):
    try:
        request = client_socket.recv(8192)
        if not request:
            client_socket.close()
            return

        client_ip = client_addr[0]

        #-------------------------------------------#
        # Inspect the incoming HTTP headers for a User-Agent value and store
        # the observed client fingerprint when a valid header is available.
        #-------------------------------------------#
        try:
            request_str = request.decode('utf-8', errors='ignore')
            for line in request_str.split("\r\n"):
                if line.lower().startswith("user-agent:"):
                    config.record_fingerprint(client_ip, line.split(":", 1)[1].strip())
                    break
        except: pass

        #-------------------------------------------#
        # Parse the incoming HTTP request to determine its method, target
        # URL, and destination hostname before forwarding the request.
        #-------------------------------------------#
        first_line = request.split(b'\r\n')[0].decode('utf-8', errors='ignore')
        parts = first_line.split(" ")
        if len(parts) < 2:
            client_socket.close()
            return

        method = parts[0]
        url = parts[1]

        target_domain = ""
        if ":" in url and not "://" in url:
            target_domain = url.split(":")[0]
        else:
            target_domain = url.replace("http://", "").replace("https://", "").split("/")[0]

        #-------------------------------------------#
        # Compare the requested hostname with client-specific and global
        # blocking rules. A matching regular expression marks the target
        # as blocked before the connection can continue.
        #-------------------------------------------#
        is_banned = False
        with config.FORBIDDEN_LOCK:
            prohibitions = config.ACTIVE_BANNED_SITE_TARGETS.get(client_ip, []) + config.ACTIVE_BANNED_SITE_TARGETS.get("HEPSİ", [])
            for regex_pattern in prohibitions:
                if target_domain and re.search(regex_pattern, target_domain, re.IGNORECASE):
                    is_banned = True
                    break

        if is_banned:
            print(f"[⚠️ PROXY BLOCKED] {client_ip} -> '{target_domain}' was blocked.")
            config.add_live_log(client_ip, target_domain, durum="BLOCKED")
            if method == "CONNECT":
                client_socket.close()
            else:
                dynamic_html = create_html("Access to this network resource has been restricted.")
                response = f"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: {len(dynamic_html.encode('utf-8'))}\r\n\r\n{dynamic_html}"
                client_socket.sendall(response.encode('utf-8'))
                client_socket.close()
            return

        #-------------------------------------------#
        # Check whether the client has an authorized session. Clients
        # without a valid session are directed through the local access
        # interface instead of continuing to external destinations.
        #-------------------------------------------#
        has_session = False
        with config.SESSION_LOCK:
            if client_ip in config.ACTIVE_SESSIONS or client_ip == config.MY_IP:
                has_session = True

        if not has_session:
            #-------------------------------------------#
            # Close unauthenticated HTTPS CONNECT requests because the
            # access interface is served through ordinary HTTP in this
            # implementation.
            #-------------------------------------------#
            if method == "CONNECT":
                client_socket.close()
                return

            #-------------------------------------------#
            # Detect an access-form submission, extract the supplied
            # credentials, and compare them with the configured values.
            # The authentication result is recorded in the database.
            #-------------------------------------------#
            if b"user=" in request and b"pass=" in request:
                user_val, pass_val = "Unknown", "Unknown"
                try:
                    request_str = request.decode('utf-8', errors='ignore')
                    first_line_str = request_str.split("\r\n")[0]
                    query_string = first_line_str.split(" ")[1].split("?")[1]
                    params = dict(x.split("=") for x in query_string.split("&"))
                    user_val = params.get('user', 'Unknown')
                    pass_val = params.get('pass', 'Unknown')
                except: pass

                if user_val == config.PERMISSION_USER and pass_val == config.PERMISSION_PASS:
                    InfiniDB.write_db_log(client_ip, user_val, pass_val, "SUCCESSFUL LOGIN")
                    InfiniDB.add_db_session(client_ip)

                    with config.SESSION_LOCK:
                        if isinstance(config.ACTIVE_SESSIONS, set):
                            config.ACTIVE_SESSIONS.add(client_ip)
                        elif client_ip not in config.ACTIVE_SESSIONS:
                            config.ACTIVE_SESSIONS.append(client_ip)
                    
                    success_html = "HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n<h1>ACCESS APPROVED. You can use the Internet.</h1>"
                    client_socket.sendall(success_html.encode())
                    client_socket.close()
                    return
                else:
                    InfiniDB.write_db_log(client_ip, user_val, pass_val, "REJECTED")
                    dynamic_html = create_html("Invalid username or password.")
                    response = f"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: {len(dynamic_html.encode('utf-8'))}\r\n\r\n{dynamic_html}"
                    client_socket.sendall(response.encode('utf-8'))
                    client_socket.close()
                    return

            #-------------------------------------------#
            # Prevent an access-interface redirect loop. Requests addressed
            # to the gateway itself receive the interface directly, while
            # other destinations are redirected to the local gateway URL.
            #-------------------------------------------#
            if config.MY_IP in target_domain or f"127.0.0.1" in target_domain:
                dynamic_html = create_html()
                response = (
                    f"HTTP/1.1 200 OK\r\n"
                    f"Content-Type: text/html; charset=utf-8\r\n"
                    f"Content-Length: {len(dynamic_html.encode('utf-8'))}\r\n"
                    f"Connection: close\r\n\r\n"
                    f"{dynamic_html}"
                )
            else:
                dynamic_html = create_html()
                response = (
                    f"HTTP/1.1 302 Found\r\n"
                    f"Location: http://{config.MY_IP}:{config.PROXY_PORT}/\r\n"
                    f"Content-Type: text/html; charset=utf-8\r\n"
                    f"Content-Length: {len(dynamic_html.encode('utf-8'))}\r\n"
                    f"Connection: close\r\n\r\n"
                    f"{dynamic_html}"
                )
            client_socket.sendall(response.encode('utf-8'))
            client_socket.close()
            return

        #-------------------------------------------#
        # Route traffic for an authorized client. HTTPS CONNECT requests
        # establish a remote TCP connection and use the SNI-aware tunnel
        # handler, while ordinary HTTP requests are forwarded directly.
        #-------------------------------------------#
        if method == "CONNECT":
            host, port = url.split(":") if ":" in url else (url, 443)
            remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_socket.connect((host, int(port)))
            client_socket.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            
            secure_sni_tunnel(client_socket, remote_socket, client_ip)
            return
        else:
            host_port = url.split("://")[1].split("/")[0] if "://" in url else url.split("/")[0]
            host, port = host_port.split(":") if ":" in host_port else (host_port, 80)
            
            remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_socket.connect((host, int(port)))
            remote_socket.sendall(request)
            
            t1 = threading.Thread(target=rate_limited_pipe, args=(client_socket, remote_socket, client_ip), daemon=True)
            t2 = threading.Thread(target=rate_limited_pipe, args=(remote_socket, client_socket, client_ip), daemon=True)
            t1.start()
            t2.start()
            t1.join()
            t2.join()

    except Exception as e:
        try: client_socket.close()
        except: pass

def start_proxy():
    proxy_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    proxy_server.bind((config.MY_IP, config.PROXY_PORT))
    proxy_server.listen(200)
    print(f"[*] InfiniDHCP Gateway Proxy is active on {config.MY_IP}:{config.PROXY_PORT}.")
    while True:
        client_sock, addr = proxy_server.accept()
        threading.Thread(target=proxy_handler, args=(client_sock, addr)).start()