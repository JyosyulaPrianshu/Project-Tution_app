from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from config import Config
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_mail import Mail

# Initialize extensions
login_manager = LoginManager()
db = SQLAlchemy()
csrf = CSRFProtect()
migrate = Migrate()
socketio = SocketIO(cors_allowed_origins="*")
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)
    mail.init_app(app)

    from app.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.utils import assign_monthly_dues
    @app.before_request
    def before_any_request():
        assign_monthly_dues()

    # Register blueprints
    from app.routes.student import student_bp
    from app.routes.admin import admin_bp
    from app.routes.main import main_bp
    app.register_blueprint(student_bp, url_prefix="/student")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(main_bp)

    return app 