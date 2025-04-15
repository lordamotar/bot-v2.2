from aiogram import types, Bot
from database import Database
from keyboards import (
    get_main_keyboard, 
    get_admin_keyboard,
    get_pending_chats_keyboard,
    get_active_chats_keyboard,
    get_managers_list_keyboard,
    get_extended_chat_keyboard
)
import logging
from utils.analytics import AnalyticsReporter
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

async def handle_admin_panel(message: types.Message, db: Database):
    """Обработчик для открытия панели администратора"""
    user_id = message.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if not db.is_admin(user_id):
        await message.answer(
            "У вас нет прав доступа к панели администратора",
            reply_markup=get_main_keyboard()
        )
        return
    
    await message.answer(
        "Панель администратора. Выберите действие:",
        reply_markup=get_admin_keyboard()
    )

async def handle_admin_stats(message: types.Message, db: Database):
    """Обработчик для отображения статистики"""
    user_id = message.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if not db.is_admin(user_id):
        return
    
    stats = db.get_dashboard_stats()
    
    await message.answer(
        f"📊 *Статистика системы:*\n\n"
        f"👨‍💼 Менеджеры: {stats['total_managers']}\n"
        f"✅ Доступно менеджеров: {stats['available_managers']}\n"
        f"⏳ Ожидающих чатов: {stats['pending_chats']}\n"
        f"💬 Активных чатов: {stats['active_chats']}\n",
        parse_mode="Markdown",
        reply_markup=get_admin_keyboard()
    )

async def handle_admin_pending_chats(message: types.Message, db: Database):
    """Обработчик для отображения ожидающих чатов"""
    user_id = message.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if not db.is_admin(user_id):
        return
    
    pending_chats = db.get_pending_chats()
    
    if not pending_chats:
        await message.answer(
            "В настоящее время нет ожидающих чатов",
            reply_markup=get_admin_keyboard()
        )
        return
    
    await message.answer(
        f"Найдено {len(pending_chats)} ожидающих чатов. Выберите чат для принятия:",
        reply_markup=get_pending_chats_keyboard(pending_chats)
    )

async def handle_admin_active_chats(message: types.Message, db: Database):
    """Обработчик для отображения активных чатов"""
    user_id = message.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if not db.is_admin(user_id):
        return
    
    active_chats = db.get_all_active_chats()
    
    if not active_chats:
        await message.answer(
            "В настоящее время нет активных чатов",
            reply_markup=get_admin_keyboard()
        )
        return
    
    formatted_chats = []
    
    for chat in active_chats:
        client_id, username, client_name, client_phone, manager_id = chat
        manager_name = db.get_manager_name(manager_id) or f"ID: {manager_id}"
        
        formatted_chats.append((
            client_id, 
            username, 
            f"{client_name or username} (Менеджер: {manager_name})", 
            client_phone
        ))
    
    await message.answer(
        f"Найдено {len(active_chats)} активных чатов:",
        reply_markup=get_active_chats_keyboard(formatted_chats)
    )

async def handle_admin_managers(message: types.Message, db: Database):
    """Обработчик для отображения списка менеджеров"""
    user_id = message.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if not db.is_admin(user_id):
        return
    
    managers = db.get_all_managers()
    
    if not managers:
        await message.answer(
            "В системе не найдено менеджеров",
            reply_markup=get_admin_keyboard()
        )
        return
    
    # Создаем клавиатуру со статистикой
    keyboard = []
    
    for manager in managers:
        manager_id, name, is_admin, is_available, active_chats = manager
        manager_name = name or f"ID: {manager_id}"
        status = "🟢 " if is_available else "🔴 "
        admin_badge = "👑 " if is_admin else ""
        
        # Добавляем кнопку управления менеджером
        keyboard.append([types.KeyboardButton(text=f"{admin_badge}{status}{manager_name} ({manager_id})")])
        
        # Добавляем кнопку статистики для этого менеджера
        keyboard.append([types.KeyboardButton(text=f"Статистика: {manager_name} ({manager_id})")])
    
    # Добавляем кнопку возврата
    keyboard.append([types.KeyboardButton(text="Панель администратора")])
    
    await message.answer(
        f"Найдено {len(managers)} менеджеров:",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True
        )
    )

async def handle_admin_take_chat(message: types.Message, bot: Bot, db: Database):
    """Обработчик для принятия чата администратором"""
    user_id = message.from_user.id
    admin_name = message.from_user.first_name or "Администратор"
    
    # Проверяем, является ли пользователь администратором
    if not db.is_admin(user_id):
        return
    
    # Извлекаем имя клиента из текста кнопки
    text = message.text
    if not text.startswith("Взять чат с "):
        await message.answer(
            "Неверный формат команды",
            reply_markup=get_admin_keyboard()
        )
        return
    
    client_info = text.replace("Взять чат с ", "")
    
    # Ищем клиента по имени и телефону
    pending_chats = db.get_pending_chats()
    target_client_id = None
    
    for chat in pending_chats:
        client_id, username, client_name, client_phone, _ = chat
        display_name = client_name if client_name else username
        display_text = f"{display_name}"
        if client_phone:
            display_text += f" ({client_phone})"
        
        if display_text == client_info:
            target_client_id = client_id
            break
    
    if not target_client_id:
        await message.answer(
            "Клиент не найден или чат уже был принят другим менеджером",
            reply_markup=get_admin_keyboard()
        )
        return
    
    # Принимаем чат
    if db.activate_chat(target_client_id, user_id):
        # Увеличиваем счетчик активных чатов администратора
        db.increment_manager_active_chats(user_id)
        
        # Обновляем активность администратора
        db.update_manager_activity(user_id)
        
        # Уведомляем клиента о подключении администратора
        await bot.send_message(
            target_client_id,
            "Администратор подключился к чату. Вы можете задать ваш вопрос."
        )
        
        # Отправляем автоматическое приветствие от имени администратора
        greeting_message = f"Здравствуйте! Меня зовут {admin_name}, я администратор поддержки. Чем могу вам помочь?"
        await bot.send_message(
            target_client_id,
            greeting_message
        )
        
        # Сохраняем приветственное сообщение в истории
        db.save_message(target_client_id, user_id, greeting_message, 'text')
        
        # Уведомляем администратора
        await message.answer(
            "Вы подключились к чату с клиентом.",
            reply_markup=get_extended_chat_keyboard()
        )
    else:
        await message.answer(
            "Не удалось подключиться к чату",
            reply_markup=get_admin_keyboard()
        )

async def handle_admin_manager_stats(message: types.Message, db: Database, config):
    """Обработчик для отображения детальной статистики по менеджеру"""
    user_id = message.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if not db.is_admin(user_id):
        return
    
    # Извлекаем ID менеджера из текста кнопки
    text = message.text
    if not text.startswith("Статистика: "):
        await message.answer(
            "Неверный формат команды",
            reply_markup=get_admin_keyboard()
        )
        return
    
    manager_info = text.replace("Статистика: ", "")
    manager_id = int(manager_info.split("(")[1].split(")")[0])
    
    # Получаем базовую статистику менеджера из БД
    manager_stats = db.get_manager_stats(manager_id)
    if not manager_stats:
        await message.answer(
            "Не удалось получить статистику для этого менеджера",
            reply_markup=get_admin_keyboard()
        )
        return
    
    active_chats, total_chats, rating = manager_stats
    manager_name = db.get_manager_name(manager_id) or f"Менеджер {manager_id}"
    
    # Получаем расширенную статистику из аналитики
    # За последние 7 дней
    week_report = AnalyticsReporter.get_manager_performance_report(
        config.db.database, manager_id=manager_id, days=7
    )
    
    # За последние 30 дней
    month_report = AnalyticsReporter.get_manager_performance_report(
        config.db.database, manager_id=manager_id, days=30
    )
    
    # Получаем отчет о времени отклика
    response_report = AnalyticsReporter.get_response_time_report(days=30)
    response_stats = None
    
    # Ищем менеджера в отчете о времени отклика
    for manager_report in response_report:
        if str(manager_report['manager_id']) == str(manager_id):
            response_stats = manager_report
            break
    
    # Формируем сообщение
    stats_text = f"📊 *Статистика менеджера: {manager_name}*\n\n"
    
    # Текущие показатели
    stats_text += "*Текущие показатели:*\n"
    stats_text += f"• Активных чатов: {active_chats}\n"
    stats_text += f"• Всего чатов: {total_chats}\n"
    stats_text += f"• Рейтинг: {rating:.1f}/5.0\n\n"
    
    # Статистика за неделю
    if week_report:
        wr = week_report[0]
        stats_text += "*Статистика за 7 дней:*\n"
        stats_text += f"• Обработано чатов: {wr['total_chats']}\n"
        stats_text += f"• Средний рейтинг: {wr['avg_rating']}/5.0 ({wr['rating_count']} оценок)\n"
        stats_text += f"• Положительных оценок (4-5): {wr['positive_ratings']}\n"
        stats_text += f"• Отрицательных оценок (1-2): {wr['negative_ratings']}\n\n"
    
    # Статистика за месяц
    if month_report:
        mr = month_report[0]
        stats_text += "*Статистика за 30 дней:*\n"
        stats_text += f"• Обработано чатов: {mr['total_chats']}\n"
        stats_text += f"• Средний рейтинг: {mr['avg_rating']}/5.0 ({mr['rating_count']} оценок)\n"
        stats_text += f"• Положительных оценок (4-5): {mr['positive_ratings']}\n"
        stats_text += f"• Отрицательных оценок (1-2): {mr['negative_ratings']}\n\n"
    
    # Статистика времени отклика
    if response_stats:
        stats_text += "*Время отклика:*\n"
        stats_text += f"• Среднее время: {response_stats['avg_response_time']} сек\n"
        stats_text += f"• Минимальное время: {response_stats['min_response_time']} сек\n"
        stats_text += f"• Максимальное время: {response_stats['max_response_time']} сек\n"
        stats_text += f"• Количество ответов: {response_stats['response_count']}\n\n"
    
    # Добавляем кнопку "Полный отчет" для более детальной статистики
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text=f"Отчет: {manager_name} ({manager_id})")],
            [types.KeyboardButton(text="Панель администратора")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        stats_text,
        parse_mode="Markdown",
        reply_markup=keyboard
    ) 