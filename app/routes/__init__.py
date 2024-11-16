# routes/__init__.py

from .admin import admin  # Import the admin blueprint
from .data_entry import data_entry  # Import the data_entry blueprint

def register_blueprints(app):
    """
    Registers all route blueprints with the Flask app instance.
    """
    # Register each blueprint with its respective URL prefix
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(data_entry, url_prefix='/')
