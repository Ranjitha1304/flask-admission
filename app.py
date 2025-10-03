from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # keep this secret in production!

# SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
db = SQLAlchemy(app)

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'ranjitha13cs@gmail.com'  # replace with your email
app.config['MAIL_PASSWORD'] = 'iixy zrjl wzbc vqtk'   # replace with your email app password (or leave blank for testing)
mail = Mail(app)

# Student model
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    course = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default="Pending")  # Pending / Approved / Rejected

# Admin credentials (simple)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'

# ---------------- Home Page ----------------
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        course = request.form['course']

        # Check if email already exists
        existing = Student.query.filter_by(email=email).first()
        if existing:
            flash('Email already registered!', 'danger')
            return redirect(url_for('index'))

        student = Student(name=name, email=email, course=course)
        db.session.add(student)
        db.session.commit()
        flash('Registration submitted! Waiting for admin approval.', 'success')
        return redirect(url_for('success'))
    return render_template('index.html')

# ---------------- Success Page ----------------
@app.route('/success')
def success():
    return render_template('success.html')

# ---------------- Admin Login ----------------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash('Logged in successfully.', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'danger')
            return redirect(url_for('admin_login'))
    return render_template('login.html')

# ---------------- Admin Dashboard ----------------
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        flash('Please login first.', 'danger')
        return redirect(url_for('admin_login'))

    students = Student.query.all()
    return render_template('admin.html', students=students)

# ---------------- Approve Student ----------------
@app.route('/approve/<int:id>')
def approve(id):
    if not session.get('admin_logged_in'):
        flash('Please login first.', 'danger')
        return redirect(url_for('admin_login'))

    student = Student.query.get_or_404(id)
    if student.status != "Approved":
        student.status = "Approved"
        db.session.commit()
        try:
            msg = Message('Admission Approved',
                          sender=app.config.get('MAIL_USERNAME'),
                          recipients=[student.email])
            msg.body = f"Hello {student.name},\n\nYour admission for {student.course} has been approved!"
            mail.send(msg)
        except Exception:
            flash("Email sending failed, but status updated.", "warning")
        flash(f"{student.name} has been approved.", 'success')
    else:
        flash(f"{student.name} is already approved.", 'info')

    return redirect(url_for('admin_dashboard'))

# ---------------- Reject Student ----------------
@app.route('/reject/<int:id>')
def reject(id):
    if not session.get('admin_logged_in'):
        flash('Please login first.', 'danger')
        return redirect(url_for('admin_login'))

    student = Student.query.get_or_404(id)
    if student.status != "Rejected":
        student.status = "Rejected"
        db.session.commit()
        try:
            msg = Message('Admission Rejected',
                          sender=app.config.get('MAIL_USERNAME'),
                          recipients=[student.email])
            msg.body = f"Hello {student.name},\n\nWe are sorry. Your admission for {student.course} has been rejected."
            mail.send(msg)
        except Exception:
            flash("Email sending failed, but status updated.", "warning")
        flash(f"{student.name} has been rejected.", 'danger')
    else:
        flash(f"{student.name} is already rejected.", 'info')

    return redirect(url_for('admin_dashboard'))

# ---------------- Admin Logout ----------------
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

# ---------------- Run App ----------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
