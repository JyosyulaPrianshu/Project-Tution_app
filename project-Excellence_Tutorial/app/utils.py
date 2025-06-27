from datetime import datetime, date
from app.models import Fee, Notification, Profile, User, Setting
from app import db, socketio
from flask import url_for
import pytz
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from flask_mail import Message
import os

def check_monthly_fee_notifications():
    """Check if it's the 1st of the month and send fee notifications"""
    today = date.today()
    
    # Check if it's the 1st of the month
    if today.day == 1:
        current_month = today.strftime('%B %Y')  # e.g., "July 2025"
        
        # Get all students
        students = Profile.query.all()
        
        for student in students:
            # Check if fee notification already sent for this month
            existing_notification = Notification.query.filter_by(
                user_id=student.user_id,
                message=f"Fee due for {current_month}"
            ).first()
            
            if not existing_notification:
                # Create fee notification
                notification = Notification(
                    user_id=student.user_id,
                    message=f"Fee due for {current_month}"
                )
                db.session.add(notification)
                
                # Send real-time popup notification
                socketio.emit('fee_notification', {
                    'message': f'Fee due for {current_month}',
                    'url': url_for('student.fee'),
                    'button': 'Pay Now'
                }, room=f'student_{student.user_id}')
        
        db.session.commit()

def get_fee_status_for_student(user_id):
    """Get fee status for a specific student"""
    fees = Fee.query.filter_by(user_id=user_id).order_by(Fee.month.desc()).all()
    
    outstanding_fees = [fee for fee in fees if not fee.is_paid]
    paid_fees = [fee for fee in fees if fee.is_paid]
    total_due = sum(fee.amount_due for fee in outstanding_fees)
    
    return {
        'outstanding_fees': outstanding_fees,
        'paid_fees': paid_fees,
        'total_due': total_due,
        'total_fees': len(fees)
    }

def get_pending_approvals_count():
    """Get count of pending cash payment approvals"""
    from app.models import Payment
    return Payment.query.filter_by(method='Cash', is_confirmed=False).count()

def assign_monthly_dues():
    india_tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(india_tz)
    current_month_label = now.strftime('%B %Y')
    monthly_due_setting = Setting.query.filter_by(key='monthly_due_amount').first()
    schedule_setting = Setting.query.filter_by(key='monthly_dues_enabled').first()
    if schedule_setting and schedule_setting.value != 'true':
        return  # Do not assign dues if schedule is disabled
    try:
        due_amount = int(monthly_due_setting.value) if monthly_due_setting and monthly_due_setting.value.isdigit() else 1500
    except Exception:
        due_amount = 1500
    users = User.query.filter_by(is_admin=False).all()
    for user in users:
        joined = user.created_at.astimezone(india_tz)
        # Existing users or new users who joined before the 10th of this month
        if (joined.year < now.year or
            joined.month < now.month or
            (joined.year == now.year and joined.month == now.month and joined.day <= 10)):
            if not Fee.query.filter_by(user_id=user.id, month=current_month_label).first():
                fee = Fee(user_id=user.id, month=current_month_label, amount_due=due_amount, is_paid=False)
                db.session.add(fee)
    db.session.commit()

# Token helpers

def generate_password_reset_token(user_email, expires_sec=3600):
    s = URLSafeTimedSerializer(os.environ.get('SECRET_KEY', 'devkey'))
    return s.dumps(user_email, salt='password-reset-salt')

def verify_password_reset_token(token, max_age=3600):
    s = URLSafeTimedSerializer(os.environ.get('SECRET_KEY', 'devkey'))
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=max_age)
    except Exception:
        return None
    return email

# Email helper

def send_password_reset_email(user, token, is_admin=False):
    from app import mail
    if is_admin:
        reset_url = url_for('admin.reset_password', token=token, _external=True)
    else:
        reset_url = url_for('student.reset_password', token=token, _external=True)
    msg = Message('Password Reset Request', sender='your_gmail_address@gmail.com', recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:\n{reset_url}\n\nIf you did not make this request, simply ignore this email.'''
    mail.send(msg) 