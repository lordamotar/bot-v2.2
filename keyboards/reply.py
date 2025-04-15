from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Каталог")],
            [KeyboardButton(text="Контакты")],
            [KeyboardButton(text="Связаться с менеджером")]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_cities_keyboard(cities: list[str]) -> ReplyKeyboardMarkup:
    """Клавиатура со списком городов в два столбца"""
    # Создаем список кнопок по два города в строке
    keyboard = []
    for i in range(0, len(cities), 2):
        row = []
        row.append(KeyboardButton(text=cities[i]))
        if i + 1 < len(cities):  # Проверяем, есть ли второй город для строки
            row.append(KeyboardButton(text=cities[i + 1]))
        keyboard.append(row)

    # Добавляем кнопку "Назад" отдельной строкой
    keyboard.append([KeyboardButton(text="Назад")])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_chat_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="История сообщений")],
            [KeyboardButton(text="Завершить чат")]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_manager_keyboard(username: str, client_name: str = None, client_phone: str = None) -> ReplyKeyboardMarkup:
    # Формируем текст кнопки с информацией о клиенте
    button_text = f"Принять чат с {username}"
    if client_name and client_phone:
        button_text = f"Принять чат с {username} ({client_name}, {client_phone})"
    elif client_name:
        button_text = f"Принять чат с {username} ({client_name})"

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=button_text)]],
        resize_keyboard=True
    )
    return keyboard


def get_streets_keyboard(streets: list[str]) -> ReplyKeyboardMarkup:
    """Клавиатура со списком улиц в два столбца"""
    # Создаем список кнопок по две улицы в строке
    keyboard = []
    for i in range(0, len(streets), 2):
        row = []
        row.append(KeyboardButton(text=streets[i]))
        if i + 1 < len(streets):  # Проверяем, есть ли вторая улица для строки
            row.append(KeyboardButton(text=streets[i + 1]))
        keyboard.append(row)

    # Добавляем кнопку "Назад к городам" отдельной строкой
    keyboard.append([KeyboardButton(text="Назад к городам")])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_rating_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для оценки чата"""
    keyboard = [
        [
            KeyboardButton(text="Оценка: 1"),
            KeyboardButton(text="Оценка: 2"),
            KeyboardButton(text="Оценка: 3"),
            KeyboardButton(text="Оценка: 4"),
            KeyboardButton(text="Оценка: 5"),
        ],
        [KeyboardButton(text="Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_manager_status_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для управления статусом менеджера"""
    keyboard = [
        [
            KeyboardButton(text="Доступен для чатов"),
            KeyboardButton(text="Недоступен для чатов")
        ],
        [KeyboardButton(text="Активные чаты")],
        [KeyboardButton(text="Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_share_contact_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для запроса контактных данных"""
    keyboard = [
        [KeyboardButton(text="Поделиться контактом", request_contact=True)],
        [KeyboardButton(text="Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_catalog_categories_keyboard(categories: list[str]) -> ReplyKeyboardMarkup:
    """Клавиатура для категорий каталога"""
    keyboard = []
    for category in categories:
        keyboard.append([KeyboardButton(text=category)])
    
    # Добавляем кнопку "Назад" отдельной строкой
    keyboard.append([KeyboardButton(text="Назад")])
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_catalog_subcategories_keyboard(subcategories: list[str]) -> ReplyKeyboardMarkup:
    """Клавиатура для подкатегорий каталога"""
    keyboard = []
    # Добавляем по две подкатегории в ряд, если возможно
    for i in range(0, len(subcategories), 2):
        row = []
        row.append(KeyboardButton(text=subcategories[i]))
        if i + 1 < len(subcategories):
            row.append(KeyboardButton(text=subcategories[i + 1]))
        keyboard.append(row)
    
    # Добавляем кнопку "Назад к категориям"
    keyboard.append([KeyboardButton(text="Назад к категориям")])
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_catalog_types_keyboard(types: list[str]) -> ReplyKeyboardMarkup:
    """Клавиатура для типов товаров"""
    keyboard = []
    for type_name in types:
        keyboard.append([KeyboardButton(text=type_name)])
    
    # Добавляем кнопку "Назад к подкатегориям"
    keyboard.append([KeyboardButton(text="Назад к подкатегориям")])
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_catalog_sizes_keyboard(sizes: list[str]) -> ReplyKeyboardMarkup:
    """Клавиатура для размеров товаров"""
    keyboard = []
    # Добавляем по три размера в ряд, если возможно
    for i in range(0, len(sizes), 3):
        row = []
        row.append(KeyboardButton(text=sizes[i]))
        if i + 1 < len(sizes):
            row.append(KeyboardButton(text=sizes[i + 1]))
        if i + 2 < len(sizes):
            row.append(KeyboardButton(text=sizes[i + 2]))
        keyboard.append(row)
    
    # Добавляем кнопку "Назад"
    if len(sizes) > 0:
        keyboard.append([KeyboardButton(text="Назад")])
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_admin_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для панели администратора"""
    keyboard = [
        [KeyboardButton(text="Статистика")],
        [KeyboardButton(text="Ожидающие чаты"), KeyboardButton(text="Активные чаты")],
        [KeyboardButton(text="Управление менеджерами")],
        [KeyboardButton(text="Отчеты")],
        [KeyboardButton(text="Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_active_chats_keyboard(chats_list: list) -> ReplyKeyboardMarkup:
    """Клавиатура со списком активных чатов
    
    Args:
        chats_list: Список кортежей (client_id, username, client_name, client_phone)
    """
    keyboard = []
    for chat in chats_list:
        client_id, username, client_name, client_phone = chat
        display_name = client_name if client_name else username
        display_text = f"{display_name}"
        if client_phone:
            display_text += f" ({client_phone})"
        keyboard.append([KeyboardButton(text=f"Чат с {display_text}")])
    
    keyboard.append([KeyboardButton(text="Назад")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_pending_chats_keyboard(chats_list: list) -> ReplyKeyboardMarkup:
    """Клавиатура со списком ожидающих чатов
    
    Args:
        chats_list: Список кортежей (client_id, username, client_name, client_phone, client_nickname)
    """
    keyboard = []
    for chat in chats_list:
        client_id, username, client_name, client_phone, client_nickname = chat
        display_name = client_name if client_name else username
        display_text = f"{display_name}"
        if client_phone:
            display_text += f" ({client_phone})"
        keyboard.append([KeyboardButton(text=f"Взять чат с {display_text}")])
    
    keyboard.append([KeyboardButton(text="Назад")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_managers_list_keyboard(managers_list: list) -> ReplyKeyboardMarkup:
    """Клавиатура со списком менеджеров
    
    Args:
        managers_list: Список кортежей (id, name, is_admin, is_available, active_chats)
    """
    keyboard = []
    for manager in managers_list:
        manager_id, name, is_admin, is_available, active_chats = manager
        display_name = name if name else f"ID: {manager_id}"
        status = "👑 " if is_admin else ""
        status += "✅ " if is_available else "❌ "
        status += f"({active_chats} чатов)"
        keyboard.append([KeyboardButton(text=f"{status} {display_name}")])
    
    keyboard.append([KeyboardButton(text="Назад")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_chat_transfer_keyboard(managers_list: list) -> ReplyKeyboardMarkup:
    """Клавиатура для передачи чата другому менеджеру
    
    Args:
        managers_list: Список кортежей (id, name, is_admin, is_available, active_chats)
    """
    keyboard = []
    for manager in managers_list:
        manager_id, name, is_admin, is_available, active_chats = manager
        if not is_available:
            continue  # Пропускаем недоступных менеджеров
            
        display_name = name if name else f"ID: {manager_id}"
        status = "👑 " if is_admin else ""
        status += f"({active_chats} чатов)"
        keyboard.append([KeyboardButton(text=f"Передать: {status} {display_name}")])
    
    keyboard.append([KeyboardButton(text="Отмена")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_extended_chat_keyboard() -> ReplyKeyboardMarkup:
    """Расширенная клавиатура для чата с функцией передачи"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="История сообщений")],
            [KeyboardButton(text="Передать другому менеджеру")],
            [KeyboardButton(text="Завершить чат")]
        ],
        resize_keyboard=True
    )
    return keyboard
