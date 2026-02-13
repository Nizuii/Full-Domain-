from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_wtf import CSRFProtect  # ✅ Added for CSRF protection
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import random
import time
import re  # ✅ For email validation

# -------------------- EMAIL LOGIN -------------------- #
app = Flask(__name__)
app.secret_key = "supersecretkey"

email_input = input("Enter your email address: ")
email_password = input("Enter email password: ")

# -------------------- CSRF PROTECTION -------------------- #
csrf = CSRFProtect(app)  # ✅ Enable CSRF protection for all POST routes

# -------------------- DATABASE -------------------- #
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# -------------------- MAIL CONFIG -------------------- #
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = email_input
app.config['MAIL_PASSWORD'] = email_password
app.config['MAIL_DEFAULT_SENDER'] = email_input
mail = Mail(app)

# -------------------- DATABASE SETUP -------------------- #
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

with app.app_context():
    db.create_all()

# -------------------- LOGIN REQUIRED DECORATOR -------------------- #
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in first!", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# -------------------- PREVENT LOGGED-IN USERS -------------------- #
def prevent_logged_in_access(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' in session:
            flash("You are already logged in!", "info")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# -------------------- DISABLE CACHING -------------------- #
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Surrogate-Control'] = 'no-store'
    return response

# -------------------- EMAIL VALIDATION FUNCTION -------------------- #
def is_valid_email(email):
    # ✅ Reliable email regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email)

# -------------------- ROUTES -------------------- #

# HOME
@app.route('/')
@prevent_logged_in_access
def home():
    return render_template('index.html')

# LOGIN
@app.route('/login', methods=['GET', 'POST'])
@prevent_logged_in_access
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not is_valid_email(email):
            flash("Invalid email format!", "danger")
            return redirect(url_for('login'))

        user = User.query.filter_by(email=email).first()
        if not user:
            flash("Email not registered!", "danger")
            return redirect(url_for('login'))

        if not check_password_hash(user.password, password):
            flash("Incorrect password!", "danger")
            return redirect(url_for('login'))

        generated_otp = random.randint(100000, 999999)
        session['otp'] = generated_otp
        session['email'] = email
        session['temp_user_id'] = user.id
        session['temp_username'] = user.username

        try:
            msg = Message("Your Login OTP Code", recipients=[email])
            msg.body = f"Hello {user.username},\n\nYour OTP for login is {generated_otp}.\nThis code will expire in 5 minutes."
            mail.send(msg)
            flash("OTP sent to your email. Please verify to continue.", "info")
        except Exception as e:
            flash(f"Failed to send OTP: {str(e)}", "danger")
            return redirect(url_for('login'))

        return redirect(url_for('otp_verification'))

    return render_template('login.html')

# SIGNUP
@app.route('/signup', methods=['GET', 'POST'])
@prevent_logged_in_access
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        if not is_valid_email(email):
            flash("Invalid email format! Please enter a valid email like test@example.com", "danger")
            return redirect(url_for('register'))

        if password1 != password2:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password1)
        try:
            new_user = User(username=username, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()

            generated_otp = random.randint(100000, 999999)
            session['otp'] = generated_otp
            session['email'] = email

            msg = Message("Your Signup OTP Code", recipients=[email])
            msg.body = f"Hello {username},\n\nYour OTP for signup is {generated_otp}.\nPlease verify to activate your account."
            mail.send(msg)

            flash("Signup successful! Please verify OTP.", "success")
            return redirect(url_for('otp_verification'))
        except IntegrityError:
            db.session.rollback()
            flash("Email or username already registered!", "warning")
            return redirect(url_for('register'))

    return render_template('register.html')

# OTP VERIFICATION
@app.route('/otp_verification', methods=['GET', 'POST'])
@prevent_logged_in_access
def otp_verification():
    if request.method == 'POST':
        otp_number = request.form.get('otp')
        if str(otp_number) != str(session.get('otp')):
            flash("Incorrect OTP", 'warning')
            return redirect(url_for('otp_verification'))

        user = User.query.filter_by(email=session.get('email')).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.username

        session.pop('otp', None)
        session.pop('temp_user_id', None)
        session.pop('temp_username', None)

        flash('Verification success', 'success')
        return redirect(url_for('dashboard'))

    return render_template('otp_verification.html')

# RESEND OTP
@app.route('/resend_otp')
@prevent_logged_in_access
def resend_otp():
    email = session.get('email')
    if not email:
        flash("Session expired. Please log in again.", "warning")
        return redirect(url_for('login'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('login'))

    new_otp = random.randint(100000, 999999)
    session['otp'] = new_otp
    session['otp_time'] = time.time()

    try:
        msg = Message("Your New OTP Code", recipients=[email])
        msg.body = f"Hello {user.username},\n\nYour new OTP is {new_otp}.\nThis code will expire in 5 minutes."
        mail.send(msg)
        flash("A new OTP has been sent to your email.", "info")
    except Exception as e:
        flash(f"Failed to resend OTP: {str(e)}", "danger")

    return redirect(url_for('otp_verification'))

# DASHBOARD
@app.route('/home')
@login_required
def dashboard():
    return render_template('dashboard.html')

# LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)
