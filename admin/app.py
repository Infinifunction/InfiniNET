import sys
import os
from flask import Flask, render_template, send_from_directory

#-------------------------------------------#
# Configure Python's module search path so the application can import
# project-level modules located in the parent directory of this package.
# The absolute path is derived from this file's location to keep imports
# consistent regardless of the directory from which the application starts.
#-------------------------------------------
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

#-------------------------------------------#
# Import the Flask blueprints that expose the administrative API endpoints.
# Each blueprint groups related routes into a separate module while allowing
# the main application object to register them as part of the admin server.
#-------------------------------------------
from admin.routes.api_bans import api_bans_bp
from admin.routes.api_speed import api_speed_bp
from admin.routes.api_system import api_system_bp
from admin.routes.api_db import api_db_bp

app = Flask(__name__, template_folder='templates', static_folder='static')

#-------------------------------------------#
# Register every administrative API blueprint with the Flask application.
# Registration makes the routes defined by these modules available through
# the main admin server without duplicating their route implementations here.
#-------------------------------------------
app.register_blueprint(api_bans_bp)
app.register_blueprint(api_speed_bp)
app.register_blueprint(api_system_bp)
app.register_blueprint(api_db_bp)

#-------------------------------------------#
# Serve static administrative-panel assets through the dedicated admin path.
# The requested filename is resolved relative to Flask's configured static
# directory, allowing CSS, JavaScript, images, and other frontend assets
# to be delivered by the application.
#-------------------------------------------
@app.route('/admin/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

#-------------------------------------------#
# Define the routes responsible for rendering the main administrative HTML
# pages. These handlers return the corresponding Jinja templates while the
# frontend JavaScript communicates with the registered API blueprints.
#-------------------------------------------
@app.route('/admin/')
@app.route('/admin')
def admin_dashboard():
    return render_template('dashboard.html')

@app.route('/admin/db-browser')
def db_browser():
    return render_template('db_browser.html')

@app.route('/admin/devices')
@app.route('/admin/devices/<ip>')
@app.route('/admin/devices/<ip>/<tab>')
def devices(ip=None, tab=None):
    return render_template('devices.html')

#-------------------------------------------#
# Start the Flask administrative server with development debugging and the
# Flask automatic reloader disabled. The default host listens on all network
# interfaces, while the port defaults to HTTP port 80 for the admin service.
#-------------------------------------------#
def run_admin_server(host='0.0.0.0', port=80):
    app.run(host=host, port=port, debug=False, use_reloader=False)

#-------------------------------------------#
# When this module is executed directly, start the administrative server.
# Importing the module does not automatically launch the server, which allows
# the Flask application object and its routes to be reused by other modules.
#-------------------------------------------#
if __name__ == '__main__':
    run_admin_server()