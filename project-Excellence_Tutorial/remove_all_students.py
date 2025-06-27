from app import create_app, db
from app.models import User, Profile, Fee, Payment, Notification, Mark

app = create_app()

with app.app_context():
    student_users = User.query.filter_by(is_admin=False).all()
    for u in student_users:
        Profile.query.filter_by(user_id=u.id).delete()
        Notification.query.filter_by(user_id=u.id).delete()
        Payment.query.filter_by(user_id=u.id).delete()
        Fee.query.filter_by(user_id=u.id).delete()
        Mark.query.filter_by(user_id=u.id).delete()
        db.session.delete(u)
    db.session.commit()
    print('All students and their related data deleted.') 