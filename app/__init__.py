from flask import Flask

def create_app():
    app = Flask(__name__)

    from app.routes import main  # Import the Blueprint
    app.register_blueprint(main)  # Register the Blueprint

    return app
