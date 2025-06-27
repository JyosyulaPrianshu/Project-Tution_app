from app import db, create_app
from app.models import Fee

app = create_app()

with app.app_context():
    fees = Fee.query.all()
    for fee in fees:
        db.session.delete(fee)
        print(f"Deleted {fee.month} for user_id={fee.user_id} (fee id: {fee.id})")
    db.session.commit()
    print('All dues removed for all students.') 