from flask import Blueprint, jsonify, request
import config
import InfiniDB

api_bans_bp = Blueprint('api_bans', __name__)

@api_bans_bp.route('/admin/api/bans/add', methods=['POST'])
def add_ban():
    data = request.json or {}
    ip = data.get('ip', '').strip()
    regex = data.get('regex', '').strip()
    
    #-------------------------------------------#
    # If the request does not specify a client IP address, use the project's
    # existing global-target sentinel value so the rule applies to the
    # general network scope instead of being associated with a specific client.
    #-------------------------------------------
    if not ip:
        ip = "ALL"

    if regex:
        #-------------------------------------------#
        # Persist the requested blocking rule in the database first. The rule
        # is added to the in-memory configuration only when this database
        # operation succeeds, keeping persistent and runtime state synchronized.
        #-------------------------------------------
        if InfiniDB.add_db_block_rule(ip, regex):
            #-------------------------------------------#
            # Update the in-memory blocking-rule collection while holding the
            # shared lock. This prevents concurrent requests from modifying
            # the same dictionary or its rule lists at the same time.
            #-------------------------------------------
            with config.FORBIDDEN_LOCK:
                if ip not in config.ACTIVE_BANNED_SITE_TARGETS:
                    config.ACTIVE_BANNED_SITE_TARGETS[ip] = []
                if regex not in config.ACTIVE_BANNED_SITE_TARGETS[ip]:
                    config.ACTIVE_BANNED_SITE_TARGETS[ip].append(regex)
            
            return jsonify({'status': 'success', 'message': 'Block rule added.'})
        return jsonify({'status': 'error', 'message': 'Database or regex error.'}), 400

    return jsonify({'status': 'error', 'message': 'Regex cannot be empty.'}), 400

@api_bans_bp.route('/admin/api/bans/remove', methods=['DELETE'])
def remove_ban():
    data = request.json or {}
    ip = data.get('ip', 'HEPSİ').strip()
    regex = data.get('regex', '').strip()
    
    if regex:
        #-------------------------------------------#
        # Remove the blocking rule from persistent storage before updating
        # the runtime collection, so the database and active configuration
        # remain aligned with the requested administrative change.
        #-------------------------------------------
        InfiniDB.delete_db_block_rule(ip, regex)
        
        #-------------------------------------------#
        # Remove the rule from the in-memory collection under the shared lock.
        # Empty rule lists are deleted afterward so the runtime configuration
        # does not retain unnecessary client entries.
        #-------------------------------------------
        with config.FORBIDDEN_LOCK:
            if ip in config.ACTIVE_BANNED_SITE_TARGETS:
                if regex in config.ACTIVE_BANNED_SITE_TARGETS[ip]:
                    config.ACTIVE_BANNED_SITE_TARGETS[ip].remove(regex)
                if not config.ACTIVE_BANNED_SITE_TARGETS[ip]:
                    del config.ACTIVE_BANNED_SITE_TARGETS[ip]
                    
        return jsonify({'status': 'success', 'message': 'Block rule removed.'})
        
    return jsonify({'status': 'error', 'message': 'Missing data.'}), 400