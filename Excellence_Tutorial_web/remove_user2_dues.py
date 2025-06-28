from app import db, create_app
from app.models import Fee

app = create_app()

with app.app_context():
    # Remove all dues labeled 'Due 2' to 'Due 8' for user_id=2
    for i in range(2, 9):
        label = f'Due {i}'
        fees = Fee.query.filter_by(user_id=2, month=label).all()
        for fee in fees:
            db.session.delete(fee)
            print(f"Deleted {label} for user_id=2 (fee id: {fee.id})")
    db.session.commit()
    print('Done removing specified dues for user_id=2.') 