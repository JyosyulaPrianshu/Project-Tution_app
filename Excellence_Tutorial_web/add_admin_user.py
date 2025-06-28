from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        email = input("Enter admin email: ")
        password = input("Enter admin password: ")
        if User.query.filter_by(email=email).first():
            print("Admin with this email already exists.")
        else:
            admin = User(email=email, password=generate_password_hash(password), is_admin=True)
            db.session.add(admin)
            db.session.commit()
            print(f"Admin user {email} created successfully.") 