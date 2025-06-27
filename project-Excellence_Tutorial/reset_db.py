from app import db, create_app
from app.models import User, Profile, Fee, Payment, Notification, PDF, Test, Mark
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Delete all data from all tables
    Notification.query.delete()
    Payment.query.delete()
    Fee.query.delete()
    Mark.query.delete()
    Test.query.delete()
    PDF.query.delete()
    Profile.query.delete()
    User.query.delete()
    db.session.commit()

    # Create a new admin user
    admin = User(email='admin@example.com', password=generate_password_hash('adminpass'), is_admin=True)
    db.session.add(admin)
    db.session.commit()

    # Create a new student user
    

    print('Database reset complete. Admin created.') 
