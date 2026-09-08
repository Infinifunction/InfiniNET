# InfiniDB.py
import sqlite3
from datetime import datetime
import re

DB_NAME = "infini_dhcp.db"

def get_connection():
    """Create and return a new SQLite database connection."""
    return sqlite3.connect(DB_NAME)

def init_db():
    """Create the database tables required by the system during initialization if they do not already exist."""
    conn = get_connection()
    cursor = conn.cursor()
    
    #-------------------------------------------#
    # Create the table used to persist currently active device sessions.
    # It stores each client IP together with the time its session began.
    #-------------------------------------------#
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ACTIVE_SESSIONS (
        ip TEXT PRIMARY KEY,
        entry_time TEXT
    )""")
    
    #-------------------------------------------#
    # Create the table that stores site-blocking rules for individual client IPs.
    # The IP/site combination is constrained to remain unique.
    #-------------------------------------------#
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS blocked_sites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ip TEXT,
        site TEXT,
        UNIQUE(ip, site)
    )""")
    
    #-------------------------------------------#
    # Create the table used to persist access-attempt logs, including timestamps,
    # client IP addresses, account fields, and the resulting status.
    #-------------------------------------------#
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS access_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time TEXT,
        ip TEXT,
        user TEXT,
        password TEXT,
        status TEXT
    )""")
    
    conn.commit()
    conn.close()
    print("[*] SQLite database schema has been verified and is ready.")

#-------------------------------------------#
# Database logging functions.
# This section handles persistent recording of access attempts.
#-------------------------------------------#
def write_db_log(ip, user, password, status):
    """Store an access attempt in the database with its timestamp, client IP, account fields, and status."""
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO access_logs (time, ip, user, password, status) VALUES (?, ?, ?, ?, ?)",
        (time, ip, user, password, status)
    )
    conn.commit()
    conn.close()

#-------------------------------------------#
# Database session management functions.
# This section manages persisted active-session records.
#-------------------------------------------#
def add_db_session(ip):
    """Persist a newly established session for the specified client IP address."""
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR REPLACE INTO ACTIVE_SESSIONS (ip, entry_time) VALUES (?, ?)", (ip, time))
        conn.commit()
    except Exception as e:
        print(f"[-] Database session insertion error: {e}")
    finally:
        conn.close()

def load_active_db_sessions():
    """Load the IP addresses of previously active sessions from the database into memory."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ip FROM ACTIVE_SESSIONS")
    sessions = [row[0] for row in cursor.fetchall()]
    conn.close()
    return sessions

def delete_db_session(ip):
    """Remove the specified client session from the database and report whether a record was deleted."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ACTIVE_SESSIONS WHERE ip = ?", (ip,))
    rowcount = cursor.rowcount
    conn.commit()
    conn.close()
    return rowcount > 0

#-------------------------------------------#
# Block-rule management functions.
# This section stores, removes, validates, and reloads site-blocking rules.
#-------------------------------------------#
def add_db_block_rule(ip, site):
    """Add and validate a site-blocking rule associated with a client IP address."""
    #-------------------------------------------#
        # Validate the supplied pattern before storing it so malformed regular
        # expressions cannot be persisted as blocking rules.
        #-------------------------------------------#
    try:
        re.compile(site)
    except re.error:
        print(f"[-] ERROR: Invalid regular expression format -> {site}")
        return False

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO blocked_sites (ip, site) VALUES (?, ?)", (ip, site))
        conn.commit()
        return True
    except Exception as e:
        print(f"[-] Database block-rule insertion error: {e}")
        return False
    finally:
        conn.close()

def delete_db_block_rule(ip, site):
    """Remove a site-blocking rule associated with the specified client IP address."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM blocked_sites WHERE ip = ? AND site = ?", (ip, site))
    number_of_rows = cursor.rowcount
    conn.commit()
    conn.close()
    return number_of_rows > 0

def load_db_block_rules():
    """Load all stored site-blocking rules into an in-memory dictionary during system startup."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ip, site FROM blocked_sites")
    prohibitions = {}
    for ip, site in cursor.fetchall():
        if ip not in prohibitions:
            prohibitions[ip] = []
        if site not in prohibitions[ip]:
            prohibitions[ip].append(site)
    conn.close()
    return prohibitions