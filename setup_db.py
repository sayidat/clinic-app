import sqlite3
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def setup_database():
    conn = sqlite3.connect('clinic.db')
    c = conn.cursor()
    
    # Create users table with correct schema
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'PATIENT',
        phone TEXT,
        specialization TEXT,
        age INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Create appointments table
    c.execute('''CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        patient_age INTEGER,
        patient_reason TEXT,
        appointment_date DATE NOT NULL,
        slot TEXT NOT NULL,
        payment_method TEXT,
        status TEXT DEFAULT 'PENDING',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES users(id),
        FOREIGN KEY (doctor_id) REFERENCES users(id)
    )''')
    
    print("✓ Tables created successfully")
    
    # Insert default admin
    admin_email = 'admin@clinic.com'
    c.execute("SELECT id FROM users WHERE email = ?", (admin_email,))
    if not c.fetchone():
        hashed_pwd = hash_password('admin123')
        c.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                  ('System Admin', admin_email, hashed_pwd, 'ADMIN'))
        print("✓ Admin account created")
    
    # Insert sample doctors
    doctors = [
        ('Dr. Sarah Johnson', 'dr.sarah@clinic.com', 'doctor123', 'Cardiologist'),
        ('Dr. Michael Chen', 'dr.michael@clinic.com', 'doctor123', 'Neurologist'),
        ('Dr. Emily Brown', 'dr.emily@clinic.com', 'doctor123', 'Pediatrician')
    ]
    
    for name, email, pwd, spec in doctors:
        c.execute("SELECT id FROM users WHERE email = ?", (email,))
        if not c.fetchone():
            hashed_pwd = hash_password(pwd)
            c.execute("INSERT INTO users (name, email, password, role, specialization) VALUES (?, ?, ?, ?, ?)",
                      (name, email, hashed_pwd, 'DOCTOR', spec))
            print(f"✓ Doctor account created: {name}")
    
    # Insert sample patient
    c.execute("SELECT id FROM users WHERE email = ?", ('patient@example.com',))
    if not c.fetchone():
        hashed_pwd = hash_password('patient123')
        c.execute("INSERT INTO users (name, email, password, role, phone, age) VALUES (?, ?, ?, ?, ?, ?)",
                  ('John Doe', 'patient@example.com', hashed_pwd, 'PATIENT', '9876543210', 30))
        print("✓ Patient account created: John Doe")
    
    conn.commit()
    
    # Display all tables and records
    print("\n" + "="*50)
    print("DATABASE SETUP COMPLETE!")
    print("="*50)
    
    # Show users table
    print("\n📋 USERS TABLE:")
    print("-" * 50)
    users = c.execute("SELECT id, name, email, role, age FROM users").fetchall()
    for user in users:
        age_display = f"Age: {user[4]}" if user[4] else "Age: N/A"
        print(f"ID: {user[0]} | Name: {user[1]} | Email: {user[2]} | Role: {user[3]} | {age_display}")
    
    # Show appointments table
    print("\n📋 APPOINTMENTS TABLE:")
    print("-" * 50)
    appointments = c.execute("SELECT * FROM appointments").fetchall()
    if appointments:
        for apt in appointments:
            print(f"ID: {apt[0]} | Status: {apt[8]}")
    else:
        print("No appointments yet")
    
    conn.close()
    
    print("\n✅ Database 'clinic.db' created successfully!")
    print("\n🔑 Login Credentials:")
    print("   " + "="*40)
    print("   Admin  - admin@clinic.com / admin123")
    print("   Doctor - dr.sarah@clinic.com / doctor123")
    print("   Doctor - dr.michael@clinic.com / doctor123")
    print("   Doctor - dr.emily@clinic.com / doctor123")
    print("   Patient - patient@example.com / patient123")
    print("   " + "="*40)

if __name__ == '__main__':
    setup_database()