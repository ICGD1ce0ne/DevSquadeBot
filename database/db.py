import sqlite3
from sqlite3 import Error


def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('bot_database.db')
        return conn
    except Error as e:
        print(e)
    return conn


def init_db():
    conn = create_connection()
    if conn is not None:
        try:
            c = conn.cursor()

            # Таблица работников
            c.execute('''CREATE TABLE IF NOT EXISTS employees
                         (user_id INTEGER PRIMARY KEY, 
                          username TEXT, 
                          full_name TEXT, 
                          category TEXT)''')

            # Таблица групп
            c.execute('''CREATE TABLE IF NOT EXISTS groups
                         (group_id INTEGER PRIMARY KEY AUTOINCREMENT,
                          group_name TEXT UNIQUE)''')

            # Таблица связи работников и групп
            c.execute('''CREATE TABLE IF NOT EXISTS employee_groups
                         (user_id INTEGER,
                          group_id INTEGER,
                          FOREIGN KEY (user_id) REFERENCES employees (user_id),
                          FOREIGN KEY (group_id) REFERENCES groups (group_id),
                          PRIMARY KEY (user_id, group_id))''')

            # Таблица задач
            c.execute('''CREATE TABLE IF NOT EXISTS tasks
                         (task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                          title TEXT,
                          description TEXT,
                          group_id INTEGER,
                          assigned_to INTEGER,
                          created_by INTEGER,
                          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                          deadline TIMESTAMP,
                          status TEXT DEFAULT 'active',
                          FOREIGN KEY (group_id) REFERENCES groups (group_id),
                          FOREIGN KEY (assigned_to) REFERENCES employees (user_id))''')

            conn.commit()
        except Error as e:
            print(e)
        finally:
            conn.close()