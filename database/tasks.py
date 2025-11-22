from database.db import create_connection

def create_task_in_db(conn, title, description, group_id, assigned_to, created_by, deadline):
    sql = '''INSERT INTO tasks(title, description, group_id, assigned_to, created_by, deadline)
             VALUES(?,?,?,?,?,?)'''
    cur = conn.cursor()
    cur.execute(sql, (title, description, group_id, assigned_to, created_by, deadline))
    conn.commit()
    return cur.lastrowid

def get_user_tasks(conn, user_id):
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE assigned_to=?", (user_id,))
    return cur.fetchall()

def get_active_tasks(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE status='active'")
    return cur.fetchall()


def get_completed_tasks(conn, since_date=None):
    cur = conn.cursor()
    if since_date:
        cur.execute("SELECT * FROM tasks WHERE status='completed' AND created_at >= ?", (since_date,))
    else:
        cur.execute("SELECT * FROM tasks WHERE status='completed'")
    return cur.fetchall()


def get_all_tasks(conn):
    """Получить все задачи с информацией о группе"""
    cur = conn.cursor()
    cur.execute("""
        SELECT t.*, g.group_name 
        FROM tasks t
        LEFT JOIN groups g ON t.group_id = g.group_id
        ORDER BY t.status, t.deadline
    """)
    return [dict(zip([column[0] for column in cur.description], row)) for row in cur.fetchall()]

def get_tasks_by_groups(conn):
    """Получить задачи сгруппированные по командам"""
    cur = conn.cursor()
    cur.execute("""
        SELECT g.group_name, t.title, t.description, t.deadline, t.status
        FROM tasks t
        JOIN groups g ON t.group_id = g.group_id
        ORDER BY g.group_name, t.status
    """)
    return cur.fetchall()

def complete_task_in_db(conn, task_id):
    """Пометить задачу как выполненную"""
    sql = '''UPDATE tasks SET status='completed' WHERE task_id=?'''
    cur = conn.cursor()
    cur.execute(sql, (task_id,))
    conn.commit()
    return cur.rowcount

def get_active_tasks_count(conn):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM tasks WHERE status='active'")
    return cur.fetchone()[0]

def delete_task_in_db(conn, task_id):
    """Удалить задачу из базы данных"""
    sql = '''DELETE FROM tasks WHERE task_id=?'''
    cur = conn.cursor()
    cur.execute(sql, (task_id,))
    conn.commit()
    return cur.rowcount