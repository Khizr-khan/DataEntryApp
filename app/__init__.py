from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

# Initialize the database object
db = SQLAlchemy()
migrate = Migrate()  # Initialize migrate without the app

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize the database and migration objects with the app
    db.init_app(app)
    migrate.init_app(app, db)

    # Import and register blueprints
    from .routes import register_blueprints
    register_blueprints(app)

    return app
