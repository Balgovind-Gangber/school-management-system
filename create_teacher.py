from sqlalchemy.sql import roles

from app import db, User, app
from werkzeug.security import generate_password_hash, check_password_hash


with app.app_context():
        password_hash = generate_password_hash('teacher123')

        teacher = User(username = 'teacher1',password=password_hash,role='teacher',status='approved')
        db.session.add(teacher)
        db.session.commit()
        print(" teacher created successfully")

