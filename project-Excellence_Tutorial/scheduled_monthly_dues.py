from app import db, create_app
from app.models import User, Fee
from datetime import datetime
import pytz

DUE_AMOUNT = 1500

app = create_app()
india_tz = pytz.timezone('Asia/Kolkata')

with app.app_context():
    now = datetime.now(india_tz)
    current_month_label = now.strftime('%B %Y')
    today = now.day
    users = User.query.filter_by(is_admin=False).all()
    for user in users:
        # Only assign if user joined before the 10th of this month
        if user.created_at.astimezone(india_tz).day < 10 or user.created_at.astimezone(india_tz).month < now.month or user.created_at.astimezone(india_tz).year < now.year:
            # Prevent duplicate due for this month
            if not Fee.query.filter_by(user_id=user.id, month=current_month_label).first():
                fee = Fee(user_id=user.id, month=current_month_label, amount_due=DUE_AMOUNT, is_paid=False)
                db.session.add(fee)
                print(f"Assigned {current_month_label} due to user {user.id} (roll:{user.profile.roll_number})")
    db.session.commit()
    print(f'All eligible users have been assigned {current_month_label} due.') 