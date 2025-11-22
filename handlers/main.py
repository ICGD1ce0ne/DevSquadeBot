from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config.config import ADMIN_ID
from handlers.employees import register_employee_handlers
from handlers.groups import register_group_handlers
from handlers.tasks import register_task_handlers
from keyboards.keyboards import group_management_keyboard
from handlers.reports import register_report_handlers
from keyboards.keyboards import admin_tasks_keyboard
from database.db import create_connection
from database.tasks import get_all_tasks, complete_task_in_db, delete_task_in_db



def register_handlers(bot):
    # Регистрируем все обработчики
    register_report_handlers(bot)
    register_employee_handlers(bot)
    register_group_handlers(bot)
    register_task_handlers(bot)

    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        if message.from_user.id == ADMIN_ID:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔐 Админ-панель", callback_data='admin_menu'))
            bot.reply_to(message, "Добро пожаловать в менеджер задач!", reply_markup=markup)
        else:
            bot.reply_to(message,
                         "Добро пожаловать! Доступные команды:\n\n"
                         "/start или /help - Начальное приветствие и краткая информация о боте\n"
                         "/tasks - Показать меню задач (доступные задачи и действия)\n\n"
                         "Команды для работы с задачами:\n"
                         "/tasks - Просмотр своих задач и задач групп\n\n"
                         "Команды для работы с группами:\n"
                         "/list_teams - Просмотр списка всех групп с их участниками"
                         )

    @bot.message_handler(commands=['admin'])
    def admin_menu_command(message):
        show_admin_menu(bot, message.chat.id, message.message_id)

    @bot.callback_query_handler(func=lambda call: call.data == 'admin_menu')
    def admin_menu_callback(call):
        show_admin_menu(bot, call.message.chat.id, call.message.message_id)

    @bot.callback_query_handler(func=lambda call: call.data == 'admin_employees')
    def admin_employees(call):
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "⛔ У вас нет прав доступа!", show_alert=True)
            return

        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("Добавить работника", callback_data='add_employee'),
            InlineKeyboardButton("Удалить работника", callback_data='remove_employee')
        )
        markup.row(InlineKeyboardButton("Список работников", callback_data='list_employees'))
        markup.row(InlineKeyboardButton("🔙 Назад", callback_data='admin_menu'))

        bot.edit_message_text("Меню работников:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data == 'admin_groups')
    def admin_groups(call):
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "⛔ У вас нет прав доступа!", show_alert=True)
            return

        bot.edit_message_text(
            "Меню групп:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=group_management_keyboard()
        )

    # Обновите обработчик admin_tasks
    @bot.callback_query_handler(func=lambda call: call.data == 'admin_tasks')
    def admin_tasks(call):
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "⛔ У вас нет прав доступа!", show_alert=True)
            return

        bot.edit_message_text(
            "Меню управления задачами:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=admin_tasks_keyboard()
        )

    @bot.callback_query_handler(func=lambda call: call.data == 'all_tasks_admin')
    def show_all_tasks_admin(call):
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "⛔ Только администратор может просматривать этот список!",
                                      show_alert=True)
            return

        conn = create_connection()
        tasks = get_all_tasks(conn)  # Убедитесь, что эта функция есть в database/tasks.py
        conn.close()

        if not tasks:
            bot.edit_message_text("Нет задач в базе.", call.message.chat.id, call.message.message_id)
            return

        response = "📋 Все задачи (управление):\n\n"
        for task in tasks:
            status = "✅" if task['status'] == 'completed' else "🟡"
            response += f"{status} ID:{task['task_id']} - {task['title']}\n"
            response += f"Группа: {task.get('group_name', 'Без группы')}\n"
            response += f"Дедлайн: {task['deadline']}\n\n"

        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("Завершить задачу", callback_data='admin_complete_task_prompt'),
            InlineKeyboardButton("Удалить задачу", callback_data='admin_delete_task_prompt')
        )
        markup.row(InlineKeyboardButton("🔙 Назад", callback_data='admin_tasks'))

        bot.edit_message_text(response, call.message.chat.id, call.message.message_id, reply_markup=markup)

    # Добавьте обработчики для завершения и удаления задач
    @bot.callback_query_handler(func=lambda call: call.data == 'admin_complete_task_prompt')
    def admin_complete_task_prompt(call):
        """Запрос ID задачи для завершения (админ)"""
        bot.send_message(call.message.chat.id, "Введите ID задачи для завершения:")
        bot.register_next_step_handler(call.message, process_task_completion)

    @bot.callback_query_handler(func=lambda call: call.data == 'admin_delete_task_prompt')
    def admin_delete_task_prompt(call):
        """Запрос ID задачи для удаления (админ)"""
        bot.send_message(call.message.chat.id, "Введите ID задачи для удаления:")
        bot.register_next_step_handler(call.message, process_task_deletion)

    def process_task_completion(message):
        """Обработка завершения задачи"""
        if message.from_user.id != ADMIN_ID:
            return bot.reply_to(message, "⛔ Только администратор может выполнять это действие!")

        try:
            task_id = int(message.text)
            conn = create_connection()
            complete_task_in_db(conn, task_id)
            conn.close()
            bot.reply_to(message, f"✅ Задача {task_id} отмечена как выполненная!")
            # Обновляем список задач
            show_all_tasks_admin(message)
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка: {e}\nВведите корректный ID задачи")

    def process_task_deletion(message):
        """Обработка удаления задачи"""
        if message.from_user.id != ADMIN_ID:
            return bot.reply_to(message, "⛔ Только администратор может выполнять это действие!")

        try:
            task_id = int(message.text)
            conn = create_connection()
            deleted_count = delete_task_in_db(conn, task_id)
            conn.close()

            if deleted_count > 0:
                bot.reply_to(message, f"✅ Задача {task_id} удалена!")
                # Обновляем список задач
                show_all_tasks_admin(message)
            else:
                bot.reply_to(message, f"❌ Задача с ID {task_id} не найдена")
        except ValueError:
            bot.reply_to(message, "❌ Ошибка: Введите числовой ID задачи")
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка: {e}\nВведите корректный ID задачи")

def show_admin_menu(bot, chat_id, message_id=None):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("📋 Работники", callback_data='admin_employees'),
        InlineKeyboardButton("👥 Группы", callback_data='admin_groups')
    )
    markup.row(
        InlineKeyboardButton("📌 Задачи", callback_data='admin_tasks'),
        InlineKeyboardButton("📊 Отчеты", callback_data='admin_reports')
    )

    if message_id:
        bot.edit_message_text("🔐 Админ-панель:", chat_id, message_id, reply_markup=markup)
    else:
        bot.send_message(chat_id, "🔐 Админ-панель:", reply_markup=markup)

