from app import create_app
from flask_wtf.csrf import generate_csrf

app = create_app()

with app.app_context():
    print("=== CSRF Debug Test ===")
    
    # Generate a CSRF token
    try:
        token = generate_csrf()
        print(f"Generated CSRF token: {token}")
        print(f"Token length: {len(token)}")
        
        # Test if token is valid
        from flask_wtf.csrf import validate_csrf
        validate_csrf(token)
        print("✅ CSRF token is valid")
    except Exception as e:
        print(f"❌ CSRF token error: {e}")
    
    print("=== Debug Complete ===") 