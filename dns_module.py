import socket
import threading
from scapy.all import DNS, DNSRR, DNSQR
import config
import re
import urllib.request


def query_doh(dns_wire_data):
    #-------------------------------------------#
    # Sends the raw DNS packet to Cloudflare's DNS-over-HTTPS endpoint.
    # The request uses the standard DNS message media type so the response
    # can be forwarded directly to the requesting client when successful.
    #-------------------------------------------#
    try:
        url = "https://1.1.1.1/dns-query"
        req = urllib.request.Request(
            url,
            data=dns_wire_data,
            headers={
                'Content-Type': 'application/dns-message',
                'Accept': 'application/dns-message'
            }
        )

        with urllib.request.urlopen(req, timeout=2.5) as resp:
            return resp.read()
    except Exception:
        #-------------------------------------------#
        # Returns None when the DoH request fails so the caller can use
        # the configured traditional DNS fallback mechanism instead.
        #-------------------------------------------#
        return None


def process_dns_request(dns_server, data, addr):
    #-------------------------------------------#
    # Parses and processes an incoming DNS request. The function checks
    # configured domain-blocking rules first, then attempts secure DNS
    # resolution through DoH before falling back to TCP-based DNS resolution.
    #-------------------------------------------#
    try:
        dns_pkt = DNS(data)

        if dns_pkt.qr == 0 and dns_pkt.qd:
            qname = dns_pkt[DNSQR].qname.decode(
                'utf-8',
                errors='ignore'
            ).strip('.')
            client_ip = addr[0]

            is_banned = False

            with config.FORBIDDEN_LOCK:
                if client_ip in config.ACTIVE_BANNED_SITE_TARGETS:
                    for regex_sablonu in config.ACTIVE_BANNED_SITE_TARGETS[client_ip]:
                        try:
                            if re.search(
                                regex_sablonu,
                                qname,
                                re.IGNORECASE
                            ):
                                is_banned = True
                                break
                        except Exception:
                            pass

            if is_banned:
                print(
                    f"\n[⚠️ DNS BLOCK] Target: {client_ip} -> "
                    f"'{qname}' was blocked!"
                )
                config.add_live_log(
                    client_ip,
                    qname,
                    status="BLOCKED"
                )

                #-------------------------------------------#
                # Creates a synthetic DNS response for a blocked domain.
                # The response preserves the original transaction context
                # while returning the configured local server address as
                # the A-record destination.
                #-------------------------------------------#
                fake_response = DNS(
                    id=dns_pkt.id,
                    qr=1,
                    aa=1,
                    qd=dns_pkt.qd,
                    an=DNSRR(
                        rrname=dns_pkt[DNSQR].qname,
                        type='A',
                        ttl=10,
                        rdata=config.MY_IP
                    )
                )

                dns_server.sendto(fake_response.build(), addr)
                return

            #-------------------------------------------#
            # Attempts DNS-over-HTTPS first so normal DNS resolution can
            # use an HTTPS transport before the traditional DNS fallback.
            # The complete DNS wire response is returned directly to the
            # original client when the DoH request succeeds.
            #-------------------------------------------#
            doh_response = query_doh(data)

            if doh_response:
                dns_server.sendto(doh_response, addr)
                return

            #-------------------------------------------#
            # Falls back to TCP DNS resolution when the DoH request fails.
            # The configured upstream DNS server is contacted over TCP port
            # 53, and the DNS message is sent with the required two-byte
            # length prefix used by DNS-over-TCP.
            #-------------------------------------------#
            real_dns_sock = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )
            real_dns_sock.settimeout(2.0)

            try:
                real_dns_sock.connect((config.REAL_DNS, 53))

                #-------------------------------------------#
                # Prefixes the DNS message with its two-byte network-order
                # length so the upstream TCP DNS server can determine where
                # the complete DNS request ends.
                #-------------------------------------------#
                length_prefix = len(data).to_bytes(
                    2,
                    byteorder='big'
                )
                real_dns_sock.sendall(length_prefix + data)

                resp_len_bytes = real_dns_sock.recv(2)
                resp_len = int.from_bytes(
                    resp_len_bytes,
                    byteorder='big'
                )
                response = real_dns_sock.recv(resp_len)
                dns_server.sendto(response, addr)

            except Exception:
                pass
            finally:
                real_dns_sock.close()

    except Exception:
        pass


def start_dns():
    #-------------------------------------------#
    # Creates the UDP DNS server socket, binds it to the configured local
    # address and DNS port, and continuously accepts incoming DNS requests.
    # Each request is processed in a separate daemon thread so multiple
    # clients can be handled concurrently.
    #-------------------------------------------#
    dns_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dns_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    dns_server.bind((config.MY_IP, config.DNS_PORT))

    print(
        f"[*] InfiniNET Dynamic DNS Module is active on "
        f"{config.MY_IP}:{config.DNS_PORT} (DoH supported)."
    )

    while True:
        try:
            data, addr = dns_server.recvfrom(2048)
            threading.Thread(
                target=process_dns_request,
                args=(dns_server, data, addr),
                daemon=True
            ).start()
        except Exception:
            pass
