from app import create_app, db
from app.models import User, Profile, Fee, Payment
from datetime import datetime

app = create_app()

with app.app_context():
    print("=== Testing Fee Management System ===")
    
    # Get all students
    students = Profile.query.all()
    print(f"Found {len(students)} students")
    
    if students:
        # Add sample fees for each student
        months = ['January 2025', 'February 2025', 'March 2025', 'April 2025', 'May 2025']
        amounts = [1500, 1500, 1500, 1500, 1500]
        
        for student in students:
            print(f"\nProcessing student: {student.full_name} (ID: {student.roll_number})")
            
            for i, month in enumerate(months):
                # Check if fee already exists
                existing_fee = Fee.query.filter_by(user_id=student.user_id, month=month).first()
                if not existing_fee:
                    fee = Fee(
                        user_id=student.user_id,
                        month=month,
                        amount_due=amounts[i],
                        is_paid=False
                    )
                    db.session.add(fee)
                    print(f"  ✓ Added fee for {month}: ₹{amounts[i]}")
                else:
                    print(f"  - Fee for {month} already exists")
        
        db.session.commit()
        print("\n✅ Sample fees added successfully!")
        
        # Show fee summary
        print("\n=== Fee Summary ===")
        total_fees = Fee.query.count()
        paid_fees = Fee.query.filter_by(is_paid=True).count()
        outstanding_fees = total_fees - paid_fees
        
        print(f"Total fees: {total_fees}")
        print(f"Paid fees: {paid_fees}")
        print(f"Outstanding fees: {outstanding_fees}")
        
    else:
        print("❌ No students found. Please add students first.")
    
    print("\n=== Test Complete ===") 