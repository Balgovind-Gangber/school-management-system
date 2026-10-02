from sqlalchemy.sql import roles

from app import db, User, app
from werkzeug.security import generate_password_hash, check_password_hash


with app.app_context():
        password_hash = generate_password_hash('admin123')

        principal = User(username = 'principal',password=password_hash,role='principal',status='approved')
        db.session.add(principal)
        db.session.commit()
        print("principal created successfully")

