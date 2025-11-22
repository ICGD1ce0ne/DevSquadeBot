from database.db import create_connection

def create_group(conn, group_name):
    sql = '''INSERT INTO groups(group_name) VALUES(?)'''
    cur = conn.cursor()
    cur.execute(sql, (group_name,))
    conn.commit()
    return cur.lastrowid

def get_groups(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM groups")
    return cur.fetchall()

def delete_group(conn, group_id):
    sql = '''DELETE FROM groups WHERE group_id=?'''
    cur = conn.cursor()
    cur.execute(sql, (group_id,))
    conn.commit()
    return cur.rowcount

def add_member_to_group(conn, user_id, group_id):
    sql = '''INSERT OR IGNORE INTO employee_groups(user_id, group_id) VALUES(?,?)'''
    cur = conn.cursor()
    cur.execute(sql, (user_id, group_id))
    conn.commit()
    return cur.rowcount


def get_groups_with_members(conn):
    """Получить группы с участниками"""
    cur = conn.cursor()

    # Получаем все группы
    cur.execute("SELECT group_id, group_name FROM groups")
    groups = []

    for group_id, group_name in cur.fetchall():
        # Для каждой группы получаем участников
        cur.execute("""
            SELECT e.user_id, e.full_name 
            FROM employee_groups eg
            JOIN employees e ON eg.user_id = e.user_id
            WHERE eg.group_id = ?
        """, (group_id,))

        members = [f"{row[1]} (ID: {row[0]})" for row in cur.fetchall()]
        groups.append({
            'id': group_id,
            'name': group_name,
            'members': members
        })

    return groups


def remove_member_from_group(conn, user_id, group_id):
    """Удалить участника из группы"""
    sql = "DELETE FROM employee_groups WHERE user_id = ? AND group_id = ?"
    cur = conn.cursor()
    cur.execute(sql, (user_id, group_id))
    conn.commit()
    return cur.rowcount