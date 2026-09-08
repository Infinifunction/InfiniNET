# admin/routes/api_system.py
from flask import Blueprint, jsonify, request
import config
import InfiniDB
import socket
import os
import platform
import subprocess

try:
    import auto_reloader
except ImportError:
    auto_reloader = None

api_system_bp = Blueprint('api_system', __name__)

#-------------------------------------------#
# Measures ICMP reachability and extracts the response time in a platform-aware way.
# It selects operating-system-specific ping arguments and returns a latency value.
#-------------------------------------------
def measure_ping(ip):
    try:
        #-------------------------------------------#
        # Selects the appropriate ping and timeout flags because Windows and Unix-like systems
        # use different command-line conventions for these parameters.
        #-------------------------------------------
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        timeout_param = '-w' if platform.system().lower() == 'windows' else '-W'
        
        output = subprocess.check_output(
            ['ping', param, '1', timeout_param, '1000', ip],
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        #-------------------------------------------#
        # Parses the response-time format commonly returned by Windows ping and converts
        # the extracted millisecond value into an integer for the API response.
        #-------------------------------------------
        if "time=" in output:
            time_str = output.split("time=")[1].split("ms")[0].strip()
            return int(float(time_str))
        #-------------------------------------------#
        # Handles the compact response notation used when a Unix-like ping reports a
        # response time below one millisecond.
        #-------------------------------------------
        elif "time<" in output:
            return 1
        #-------------------------------------------#
        # Provides a small fallback latency when the command succeeded but its output did
        # not match any response-time format handled above.
        #-------------------------------------------
        return 15
    except Exception:
        #-------------------------------------------#
        # Returns zero when the target cannot provide a usable ping response or the ping
        # operation fails before a latency measurement can be extracted.
        #-------------------------------------------
        return 0

@api_system_bp.route('/admin/api/system/status', methods=['GET'])
def get_status():
    bans_list = []
    
    #-------------------------------------------#
    # Reads the active ban dictionary while holding its synchronization lock so concurrent
    # requests cannot observe an inconsistent state during updates.
    #-------------------------------------------
    with config.FORBIDDEN_LOCK:
        raw_bans = getattr(config, 'ACTIVE_BANNED_SITE_TARGETS', {})
        for ip, sites in raw_bans.items():
            for target in sites:
                bans_list.append({'ip': ip, 'target': target})

    #-------------------------------------------#
    # Converts per-IP bandwidth limits into a frontend-friendly list containing both
    # the stored KB value and a rounded MB-equivalent value.
    #-------------------------------------------
    speed_limits_list = []
    with config.SPEED_LOCK:
        raw_speeds = getattr(config, 'SPECIAL_SPEED_LIMITS', {})
        for ip, limit_kb in raw_speeds.items():
            speed_limits_list.append({
                'ip': ip,
                'limit_kb': limit_kb,
                'limit_mb': round(limit_kb / 1024, 2)
            })

    return jsonify({
        'active_sessions': list(getattr(config, 'ACTIVE_SESSIONS', set())),
        'bans': bans_list,
        'special_speeds': speed_limits_list,
        'general_speed_limit': getattr(config, 'GENERAL_SPEED_LIMIT_KB', 0),
        'live_logs': list(getattr(config, 'LIVE_LOGS', []))
    })

@api_system_bp.route('/admin/api/devices', methods=['GET'])
def get_devices():
    devices = []
    
    with config.SESSION_LOCK:
        active_threads = list(getattr(config, 'ACTIVE_SESSIONS', set()))

    #-------------------------------------------#
    # Retrieves device fingerprints and live traffic statistics maintained in memory,
    # using empty dictionaries when the corresponding configuration is unavailable.
    #-------------------------------------------
    fingerprints = getattr(config, 'DEVICE_FINGERPRINTS', {})
    traffic_stats = getattr(config, 'DEVICE_TRAFFIC_STATISTICS', {})

    for ip in active_threads:
        #-------------------------------------------#
        # Attempts reverse DNS resolution for each active client IP. If resolution fails,
        # a deterministic fallback hostname is generated from the final IP octet.
        #-------------------------------------------
        try:
            hostname = socket.gethostbyaddr(ip)[0]
        except:
            hostname = f"Device-{ip.split('.')[-1]}"

        #-------------------------------------------#
        # Determines a broad device category from the stored user-agent fingerprint so
        # the administration interface can display a readable device type and icon.
        #-------------------------------------------
        fp_info = fingerprints.get(ip, {})
        user_agent = fp_info.get('user_agent', 'Unknown / Generic Device')
        
        #-------------------------------------------#
        # Refines the device classification using recognizable Android, Apple, Windows,
        # macOS, and Linux user-agent markers, including Samsung model identifiers.
        #-------------------------------------------
        device_type = "Unknown Device"
        icon = "💻"
        
        if "Android" in user_agent or "Dalvik" in user_agent:
            #-------------------------------------------#
            # Extracts a Samsung model identifier from the user-agent when an SM-series marker
            # is present and falls back to a generic Android phone label if parsing fails.
            #-------------------------------------------
            if "SM-" in user_agent:
                try:
                    model = user_agent.split("SM-")[1].split(";")[0].split(")")[0].strip()
                    device_type = f"Samsung (SM-{model})"
                except:
                    device_type = "Android Phone"
            else:
                device_type = "Android Device"
            icon = "📱"
        elif "iPhone" in user_agent or "iPad" in user_agent:
            device_type = "iOS Device"
            icon = "📱"
        elif "Windows" in user_agent:
            device_type = "Windows PC"
            icon = "💻"
        elif "Macintosh" in user_agent:
            device_type = "Mac / macOS"
            icon = "💻"
        elif "Linux" in user_agent:
            device_type = "Linux Server/PC"
            icon = "🐧"

        #-------------------------------------------#
        # Reads the latest download and upload measurements for the current device from
        # the in-memory traffic statistics, defaulting to zero when no data is available.
        #-------------------------------------------
        ip_traffic = traffic_stats.get(ip, {})
        download_mbps = ip_traffic.get('download_mbps', 0.0)
        upload_mbps = ip_traffic.get('upload_mbps', 0.0)
        
        #-------------------------------------------#
        # Performs a reachability and latency check so the device status response includes
        # a current ping measurement alongside its traffic and fingerprint information.
        #-------------------------------------------
        ping_val = measure_ping(ip)

        devices.append({
            'ip': ip,
            'hostname': hostname,
            'device_type': device_type,
            'icon': icon,
            'user_agent': user_agent,
            'fingerprint_hash': fp_info.get('hash', 'FP-' + ip.replace('.', '')),
            'first_seen': fp_info.get('first_seen', 'Active Session'),
            #-------------------------------------------#
            # Adds connectivity and traffic metrics to the device record returned to the
            # administration frontend.
            #-------------------------------------------
            'ping': ping_val,
            'download_mbps': download_mbps,
            'upload_mbps': upload_mbps
        })

    return jsonify({'status': 'success', 'devices': devices})

@api_system_bp.route('/admin/api/system/reload', methods=['POST'])
def trigger_reload():
    if auto_reloader and hasattr(auto_reloader, 'start_hot_reload'):
        auto_reloader.start_hot_reload()
        return jsonify({'status': 'success', 'message': 'Hot Reload triggered successfully!'})
    return jsonify({'status': 'error', 'message': 'Hot reloader module could not be loaded.'}), 500

@api_system_bp.route('/admin/api/sessions/logout', methods=['POST'])
def session_logout():
    data = request.get_json() or {}
    ip = data.get('ip', '').strip()
    
    if not ip:
        return jsonify({'status': 'error', 'message': 'IP address was not specified.'}), 400

    #-------------------------------------------#
    # Removes the session from persistent database storage first so the client is no
    # longer represented as an active session after logout.
    #-------------------------------------------
    InfiniDB.delete_db_session(ip)

    #-------------------------------------------#
    # Removes the client IP from the in-memory active-session collection while holding
    # its synchronization lock and supports both set and list representations.
    #-------------------------------------------
    with config.SESSION_LOCK:
        if isinstance(config.ACTIVE_SESSIONS, set):
            config.ACTIVE_SESSIONS.discard(ip)
        elif isinstance(config.ACTIVE_SESSIONS, list):
            if ip in config.ACTIVE_SESSIONS:
                config.ACTIVE_SESSIONS.remove(ip)

    return jsonify({'status': 'success', 'message': f'{ip} session has been logged out.'})
