from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.db import create_connection
from config.config import ADMIN_ID, REPORT_CHAT_ID
from datetime import datetime
from database.groups import get_groups

from database.tasks import (
    create_task_in_db,
    get_user_tasks,
    get_all_tasks,
    get_tasks_by_groups,
    complete_task_in_db
)


def register_task_handlers(bot):
    @bot.callback_query_handler(func=lambda call: call.data == 'create_task')
    def create_task_prompt(call):
        conn = create_connection()
        groups = get_groups(conn)
        conn.close()

        markup = InlineKeyboardMarkup()
        for group in groups:
            markup.add(InlineKeyboardButton(group[1], callback_data=f'create_for_group_{group[0]}'))

        bot.edit_message_text("Выберите группу для задачи:", call.message.chat.id, call.message.message_id,
                              reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('create_for_group_'))
    def create_task_for_group(call):
        group_id = call.data.split('_')[3]
        bot.register_next_step_handler_by_chat_id(
            call.message.chat.id,
            lambda m: process_task_creation(m, group_id)
        )
        bot.edit_message_text(
            "Введите данные задачи в формате:\nНазвание|Описание|Дедлайн(ГГГГ-ММ-ДД)\nПример: Фикс бага|Исправить авторизацию|2024-12-31",
            call.message.chat.id,
            call.message.message_id
        )

    def process_task_creation(message, group_id):
        try:
            title, description, deadline = message.text.split('|')
            conn = create_connection()
            create_task_in_db(conn, title.strip(), description.strip(), int(group_id), None, message.from_user.id,
                              deadline.strip())
            conn.close()
            bot.send_message(message.chat.id, f"✅ Задача '{title}' создана!")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Ошибка: {e}\nИспользуйте правильный формат!")

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith('complete_task_') and call.data.split('_')[2].isdigit())
    def complete_task(call):
        task_id = call.data.split('_')[2]
        conn = create_connection()
        complete_task_in_db(conn, int(task_id))
        conn.close()
        bot.answer_callback_query(call.id, "✅ Задача отмечена выполненной!")

    @bot.message_handler(commands=['tasks'])
    def show_all_group_tasks(message):
        conn = create_connection()

        # Получаем все группы с задачами
        cur = conn.cursor()
        cur.execute("""
                SELECT g.group_id, g.group_name, t.task_id, t.title, t.description, t.deadline 
                FROM groups g
                LEFT JOIN tasks t ON g.group_id = t.group_id AND t.status = 'active'
                ORDER BY g.group_name, t.task_id
            """)

        tasks_by_group = {}
        for row in cur.fetchall():
            group_id, group_name, task_id, title, description, deadline = row
            if group_name not in tasks_by_group:
                tasks_by_group[group_name] = []
            if task_id:  # Если есть задачи
                tasks_by_group[group_name].append({
                    'title': title,
                    'description': description,
                    'deadline': deadline
                })

        conn.close()

        # Формируем ответ
        response = "📌 Активные задачи по командам:\n\n"
        for group_name, tasks in tasks_by_group.items():
            response += f"Команда - {group_name}\n"
            if tasks:
                for i, task in enumerate(tasks, 1):
                    response += f"{i}) {task['title']}\n"
                    response += f"   Описание: {task['description']}\n"
                    response += f"   Дедлайн: {task['deadline']}\n\n"
            else:
                response += "   Нет активных задач\n\n"

        bot.send_message(message.chat.id, response)

    @bot.message_handler(commands=['tasks'])
    def show_tasks_menu(message):
        """Показать меню задач"""
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("Мои задачи", callback_data='my_tasks'),
            InlineKeyboardButton("Все задачи", callback_data='all_tasks')
        )
        if message.from_user.id == ADMIN_ID:
            markup.row(InlineKeyboardButton("Создать задачу", callback_data='create_task'))
        bot.send_message(message.chat.id, "Меню задач:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data == 'all_tasks')
    def show_all_tasks(call):
        """Показать все задачи с кнопками управления для админа"""
        conn = create_connection()
        tasks = get_all_tasks(conn)
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

        # Добавляем кнопки управления для админа
        if call.from_user.id == ADMIN_ID:
            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton("Завершить задачу", callback_data='complete_task_prompt'),
                InlineKeyboardButton("Удалить задачу", callback_data='delete_task_prompt')
            )
            markup.row(InlineKeyboardButton("🔙 Назад", callback_data='admin_tasks'))

            bot.edit_message_text(response, call.message.chat.id, call.message.message_id, reply_markup=markup)
        else:
            bot.edit_message_text(response, call.message.chat.id, call.message.message_id)

    @bot.callback_query_handler(func=lambda call: call.data == 'complete_task_prompt')
    def complete_task_prompt(call):
        """Запрос ID задачи для завершения"""
        bot.send_message(call.message.chat.id, "Введите ID задачи для завершения:")
        bot.register_next_step_handler(call.message, process_task_completion)

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
            show_all_tasks(message)  # Обновляем список задач
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка: {e}\nВведите корректный ID задачи")

    @bot.callback_query_handler(func=lambda call: call.data == 'delete_task_prompt')
    def delete_task_prompt(call):
        """Запрос ID задачи для удаления"""
        bot.send_message(call.message.chat.id, "Введите ID задачи для удаления:")
        bot.register_next_step_handler(call.message, process_task_deletion)

    def process_task_deletion(message):
        """Обработка удаления задачи"""
        if message.from_user.id != ADMIN_ID:
            return bot.reply_to(message, "⛔ Только администратор может выполнять это действие!")

        try:
            task_id = int(message.text)
            conn = create_connection()
            # Добавьте функцию delete_task_in_db в database/tasks.py
            delete_task_in_db(conn, task_id)
            conn.close()
            bot.reply_to(message, f"✅ Задача {task_id} удалена!")
            show_all_tasks(message)  # Обновляем список задач
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка: {e}\nВведите корректный ID задачи")

    @bot.callback_query_handler(func=lambda call: call.data == 'my_tasks')
    def show_my_tasks(call):
        """Показать задачи текущего пользователя"""
        conn = create_connection()
        tasks = get_user_tasks(conn, call.from_user.id)
        conn.close()

        if not tasks:
            bot.edit_message_text("У вас нет задач.", call.message.chat.id, call.message.message_id)
            return

        response = "📌 Ваши задачи:\n\n"
        for task in tasks:
            status = "✅" if task[8] == 'completed' else "🟡"
            response += f"{status} {task[1]}\n"
            response += f"Описание: {task[2]}\n"
            response += f"Дедлайн: {task[7]}\n\n"

        # Добавляем кнопку завершения только для админа
        markup = None
        if call.from_user.id == ADMIN_ID:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("Завершить выбранную", callback_data='complete_task_prompt'))

        bot.edit_message_text(response, call.message.chat.id, call.message.message_id, reply_markup=markup)


    @bot.callback_query_handler(func=lambda call: call.data.startswith('complete_task_'))
    def complete_task_handler(call):
        """Обработчик завершения задачи (только для админа)"""
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "⛔ Только администратор может отмечать задачи как выполненные!",
                                      show_alert=True)
            return

        task_id = call.data.split('_')[2]
        conn = create_connection()

        # Помечаем задачу как выполненную
        complete_task_in_db(conn, int(task_id))

        # Получаем обновленный список задач
        tasks = get_user_tasks(conn, call.from_user.id)
        conn.close()

        if not tasks:
            bot.edit_message_text("Нет активных задач.",
                                  call.message.chat.id,
                                  call.message.message_id)
            return

        response = "📌 Активные задачи:\n\n"
        for task in tasks:
            status = "✅" if task[8] == 'completed' else "🟡"
            response += f"{status} {task[1]}\n"
            response += f"Описание: {task[2]}\n"
            response += f"Дедлайн: {task[7]}\n"

            # Добавляем кнопку только для активных задач и только для админа
            if task[8] == 'active' and call.from_user.id == ADMIN_ID:
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton("Завершить", callback_data=f'complete_task_{task[0]}'))
                bot.edit_message_text(response,
                                      call.message.chat.id,
                                      call.message.message_id,
                                      reply_markup=markup)
            else:
                bot.edit_message_text(response,
                                      call.message.chat.id,
                                      call.message.message_id)

        bot.answer_callback_query(call.id, "✅ Задача отмечена как выполненная!")
