from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from flask_wtf.file import FileField, FileAllowed
from wtforms import TextAreaField
from wtforms.fields import DateField, IntegerField, SelectField

class_choices = [(str(i), f"Class {i}") for i in range(1, 13)]

class StudentSignupForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired()])
    parent_name = StringField('Parent Name', validators=[DataRequired()])
    parent_phone = StringField('Parent Phone', validators=[DataRequired(), Length(min=10, max=15)])
    student_phone = StringField('Student Phone', validators=[DataRequired(), Length(min=10, max=15)])
    student_class = SelectField('Class', choices=class_choices, validators=[DataRequired()])
    school_name = StringField('School Name', validators=[DataRequired()])
    profile_pic = FileField('Profile Picture (optional)', validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class AdminPDFUploadForm(FlaskForm):
    title = StringField('PDF Title', validators=[DataRequired()])
    pdf_file = FileField('PDF File', validators=[DataRequired(), FileAllowed(['pdf'], 'PDFs only!')])
    submit = SubmitField('Upload PDF')

class AdminNotificationForm(FlaskForm):
    message = TextAreaField('Notification message', validators=[DataRequired()])
    submit = SubmitField('Send Notification')

class AdminTestUploadForm(FlaskForm):
    date = DateField('Test Date', format='%Y-%m-%d', validators=[DataRequired()])
    name = StringField('Test Name', validators=[DataRequired()])
    question_paper = FileField('Question Paper (PDF, optional)', validators=[FileAllowed(['pdf'], 'PDFs only!')])
    total_marks = IntegerField('Total Marks', validators=[DataRequired()])
    submit = SubmitField('Create Test')

class StudentTestUpdateForm(FlaskForm):
    test_id = SelectField('Test', coerce=int, validators=[DataRequired()])
    marks_obtained = IntegerField('Marks Obtained', validators=[DataRequired()])
    submit = SubmitField('Update Marks')

class StudentFeeForm(FlaskForm):
    method = SelectField('Payment Method', choices=[('UPI', 'UPI'), ('Cash', 'Cash')], validators=[DataRequired()])
    submit = SubmitField('Pay/Request Approval')

class PasswordResetRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reset Link')

class PasswordResetForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class AddAdminUserForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Add Admin User')

class UPISettingsForm(FlaskForm):
    upi_id = StringField('UPI ID', validators=[DataRequired()])
    monthly_due_amount = IntegerField('Monthly Due Amount', validators=[DataRequired()])
    qr_code = FileField('Upload QR Code', validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')])
    submit = SubmitField('Update UPI Settings') 