from flask import Blueprint, jsonify, request
import config

api_speed_bp = Blueprint('api_speed', __name__)

@api_speed_bp.route('/admin/api/speed/ip', methods=['POST'])
def set_ip_speed():
    data = request.json or {}
    ip = data.get('ip')
    limit_kb = data.get('limit_kb', 0)
    
    if ip:
        if limit_kb > 0:
            config.SPECIAL_SPEED_LIMITS[ip] = limit_kb
        else:
            config.SPECIAL_SPEED_LIMITS.pop(ip, None)
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'IP address is required.'}), 400

@api_speed_bp.route('/admin/api/speed/everyone', methods=['POST'])
def set_everyone_speed():
    data = request.json or {}
    limit_kb = data.get('limit_kb', 0)
    config.GENERAL_SPEED_LIMIT_KB = limit_kb
    return jsonify({'status': 'success'})