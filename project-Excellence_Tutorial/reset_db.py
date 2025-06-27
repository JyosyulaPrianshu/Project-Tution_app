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
    student = User(email='student2@example.com', password=generate_password_hash('studentpass'), is_admin=False)
    db.session.add(student)
    db.session.commit()

    # Create a profile for the student (roll:2)
    profile = Profile(user_id=student.id, full_name='Test Student', parent_name='Parent Name', parent_phone='1234567890', student_phone='0987654321', student_class='10', school_name='Test School', roll_number=2)
    db.session.add(profile)
    db.session.commit()

    print('Database reset complete. Admin and student (roll:2) created.') 