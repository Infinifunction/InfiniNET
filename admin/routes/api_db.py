import sqlite3
import os
from flask import Blueprint, jsonify
import InfiniDB

api_db_bp = Blueprint('api_db', __name__)

#-------------------------------------------#
# Resolve the database path from the InfiniDB module.
# The code first prefers DB_PATH, then falls back to DB_NAME,
# and finally uses the default SQLite database filename if neither
# configuration value is available.
#-------------------------------------------#
DB_PATH = getattr(InfiniDB, 'DB_PATH', getattr(InfiniDB, 'DB_NAME', 'infini_dhcp.db'))


@api_db_bp.route('/admin/api/db/tables', methods=['GET'])
def get_db_tables():
    try:
        #-------------------------------------------#
        # Open the configured SQLite database, retrieve the names
        # of all tables registered in sqlite_master, and return
        # those names as a JSON response for the administration API.
        #-------------------------------------------#
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return jsonify(tables)
    except Exception as e:
        #-------------------------------------------#
        # Convert database-related exceptions into an HTTP 500
        # response so the administrative client receives the error
        # information instead of causing the request to terminate.
        #-------------------------------------------#
        return jsonify({'error': str(e)}), 500


@api_db_bp.route('/admin/api/db/query/<table_name>', methods=['GET'])
def query_table(table_name):
    try:
        #-------------------------------------------#
        # Open the SQLite database with row_factory enabled so each
        # returned row can be converted into a dictionary. The query
        # retrieves at most 100 records from the requested table and
        # exposes them through the administrative JSON endpoint.
        #-------------------------------------------#
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 100")
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(rows)
    except Exception as e:
        #-------------------------------------------#
        # Return database or query failures as an HTTP 400 response,
        # preserving the existing behavior of this endpoint when an
        # invalid table name or another query-related error occurs.
        #-------------------------------------------#
        return jsonify({'error': str(e)}), 400
