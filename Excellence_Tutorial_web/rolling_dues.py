import time
from datetime import datetime, timedelta
import pytz
import os
from app import db, create_app
from app.models import User, Fee

INTERVAL_SECONDS = 5 * 60  # 5 minutes
HALF_INTERVAL = INTERVAL_SECONDS // 2  # 2m30s
DUE_AMOUNT = 1500
STOP_FILE = 'stop_dues.txt'

def get_due_label(user_id):
    return f"Due {Fee.query.filter_by(user_id=user_id).count() + 1}"

def assign_due(user, label, reason, now):
    # Prevent duplicate dues for the same label
    if Fee.query.filter_by(user_id=user.id, month=label).first():
        return
    fee = Fee(user_id=user.id, month=label, amount_due=DUE_AMOUNT, is_paid=False)
    db.session.add(fee)
    print(f"[{reason}] {label} assigned to user {user.id} (roll:{user.profile.roll_number}) at {now.strftime('%H:%M:%S')}")

def main():
    app = create_app()
    india_tz = pytz.timezone('Asia/Kolkata')
    with app.app_context():
        start_time = datetime.now(india_tz)
        print(f"Rolling due generator started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        interval_start = start_time
        immediate_due_given = set()
        while True:
            now = datetime.now(india_tz)
            if os.path.exists(STOP_FILE):
                print("Stop file detected. Exiting due generator.")
                break
            elapsed = (now - interval_start).total_seconds()
            users = User.query.filter_by(is_admin=False).all()
            # Immediate due for new users in first half of interval
            for user in users:
                if user.id in immediate_due_given:
                    continue
                joined = user.created_at.astimezone(india_tz)
                if interval_start <= joined < interval_start + timedelta(seconds=HALF_INTERVAL):
                    label = get_due_label(user.id)
                    assign_due(user, label, "IMMEDIATE", now)
                    immediate_due_given.add(user.id)
            db.session.commit()
            # At each interval, assign a new due to all users
            if elapsed >= INTERVAL_SECONDS:
                for user in users:
                    label = get_due_label(user.id)
                    assign_due(user, label, "INTERVAL", now)
                db.session.commit()
                interval_start += timedelta(seconds=INTERVAL_SECONDS)
                immediate_due_given.clear()
            time.sleep(10)

if __name__ == "__main__":
    main() 