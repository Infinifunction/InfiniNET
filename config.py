import threading
from collections import deque
import time
import hashlib
import datetime

#-------------------------------------------#
# Defines the core network security and access-control configuration.
# The static server address is kept at the required local network address,
# while the DNS and proxy ports define the network services used by the system.
#-------------------------------------------#
MY_IP = "192.168.1.101"
REAL_DNS = "1.1.1.1"
DNS_PORT = 53
PROXY_PORT = 8080

#-------------------------------------------#
# Stores the credentials used by the authorized administrative account.
# These values are consumed by the application's authentication layer.
#-------------------------------------------#
PERMISSION_USER = "meto"
PERMISSION_PASS = "123"

#-------------------------------------------#
# Maintains the set of IP addresses belonging to devices with an active
# authenticated session. Access is synchronized with SESSION_LOCK.
#-------------------------------------------#
ACTIVE_SESSIONS = set()

#-------------------------------------------#
# Stores dynamically configured MITM target mappings.
# Each client IP can be associated with a list of domains that are subject
# to the application's configured traffic-handling rules.
# Example structure: {"192.168.1.102": ["google.com", "instagram.com"]}
#-------------------------------------------#
ACTIVE_BANNED_SITE_TARGETS = {}

#-------------------------------------------#
# Provides synchronization primitives for shared session and target data.
# Locks prevent concurrent threads from modifying the same structures
# inconsistently.
#-------------------------------------------#
SESSION_LOCK = threading.Lock()
FORBIDDEN_LOCK = threading.Lock()

#-------------------------------------------#
# Defines global and per-device traffic-shaping limits.
# A value of 0 for the global limit means that no global bandwidth limit
# is configured. Individual limits are expressed in KB/s.
# Example: {"192.168.1.105": 512} limits that client to 512 KB/s.
#-------------------------------------------#
GENERAL_SPEED_LIMIT_KB = 0
SPECIAL_SPEED_LIMITS = {}
SPEED_LOCK = threading.Lock()

#-------------------------------------------#
# Keeps the most recent 100 live traffic or SNI log entries in memory.
# The deque automatically discards the oldest entry when its maximum
# capacity is reached.
#-------------------------------------------#
LIVE_LOGS = deque(maxlen=100)


def add_live_log(client_ip, target, status="ALLOWED"):
    #-------------------------------------------#
    # Adds a new live traffic event to the in-memory log.
    # Entries are inserted at the beginning so the newest event is available
    # first when the log is displayed by the application.
    #-------------------------------------------#
    timestamp = time.strftime("%H:%M:%S")
    LIVE_LOGS.appendleft({
        'Time': timestamp,
        'ip': client_ip,
        'target': target,
        'status': status
    })


#-------------------------------------------#
# Stores device fingerprint information indexed by client IP.
# The associated lock ensures that fingerprint records remain consistent
# when multiple threads process network activity simultaneously.
#-------------------------------------------#
DEVICE_FINGERPRINTS = {}
FINGERPRINT_LOCK = threading.Lock()


def record_fingerprint(ip, user_agent):
    #-------------------------------------------#
    # Ignores empty or generic User-Agent values because they do not provide
    # meaningful device-identification information for the fingerprint record.
    #-------------------------------------------#
    if not user_agent or user_agent == "Unknown / Generic Device":
        return

    with FINGERPRINT_LOCK:
        #-------------------------------------------#
        # Creates a deterministic fingerprint hash from the client's IP
        # address and User-Agent string. The shortened uppercase hash is
        # used as the application's compact fingerprint identifier.
        #-------------------------------------------#
        fp_raw = f"{ip}-{user_agent}".encode('utf-8')
        fp_hash = "FP-" + hashlib.md5(fp_raw).hexdigest()[:10].upper()

        if ip not in DEVICE_FINGERPRINTS:
            DEVICE_FINGERPRINTS[ip] = {
                'user_agent': user_agent,
                'hash': fp_hash,
                'first_seen': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        else:
            #-------------------------------------------#
            # Updates the stored fingerprint information when the client's
            # User-Agent changes. This keeps the latest observed identifier
            # synchronized with the corresponding client IP address.
            #-------------------------------------------#
            DEVICE_FINGERPRINTS[ip]['user_agent'] = user_agent
            DEVICE_FINGERPRINTS[ip]['hash'] = fp_hash
