from functools import wraps
from datetime import datetime, date

import requests
from flask_sqlalchemy.model import Model
from sqlalchemy import true
from sqlalchemy.orm import backref

from flask import Flask, redirect, render_template, request, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy, session
from flask_login import UserMixin, login_user, logout_user, current_user, login_required, LoginManager
from datetime import datetime
from authlib.integrations.flask_client import OAuth
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate, migrate

app = Flask(__name__)
app.secret_key = "super secret key"
oauth = OAuth(app)

google = oauth.register(name='google',
                        client_id='701404426472-1vl7r6jevkfk62nli3cjqim5pjcfg953.apps.googleusercontent.com',
                        client_secret='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',
                        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
                        client_kwargs={'scope': 'openid email profile'
                                       })

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql+psycopg2://postgres:123@localhost/school_management"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# users table declaration
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(500), nullable=False)
    role = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(80), default="pending")


# student table declaration
class Student(db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(80), nullable=False)
    father_name = db.Column(db.String(80), nullable=False)
    mother_name = db.Column(db.String(80), nullable=False)
    date_of_birth = db.Column(db.String(80), nullable=False)
    gender = db.Column(db.String(80), nullable=False)
    class_name = db.Column(db.String(80), nullable=False)
    mobile_number = db.Column(db.String(80), nullable=False)
    address = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(80), default="pending")
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    user = db.relationship("User", backref="student")


# fees table
class Fee(db.Model):
    __tablename__ = "fees"
    id = db.Column(db.Integer, primary_key=True)
    total_amount = db.Column(db.Float, nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    student = db.relationship("Student", backref="fees")


# attendance table declaration
class Attendance(db.Model):
    date = db.Column(db.Date, nullable=False)
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(80), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    student = db.relationship("Student", backref="Attendance")


# fee payemnt table
class Payment(db.Model):
    __tablename__ = "payments"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    receipt_no = db.Column(db.String(80), nullable=False)
    paid_amount = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String(80), default="pending")
    payment_date = db.Column(db.Date, nullable=False)
    payment_mode = db.Column(db.String(80), nullable=False)
    remark = db.Column(db.String(500), nullable=False)
    transaction_id = db.Column(db.String, nullable=False)
    student = db.relationship("Student", backref="payments")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    return render_template("home.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form['role']
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user is None:
            return "User not found "
        if check_password_hash(user.password, password):
            login_user(user)
            if user.role == "teacher":
                return redirect("/teacher")
            elif user.role == "student":
                return redirect("/student")
            elif user.role == "principal":
                return redirect("/principal")
            else:
                return "invalid role"

    return render_template("home.html")


# google login route
@app.route('/login/google')
def google_login():
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)


# callback route
@app.route('/login/google/callback')
def google_callback():
    token = google.authorize_access_token()
    userinfo = token.get('userinfo')
    print(userinfo)
    return "google login successful"


# new student registration
@app.route('/student_register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        student = Student(
            student_name=request.form['student_name'],
            father_name=request.form['father_name'],
            mother_name=request.form['mother_name'],
            date_of_birth=request.form['date_of_birth'],
            gender=request.form['gender'],
            class_name=request.form['class_name'],
            mobile_number=request.form['mobile_number'],
            address=request.form['address'])

        db.session.add(student)
        db.session.commit()

        return " student created successfully"

    return render_template("student_register.html")


# role authoraization decorator
def role_required(role_required):
    def decorater(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            if current_user.role != role_required:
                return "access denied"
            return function(*args, **kwargs)

        return wrapper

    return decorater



''' @app.route('/login/google', methods=["POST"])
def google_login():
    data = request.get_json()
    creditional = data.get("creditional")

    try:
        idinfo = id_token.verify_oauth2_token(creditional, requests.Request(),
        app.config['GOOGLE_CLIENT_ID'], app.config['GOOGLE_CLIENT_SECRET'])
        email = idinfo.get("email")

        # search in users table
        user= User.query.filter_by(email=email).first()
        if not user:
            return jsonify(
                {
                    "success": False,
                    "message": "user not found"
                }
            )
    # session
    session["user_id"] = user.id
    session["username"] = user.username
    session["role"] = user.role

    # role based authentication and dashboard
    if user.role=="teacher"
        url_direct= "/teacher/dashboard"
        elif user.role=="student"
        url_direct= "/student/dashboard"
        elif user.role=="principal"
        url_direct= "/principal/dashboard"
        else
            return jsonify(
            {
                "success": False,
                message="invalid user role"
            }
             )
    return jsonify({
        "success": True,
        "redirect": url_direct
        })
        finally :
             print("google login error",e)
             return jsonify({
                     "success": False,
                    "message": "Google verification failed "
                })


'''
# rounting for principal dashboard
@app.route('/principal')
@login_required
@role_required("principal")
def principal_dashboard():
    return render_template("principal_dashboard.html", username=current_user.username)


# look pending student
@app.route('/principal/student')
@login_required
@role_required("principal")
def pending_students():
    students = Student.query.filter_by(status="pending").all()
    return render_template("principal_students.html", students=students)


#look all student list
@app.route('/principal/allstudentlist')
@login_required
@role_required("principal")
def allstudentlist():
    student = Student.query.all()
    return render_template("principal_studentlist.html", student=student)


@app.route('/principal/student/approve/<int:student_id>')
@login_required
@role_required("principal")
def approve_student(student_id):
    student = db.session.get(Student, student_id)
    if student is None:
        return "student not found"
    student.status = "approved"
    user = User(username=f"student{student.id}", password=generate_password_hash("student123"), role="student",
                status="approved")
    db.session.add(user)
    student.user = user
    db.session.commit()
    return redirect("/principal/student")


# teacher routing
@app.route('/teacher')
@login_required
@role_required("teacher")
def teacher_dashboard():
    student = Student.query.all()
    return render_template("teacher_dashboard_new.html", student=student)


# attendance
@app.route("/teacher/attendance", methods=["GET", "POST"])
@login_required
@role_required("teacher")
def teacher_attendance():
    class_name = request.values.get('class_name')
    attendance_date = request.values.get('attendance_date')
    students = None
    if class_name and attendance_date:
        students = Student.query.filter_by(class_name=class_name, status="approved").all()
        return render_template("teacher_dashboard_new.html", students=students, class_name=class_name,
                               attendance_date=attendance_date)
    return render_template("teacher_dashboard_new.html")


# save attendance
@app.route("/teacher/attendance/save", methods=["POST"])
@login_required
@role_required("teacher")
def attendance_save():
    class_name = request.form['class_name']
    attendance_date = request.form['attendance_date']
    students = Student.query.filter_by(class_name=class_name, status="approved").all()

    for student in students:
        status = request.form.get(f"status_{student.id}")
        attendance = Attendance.query.filter_by(student_id=student.id, date=attendance_date).first()
        if attendance:
            attendance.status = status

        else:
            attendance = Attendance(student_id=student.id, date=attendance_date, status=status)
            db.session.add(attendance)
    db.session.commit()
    return "attendance saved"


# search module for fees collection
@app.route("/search", methods=["POST","GET"])
@login_required
@role_required("teacher")
@login_required
@role_required("teacher")
def student_search ():
    class_name = request.args.get('class_name')

    student=[]
    if class_name:
        student = Student.query.filter_by(class_name=class_name, status="approved").all()
        return render_template("teacher_dashboard_new.html", student=student)








@app.route("/teacher/feepayment", methods=["GET", "POST"])
@login_required
@role_required("teacher")
def fees_payment():
    student = Student.query.all()

    return render_template("teacher_feepayment.html", student=student)


@app.route("/teacher/fees/student/<int:user_id>", methods=["GET"])
#@login_required
#@role_required('teacher')
def student_fee(user_id):
    student = Student.query.filter_by(user_id=user_id).first()
    if student is None:
        return "student not found"

    fee = Fee.query.filter_by(student_id=student.id).first()
    payments = Payment.query.filter_by(student_id=student.id).all()

    total_amount = fee.total_amount
    paid_amount = sum(payment.paid_amount for payment in payments)
    due_amount = total_amount - paid_amount

    return render_template("student_fee.html", student=student, total_amount=total_amount, paid_amount=paid_amount,
                           due_amount=due_amount)


# fees payment  module
@app.route("/teacher/fees/student/deposit/<int:student_id>", methods=["GET", "POST"])
#@login_required
#@role_required("teacher")
def fees_deposit(student_id):
    if request.method == "POST":
        print("post request received")
        student= Student.query.filter_by(id=student_id).first()
        deposit_amount = request.form.get("deposit_amount")
        receipt_no = f"REC-{datetime.today().strftime('%Y%m%d%H%M%S')}"
        payment_status = 'Successful'
        payment_mode = 'cash'
        payment_date = datetime.today().date()
        remark = 'paid at counter'
        transcation_id = 'nil'
        new_deposit = Payment(
            student_id=student_id,
            paid_amount=deposit_amount,
            receipt_no=receipt_no,
            payment_status=payment_status,
            payment_mode=payment_mode,
            payment_date=payment_date,
            remark=remark,
            transaction_id=transcation_id)
        db.session.add(new_deposit)
        db.session.commit()
        print("payment saved", new_deposit.id)

        receipt_data= None
        # receipt data dictionary
        receipt_data ={
            'receipt_no': receipt_no,
            'student_id': student.id,
            'student_name': student.student_name,
            'class_name': student.class_name,
            'status': payment_status,
            'deposit_amount':deposit_amount

        }

    return render_template("student_fee.html",receipt=receipt_data,student=student)


@app.route('/student')
@login_required
@role_required("student")
def student_dashboard():
    student = Student.query.filter_by(user_id=current_user.id).first()
    return render_template("student_dashboard.html", student=student)


# logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return "logout success"


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
