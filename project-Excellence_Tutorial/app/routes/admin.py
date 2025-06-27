from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app.models import User, PDF, Notification, Profile, Test, Mark, Fee, Payment, Setting
from app.forms import LoginForm, AdminPDFUploadForm, AdminNotificationForm, AdminTestUploadForm, PasswordResetRequestForm, PasswordResetForm, AddAdminUserForm, UPISettingsForm
from app import db, socketio
from app.utils import get_pending_approvals_count, generate_password_reset_token, verify_password_reset_token, send_password_reset_email
import os
from datetime import datetime, date
from flask_wtf.csrf import validate_csrf, CSRFError

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data, is_admin=True).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('admin.home1'))
        flash('Invalid admin credentials.', 'danger')
    return render_template('shared/login.html', form=form, role='admin')

@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('admin.login'))

@admin_bp.route('/home1')
@login_required
def home1():
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    
    # Check for pending approvals and show popup
    pending_count = get_pending_approvals_count()
    
    return render_template('admin/home1.html', pending_approvals=pending_count)

@admin_bp.route('/upload_pdfs', methods=['GET', 'POST'])
@login_required
def upload_pdfs():
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    form = AdminPDFUploadForm()
    if form.validate_on_submit():
        title = form.title.data
        file = form.pdf_file.data
        if file and file.filename.endswith('.pdf'):
            filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename}"
            pdf_folder = os.path.join(current_app.root_path, 'static', 'pdfs')
            os.makedirs(pdf_folder, exist_ok=True)
            file.save(os.path.join(pdf_folder, filename))
            pdf = PDF(title=title, file_path=filename)
            db.session.add(pdf)
            db.session.commit()
            # Store notification in DB (global)
            note = Notification(user_id=None, message=f'New PDF sent! <a href="{url_for("student.pdfs")}" class="underline">Open it</a>')
            db.session.add(note)
            db.session.commit()
            flash('PDF uploaded successfully!', 'success')
            socketio.emit('new_pdf', {'message': 'New PDF sent!', 'url': url_for('student.pdfs'), 'button': 'Open it'})
        else:
            flash('Invalid file. Please upload a PDF.', 'danger')
        return redirect(url_for('admin.upload_pdfs'))
    pdfs = PDF.query.order_by(PDF.uploaded_at.desc()).all()
    return render_template('admin/upload_pdfs.html', pdfs=pdfs, form=form)

@admin_bp.route('/notifystudents', methods=['GET', 'POST'])
@login_required
def notifystudents():
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    form = AdminNotificationForm()
    if form.validate_on_submit():
        message = form.message.data
        note = Notification(user_id=None, message=message)
        db.session.add(note)
        db.session.commit()
        flash('Notification sent!', 'success')
        socketio.emit('new_notification', {'message': message, 'url': url_for('student.notifications'), 'button': 'See it'})
        return redirect(url_for('admin.notifystudents'))

    # Only keep the 10 most recent notifications with non-empty messages
    notifications = Notification.query.filter(Notification.user_id == None, Notification.message != None, Notification.message != '').order_by(Notification.created_at.desc()).all()
    notifications_to_keep = notifications[:10]
    ids_to_keep = [n.id for n in notifications_to_keep]
    if len(notifications) > 10:
        Notification.query.filter(Notification.user_id == None, Notification.id.notin_(ids_to_keep)).delete(synchronize_session=False)
        db.session.commit()
    return render_template('admin/notifystudents.html', notifications=notifications_to_keep, form=form)

@admin_bp.route('/studentdetails')
@login_required
def studentdetails():
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    students = Profile.query.order_by(Profile.roll_number).all()
    return render_template('admin/studentdetails.html', students=students)

@admin_bp.route('/student/<int:student_id>')
@login_required
def student_profile(student_id):
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    student = Profile.query.get_or_404(student_id)
    marks = Mark.query.filter_by(user_id=student.user_id).join(Test).order_by(Test.date.desc()).all()
    # Get unpaid fees (dues)
    dues = Fee.query.filter_by(user_id=student.user_id, is_paid=False).all()
    # Get leaderboard for the student's class
    class_profiles = Profile.query.filter_by(student_class=student.student_class).all()
    leaderboard = []
    for p in class_profiles:
        total = db.session.query(db.func.coalesce(db.func.sum(Mark.marks_obtained), 0)).filter(Mark.user_id == p.user_id).scalar()
        leaderboard.append({'name': p.full_name, 'roll_number': p.roll_number, 'total': total})
    leaderboard = sorted(leaderboard, key=lambda x: x['total'], reverse=True)
    return render_template('admin/student_profile.html', student=student, marks=marks, dues=dues, leaderboard=leaderboard)

@admin_bp.route('/test_upload', methods=['GET', 'POST'])
@login_required
def test_upload():
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    form = AdminTestUploadForm()
    if form.validate_on_submit():
        date = form.date.data
        name = form.name.data
        total_marks = form.total_marks.data
        question_paper_file = form.question_paper.data
        question_paper_filename = None
        if question_paper_file and question_paper_file.filename:
            filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{question_paper_file.filename}"
            pdf_folder = os.path.join(current_app.root_path, 'static', 'pdfs')
            os.makedirs(pdf_folder, exist_ok=True)
            question_paper_file.save(os.path.join(pdf_folder, filename))
            question_paper_filename = filename
        test = Test(name=name, date=date, total_marks=total_marks, question_paper=question_paper_filename)
        db.session.add(test)
        db.session.commit()
        # Store notification in DB (global)
        note = Notification(user_id=None, message=f'New test update required! <a href="{url_for("student.test_update")}" class="underline">Open it</a>')
        db.session.add(note)
        db.session.commit()
        flash('Test created successfully!', 'success')
        socketio.emit('new_test', {'message': 'New test update required!', 'url': url_for('student.test_update'), 'button': 'Update'})
        return redirect(url_for('admin.test_upload'))
    tests = Test.query.order_by(Test.date.desc()).all()
    return render_template('admin/test_upload.html', form=form, tests=tests)

@admin_bp.route('/studentleads', methods=['GET', 'POST'])
@login_required
def studentleads():
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    selected_class = request.form.get('selected_class', '1')
    class_profiles = Profile.query.filter_by(student_class=selected_class).all()
    leaderboard = []
    for p in class_profiles:
        total = db.session.query(db.func.coalesce(db.func.sum(Mark.marks_obtained), 0)).filter(Mark.user_id == p.user_id).scalar()
        total_tests = db.session.query(db.func.count(Mark.id)).filter(Mark.user_id == p.user_id).scalar()
        leaderboard.append({'name': p.full_name, 'roll_number': p.roll_number, 'total': total, 'total_tests': total_tests})
    leaderboard = sorted(leaderboard, key=lambda x: x['total'], reverse=True)
    return render_template('admin/studentleads.html', leaderboard=leaderboard, selected_class=selected_class)

@admin_bp.route("/test")
def test_admin():
    return "Admin blueprint is working!"

@admin_bp.route('/fee_management')
@login_required
def fee_management():
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    
    # Get all students
    all_students = Profile.query.order_by(Profile.roll_number).all()
    
    # Get all fees with user and payment information
    all_fees = Fee.query.join(User).join(Profile).order_by(Fee.month.desc()).all()
    
    # Calculate summary statistics
    total_students = len(all_students)
    total_fees = sum(fee.amount_due for fee in all_fees)
    total_outstanding = sum(fee.amount_due for fee in all_fees if not fee.is_paid)
    
    # Get students with at least one unpaid fee (dues)
    students_with_dues_list = []
    for student in all_students:
        unpaid_fees = Fee.query.filter_by(user_id=student.user_id, is_paid=False).all()
        if unpaid_fees:
            students_with_dues_list.append({'profile': student})
    
    # Show popup if there are pending approvals
    approval_count = Payment.query.filter_by(is_confirmed=False).count()
    if approval_count > 0:
        flash('Students waiting for approval. <a href="' + url_for('admin.approve') + '" class="underline">Open Approvals</a>', 'warning')
    
    return render_template('admin/fee_management.html',
                         all_students=all_students,
                         all_fees=all_fees,
                         total_students=total_students,
                         total_fees=total_fees,
                         total_outstanding=total_outstanding,
                         students_with_dues_list=students_with_dues_list,
                         students_with_dues=len(students_with_dues_list),
                         approval_count=approval_count)

@admin_bp.route('/add_fee', methods=['POST'])
@login_required
def add_fee():
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    
    user_id = request.form.get('user_id')
    month = request.form.get('month')
    amount = request.form.get('amount')
    
    if user_id and month and amount:
        # Check if fee already exists for this user and month
        existing_fee = Fee.query.filter_by(user_id=user_id, month=month).first()
        if existing_fee:
            flash(f'Fee for {month} already exists for this student.', 'danger')
        else:
            fee = Fee(user_id=user_id, month=month, amount_due=int(amount))
            db.session.add(fee)
            db.session.commit()
            flash(f'Fee added successfully for {month}.', 'success')
    else:
        flash('Please fill all fields.', 'danger')
    
    return redirect(url_for('admin.fee_management'))

@admin_bp.route('/confirm_payment/<int:payment_id>', methods=['POST'])
@login_required
def confirm_payment(payment_id):
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    
    payment = Payment.query.get_or_404(payment_id)
    if payment.method == 'Cash' and not payment.is_confirmed:
        payment.is_confirmed = True
        payment.confirmed_at = datetime.utcnow()
        payment.fee.is_paid = True
        db.session.commit()
        flash('Cash payment confirmed successfully!', 'success')
    else:
        flash('Invalid payment or already confirmed.', 'danger')
    
    return redirect(url_for('admin.fee_management'))

@admin_bp.route('/approve')
@login_required
def approve():
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    
    # Get pending cash payments
    pending_cash_payments = Payment.query.filter_by(method='Cash', is_confirmed=False).join(Fee).join(User).join(Profile).order_by(Payment.requested_at.desc()).all()
    
    # Get pending UPI payments
    pending_upi_payments = Payment.query.filter_by(method='UPI', is_confirmed=False).join(Fee).join(User).join(Profile).order_by(Payment.requested_at.desc()).all()
    
    # Get recent approvals (only confirmed payments)
    recent_approvals = Payment.query.filter(
        Payment.is_confirmed == True
    ).join(Fee).join(User).join(Profile).order_by(Payment.confirmed_at.desc()).limit(10).all()
    
    # Calculate statistics
    pending_cash_count = len(pending_cash_payments)
    pending_upi_count = len(pending_upi_payments)
    total_pending = pending_cash_count + pending_upi_count
    
    approved_today = Payment.query.filter(
        Payment.is_confirmed == True,
        Payment.confirmed_at >= date.today()
    ).count()
    
    # For rejected payments, we need to track them differently since they're deleted
    # For now, we'll show 0 rejected today since rejected payments are deleted
    rejected_today = 0
    
    return render_template('admin/approve.html',
                         pending_cash_payments=pending_cash_payments,
                         pending_upi_payments=pending_upi_payments,
                         recent_approvals=recent_approvals,
                         pending_cash_count=pending_cash_count,
                         pending_upi_count=pending_upi_count,
                         total_pending=total_pending,
                         approved_today=approved_today,
                         rejected_today=rejected_today)

@admin_bp.route('/notify_student/<int:student_id>', methods=['POST'])
@login_required
def notify_student(student_id):
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    student = Profile.query.get_or_404(student_id)
    # Compose notification message (popup only, not stored)
    message = 'Please complete all your dues. <a href="' + url_for('student.fee') + '" class="underline">Open</a>'
    # Set pending_popup for the student
    student.pending_popup = message
    db.session.commit()
    flash('Student will see a popup about their dues next time they log in.', 'success')
    return redirect(url_for('admin.student_profile', student_id=student_id))

@admin_bp.route('/approve_payment/<int:payment_id>', methods=['POST'])
@login_required
def approve_payment(payment_id):
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    payment = Payment.query.get_or_404(payment_id)
    if payment.method in ['Cash', 'UPI'] and not payment.is_confirmed:
        payment.is_confirmed = True
        payment.confirmed_at = datetime.utcnow()
        payment.fee.is_paid = True
        db.session.commit()
        # Send popup notification to student (not stored)
        method_text = "cash" if payment.method == 'Cash' else "UPI"
        message = f"Your {method_text} payment of ₹{payment.fee.amount_due} for {payment.fee.month} has been approved by admin. <a href='{url_for('student.fee')}' class='underline'>Open</a>"
        # Store notification in DB for this student
        note = Notification(user_id=payment.user_id, message=message)
        db.session.add(note)
        db.session.commit()
        socketio.emit('new_notification', {'message': message, 'url': url_for('student.fee'), 'button': 'Open'}, room=f'user_{payment.user_id}')
        flash(f'{payment.method} payment approved successfully!', 'success')
    else:
        flash('Invalid payment request.', 'danger')
    return redirect(url_for('admin.approve'))

@admin_bp.route('/reject_payment/<int:payment_id>', methods=['POST'])
@login_required
def reject_payment(payment_id):
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    
    payment = Payment.query.get_or_404(payment_id)
    
    if payment.method in ['Cash', 'UPI'] and not payment.is_confirmed:
        # Send notification to student before deleting
        method_text = "cash" if payment.method == 'Cash' else "UPI"
        notification = Notification(
            user_id=payment.user_id,
            message=f"Your {method_text} payment request of ₹{payment.fee.amount_due} for {payment.fee.month} has been rejected by admin. Please contact admin for clarification."
        )
        db.session.add(notification)
        
        # Delete the payment request
        db.session.delete(payment)
        db.session.commit()
        
        flash(f'{payment.method} payment request rejected successfully!', 'success')
    else:
        flash('Invalid payment request.', 'danger')
    
    return redirect(url_for('admin.approve'))

@admin_bp.route('/feedues')
@login_required
def feedues():
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    
    # Get all students with their fee information
    all_students = Profile.query.all()
    
    students_with_dues_list = []
    students_paid_up_list = []
    total_outstanding = 0
    
    for student in all_students:
        # Get all fees for this student
        fees = Fee.query.filter_by(user_id=student.user_id).all()
        outstanding_fees = [fee for fee in fees if not fee.is_paid]
        paid_fees = [fee for fee in fees if fee.is_paid]
        
        total_due = sum(fee.amount_due for fee in outstanding_fees)
        total_paid = sum(fee.amount_due for fee in paid_fees)
        
        if outstanding_fees:
            # Student has dues
            students_with_dues_list.append({
                'profile': student,
                'outstanding_fees': outstanding_fees,
                'due_count': len(outstanding_fees),
                'total_due': total_due
            })
            total_outstanding += total_due
        else:
            # Student is paid up
            students_paid_up_list.append({
                'profile': student,
                'total_paid': total_paid
            })
    
    # Sort students with dues by due count (descending)
    students_with_dues_list.sort(key=lambda x: x['due_count'], reverse=True)
    
    return render_template('admin/feedues.html',
                         students_with_dues_list=students_with_dues_list,
                         students_paid_up_list=students_paid_up_list,
                         students_with_dues=len(students_with_dues_list),
                         students_paid_up=len(students_paid_up_list),
                         total_outstanding=total_outstanding,
                         total_students=len(all_students))

@admin_bp.route('/dues', methods=['GET', 'POST'])
@login_required
def dues_management():
    if not current_user.is_admin:
        return redirect(url_for('student.home'))

    # Handle add due form
    if request.method == 'POST' and 'add_due' in request.form:
        try:
            validate_csrf(request.form.get('csrf_token'))
        except CSRFError:
            flash('Invalid CSRF token.', 'danger')
            return redirect(url_for('admin.dues_management'))
        user_id = request.form.get('user_id')
        month = request.form.get('month')
        amount = request.form.get('amount')
        is_paid = request.form.get('is_paid') == 'on'
        if user_id and month and amount:
            if user_id == 'all':
                # Add due for all students
                students = Profile.query.all()
                added_count = 0
                for student in students:
                    if not Fee.query.filter_by(user_id=student.user_id, month=month).first():
                        fee = Fee(user_id=student.user_id, month=month, amount_due=int(amount), is_paid=is_paid)
                        db.session.add(fee)
                        added_count += 1
                db.session.commit()
                flash(f'Due added for {added_count} students.', 'success')
            else:
                if not Fee.query.filter_by(user_id=user_id, month=month).first():
                    fee = Fee(user_id=user_id, month=month, amount_due=int(amount), is_paid=is_paid)
                    db.session.add(fee)
                    db.session.commit()
                    flash('Due added successfully.', 'success')
                else:
                    flash('Due for this user and month already exists.', 'danger')
        else:
            flash('Please fill all fields.', 'danger')
        return redirect(url_for('admin.dues_management'))

    # Handle edit due form
    if request.method == 'POST' and 'edit_due' in request.form:
        try:
            validate_csrf(request.form.get('csrf_token'))
        except CSRFError:
            flash('Invalid CSRF token.', 'danger')
            return redirect(url_for('admin.dues_management'))
        fee_id = request.form.get('fee_id')
        amount = request.form.get('edit_amount')
        month = request.form.get('edit_month')
        is_paid = request.form.get('edit_is_paid') == 'on'
        fee = Fee.query.get(fee_id)
        if fee:
            fee.amount_due = int(amount)
            fee.month = month
            fee.is_paid = is_paid
            db.session.commit()
            flash('Due updated successfully.', 'success')
        else:
            flash('Due not found.', 'danger')
        return redirect(url_for('admin.dues_management'))

    # Handle delete due
    if request.method == 'POST' and 'delete_due' in request.form:
        try:
            validate_csrf(request.form.get('csrf_token'))
        except CSRFError:
            flash('Invalid CSRF token.', 'danger')
            return redirect(url_for('admin.dues_management'))
        fee_id = request.form.get('fee_id')
        fee = Fee.query.get(fee_id)
        if fee:
            db.session.delete(fee)
            db.session.commit()
            flash('Due deleted successfully.', 'success')
        else:
            flash('Due not found.', 'danger')
        return redirect(url_for('admin.dues_management'))

    # Handle mark as paid/unpaid
    if request.method == 'POST' and 'toggle_paid' in request.form:
        try:
            validate_csrf(request.form.get('csrf_token'))
        except CSRFError:
            flash('Invalid CSRF token.', 'danger')
            return redirect(url_for('admin.dues_management'))
        fee_id = request.form.get('fee_id')
        fee = Fee.query.get(fee_id)
        if fee:
            fee.is_paid = not fee.is_paid
            db.session.commit()
            flash('Due payment status updated.', 'success')
        else:
            flash('Due not found.', 'danger')
        return redirect(url_for('admin.dues_management'))

    # List all dues (reuse fee_management table data)
    dues = Fee.query.order_by(Fee.month.desc()).all()
    students = Profile.query.order_by(Profile.roll_number).all()
    return render_template('admin/dues_management.html', dues=dues, students=students)

@admin_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data, is_admin=True).first()
        if user:
            token = generate_password_reset_token(user.email)
            send_password_reset_email(user, token, is_admin=True)
        flash('If your email is registered as an admin, you will receive a password reset link.', 'info')
        return redirect(url_for('admin.login'))
    return render_template('student/forgot_password.html', form=form)

@admin_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_password_reset_token(token)
    if not email:
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('admin.forgot_password'))
    user = User.query.filter_by(email=email, is_admin=True).first()
    if not user:
        flash('Invalid admin user.', 'danger')
        return redirect(url_for('admin.forgot_password'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user.password = generate_password_hash(form.password.data)
        db.session.commit()
        flash('Your password has been updated! You can now log in as admin.', 'success')
        return redirect(url_for('admin.login'))
    return render_template('student/reset_password.html', form=form)

@admin_bp.route('/adduser', methods=['GET', 'POST'])
@login_required
def add_user():
    if not current_user.is_admin:
        return redirect(url_for('admin.login'))
    form = AddAdminUserForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Admin with this email already exists.', 'danger')
        else:
            new_admin = User(email=form.email.data, password=generate_password_hash(form.password.data), is_admin=True)
            db.session.add(new_admin)
            db.session.commit()
            flash('New admin user added successfully!', 'success')
            return redirect(url_for('main.landing'))
    return render_template('admin/add_user.html', form=form)

@admin_bp.route('/upi_settings', methods=['GET', 'POST'])
@login_required
def upi_settings():
    if not current_user.is_admin:
        return redirect(url_for('admin.login'))
    upi_setting = Setting.query.filter_by(key='upi_id').first()
    qr_setting = Setting.query.filter_by(key='upi_qr').first()
    monthly_due_setting = Setting.query.filter_by(key='monthly_due_amount').first()
    schedule_setting = Setting.query.filter_by(key='monthly_dues_enabled').first()
    schedule_enabled = schedule_setting.value == 'true' if schedule_setting else True
    form = UPISettingsForm(
        upi_id=upi_setting.value if upi_setting else '',
        monthly_due_amount=int(monthly_due_setting.value) if monthly_due_setting and monthly_due_setting.value.isdigit() else 1500
    )
    # Handle toggle for schedule
    if request.method == 'POST' and 'toggle_schedule' in request.form:
        new_state = request.form.get('toggle_schedule') == 'enable'
        if schedule_setting:
            schedule_setting.value = 'true' if new_state else 'false'
        else:
            schedule_setting = Setting(key='monthly_dues_enabled', value='true' if new_state else 'false')
            db.session.add(schedule_setting)
        db.session.commit()
        flash(f"Monthly dues schedule {'enabled' if new_state else 'disabled'}!", 'success')
        return redirect(url_for('admin.upi_settings'))
    if form.validate_on_submit():
        print('[DEBUG] UPISettingsForm submitted')
        # Update UPI ID
        if upi_setting:
            print(f'[DEBUG] Updating existing UPI ID: {upi_setting.value} -> {form.upi_id.data}')
            upi_setting.value = form.upi_id.data
        else:
            print(f'[DEBUG] Creating new UPI ID: {form.upi_id.data}')
            upi_setting = Setting(key='upi_id', value=form.upi_id.data)
            db.session.add(upi_setting)
        # Update Monthly Due Amount
        if monthly_due_setting:
            print(f'[DEBUG] Updating existing monthly due amount: {monthly_due_setting.value} -> {form.monthly_due_amount.data}')
            monthly_due_setting.value = str(form.monthly_due_amount.data)
        else:
            print(f'[DEBUG] Creating new monthly due amount: {form.monthly_due_amount.data}')
            monthly_due_setting = Setting(key='monthly_due_amount', value=str(form.monthly_due_amount.data))
            db.session.add(monthly_due_setting)
        # Update all dues (Fee records) to new amount
        new_amount = int(form.monthly_due_amount.data)
        all_fees = Fee.query.all()
        for fee in all_fees:
            fee.amount_due = new_amount
        db.session.commit()
        print('[DEBUG] All Fee records updated to new amount')
        # Handle QR code upload
        if form.qr_code.data:
            qr_file = form.qr_code.data
            filename = f"upi_qr.{qr_file.filename.rsplit('.', 1)[-1].lower()}"
            qr_folder = os.path.join(current_app.root_path, 'static', 'qr')
            os.makedirs(qr_folder, exist_ok=True)
            qr_path = os.path.join(qr_folder, filename)
            print(f'[DEBUG] Saving QR file to: {qr_path}')
            qr_file.save(qr_path)
            rel_path = f'qr/{filename}'
            if qr_setting:
                print(f'[DEBUG] Updating existing QR setting: {qr_setting.value} -> {rel_path}')
                qr_setting.value = rel_path
            else:
                print(f'[DEBUG] Creating new QR setting: {rel_path}')
                qr_setting = Setting(key='upi_qr', value=rel_path)
                db.session.add(qr_setting)
        db.session.commit()
        print('[DEBUG] Settings committed to database')
        flash('UPI settings updated successfully!', 'success')
        return redirect(url_for('admin.upi_settings'))
    qr_url = url_for('static', filename=qr_setting.value) if qr_setting else None
    return render_template('admin/upi_settings.html', form=form, qr_url=qr_url, schedule_enabled=schedule_enabled) 