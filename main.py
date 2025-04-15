import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import load_config
from database import Database
from handlers.client import (
    handle_start, 
    handle_support_request, 
    handle_chat_history, 
    handle_view_media,
    handle_rating,
    handle_rating_comment,
    handle_share_contact,
    process_contact_data
)
from handlers.manager import (
    handle_accept_chat, 
    handle_manager_status, 
    handle_set_availability,
    handle_manager_active_chats,
    handle_chat_selection,
    handle_transfer_chat_request,
    handle_transfer_chat
)
from handlers.admin import (
    handle_admin_panel,
    handle_admin_stats,
    handle_admin_pending_chats,
    handle_admin_active_chats,
    handle_admin_managers,
    handle_admin_take_chat,
    handle_admin_manager_stats
)
from handlers.common import handle_close_chat, handle_message
from handlers.contacts import (
    handle_contacts,
    handle_back,
    handle_city_selection,
    handle_back_to_cities,
    handle_street_selection
)
from handlers.catalog import (
    handle_catalog,
    handle_category_selection,
    handle_subcategory_selection,
    handle_type_selection,
    handle_size_selection,
    handle_back_to_categories,
    handle_back_to_subcategories,
    handle_back_from_sizes,
    user_catalog_selections
)
from utils.logger import (
    logger, 
    PerformanceMonitor, 
    BotMonitoring
)
from utils.analytics import ManagerAnalytics, BotAnalytics

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Загрузка конфигурации
config = load_config()
bot = Bot(token=config.config.token)
dp = Dispatcher()
# Сначала инициализируем базу данных
db = Database(config.db.database)
# Затем добавляем зависимости
dp.workflow_data.update({"db": db, "config": config, "bot": bot})  # Добавляем зависимости

# Инициализация менеджеров
for manager_id in config.config.managers:
    db.add_manager(manager_id)

# Устанавливаем администратора, если есть
if config.config.admin_manager_id:
    db.add_manager(config.config.admin_manager_id, is_admin=True)

# Инициализация аналитики и мониторинга
analytics = ManagerAnalytics(db, bot, config)
bot_monitoring = BotAnalytics(db, bot, config)


# Регистрация хендлеров без декораторов PerformanceMonitor для критичных функций
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await handle_start(message, config, db)


@dp.message(lambda message: message.text == "Контакты")
@PerformanceMonitor.measure("contacts")
async def contacts(message: types.Message):
    await handle_contacts(message, db)


@dp.message(lambda message: message.text == "Каталог")
@PerformanceMonitor.measure("catalog")
async def catalog(message: types.Message):
    await handle_catalog(message, db)


@dp.message(lambda message: message.text in db.get_product_categories() if hasattr(db, 'get_product_categories') else False)
async def category_selection(message: types.Message):
    await handle_category_selection(message, db)


@dp.message(lambda message: message.text == "Назад к категориям")
async def back_to_categories(message: types.Message):
    await handle_back_to_categories(message, db)


@dp.message(lambda message: message.text in (
    db.get_product_subcategories(user_catalog_selections.get(message.from_user.id, {}).get('category', '')) 
    if hasattr(db, 'get_product_subcategories') and message.from_user.id in user_catalog_selections 
    else []
))
async def subcategory_selection(message: types.Message):
    await handle_subcategory_selection(message, db)


@dp.message(lambda message: message.text == "Назад к подкатегориям")
async def back_to_subcategories(message: types.Message):
    await handle_back_to_subcategories(message, db)


@dp.message(lambda message: message.text in (
    db.get_product_types(
        user_catalog_selections.get(message.from_user.id, {}).get('category', ''),
        user_catalog_selections.get(message.from_user.id, {}).get('subcategory', '')
    ) if hasattr(db, 'get_product_types') and message.from_user.id in user_catalog_selections 
    else []
))
async def type_selection(message: types.Message):
    await handle_type_selection(message, db)


@dp.message(lambda message: message.text in (
    db.get_product_sizes(
        user_catalog_selections.get(message.from_user.id, {}).get('category', ''),
        user_catalog_selections.get(message.from_user.id, {}).get('subcategory', ''),
        user_catalog_selections.get(message.from_user.id, {}).get('type', None)
    ) if hasattr(db, 'get_product_sizes') and message.from_user.id in user_catalog_selections 
    else []
))
async def size_selection(message: types.Message):
    await handle_size_selection(message, db)


@dp.message(lambda message: message.text == "Назад" and message.from_user.id in user_catalog_selections)
async def back_from_sizes(message: types.Message):
    await handle_back_from_sizes(message, db)


@dp.message(lambda message: message.text == "Назад")
async def back(message: types.Message):
    await handle_back(message)


@dp.message(lambda message: message.text == "Назад к городам")
async def back_to_cities(message: types.Message):
    await handle_back_to_cities(message, db)


@dp.message(lambda message: message.text in db.get_all_cities())
async def city_selected(message: types.Message):
    await handle_city_selection(message, db)


@dp.message(lambda message: message.text == "Связаться с менеджером")
@PerformanceMonitor.measure("support_request")
async def request_support(message: types.Message):
    await handle_support_request(message, bot, db, config)


@dp.message(lambda message: message.text == "Поделиться контактом")
async def share_contact(message: types.Message):
    await handle_share_contact(message, bot, db, config)


@dp.message(lambda message: message.contact is not None)
async def contact_handler(message: types.Message):
    await process_contact_data(message, bot, db, config)


@dp.message(lambda message: message.text.startswith("Принять чат"))
@PerformanceMonitor.measure("accept_chat")
async def accept_chat(message: types.Message):
    await handle_accept_chat(message, bot, db, config.config.managers)


@dp.message(lambda message: message.text == "Завершить чат")
@PerformanceMonitor.measure("close_chat")
async def close_chat(message: types.Message):
    await handle_close_chat(message, bot, db, config)


@dp.message(lambda message: message.text == "История сообщений")
async def chat_history(message: types.Message):
    await handle_chat_history(message, db)


@dp.message(lambda message: message.text.startswith("/view_"))
async def view_media(message: types.Message):
    await handle_view_media(message, db, bot)


@dp.message(lambda message: message.text.startswith("Оценка: "))
@PerformanceMonitor.measure("rate_chat")
async def rate_chat(message: types.Message):
    await handle_rating(message, db)


@dp.message(lambda message: message.text in [street for city_id in range(1, 18)
           for street in db.get_streets_by_city(city_id)])
async def street_selected(message: types.Message):
    await handle_street_selection(message, db)


@dp.message(lambda message: message.text == "Пропустить" or 
            (db.get_chat_rating(message.from_user.id) is not None and 
             not message.text.startswith("Оценка: ") and
             not message.text.startswith("/") and
             not db.is_client_in_active_chat(message.from_user.id)))
async def add_rating_comment(message: types.Message):
    await handle_rating_comment(message, db)


@dp.message(lambda message: message.text == "Главное меню")
async def main_menu(message: types.Message):
    await handle_start(message, config, db)


@dp.message(lambda message: message.text == "Доступен для чатов")
@PerformanceMonitor.measure("manager_available")
async def set_available(message: types.Message):
    await handle_set_availability(message, db, True)


@dp.message(lambda message: message.text == "Недоступен для чатов")
@PerformanceMonitor.measure("manager_unavailable")
async def set_unavailable(message: types.Message):
    await handle_set_availability(message, db, False)


@dp.message(lambda message: message.text == "Статус менеджера")
async def manager_status(message: types.Message):
    await handle_manager_status(message, db)


@dp.message(lambda message: message.text == "Активные чаты" and message.from_user.id in config.config.managers)
async def manager_active_chats(message: types.Message):
    await handle_manager_active_chats(message, db)


@dp.message(lambda message: message.text == "Передать другому менеджеру")
async def transfer_chat_request(message: types.Message):
    await handle_transfer_chat_request(message, db)


@dp.message(lambda message: message.text.startswith("Передать: "))
@PerformanceMonitor.measure("transfer_chat")
async def transfer_chat(message: types.Message):
    await handle_transfer_chat(message, bot, db)


@dp.message(lambda message: message.text.startswith("Чат с "))
async def chat_selection(message: types.Message):
    await handle_chat_selection(message, db)


@dp.message(lambda message: message.text == "Панель администратора" and db.is_admin(message.from_user.id))
async def admin_panel(message: types.Message):
    await handle_admin_panel(message, db)


@dp.message(lambda message: message.text == "Статистика" and db.is_admin(message.from_user.id))
async def admin_stats(message: types.Message):
    await handle_admin_stats(message, db)


@dp.message(lambda message: message.text == "Ожидающие чаты" and db.is_admin(message.from_user.id))
async def admin_pending_chats(message: types.Message):
    await handle_admin_pending_chats(message, db)


@dp.message(lambda message: message.text == "Активные чаты" and db.is_admin(message.from_user.id))
async def admin_active_chats(message: types.Message):
    await handle_admin_active_chats(message, db)


@dp.message(lambda message: message.text == "Управление менеджерами" and db.is_admin(message.from_user.id))
async def admin_managers(message: types.Message):
    await handle_admin_managers(message, db)


@dp.message(lambda message: message.text.startswith("Взять чат с ") and db.is_admin(message.from_user.id))
@PerformanceMonitor.measure("admin_take_chat")
async def admin_take_chat(message: types.Message):
    await handle_admin_take_chat(message, bot, db)


@dp.message(lambda message: message.text.startswith("Статистика: ") and db.is_admin(message.from_user.id))
async def admin_manager_specific_stats(message: types.Message):
    await handle_admin_manager_stats(message, db, config)


# Новые хендлеры для отчетов и аналитики
@dp.message(lambda message: message.text == "Отчеты" and db.is_admin(message.from_user.id))
async def admin_reports(message: types.Message):
    await message.answer(
        "📊 *Меню отчетов*\n\n"
        "Выберите тип отчета:",
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="Отчет за сегодня")],
                [types.KeyboardButton(text="Отчет за неделю")],
                [types.KeyboardButton(text="Отчет по менеджерам")],
                [types.KeyboardButton(text="Панель администратора")]
            ],
            resize_keyboard=True
        )
    )


@dp.message(lambda message: message.text == "Отчет за сегодня" and db.is_admin(message.from_user.id))
async def admin_daily_report(message: types.Message):
    await message.answer("Генерирую отчет за сегодня...")
    await analytics.generate_daily_report()
    await message.answer("✅ Отчет успешно сгенерирован и отправлен вам.")


@dp.message(lambda message: message.text == "Отчет за неделю" and db.is_admin(message.from_user.id))
async def admin_weekly_report(message: types.Message):
    await message.answer("Генерирую недельный отчет...")
    
    # Получаем отчеты
    manager_report = AnalyticsReporter.get_manager_performance_report(
        config.db.database, days=7
    )
    
    if not manager_report:
        await message.answer("Нет данных для формирования отчета за указанный период.")
        return
    
    # Формируем текст отчета
    report_text = "📊 *Недельный отчет по работе менеджеров*\n\n"
    
    for manager in manager_report:
        report_text += (
            f"👨‍💼 *{manager['manager_name']}* (ID: {manager['manager_id']})\n"
            f"   - Всего чатов: {manager['total_chats']}\n"
            f"   - Средний рейтинг: {manager['avg_rating']}/5.0 ({manager['rating_count']} оценок)\n"
            f"   - Положительных оценок (4-5): {manager['positive_ratings']}\n"
            f"   - Отрицательных оценок (1-2): {manager['negative_ratings']}\n\n"
        )
    
    # Отправляем отчет
    await message.answer(
        report_text,
        parse_mode="Markdown"
    )


@dp.message(lambda message: message.text == "Отчет по менеджерам" and db.is_admin(message.from_user.id))
async def admin_manager_report(message: types.Message):
    # Получаем список всех менеджеров
    managers = db.get_all_managers()
    
    if not managers:
        await message.answer("В системе нет зарегистрированных менеджеров.")
        return
    
    # Строим клавиатуру для выбора менеджера
    keyboard = []
    for manager in managers:
        manager_id, name, is_admin, is_available, active_chats = manager
        manager_name = name or f"Менеджер {manager_id}"
        keyboard.append([types.KeyboardButton(text=f"Отчет: {manager_name} ({manager_id})")])
    
    keyboard.append([types.KeyboardButton(text="Отчеты")])
    
    # Отправляем сообщение
    await message.answer(
        "Выберите менеджера для формирования отчета:",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True
        )
    )


@dp.message(lambda message: message.text.startswith("Отчет: ") and db.is_admin(message.from_user.id))
async def admin_specific_manager_report(message: types.Message):
    # Извлекаем ID менеджера из текста
    text = message.text
    manager_id = int(text.split("(")[1].split(")")[0])
    
    # Генерируем отчет для этого менеджера
    await message.answer(f"Генерирую отчет для менеджера {manager_id}...")
    await analytics.send_manager_report(manager_id, message.from_user.id)


@dp.message()
@PerformanceMonitor.measure("handle_messages")
async def handle_messages(message: types.Message):
    await handle_message(message, bot, db, config)


async def main():
    # Запускаем аналитику и мониторинг
    await bot_monitoring.start_monitoring()
    
    # Запускаем планировщик отчетов в фоновом режиме
    asyncio.create_task(analytics.start_scheduler())
    
    # Запускаем бота
    await dp.start_polling(bot)


# Обработчик сигналов для корректного завершения работы
def signal_handler(sig, frame):
    logger.info(f"Received signal {sig}, shutting down...")
    bot_monitoring.log_bot_stop()
    sys.exit(0)


if __name__ == "__main__":
    try:
        # Регистрируем обработчики сигналов
        import signal
        import sys
        signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # kill
        
        asyncio.run(main())
    except KeyboardInterrupt:
        # Логируем завершение работы бота
        bot_monitoring.log_bot_stop()
        logger.info("Bot stopped by user")
    except Exception as e:
        # Логируем ошибку
        logger.error(f"Bot stopped due to error: {e}", exc_info=True)
        # Логируем завершение работы бота
        bot_monitoring.log_bot_stop()
