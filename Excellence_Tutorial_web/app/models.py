from . import db
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    profile = db.relationship('Profile', backref='user', uselist=False)
    fees = db.relationship('Fee', backref='user', lazy=True)
    payments = db.relationship('Payment', backref='user', lazy=True)

class Profile(db.Model):
    __tablename__ = 'profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    full_name = db.Column(db.String(120), nullable=False)
    parent_name = db.Column(db.String(120), nullable=False)
    parent_phone = db.Column(db.String(20), nullable=False)
    student_phone = db.Column(db.String(20), nullable=False)
    student_class = db.Column(db.String(20), nullable=False)
    school_name = db.Column(db.String(120), nullable=False)
    roll_number = db.Column(db.Integer, unique=True)
    last_seen_pdf_id = db.Column(db.Integer, default=0)
    last_seen_test_id = db.Column(db.Integer, default=0)
    last_seen_notification_id = db.Column(db.Integer, default=0)
    profile_pic = db.Column(db.String(256))
    pending_popup = db.Column(db.Text)  # One-time popup message for the student

class Test(db.Model):
    __tablename__ = 'tests'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text)
    total_marks = db.Column(db.Integer)
    question_paper = db.Column(db.String(256))
    marks = db.relationship('Mark', backref='test', lazy=True)

class Mark(db.Model):
    __tablename__ = 'marks'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'))
    marks_obtained = db.Column(db.Integer)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class Fee(db.Model):
    __tablename__ = 'fees'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    month = db.Column(db.String(20), nullable=False)
    amount_due = db.Column(db.Integer, nullable=False)
    is_paid = db.Column(db.Boolean, default=False)
    payments = db.relationship('Payment', backref='fee', lazy=True)

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    fee_id = db.Column(db.Integer, db.ForeignKey('fees.id'))
    method = db.Column(db.String(20))  # UPI or Cash
    reference = db.Column(db.String(100))  # UPI reference number
    is_confirmed = db.Column(db.Boolean, default=False)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime)

class PDF(db.Model):
    __tablename__ = 'pdfs'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    file_path = db.Column(db.String(256), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # null for all students
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

class Setting(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    value = db.Column(db.String(256), nullable=False)
    # For scheduled monthly dues, use key 'monthly_dues_enabled' with value 'true' or 'false' 