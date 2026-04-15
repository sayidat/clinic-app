from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import hashlib
from datetime import datetime, date
from functools import wraps

app = Flask(__name__)
app.secret_key = "clinic_secret_key_2026_secure_key"

# Database connection helper
def get_db():
    conn = sqlite3.connect('clinic.db')
    conn.row_factory = sqlite3.Row
    return conn

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Role required decorator
def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session or session['role'] not in roles:
                flash('Access denied!', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Hash password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Get available slots for a doctor on a specific date
def get_available_slots(doctor_id, date):
    all_slots = ["09:00 AM", "10:00 AM", "11:00 AM", "02:00 PM", "03:00 PM", "04:00 PM"]
    conn = get_db()
    c = conn.cursor()
    booked_slots = c.execute(
        "SELECT slot FROM appointments WHERE doctor_id = ? AND appointment_date = ? AND status != 'CANCELLED'",
        (doctor_id, date)
    ).fetchall()
    conn.close()
    booked_slots_list = [slot['slot'] for slot in booked_slots]
    available_slots = [slot for slot in all_slots if slot not in booked_slots_list]
    return available_slots

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'PATIENT')
        phone = request.form.get('phone')
        age = request.form.get('age')
        specialization = request.form.get('specialization') if role == 'DOCTOR' else None
        
        conn = get_db()
        c = conn.cursor()
        try:
            hashed = hash_password(password)
            c.execute("""INSERT INTO users (name, email, password, role, phone, age, specialization)
                         VALUES (?, ?, ?, ?, ?, ?, ?)""", 
                      (name, email, hashed, role, phone, age, specialization))
            conn.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Email already exists!", "danger")
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()
        
        if user and user['password'] == hash_password(password):
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['name'] = user['name']
            session['email'] = user['email']
            
            flash(f"Welcome back, {user['name']}!", "success")
            
            if user['role'] == 'ADMIN':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'DOCTOR':
                return redirect(url_for('doctor_dashboard'))
            else:
                return redirect(url_for('patient_dashboard'))
        else:
            flash("Invalid email or password!", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('index'))

# Patient Routes
@app.route('/patient/dashboard')
@login_required
@role_required('PATIENT')
def patient_dashboard():
    user_id = session['user_id']
    conn = get_db()
    c = conn.cursor()
    
    # Get upcoming appointments
    upcoming = c.execute('''
        SELECT a.*, u.name as doctor_name, u.specialization 
        FROM appointments a 
        JOIN users u ON a.doctor_id = u.id 
        WHERE a.patient_id = ? AND a.status != 'COMPLETED' AND a.appointment_date >= date('now')
        ORDER BY a.appointment_date ASC, a.slot ASC
    ''', (user_id,)).fetchall()
    
    # Get past appointments
    past = c.execute('''
        SELECT a.*, u.name as doctor_name, u.specialization 
        FROM appointments a 
        JOIN users u ON a.doctor_id = u.id 
        WHERE a.patient_id = ? AND (a.status = 'COMPLETED' OR a.appointment_date < date('now'))
        ORDER BY a.appointment_date DESC, a.slot DESC
    ''', (user_id,)).fetchall()
    
    conn.close()
    return render_template('patient_dashboard.html', upcoming=upcoming, past=past)

@app.route('/patient/book', methods=['GET', 'POST'])
@login_required
@role_required('PATIENT')
def book_appointment():
    conn = get_db()
    c = conn.cursor()
    
    if request.method == 'POST':
        doctor_id = request.form['doctor_id']
        appointment_date = request.form['appointment_date']
        slot = request.form['slot']
        patient_age = request.form['patient_age']
        patient_reason = request.form['patient_reason']
        payment_method = request.form['payment_method']
        patient_id = session['user_id']
        
        # Check if slot is still available
        available_slots = get_available_slots(doctor_id, appointment_date)
        if slot not in available_slots:
            flash("This slot is no longer available!", "danger")
            return redirect(url_for('book_appointment'))
        
        try:
            c.execute('''
                INSERT INTO appointments (patient_id, doctor_id, patient_age, patient_reason, 
                                        appointment_date, slot, payment_method, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDING')
            ''', (patient_id, doctor_id, patient_age, patient_reason, appointment_date, slot, payment_method))
            conn.commit()
            flash("Appointment booked successfully!", "success")
            return redirect(url_for('patient_dashboard'))
        except Exception as e:
            flash(f"Error booking appointment: {str(e)}", "danger")
        finally:
            conn.close()
    
    # GET request - show booking form
    doctors = c.execute("SELECT id, name, specialization FROM users WHERE role = 'DOCTOR'").fetchall()
    conn.close()
    return render_template('book_appointment.html', doctors=doctors, today=date.today().isoformat())

@app.route('/get_slots/<int:doctor_id>/<date>')
@login_required
def get_slots(doctor_id, date):
    available_slots = get_available_slots(doctor_id, date)
    return {'slots': available_slots}

@app.route('/patient/cancel/<int:appointment_id>')
@login_required
@role_required('PATIENT')
def cancel_appointment(appointment_id):
    conn = get_db()
    c = conn.cursor()
    
    # Verify appointment belongs to patient
    c.execute("UPDATE appointments SET status = 'CANCELLED' WHERE id = ? AND patient_id = ?",
              (appointment_id, session['user_id']))
    conn.commit()
    conn.close()
    
    flash("Appointment cancelled successfully!", "success")
    return redirect(url_for('patient_dashboard'))

# Doctor Routes
@app.route('/doctor/dashboard')
@login_required
@role_required('DOCTOR')
def doctor_dashboard():
    doctor_id = session['user_id']
    conn = get_db()
    c = conn.cursor()
    
    # Get today's appointments
    today = datetime.now().strftime('%Y-%m-%d')
    today_appointments = c.execute('''
        SELECT a.*, u.name as patient_name, u.email, u.phone, u.age as patient_age_reg
        FROM appointments a 
        JOIN users u ON a.patient_id = u.id 
        WHERE a.doctor_id = ? AND a.appointment_date = ? AND a.status != 'CANCELLED'
        ORDER BY a.slot ASC
    ''', (doctor_id, today)).fetchall()
    
    # Get upcoming appointments
    upcoming = c.execute('''
        SELECT a.*, u.name as patient_name, u.email, u.phone
        FROM appointments a 
        JOIN users u ON a.patient_id = u.id 
        WHERE a.doctor_id = ? AND a.appointment_date > ? AND a.status = 'PENDING'
        ORDER BY a.appointment_date ASC, a.slot ASC
    ''', (doctor_id, today)).fetchall()
    
    # Get completed appointments
    completed = c.execute('''
        SELECT a.*, u.name as patient_name
        FROM appointments a 
        JOIN users u ON a.patient_id = u.id 
        WHERE a.doctor_id = ? AND a.status = 'COMPLETED'
        ORDER BY a.appointment_date DESC
        LIMIT 10
    ''', (doctor_id,)).fetchall()
    
    conn.close()
    return render_template('doctor_dashboard.html', today_appointments=today_appointments, 
                         upcoming=upcoming, completed=completed)

@app.route('/doctor/complete/<int:appointment_id>')
@login_required
@role_required('DOCTOR')
def complete_appointment(appointment_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE appointments SET status = 'COMPLETED' WHERE id = ?", (appointment_id,))
    conn.commit()
    conn.close()
    flash("Appointment marked as completed!", "success")
    return redirect(url_for('doctor_dashboard'))

# Admin Routes
@app.route('/admin/dashboard')
@login_required
@role_required('ADMIN')
def admin_dashboard():
    conn = get_db()
    c = conn.cursor()
    
    # Statistics
    total_patients = c.execute("SELECT COUNT(*) as count FROM users WHERE role = 'PATIENT'").fetchone()['count']
    total_doctors = c.execute("SELECT COUNT(*) as count FROM users WHERE role = 'DOCTOR'").fetchone()['count']
    total_appointments = c.execute("SELECT COUNT(*) as count FROM appointments").fetchone()['count']
    pending_appointments = c.execute("SELECT COUNT(*) as count FROM appointments WHERE status = 'PENDING'").fetchone()['count']
    completed_appointments = c.execute("SELECT COUNT(*) as count FROM appointments WHERE status = 'COMPLETED'").fetchone()['count']
    cancelled_appointments = c.execute("SELECT COUNT(*) as count FROM appointments WHERE status = 'CANCELLED'").fetchone()['count']
    
    # Recent appointments
    recent_appointments = c.execute('''
        SELECT a.*, p.name as patient_name, d.name as doctor_name, d.specialization
        FROM appointments a
        JOIN users p ON a.patient_id = p.id
        JOIN users d ON a.doctor_id = d.id
        ORDER BY a.created_at DESC
        LIMIT 10
    ''').fetchall()
    
    # All users
    users = c.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    
    conn.close()
    return render_template('admin_dashboard.html', 
                         total_patients=total_patients,
                         total_doctors=total_doctors,
                         total_appointments=total_appointments,
                         pending_appointments=pending_appointments,
                         completed_appointments=completed_appointments,
                         cancelled_appointments=cancelled_appointments,
                         recent_appointments=recent_appointments,
                         users=users)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)