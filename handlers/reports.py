from datetime import datetime, timedelta
import time
from database.db import create_connection
from database.tasks import get_completed_tasks, get_active_tasks_count
import threading
from config.config import REPORT_CHAT_ID

def register_report_handlers(bot):
    @bot.callback_query_handler(func=lambda call: call.data == 'admin_reports')
    def show_reports(call):
        conn = create_connection()
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
        tasks = get_completed_tasks(conn, week_ago)
        conn.close()

        response = "📊 Отчет за неделю:\n\n"
        response += f"✅ Выполнено задач: {len(tasks)}\n\n"

        if tasks:
            response += "Последние выполненные задачи:\n"
            for task in tasks[-5:]:  # Показываем последние 5 задач
                response += f"- {task[1]} (выполнено {task[6]})\n"

        bot.edit_message_text(response, call.message.chat.id, call.message.message_id)


def generate_weekly_report():
    conn = create_connection()
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')

    completed_tasks = get_completed_tasks(conn, week_ago)
    active_tasks_count = get_active_tasks_count(conn)
    conn.close()

    report = "📊 Еженедельный отчет по задачам\n\n"
    report += f"✅ Выполнено задач за неделю: {len(completed_tasks)}\n"
    report += f"🟡 Активных задач: {active_tasks_count}\n\n"

    if completed_tasks:
        report += "Последние выполненные задачи:\n"
        for task in completed_tasks[-5:]:
            report += f"- {task[1]} (выполнена {task[6]})\n"

    return report


def start_report_scheduler(bot):
    def run():
        while True:
            try:
                report = generate_weekly_report()
                bot.send_message(REPORT_CHAT_ID, report)
                # 120 секунд = 2 минуты для теста, в продакшене используйте 604800 (1 неделя)
                time.sleep(604800)
            except Exception as e:
                print(f"Ошибка при отправке отчета: {e}")
                time.sleep(60)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()