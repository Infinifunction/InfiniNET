# InfiniNET

> **Gateway-based network configuration, access control, traffic monitoring and network management system.**

InfiniNET is a Python-based network management system designed to operate as a **Gateway** for a local network. The Gateway device provides network services such as DHCP, DNS, proxying and WPAD, while also offering a web-based administration panel for monitoring and managing connected devices.

The project is intended for **authorized network administration, testing, development and educational purposes**.

---

## ✨ Features

InfiniNET provides a centralized set of network management capabilities.

### Network Management

- Gateway-based network management
- DHCP server functionality
- Automatic IP address assignment
- DNS server / DNS proxy functionality
- DNS-based domain blocking
- HTTP/HTTPS proxy functionality
- WPAD / PAC configuration distribution
- Static Gateway IP requirement
- Active session management

### Captive Portal

- Captive Portal authentication flow
- Administrator-defined username and password
- Access control for devices joining the network
- Unauthorized-client access handling
- Login/access event recording

### Traffic Monitoring

- Live traffic monitoring
- Live traffic logs
- HTTP request monitoring
- HTTPS SNI inspection for configured blocking rules
- Download / upload activity indicators
- Real-time network status information

### Speed Control

- Device-specific bandwidth limit
- Global network bandwidth limit
- Dynamic speed-limit management from the admin panel
- Ability to remove a device-specific limit

### Device Management

- Active device detection
- IP address information
- Hostname information
- User-Agent information
- Device type information
- Device fingerprint data
- Fingerprint hash
- First-seen information
- Device ping/status information
- Traffic direction indicators
- Ability to terminate a device session
- Device inventory interface

### Database

InfiniNET uses SQLite through the `InfiniDB.py` database layer.

The database system is used for storing and restoring project state such as:

- Active sessions
- Blocking rules
- Access logs
- Device/session-related records

The project also contains a web-based database browser for viewing available SQLite tables and their records.

### Administration Panel

The Flask-based administration panel provides interfaces for:

- Dashboard statistics
- Active sessions
- Blocking rules
- Global and device-specific speed limits
- Live traffic information
- Device inventory
- Device details
- Fingerprint information
- Database browsing
- Session termination
- Hot-reload triggering

---

## 🏗️ System Architecture

The main entry point of the project is:

```text
InfiniDHCP.py
```

The intended operating model is:

```text
                    ┌─────────────────────────┐
                    │      Admin / Manager    │
                    │     Web Administration  │
                    └────────────┬────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────┐
│                       InfiniNET Gateway                      │
│                                                              │
│  DHCP        DNS        Proxy        WPAD        Captive     │
│  Server      Server     Layer        Service     Portal      │
│                                                              │
│                 InfiniDB / Runtime State                     │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               │
                 ┌─────────────┴─────────────┐
                 │        Local Network      │
                 └─────────────┬─────────────┘
                               │
               ┌───────────────┼────────────────┐
               │               │                │
             Device A        Device B         Device C
```

### How the system works

1. The device selected as the Gateway starts `InfiniDHCP.py`.
2. The Gateway provides DHCP service to connected clients.
3. Clients receive IP addresses from the configured range.
4. The Gateway provides gateway, DNS and WPAD information through DHCP.
5. DNS requests are handled by the project's DNS layer.
6. HTTP/HTTPS traffic is processed through the proxy layer.
7. Clients are directed through the Captive Portal authentication flow according to the active configuration.
8. Authorized users can access the network according to the configured rules.
9. The administration panel provides live visibility and management controls.

---

## 📦 Requirements

### Software

- Python **3.10**
- Npcap
- SQLite
- JavaScript-enabled web browser

### Python Dependencies

The current `requirements.txt` contains:

```text
Flask==3.1.3
scapy==2.7.0
```

The dependency list should always be installed using the repository's `requirements.txt` file.

---

## 🚀 Installation

### 1. Install Python

Install **Python 3.10** on the Gateway machine.

Verify the installation:

```bash
python --version
```

Expected version:

```text
Python 3.10.x
```

### 2. Install Npcap

Install **Npcap** on systems where packet capture support is required.

### 3. Install Python dependencies

From the project root:

```bash
pip install -r requirements.txt
```

### 4. Configure the Gateway IP

The Gateway device must use a **static IP address**.

Required Gateway IP:

```text
192.168.1.101
```

Make sure this address does not conflict with another device on the network.

### 5. Start InfiniNET

Run the main launcher:

```bash
python InfiniDHCP.py
```

The main launcher initializes the project's core components and starts the required services.

---

## 📁 Project Structure

```text
InfiniNET/
│
├── auto_reloader.py
├── config.py
├── dhcp_module.py
├── dns_module.py
├── InfiniDB.py
├── InfiniDHCP.py
├── proxy_module.py
├── requirements.txt
├── templates.py
├── wpad_module.py
│
└── admin/
    ├── app.py
    │
    ├── routes/
    │   ├── api_bans.py
    │   ├── api_db.py
    │   ├── api_speed.py
    │   └── api_system.py
    │
    ├── static/
    │   ├── css/
    │   │   └── style.css
    │   └── js/
    │       └── dashboard.js
    │
    └── templates/
        ├── dashboard.html
        ├── db_browser.html
        └── devices.html
```

---

## 🧩 Core Modules

### `InfiniDHCP.py`

The main orchestrator and application launcher.

It loads the database and saved state, initializes hot-reload, DNS, WPAD, DHCP, console and administration components, and then starts the proxy layer.

### `dhcp_module.py`

The DHCP server module.

Responsibilities include:

- Listening for DHCP requests on UDP port 67
- Assigning addresses from `192.168.1.105`–`192.168.1.200`
- Creating DHCP OFFER and ACK packets
- Recording client IP information
- Providing gateway, DNS and WPAD information to clients

### `dns_module.py`

The DNS server / proxy layer.

It:

- Receives DNS queries over UDP
- Checks client-specific domain blocking rules
- Returns a local address for blocked domains
- Uses DNS-over-HTTPS for non-blocked domains
- Falls back to the configured DNS server over TCP/53 if DoH fails
- Processes DNS requests concurrently

### `proxy_module.py`

The HTTP/HTTPS proxy layer.

It:

- Accepts client connections
- Processes HTTP requests
- Handles unauthorized-client access flows
- Checks active blocking rules
- Transfers authorized traffic
- Inspects SNI information for HTTPS CONNECT requests
- Applies configured speed limits during traffic transfer

### `InfiniDB.py`

The SQLite database layer.

It manages database connections and stores project data such as:

- Active sessions
- Blocking rules
- Access logs

It also restores stored information into runtime memory when the application starts.

### `config.py`

Central runtime configuration and state management.

It contains or manages values related to:

- IP settings
- DNS configuration
- Proxy configuration
- Sessions
- Site targets
- Speed limits
- Live logs
- Device fingerprint information

### `wpad_module.py`

The WPAD service.

It runs a small HTTP server on TCP port 80 and provides a PAC configuration containing `FindProxyForURL`.

The proxy address and port are obtained dynamically from the project configuration.

### `templates.py`

Provides the dynamically generated HTML used by the access/login interface.

### `auto_reloader.py`

Monitors project `.py`, `.js`, `.html` and `.css` files and reloads relevant Python modules when changes are detected.

---

## 🖥️ Administration Panel

The administration panel is built with Flask.

### `admin/app.py`

Application entry point for the administration panel.

It:

- Registers API blueprints
- Serves static files
- Provides dashboard, database browser and device routes
- Starts the administration server

### API Routes

#### Ban Management — `api_bans.py`

```text
POST   /admin/api/bans/add
DELETE /admin/api/bans/remove
```

Used to add and remove IP/regex blocking rules.

Blocking rules are stored in the database and synchronized with the in-memory blocking list.

#### Database API — `api_db.py`

```text
GET /admin/api/db/tables
GET /admin/api/db/query/<table_name>
```

Provides access to database table information through JSON responses.

The table query endpoint returns up to 100 records.

#### Speed Management — `api_speed.py`

```text
POST /admin/api/speed/ip
POST /admin/api/speed/everyone
```

Used to manage device-specific and global bandwidth limits.

A device-specific limit of `0` removes the custom limit.

#### System and Device API — `api_system.py`

Provides information and operations for:

- System status
- Active sessions
- Blocking rules
- Speed limits
- Live logs
- Active devices
- Hostnames
- User-Agent data
- Device types
- Fingerprints
- Ping information
- Download/upload indicators
- Hot-reload
- Session termination

---

## 🎨 Frontend

### `dashboard.html`

Main administration dashboard.

It provides:

- System status
- Active sessions
- Blocking information
- Speed limit controls
- Live traffic/SNI information
- Device inventory navigation
- Database browser navigation

### `devices.html`

Device inventory and device details interface.

It displays information such as:

- Fingerprint data
- Device type
- Fingerprint hash
- First-seen timestamp
- User-Agent
- Real-time ping
- Bandwidth information
- Traffic direction

### `db_browser.html`

Web interface for browsing the SQLite database.

It loads available tables from the backend API and dynamically displays selected table records.

### `dashboard.js`

Client-side JavaScript responsible for:

- Dashboard statistics
- Active sessions
- Blocking rules
- Speed limits
- Live traffic
- Device list
- Device details modal
- Device status updates
- Session termination
- Ban actions
- Speed-limit actions
- Hot-reload requests

### `style.css`

Main administration-panel stylesheet containing layouts, tables, controls, device cards, status indicators, modals and other UI components.

---

## 🔐 Security & Ethical Use

InfiniNET is designed as a **network administration and management tool**.

It must only be deployed on networks, systems and devices for which the operator has appropriate authorization.

The project does **not** grant permission to monitor, intercept, block, throttle or otherwise control third-party network traffic. The operator is solely responsible for ensuring that the system is used in compliance with applicable laws, regulations, organizational policies and user-consent requirements.

### Important notice

InfiniFunction and its contributors do not authorize or endorse unlawful use of the software.

InfiniFunction and its contributors are not responsible for damage, unauthorized access, privacy violations, data misuse, unlawful monitoring, service disruption or any other consequences resulting from improper, illegal or unauthorized use of the project.

**Use InfiniNET only in environments where you have explicit administrative authority or appropriate permission.**

---

## 🔒 Privacy & Data Protection Notice

InfiniNET includes a database and runtime monitoring system that operates on the machine where the Gateway is installed.

Depending on configuration, the system may process network-management information such as:

- IP addresses
- Session information
- Access timestamps
- Hostnames
- User-Agent information
- Device/fingerprint information
- Domain or traffic-related records
- Administrative logs

The operator is responsible for determining what information is collected, why it is collected, how long it is retained, who can access it and whether consent or additional disclosure is legally required.

The database should be protected from unauthorized access and should not be exposed publicly without appropriate security controls.

InfiniFunction and its contributors are not responsible for data leakage, unauthorized database access, misuse of collected information, or violations caused by the deployment or configuration of the system.

**Before deploying the project in a real environment, review your applicable privacy, data-protection and network-monitoring obligations.**

---

## ⚠️ Limitations & Known Issues

The project has been tested according to the development environment and no known functional issue was identified at the time of documentation.

However:

- Network environments can behave differently.
- Operating-system configuration may affect networking components.
- Firewall or packet-capture settings may affect functionality.
- Changes to dependencies or runtime environments may introduce incompatibilities.
- Localization or language changes may introduce unexpected errors in parts of the application.

If an issue occurs after modifying language, templates, JavaScript, CSS or other project files, the person making the change is responsible for validating the resulting behavior.

For reproducible issues that are believed to originate from the project itself, open a GitHub Issue and include:

- Operating system
- Python version
- Relevant error/output
- Steps to reproduce the problem
- Affected component/file
- Configuration information that can be safely shared

Do **not** include passwords, private network credentials, sensitive personal data or confidential logs in public issues.

---

## 🛠️ Development

Because InfiniNET contains multiple network services and a web administration interface, changes to one component may affect other components.

Before committing changes, test at minimum:

- DHCP behavior
- DNS resolution
- Proxy behavior
- Captive Portal access flow
- Speed-limit functionality
- Blocking rules
- Device detection
- Database operations
- Administration APIs
- Frontend updates

---

## 📌 Current Gateway Configuration

The default/required Gateway address for this project is:

```text
192.168.1.101
```

DHCP client pool:

```text
192.168.1.105 - 192.168.1.200
```

---

## 🤝 Contributing

Contributions, bug reports and improvements are welcome.

When submitting a pull request:

1. Keep changes focused.
2. Avoid unnecessary modifications to unrelated modules.
3. Test affected network components.
4. Document behavior-changing changes.
5. Never submit credentials, private network information or sensitive logs.

---

## 🐛 Issues

Please use GitHub Issues for reproducible bugs, feature requests and technical problems.

For security-sensitive problems, avoid posting confidential details publicly. Use the project's designated private reporting channel when one is available.

---

## 📚 Documentation

The following files are especially useful when understanding the project:

- `InfiniDHCP.py` — application entry point
- `config.py` — central configuration/runtime state
- `dhcp_module.py` — DHCP service
- `dns_module.py` — DNS service
- `proxy_module.py` — HTTP/HTTPS proxy
- `InfiniDB.py` — SQLite database layer
- `wpad_module.py` — WPAD service
- `admin/` — administration panel

---

## 🇹🇷 Türkçe Dokümantasyon

Türkçe dokümantasyon için:

**[README.tr.md](README.tr.md)**

---

## 📜 Disclaimer

This software is provided for legitimate network administration, testing, development and educational use.

The authors and contributors make no guarantee that the software is suitable for every environment and assume no responsibility for unauthorized deployment, unlawful monitoring, data misuse, privacy violations, network disruption or other consequences arising from its use.

**The responsibility for lawful and authorized use rests entirely with the operator.**
