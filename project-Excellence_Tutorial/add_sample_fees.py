from app import db, create_app
from app.models import User, Profile, Fee
from datetime import datetime, timedelta
import pytz

app = create_app()

with app.app_context():
    india_tz = pytz.timezone('Asia/Kolkata')
    now_india = datetime.now(india_tz)
    current_year = now_india.year
    current_month = now_india.month

    students = User.query.filter_by(is_admin=False).all()
    for student in students:
        # Get enrollment date (created_at)
        enrollment = student.created_at.astimezone(india_tz)
        enroll_year = enrollment.year
        enroll_month = enrollment.month
        # For each month from enrollment to now
        year = enroll_year
        month = enroll_month
        while (year < current_year) or (year == current_year and month <= current_month):
            month_str = datetime(year, month, 1).strftime('%B %Y')
            # Check if due already exists
            existing_fee = Fee.query.filter_by(user_id=student.id, month=month_str).first()
            if not existing_fee:
                fee = Fee(user_id=student.id, month=month_str, amount_due=1500, is_paid=False)
                db.session.add(fee)
                print(f"Added due for student roll:{student.profile.roll_number} for {month_str}")
            # Move to next month
            if month == 12:
                month = 1
                year += 1
            else:
                month += 1
    db.session.commit()
    print('All dues added for all students.') 