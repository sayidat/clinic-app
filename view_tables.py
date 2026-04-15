import sqlite3

def print_table(title, data, headers):
    """Print data in a formatted table"""
    print("\n" + "="*80)
    print(title)
    print("="*80)
    
    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in data:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)) if cell else 4)
    
    # Print header
    header_line = "|"
    for i, header in enumerate(headers):
        header_line += f" {header:<{col_widths[i]}} |"
    print(header_line)
    print("-" * len(header_line))
    
    # Print rows
    for row in data:
        row_line = "|"
        for i, cell in enumerate(row):
            cell_str = str(cell) if cell else "N/A"
            row_line += f" {cell_str:<{col_widths[i]}} |"
        print(row_line)
    
    print("="*80)

def view_all_tables():
    conn = sqlite3.connect('clinic.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = cursor.fetchall()
    
    print("\n" + "="*80)
    print("CLINIC MANAGEMENT SYSTEM - DATABASE TABLES")
    print("="*80)
    
    for table in tables:
        table_name = table[0]
        
        # Get table info
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # Get all data
        cursor.execute(f"SELECT * FROM {table_name}")
        data = cursor.fetchall()
        
        if table_name == 'users':
            # Format users table
            formatted_data = []
            for row in data:
                formatted_row = list(row)
                # Format created_at if it exists
                if len(formatted_row) > 8 and formatted_row[8]:
                    formatted_row[8] = formatted_row[8][:10]
                formatted_data.append(formatted_row)
            print_table(table_name.upper(), formatted_data, column_names)
            
        elif table_name == 'appointments':
            # Format appointments table
            formatted_data = []
            for row in data:
                formatted_row = list(row)
                if len(formatted_row) > 9 and formatted_row[9]:
                    formatted_row[9] = formatted_row[9][:10]
                formatted_data.append(formatted_row)
            print_table(table_name.upper(), formatted_data, column_names)
        else:
            print_table(table_name.upper(), data, column_names)
    
    # Show statistics
    print("\n" + "="*40)
    print("DATABASE STATISTICS")
    print("="*40)
    
    # Count users by role
    cursor.execute("""
        SELECT role, COUNT(*) as count 
        FROM users 
        GROUP BY role
    """)
    role_counts = cursor.fetchall()
    
    print("\nUsers by Role:")
    print("-" * 30)
    for role, count in role_counts:
        print(f"  {role}: {count}")
    
    # Count appointments by status
    cursor.execute("""
        SELECT status, COUNT(*) as count 
        FROM appointments 
        GROUP BY status
    """)
    status_counts = cursor.fetchall()
    
    if status_counts:
        print("\nAppointments by Status:")
        print("-" * 30)
        for status, count in status_counts:
            print(f"  {status}: {count}")
    
    conn.close()
    
    print("\n" + "="*40)
    print("Database view completed")
    print("="*40)

if __name__ == '__main__':
    view_all_tables()