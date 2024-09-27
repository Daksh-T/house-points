from flask import Flask, render_template, redirect, url_for, request, session, send_file, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import csv
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///points.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    passphrase = db.Column(db.String(150), nullable=False)

class PointTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    house = db.Column(db.String(50), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    
    teacher = db.relationship('Teacher', backref=db.backref('transactions', lazy=True))

@app.before_request
def create_tables():
    app.before_request_funcs[None].remove(create_tables)

    db.create_all()
    if not Teacher.query.filter_by(name='admin').first():
        admin_passphrase = generate_password_hash('1234')
        admin = Teacher(name='admin', passphrase=admin_passphrase)
        db.session.add(admin)
        db.session.commit()

# Routes
@app.route('/')
def index():
    if 'teacher_id' in session:
        return redirect(url_for('teachers'))
    houses = ['ruby', 'emerald', 'sapphire', 'topaz']
    points = {house: 0 for house in houses}
    transactions = PointTransaction.query.all()
    for txn in transactions:
        points[txn.house] += txn.points
    return render_template('index.html', points=points)

@app.route('/teachers', methods=['GET', 'POST'])
def teachers():
    if 'teacher_id' not in session:
        return redirect(url_for('login'))
    
    teacher = Teacher.query.get(session['teacher_id'])
    if not teacher:
        flash("Invalid session. Please log in again.", "danger")
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        action_type = request.form.get('action_type')
        house = request.form['house']
        description = request.form['description']
        
        if action_type == 'add':
            points = int(request.form['points'])
        elif action_type == 'subtract':
            points = -int(request.form['points'])
        else:
            flash("Invalid action type.", "danger")
            return redirect(url_for('teachers'))
        
        txn = PointTransaction(
            teacher_id=teacher.id,
            house=house,
            points=points,
            description=description
        )
        db.session.add(txn)
        db.session.commit()
        flash("Points updated successfully.", "success")
        return redirect(url_for('teachers'))
    
    houses = ['ruby', 'emerald', 'sapphire', 'topaz']
    points = {house: 0 for house in houses}
    transactions = PointTransaction.query.all()
    for txn in transactions:
        points[txn.house] += txn.points
    
    return render_template('teachers.html', teacher=teacher, points=points)

@app.route('/admin_panel', methods=['GET', 'POST'])
def admin_panel():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    admin = Teacher.query.filter_by(name='admin').first()
    if not admin:
        flash("Admin account not found.", "danger")
        return redirect(url_for('admin_login'))
    
    transactions = PointTransaction.query.all()
    teachers = Teacher.query.filter(Teacher.name != 'admin').all()
    
    if request.method == 'POST':
        # Handle adding a new teacher
        action = request.form.get('action')
        if action == 'add_teacher':
            name = request.form['name'].strip()
            passphrase = request.form['passphrase']
            if Teacher.query.filter_by(name=name).first():
                flash("Teacher with this name already exists.", "danger")
            else:
                hashed_passphrase = generate_password_hash(passphrase)
                new_teacher = Teacher(name=name, passphrase=hashed_passphrase)
                db.session.add(new_teacher)
                db.session.commit()
                flash(f"Teacher '{name}' added successfully.", "success")
        elif action == 'delete_teacher':
            teacher_id = request.form.get('teacher_id')
            teacher = Teacher.query.get(teacher_id)
            if teacher and teacher.name != 'admin':
                db.session.delete(teacher)
                db.session.commit()
                flash(f"Teacher '{teacher.name}' deleted successfully.", "success")
            else:
                flash("Cannot delete admin or invalid teacher.", "danger")
        return redirect(url_for('admin_panel'))
    
    return render_template('admin_panel.html', transactions=transactions, teachers=teachers)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'teacher_id' in session:
        return redirect(url_for('teachers'))
    
    if request.method == 'POST':
        name = request.form['name'].strip()
        passphrase = request.form['passphrase']
        teacher = Teacher.query.filter_by(name=name).first()
        if teacher and check_password_hash(teacher.passphrase, passphrase):
            session['teacher_id'] = teacher.id
            flash("Logged in successfully.", "success")
            return redirect(url_for('teachers'))
        else:
            flash("Invalid credentials.", "danger")
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if 'admin' in session:
        return redirect(url_for('admin_panel'))
    
    if request.method == 'POST':
        name = request.form['name'].strip()
        passphrase = request.form['passphrase']
        admin = Teacher.query.filter_by(name='admin').first()
        if admin and check_password_hash(admin.passphrase, passphrase) and name == 'admin':
            session['admin'] = True
            flash("Admin logged in successfully.", "success")
            return redirect(url_for('admin_panel'))
        else:
            flash("Invalid admin credentials.", "danger")
            return redirect(url_for('admin_login'))
    return render_template('admin_login.html')

@app.route('/logout')
def logout():
    session.pop('teacher_id', None)
    session.pop('admin', None)
    flash("Logged out successfully.", "success")
    return redirect(url_for('index'))

@app.route('/download_csv')
def download_csv():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    transactions = PointTransaction.query.all()
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Teacher Name', 'House', 'Points', 'Description'])
    for txn in transactions:
        teacher = Teacher.query.get(txn.teacher_id)
        cw.writerow([txn.id, teacher.name if teacher else 'Unknown', txn.house, txn.points, txn.description])
    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    return send_file(output, mimetype='text/csv', attachment_filename='transactions.csv', as_attachment=True)

@app.route('/revert_transaction/<int:txn_id>', methods=['POST'])
def revert_transaction(txn_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    txn = PointTransaction.query.get(txn_id)
    if txn:
        reverted_txn = PointTransaction(
            teacher_id=txn.teacher_id,
            house=txn.house,
            points=-txn.points,
            description=f"Reverted transaction ID {txn.id}: {txn.description}"
        )
        db.session.add(reverted_txn)
        db.session.commit()
        flash(f"Transaction ID {txn_id} reverted successfully.", "success")
    else:
        flash("Transaction not found.", "danger")
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(debug=False)
