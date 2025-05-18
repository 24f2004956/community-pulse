import os
from flask import Flask
from models import User

from extensions import db, login_manager, migrate
# Initialize extensions

def create_app():
    app = Flask(__name__)
    
    # Configure the app
    app.config.from_object('config.Config')
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.events import events_bp
    from routes.admin import admin_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(admin_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    
    return app
    

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)