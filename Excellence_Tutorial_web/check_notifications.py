from app import db, create_app
from app.models import Notification

app = create_app()

with app.app_context():
    notifications = Notification.query.filter_by(user_id=2).order_by(Notification.created_at.desc()).all()
    print(f"Found {len(notifications)} notifications for user_id=2:")
    for n in notifications:
        print(f"[{n.created_at}] {n.message}") 