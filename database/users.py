from database.db import create_connection

def add_employee_to_db(conn, user_id, username, full_name, category):
    sql = '''INSERT OR REPLACE INTO employees(user_id, username, full_name, category)
             VALUES(?,?,?,?)'''
    cur = conn.cursor()
    cur.execute(sql, (user_id, username, full_name, category))
    conn.commit()
    return cur.lastrowid

def get_employees(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM employees")
    return cur.fetchall()

def remove_employee_from_db(conn, user_id):
    sql = '''DELETE FROM employees WHERE user_id=?'''
    cur = conn.cursor()
    cur.execute(sql, (user_id,))
    conn.commit()
    return cur.rowcount
