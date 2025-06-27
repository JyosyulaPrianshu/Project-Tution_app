from app import db, create_app
from app.models import Fee

app = create_app()

with app.app_context():
    old_dues = Fee.query.filter(Fee.month.like('Due%')).all()
    for fee in old_dues:
        db.session.delete(fee)
        print(f"Deleted old due '{fee.month}' for user_id={fee.user_id} (fee id: {fee.id})")
    db.session.commit()
    print('All old dues with labels like "Due 1", "Due 2", etc. have been removed.') 