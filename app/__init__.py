from flask import Flask, send_from_directory
from app.database import init_db_pool
import os
import secrets

def create_app():
    app = Flask(__name__)
    
    # Configure session with a secret key
    app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(16)
    
    # Initialize the connection pool - do this early in startup
    init_db_pool()
    
    # Enable gzip compression
    try:
        from flask_compress import Compress
        compress = Compress()
        compress.init_app(app)
    except ImportError:
        print("Warning: flask_compress not installed. Response compression disabled.")
    
    # Configure aggressive caching for static assets
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 year in seconds
    
    # Static file handling with improved caching
    @app.route('/static/<path:filename>')
    def static_files(filename):
        response = send_from_directory(app.static_folder, filename)
        # Add cache headers
        response.headers['Cache-Control'] = 'public, max-age=31536000'
        return response
    
    # Register the Blueprint
    from app.routes import main
    app.register_blueprint(main)

    # Register error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return "Page not found", 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return "Internal server error", 500

    return app