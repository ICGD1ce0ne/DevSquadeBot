from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.db import create_connection
from config.config import ADMIN_ID
from database.users import get_employees
from database.groups import add_member_to_group

from database.groups import (
    create_group,
    get_groups,
    delete_group,
    add_member_to_group,
    get_groups_with_members,  # Добавляем этот импорт
    remove_member_from_group  # И этот тоже
)

def register_group_handlers(bot):
    @bot.message_handler(commands=['groups'])
    def groups_menu(message):
        if message.from_user.id != ADMIN_ID:
            bot.reply_to(message, "⛔ У вас нет прав доступа!")
            return

        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("Создать группу", callback_data='create_group'),
            InlineKeyboardButton("Удалить группу", callback_data='delete_group')
        )
        markup.row(InlineKeyboardButton("Список групп", callback_data='list_groups'))

        bot.send_message(message.chat.id, "Меню групп:", reply_markup=markup)


    @bot.callback_query_handler(func=lambda call: call.data == 'create_group')
    def create_group_prompt(call):
        bot.send_message(call.message.chat.id, "Введите название новой группы:\n/group_add [название]")

    @bot.message_handler(commands=['group_add'])
    def group_add(message):
        if message.from_user.id != ADMIN_ID:
            bot.reply_to(message, "⛔ У вас нет прав доступа!")
            return

        try:
            group_name = message.text.split(maxsplit=1)[1]
            conn = create_connection()
            create_group(conn, group_name)
            conn.close()
            bot.reply_to(message, f"✅ Группа '{group_name}' создана!")
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка: {e}\nИспользуйте формат: /group_add [название]")

    @bot.callback_query_handler(func=lambda call: call.data == 'delete_group')
    def delete_group_prompt(call):
        conn = create_connection()
        groups = get_groups(conn)
        conn.close()

        if not groups:
            bot.send_message(call.message.chat.id, "Нет групп для удаления.")
            return

        markup = InlineKeyboardMarkup()
        for group in groups:
            markup.add(InlineKeyboardButton(group[1], callback_data=f'del_group_{group[0]}'))

        bot.send_message(call.message.chat.id, "Выберите группу для удаления:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('del_group_'))
    def delete_group_handler(call):
        group_id = int(call.data.split('_')[2])
        conn = create_connection()
        delete_group(conn, group_id)
        conn.close()
        bot.edit_message_text(f"✅ Группа удалена!", call.message.chat.id, call.message.message_id)

    @bot.callback_query_handler(func=lambda call: call.data == 'add_member')
    def add_member_prompt(call):
        conn = create_connection()
        groups = get_groups(conn)
        conn.close()

        markup = InlineKeyboardMarkup()
        for group in groups:
            markup.add(InlineKeyboardButton(group[1], callback_data=f'select_group_{group[0]}'))

        bot.edit_message_text("Выберите группу:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('select_group_'))
    def select_group_for_member(call):
        group_id = call.data.split('_')[2]
        conn = create_connection()
        employees = get_employees(conn)
        conn.close()

        markup = InlineKeyboardMarkup()
        for emp in employees:
            markup.add(InlineKeyboardButton(emp[2], callback_data=f'add_to_group_{group_id}_{emp[0]}'))

        bot.edit_message_text("Выберите работника:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('add_to_group_'))
    def add_member_to_group_handler(call):
        try:
            # Разбираем callback_data в формате "add_to_group_{group_id}_{user_id}"
            parts = call.data.split('_')
            group_id = parts[3]  # Изменено с 2 на 3
            user_id = parts[4]  # Изменено с 3 на 4

            conn = create_connection()
            add_member_to_group(conn, int(user_id), int(group_id))
            conn.close()

            bot.answer_callback_query(call.id, "✅ Работник добавлен в группу!")
        except Exception as e:
            bot.answer_callback_query(call.id, f"❌ Ошибка: {str(e)}", show_alert=True)

    @bot.callback_query_handler(func=lambda call: call.data == 'list_groups')
    def list_groups(call):
        conn = create_connection()
        try:
            groups = get_groups_with_members(conn)

            if not groups:
                bot.edit_message_text("Нет групп в базе.", call.message.chat.id, call.message.message_id)
                return

            response = "📋 Список групп и участников:\n\n"
            for group in groups:
                response += f"🔹 {group['name']} (ID: {group['id']})\n"
                if group['members']:
                    response += "Участники:\n" + "\n".join([f" • {m}" for m in group['members']]) + "\n\n"
                else:
                    response += "Нет участников\n\n"

            bot.edit_message_text(response, call.message.chat.id, call.message.message_id)
        finally:
            conn.close()

    @bot.callback_query_handler(func=lambda call: call.data == 'remove_member')
    def remove_member_prompt(call):
        """Показать список групп с участниками для удаления"""
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "⛔ У вас нет прав доступа!", show_alert=True)
            return

        conn = create_connection()
        try:
            groups = get_groups_with_members(conn)

            if not groups:
                bot.answer_callback_query(call.id, "Нет групп в базе.", show_alert=True)
                return

            markup = InlineKeyboardMarkup()
            for group in groups:
                if group['members']:
                    for member in group['members']:
                        # Извлекаем user_id из строки вида "Имя (ID: 123)"
                        user_id = member.split('ID: ')[1].replace(')', '').strip()
                        btn_text = f"{group['name']} - {member.split('(')[0].strip()}"
                        markup.add(
                            InlineKeyboardButton(
                                btn_text,
                                callback_data=f'remove_member_{group["id"]}_{user_id}'
                            )
                        )

            if not markup.keyboard:  # Если нет участников
                bot.answer_callback_query(call.id, "Нет участников для удаления.", show_alert=True)
                return

            bot.edit_message_text(
                "Выберите участника для удаления:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )
        finally:
            conn.close()

    @bot.callback_query_handler(func=lambda call: call.data.startswith('remove_member_'))
    def remove_member_handler(call):
        """Обработчик удаления участника из группы"""
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "⛔ У вас нет прав доступа!", show_alert=True)
            return

        try:
            # Разбираем callback_data в формате "remove_member_{group_id}_{user_id}"
            parts = call.data.split('_')
            if len(parts) != 4:  # remove_member + group_id + user_id
                raise ValueError("Неверный формат данных")

            group_id = parts[2]
            user_id = parts[3]

            conn = create_connection()
            result = remove_member_from_group(conn, int(user_id), int(group_id))
            conn.close()

            if result > 0:
                bot.answer_callback_query(call.id, "✅ Участник удален из группы!")
                # Обновляем список групп
                list_groups(call)
            else:
                bot.answer_callback_query(call.id, "❌ Участник не найден в группе!", show_alert=True)
        except Exception as e:
            bot.answer_callback_query(call.id, f"❌ Ошибка: {str(e)}", show_alert=True)

    @bot.message_handler(commands=['list_teams'])
    def list_teams_command(message):
        """Показать список всех групп с участниками"""
        conn = create_connection()
        try:
            groups = get_groups_with_members(conn)

            if not groups:
                bot.reply_to(message, "В системе пока нет групп.")
                return

            response = "📋 Список команд и участников:\n\n"
            for group in groups:
                response += f"🔹 {group['name']}\n"
                if group['members']:
                    response += "Участники:\n" + "\n".join([f" • {m}" for m in group['members']]) + "\n\n"
                else:
                    response += "Нет участников\n\n"

            bot.reply_to(message, response)
        finally:
            conn.close()