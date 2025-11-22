from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("Работники", callback_data='employees'),
        InlineKeyboardButton("Группы", callback_data='groups')
    )
    markup.row(InlineKeyboardButton("Задачи", callback_data='tasks'))
    return markup

def tasks_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("Создать задачу", callback_data='create_task'),
        InlineKeyboardButton("Мои задачи", callback_data='my_tasks')
    )
    markup.row(
        InlineKeyboardButton("Групповые задачи", callback_data='group_tasks'),
        InlineKeyboardButton("Завершить задачу", callback_data='complete_task')
    )
    return markup

def group_management_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("➕ Добавить группу", callback_data='create_group'),
        InlineKeyboardButton("➖ Удалить группу", callback_data='delete_group')
    )
    markup.row(
        InlineKeyboardButton("👥 Добавить участника", callback_data='add_member'),
        InlineKeyboardButton("🚪 Удалить участника", callback_data='remove_member')  # Оставляем как было
    )
    markup.row(
        InlineKeyboardButton("📋 Список групп", callback_data='list_groups'),
        InlineKeyboardButton("🔙 Назад", callback_data='admin_menu')
    )
    return markup

def task_actions_keyboard(task_id, is_admin=False):
    markup = InlineKeyboardMarkup()
    if is_admin:
        markup.add(InlineKeyboardButton("Завершить", callback_data=f'complete_task_{task_id}'))
    return markup

def admin_tasks_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("Создать задачу", callback_data='create_task'),
        InlineKeyboardButton("Все задачи", callback_data='all_tasks_admin')
    )
    markup.row(InlineKeyboardButton("🔙 Назад", callback_data='admin_menu'))
    return markup