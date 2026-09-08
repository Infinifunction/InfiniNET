import socket
import threading
import config

def process_wpad_request(client_socket):
    try:
        request = client_socket.recv(1024)
        if not request:
            client_socket.close()
            return

        # -------------------------------------------#
        # Generate the Proxy Auto-Configuration (PAC) script returned to clients.
        # The proxy server address and port are read dynamically from the central
        # configuration module so that the generated WPAD response always matches
        # the currently configured proxy endpoint.
        # -------------------------------------------
        wpad_script = f'function FindProxyForURL(url, host) {{ return "PROXY {config.MY_IP}:{config.PROXY_PORT}; DIRECT"; }}'
        
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: application/x-ns-proxy-autoconfig\r\n"
            f"Content-Length: {len(wpad_script.encode('utf-8'))}\r\n"
            "Access-Control-Allow-Origin: *\r\n"
            "Connection: close\r\n\r\n"
            f"{wpad_script}"
        )
        
        client_socket.sendall(response.encode('utf-8'))
    except Exception as e:
        pass
    finally:
        try:
            client_socket.close()
        except:
            pass

def start_wpad():
    # -------------------------------------------#
    # Start the lightweight WPAD HTTP server on TCP port 80.
    # WPAD clients can request the automatically generated PAC configuration
    # from this endpoint, allowing them to discover the configured proxy
    # without requiring the proxy address to be entered manually.
    # -------------------------------------------

    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # -------------------------------------------#
        # Bind the WPAD listener to TCP port 80, the conventional HTTP port used
        # by this module for serving Web Proxy Auto-Discovery configuration.
        # -------------------------------------------

        server.bind((config.MY_IP, 80))
        server.listen(50)
        print(f"[*] InfiniDHCP Auto-Proxy (WPAD) module is active on {config.MY_IP}:80.")
        
        while True:
            client_sock, addr = server.accept()
            threading.Thread(target=process_wpad_request, args=(client_sock,), daemon=True).start()
    except Exception as e:
        print(f"[!] Failed to start the WPAD server (port 80 permission error or another service is using it): {e}")