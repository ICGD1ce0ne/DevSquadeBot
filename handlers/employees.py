from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.users import add_employee_to_db, get_employees, remove_employee_from_db
from database.db import create_connection
from config.config import ADMIN_ID

def register_employee_handlers(bot):
    @bot.message_handler(commands=['employees'])
    def employees_menu(message):
        if message.from_user.id != ADMIN_ID:
            bot.reply_to(message, "⛔ У вас нет прав доступа!")
            return

        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("Добавить работника", callback_data='add_employee'),
            InlineKeyboardButton("Удалить работника", callback_data='remove_employee')
        )
        markup.row(InlineKeyboardButton("Список работников", callback_data='list_employees'))

        bot.send_message(message.chat.id, "Меню работников:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data == 'list_employees')
    def list_employees(call):
        conn = create_connection()
        employees = get_employees(conn)
        conn.close()

        if not employees:
            bot.edit_message_text("Нет работников в базе.", call.message.chat.id, call.message.message_id)
            return

        response = "📋 Список работников:\n\n"
        categories = {}

        for emp in employees:
            if emp[3] not in categories:
                categories[emp[3]] = []
            categories[emp[3]].append(f"{emp[2]} (@{emp[1]})")

        for category, emps in categories.items():
            response += f"=== {category} ===\n" + "\n".join(emps) + "\n\n"

        bot.edit_message_text(response, call.message.chat.id, call.message.message_id)

    @bot.callback_query_handler(func=lambda call: call.data == 'add_employee')
    def add_employee_prompt(call):
        bot.send_message(call.message.chat.id, "Введите данные работника в формате:\n/user_add [user_id] [username] [full_name] [category]")

    @bot.message_handler(commands=['user_add'])
    def add_employee(message):
        if message.from_user.id != ADMIN_ID:
            bot.reply_to(message, "⛔ У вас нет прав доступа!")
            return

        try:
            _, user_id, username, full_name, category = message.text.split(maxsplit=4)
            conn = create_connection()
            add_employee_to_db(conn, int(user_id), username, full_name, category)
            conn.close()
            bot.reply_to(message, f"✅ Работник {full_name} добавлен!")
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка: {e}\nИспользуйте формат: /user_add [user_id] [username] [full_name] [category]")

    @bot.callback_query_handler(func=lambda call: call.data == 'remove_employee')
    def remove_employee_prompt(call):
        conn = create_connection()
        employees = get_employees(conn)
        conn.close()

        markup = InlineKeyboardMarkup()
        for emp in employees:
            markup.add(InlineKeyboardButton(emp[2], callback_data=f'remove_emp_{emp[0]}'))

        bot.edit_message_text("Выберите работника для удаления:", call.message.chat.id, call.message.message_id,
                              reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('remove_emp_'))
    def remove_employee_handler(call):
        user_id = call.data.split('_')[2]
        conn = create_connection()
        remove_employee_from_db(conn, int(user_id))
        conn.close()
        bot.answer_callback_query(call.id, "✅ Работник удален!")