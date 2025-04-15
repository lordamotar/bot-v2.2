from aiogram import types, Bot
from database import Database
from keyboards import (
    get_chat_keyboard, 
    get_main_keyboard, 
    get_manager_status_keyboard,
    get_active_chats_keyboard,
    get_chat_transfer_keyboard,
    get_extended_chat_keyboard
)
from utils.logger import ManagerMetrics
from datetime import datetime


async def handle_accept_chat(message: types.Message, bot: Bot, db: Database, managers_list: list):
    """Обработчик для принятия чата менеджером"""
    manager_id = message.from_user.id
    manager_name = message.from_user.first_name or "Менеджер"
    
    # Проверяем, является ли пользователь менеджером
    if manager_id not in managers_list:
        return

    # Извлекаем username клиента из текста кнопки
    # Формат "Принять чат с username (имя, телефон)" или "Принять чат с username"
    button_text = message.text
    username_part = button_text.replace("Принять чат с ", "")
    
    # Проверяем, содержит ли кнопка дополнительную информацию
    if "(" in username_part:
        username = username_part.split("(")[0].strip()
    else:
        username = username_part.strip()

    # Находим чат в БД и активируем его
    client_id = db.get_client_id_by_username(username)
    if not client_id:
        await message.answer("Не удалось найти чат с указанным пользователем")
        return
        
    # Проверяем, не занят ли уже чат другим менеджером
    if db.is_client_in_active_chat(client_id):
        active_chat = db.get_active_chat_by_client_id(client_id)
        if active_chat and active_chat[1] and active_chat[1] != manager_id:
            await message.answer(
                f"Этот чат уже принят другим менеджером.",
                reply_markup=get_main_keyboard()
            )
            return
    
    # Получаем имя клиента из контактной информации
    client_contact = db.get_client_contact_info(client_id)
    client_name = client_contact[0] if client_contact and client_contact[0] else username
    
    # Активируем чат и обновляем счетчики для менеджера
    if db.activate_chat(client_id, manager_id):
        # Увеличиваем счетчик активных чатов менеджера
        db.increment_manager_active_chats(manager_id)
        
        # Обновляем активность менеджера
        db.update_manager_activity(manager_id)
        
        # Уведомляем клиента о подключении менеджера
        await bot.send_message(
            client_id,
            "Менеджер подключился к чату. Вы можете задать ваш вопрос.",
            reply_markup=get_chat_keyboard()
        )
        
        # Отправляем автоматическое приветствие от имени менеджера
        greeting_message = f"Здравствуйте, {client_name}! Меня зовут {manager_name}. Чем могу вам помочь?"
        await bot.send_message(
            client_id,
            greeting_message,
            reply_markup=get_chat_keyboard()
        )
        
        # Сохраняем приветственное сообщение в истории
        db.save_message(client_id, manager_id, greeting_message, 'text')
        
        # Уведомляем менеджера
        await message.answer(
            f"Вы подключились к чату с клиентом {username}",
            reply_markup=get_extended_chat_keyboard()
        )

        # Логируем принятие чата для аналитики
        try:
            # Получаем сообщения из чата для определения времени создания
            chat_history = db.get_chat_history(client_id, limit=1)
            if chat_history:
                # Берем время первого сообщения как время создания чата
                chat_start_time = datetime.fromisoformat(chat_history[-1][5].replace(' ', 'T'))
                response_time = (datetime.now() - chat_start_time).total_seconds()
                
                # Логируем событие с временем отклика
                ManagerMetrics.log_chat_accepted(
                    client_id=client_id,
                    manager_id=manager_id,
                    response_time=response_time
                )
            else:
                # Если история пуста, просто логируем принятие чата без времени отклика
                ManagerMetrics.log_chat_accepted(
                    client_id=client_id,
                    manager_id=manager_id
                )
        except Exception as e:
            # Если возникает ошибка при логировании, игнорируем её,
            # чтобы не прерывать основной процесс
            pass


async def handle_manager_status(message: types.Message, db: Database):
    """Обработчик для управления статусом менеджера"""
    manager_id = message.from_user.id
    
    # Получаем статистику менеджера
    stats = db.get_manager_stats(manager_id)
    if not stats:
        await message.answer("Не удалось получить информацию о вашем статусе")
        return
        
    active_chats, total_chats, rating = stats
    
    await message.answer(
        f"🔹 Ваш статус:\n"
        f"• Активных чатов: {active_chats}\n"
        f"• Всего чатов: {total_chats}\n"
        f"• Средняя оценка: {rating:.1f}/5.0\n\n"
        f"Выберите действие:",
        reply_markup=get_manager_status_keyboard()
    )


async def handle_set_availability(message: types.Message, db: Database, available: bool):
    """Обработчик для установки доступности менеджера"""
    manager_id = message.from_user.id
    
    if db.set_manager_availability(manager_id, available):
        status = "доступен для новых чатов" if available else "недоступен для новых чатов"
        await message.answer(
            f"Ваш статус изменен. Теперь вы {status}.",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer(
            "Не удалось изменить ваш статус",
            reply_markup=get_main_keyboard()
        )


async def handle_manager_active_chats(message: types.Message, db: Database):
    """Обработчик для отображения активных чатов менеджера"""
    manager_id = message.from_user.id
    
    active_chats = db.get_active_chats_by_manager(manager_id)
    
    if not active_chats:
        await message.answer(
            "У вас нет активных чатов",
            reply_markup=get_manager_status_keyboard()
        )
        return
    
    await message.answer(
        f"У вас {len(active_chats)} активных чатов:",
        reply_markup=get_active_chats_keyboard(active_chats)
    )


async def handle_chat_selection(message: types.Message, db: Database):
    """Обработчик для выбора чата из списка"""
    manager_id = message.from_user.id
    
    # Извлекаем имя клиента из текста кнопки
    text = message.text
    if not text.startswith("Чат с "):
        return
    
    client_info = text.replace("Чат с ", "")
    
    # Ищем клиента по имени и телефону
    active_chats = db.get_active_chats_by_manager(manager_id)
    target_client_id = None
    
    for chat in active_chats:
        client_id, username, client_name, client_phone = chat
        display_name = client_name if client_name else username
        display_text = f"{display_name}"
        if client_phone:
            display_text += f" ({client_phone})"
        
        if display_text == client_info:
            target_client_id = client_id
            break
    
    if not target_client_id:
        await message.answer(
            "Чат не найден или уже завершен",
            reply_markup=get_manager_status_keyboard()
        )
        return
    
    # Показываем клавиатуру чата
    await message.answer(
        f"Вы в чате с клиентом {client_info}",
        reply_markup=get_extended_chat_keyboard()
    )


async def handle_transfer_chat_request(message: types.Message, db: Database):
    """Обработчик для запроса на передачу чата другому менеджеру"""
    manager_id = message.from_user.id
    
    # Проверяем, есть ли у менеджера активный чат
    active_chat = db.get_active_chat(manager_id)
    if not active_chat:
        await message.answer(
            "У вас нет активного чата для передачи",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Получаем список доступных менеджеров
    managers = db.get_all_managers()
    available_managers = [m for m in managers if m[0] != manager_id]
    
    if not available_managers:
        await message.answer(
            "Нет доступных менеджеров для передачи чата",
            reply_markup=get_extended_chat_keyboard()
        )
        return
    
    await message.answer(
        "Выберите менеджера для передачи чата:",
        reply_markup=get_chat_transfer_keyboard(available_managers)
    )


async def handle_transfer_chat(message: types.Message, bot: Bot, db: Database):
    """Обработчик для передачи чата другому менеджеру"""
    manager_id = message.from_user.id
    
    # Проверяем, есть ли у менеджера активный чат
    active_chat = db.get_active_chat(manager_id)
    if not active_chat:
        await message.answer(
            "У вас нет активного чата для передачи",
            reply_markup=get_main_keyboard()
        )
        return
    
    client_id = active_chat[0]
    
    # Извлекаем ID нового менеджера из текста кнопки
    text = message.text
    if not text.startswith("Передать: "):
        return
    
    # Получаем список всех менеджеров
    managers = db.get_all_managers()
    
    # Ищем нового менеджера по тексту кнопки
    new_manager_id = None
    for manager in managers:
        manager_id_from_db, name, is_admin, is_available, active_chats = manager
        if manager_id_from_db == manager_id:
            continue  # Пропускаем текущего менеджера
            
        display_name = name if name else f"ID: {manager_id_from_db}"
        status = "👑 " if is_admin else ""
        status += f"({active_chats} чатов)"
        button_text = f"Передать: {status} {display_name}"
        
        if button_text == text:
            new_manager_id = manager_id_from_db
            break
    
    if not new_manager_id:
        await message.answer(
            "Менеджер не найден",
            reply_markup=get_extended_chat_keyboard()
        )
        return
    
    # Передаем чат новому менеджеру
    if db.transfer_chat(client_id, new_manager_id):
        # Получаем имя клиента
        client_contact = db.get_client_contact_info(client_id)
        client_name = client_contact[0] if client_contact and client_contact[0] else "Клиент"
        
        # Получаем имя нового менеджера
        new_manager_name = db.get_manager_name(new_manager_id) or "Менеджер"
        
        # Уведомляем клиента о смене менеджера
        await bot.send_message(
            client_id,
            f"Ваш чат был передан другому менеджеру: {new_manager_name}"
        )
        
        # Уведомляем нового менеджера
        await bot.send_message(
            new_manager_id,
            f"Вам передан чат с клиентом {client_name}",
            reply_markup=get_extended_chat_keyboard()
        )
        
        # Уведомляем текущего менеджера
        await message.answer(
            f"Чат с клиентом {client_name} успешно передан менеджеру {new_manager_name}",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer(
            "Не удалось передать чат",
            reply_markup=get_extended_chat_keyboard()
        )