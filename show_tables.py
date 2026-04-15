import sqlite3

def show_tables():
    conn = sqlite3.connect('clinic.db')
    cursor = conn.cursor()
    
    # Show USERS table
    print("\n" + "="*100)
    print("USERS TABLE")
    print("="*100)
    
    cursor.execute("SELECT id, name, email, role, phone, age, created_at FROM users")
    users = cursor.fetchall()
    
    print(f"{'ID':<5} {'Name':<25} {'Email':<30} {'Role':<10} {'Phone':<12} {'Age':<5} {'Created At':<12}")
    print("-"*100)
    for user in users:
        created_date = user[6][:10] if user[6] else "N/A"
        print(f"{user[0]:<5} {user[1]:<25} {user[2]:<30} {user[3]:<10} {str(user[4]):<12} {str(user[5]):<5} {created_date:<12}")
    
    # Show APPOINTMENTS table
    print("\n" + "="*100)
    print("APPOINTMENTS TABLE")
    print("="*100)
    
    cursor.execute("""
        SELECT a.id, u.name as patient, d.name as doctor, a.appointment_date, 
               a.slot, a.patient_reason, a.payment_method, a.status
        FROM appointments a
        JOIN users u ON a.patient_id = u.id
        JOIN users d ON a.doctor_id = d.id
        ORDER BY a.appointment_date DESC
    """)
    appointments = cursor.fetchall()
    
    if appointments:
        print(f"{'ID':<5} {'Patient':<25} {'Doctor':<25} {'Date':<12} {'Slot':<12} {'Payment':<12} {'Status':<12}")
        print("-"*100)
        for apt in appointments:
            reason = (apt[5][:30] + '...') if apt[5] and len(apt[5]) > 30 else (apt[5] or 'N/A')
            print(f"{apt[0]:<5} {apt[1]:<25} {apt[2]:<25} {apt[3]:<12} {apt[4]:<12} {apt[6]:<12} {apt[7]:<12}")
    else:
        print("No appointments found")
    
    conn.close()

if __name__ == '__main__':
    show_tables()