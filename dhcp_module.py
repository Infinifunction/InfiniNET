import socket
import threading
import struct
import config
import InfiniDB

#-------------------------------------------#
# Defines the DHCP option codes used when constructing DHCP response packets.
# These constants identify network parameters such as the subnet mask,
# gateway, DNS server, lease duration, message type, server identifier,
# and WPAD configuration.
#-------------------------------------------#
OPTION_SUBNET_MASK = 1
OPTION_ROUTER = 3
OPTION_DNS = 6
OPTION_LEASE_TIME = 51
OPTION_DHCP_MSG_TYPE = 53
OPTION_SERVER_ID = 54
OPTION_WPAD = 252

#-------------------------------------------#
# Maintains the in-memory DHCP lease table.
# Each client MAC address is mapped to the IP address currently assigned
# to that client. The index tracks the next address in the configured
# 192.168.1.105-192.168.1.200 allocation range.
#-------------------------------------------#
LEASED_IPS = {}
IP_POOL_LAST_INDEX = 105


def wrap_ip(ip_str):
    #-------------------------------------------#
    # Converts a dotted-decimal IPv4 address into its packed four-byte
    # representation so it can be inserted directly into binary network
    # protocol structures.
    #-------------------------------------------#
    return socket.inet_aton(ip_str)


def get_ip_from_pool(client_mac):
    #-------------------------------------------#
    # Returns the existing DHCP lease for a known client or assigns the
    # next available address from the configured local IP allocation range.
    # The allocation index wraps back to the beginning when the upper
    # boundary of the pool is reached.
    #-------------------------------------------#
    global IP_POOL_LAST_INDEX

    if client_mac in LEASED_IPS:
        return LEASED_IPS[client_mac]

    #-------------------------------------------#
    # Advances through the configured 192.168.1.105-192.168.1.200 address
    # range and wraps back to 192.168.1.105 after reaching the upper limit.
    #-------------------------------------------#
    IP_POOL_LAST_INDEX += 1
    if IP_POOL_LAST_INDEX > 200:
        IP_POOL_LAST_INDEX = 105

    new_ip = f"192.168.1.{IP_POOL_LAST_INDEX}"
    LEASED_IPS[client_mac] = new_ip
    return new_ip


def create_dhcp_packet(xid, client_mac, yiaddr, msg_type):
    #-------------------------------------------#
    # Builds the binary DHCP response header using the transaction ID,
    # client hardware address, assigned IP address, and DHCP message type.
    # The resulting structure follows the standard BOOTP/DHCP header layout.
    #-------------------------------------------#
    op = 2
    htype = 1
    hlen = 6
    hops = 0

    header = struct.pack(
        '!BBBBIHH4s4s4s4s16s64s128s',
        op, htype, hlen, hops, xid, 0, 0,
        b'\x00\x00\x00\x00',
        wrap_ip(yiaddr),
        wrap_ip(config.MY_IP),
        b'\x00\x00\x00\x00',
        client_mac + b'\x00' * 10,
        b'\x00' * 64,
        b'\x00' * 128
    )

    #-------------------------------------------#
    # Appends the DHCP magic cookie that marks the beginning of the
    # DHCP options section according to the DHCP/BOOTP packet format.
    #-------------------------------------------#
    magic_cookie = b'\x63\x82\x53\x63'

    #-------------------------------------------#
    # Constructs the DHCP option payload containing the response type,
    # server identifier, one-day lease duration, subnet mask, gateway,
    # DNS server, and the application's WPAD auto-proxy configuration.
    #-------------------------------------------#
    options = bytearray()
    options.extend(
        struct.pack('!BBB', OPTION_DHCP_MSG_TYPE, 1, msg_type)
    )
    options.extend(
        struct.pack('!BB4s', OPTION_SERVER_ID, 4, wrap_ip(config.MY_IP))
    )
    options.extend(
        struct.pack('!BB4s', OPTION_LEASE_TIME, 4, struct.pack('!I', 86400))
    )
    options.extend(
        struct.pack('!BB4s', OPTION_SUBNET_MASK, 4, wrap_ip('255.255.255.0'))
    )
    options.extend(
        struct.pack('!BB4s', OPTION_ROUTER, 4, wrap_ip(config.MY_IP))
    )
    options.extend(
        struct.pack('!BB4s', OPTION_DNS, 4, wrap_ip(config.MY_IP))
    )

    #-------------------------------------------#
    # Encodes the WPAD configuration as DHCP option 252.
    # Clients that support WPAD can use this URL to locate the automatic
    # proxy configuration exposed by the local application.
    #-------------------------------------------#
    wpad_url = f"http://{config.MY_IP}/wpad.dat".encode('utf-8')
    options.extend(
        struct.pack(f'!BB{len(wpad_url)}s', OPTION_WPAD, len(wpad_url), wpad_url)
    )

    #-------------------------------------------#
    # Marks the end of the DHCP option list before returning the complete
    # binary response packet to the caller.
    #-------------------------------------------#
    options.append(255)

    return header + magic_cookie + bytes(options)


def dhcp_listener():
    #-------------------------------------------#
    # Creates and configures the UDP socket used by the DHCP listener.
    # Broadcast support and address reuse are enabled because DHCP clients
    # commonly communicate through broadcast traffic during discovery.
    #-------------------------------------------#
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    try:
        #-------------------------------------------#
        # Binds the listener to the standard DHCP server port on all local
        # interfaces. Binding to this privileged port may require elevated
        # operating-system permissions.
        #-------------------------------------------#
        server.bind(('0.0.0.0', 67))
        print(
            "[*] InfiniDHCP Server is active on UDP port 67. "
            "(Gateway, DNS, and Auto-Proxy configuration are being distributed)"
        )
    except Exception as error:
        print(
            f"[!] DHCP Server Bind Error (Administrator privileges required): {error}"
        )
        return

    while True:
        try:
            data, addr = server.recvfrom(2048)

            #-------------------------------------------#
            # DHCP packets require a minimum BOOTP header size. Invalid or
            # incomplete packets are ignored before any field is parsed.
            #-------------------------------------------#
            if len(data) < 240:
                continue

            xid = struct.unpack('!I', data[4:8])[0]
            client_mac = data[28:34]
            mac_str = ":".join(f"{byte:02x}" for byte in client_mac)

            #-------------------------------------------#
            # Parses the DHCP options area to identify the DHCP message type.
            # Option 53 distinguishes requests such as DISCOVER and REQUEST,
            # allowing the listener to select the appropriate response.
            #-------------------------------------------#
            options_data = data[240:]
            msg_type = None
            i = 0

            while i < len(options_data):
                option_code = options_data[i]

                if option_code == 255:
                    break

                if option_code == 0:
                    i += 1
                    continue

                option_length = options_data[i + 1]

                if option_code == 53:
                    msg_type = options_data[i + 2]
                    break

                i += 2 + option_length

            assigned_ip = get_ip_from_pool(client_mac)

            if msg_type == 1:
                #-------------------------------------------#
                # Handles a DHCP DISCOVER message by creating and broadcasting
                # a DHCP OFFER containing the IP address selected for the client.
                #-------------------------------------------#
                print(
                    f"[📡 DHCP DISCOVER] Client MAC: {mac_str} "
                    f"➡️ Offered IP: {assigned_ip}"
                )
                offer_packet = create_dhcp_packet(
                    xid,
                    client_mac,
                    assigned_ip,
                    msg_type=2
                )
                server.sendto(offer_packet, ('255.255.255.255', 68))

            elif msg_type == 3:
                #-------------------------------------------#
                # Handles a DHCP REQUEST message by generating a DHCP ACK,
                # confirming the selected address and completing the lease
                # process for the requesting client.
                #-------------------------------------------#
                print(
                    f"[✅ DHCP REQUEST] Client MAC: {mac_str} "
                    f"➡️ Confirmed IP: {assigned_ip}"
                )
                ack_packet = create_dhcp_packet(
                    xid,
                    client_mac,
                    assigned_ip,
                    msg_type=5
                )
                server.sendto(ack_packet, ('255.255.255.255', 68))

                #-------------------------------------------#
                # Registers the newly assigned client address in the database
                # and in the application's in-memory active-session collection.
                # The existing database API name is preserved because it belongs
                # to the imported InfiniDB module.
                #-------------------------------------------#
                InfiniDB.db_oturum_ekle(assigned_ip)

                with config.SESSION_LOCK:
                    if isinstance(config.ACTIVE_SESSIONS, set):
                        config.ACTIVE_SESSIONS.add(assigned_ip)
                    elif assigned_ip not in config.ACTIVE_SESSIONS:
                        config.ACTIVE_SESSIONS.append(assigned_ip)

        except Exception:
            #-------------------------------------------#
            # Keeps the DHCP listener running when an individual packet causes
            # an unexpected processing error. The current behavior intentionally
            # suppresses packet-level exceptions so one malformed request does
            # not terminate the long-running listener thread.
            #-------------------------------------------#
            pass


def start_dhcp():
    #-------------------------------------------#
    # Starts the DHCP listener in a daemon background thread so the listener
    # operates independently while allowing the main application to continue
    # executing normally.
    #-------------------------------------------#
    threading.Thread(target=dhcp_listener, daemon=True).start()
