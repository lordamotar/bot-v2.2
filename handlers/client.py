from aiogram import types, Bot
from database import Database
from keyboards import (
    get_main_keyboard, 
    get_chat_keyboard, 
    get_manager_keyboard, 
    get_rating_keyboard,
    get_share_contact_keyboard,
    get_admin_keyboard
)
import logging
from datetime import datetime
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

logger = logging.getLogger(__name__)


async def handle_start(message: types.Message, config=None, db=None):
    user_id = message.from_user.id
    
    # Проверяем, является ли пользователь менеджером
    is_manager = config and user_id in config.config.managers
    
    if is_manager:
        # Проверяем, является ли менеджер администратором
        is_admin = db and db.is_admin(user_id)
        
        if is_admin:
            # Если это администратор, показываем меню с опцией администратора
            await message.answer(
                "Добро пожаловать, Администратор! "
                "Выберите нужное действие ниже:",
                reply_markup=get_admin_keyboard()
            )
        else:
            # Обычное меню для менеджера
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="Каталог")],
                    [KeyboardButton(text="Контакты")],
                    [KeyboardButton(text="Статус менеджера")]
                ],
                resize_keyboard=True
            )
            await message.answer(
                "Добро пожаловать в панель управления менеджера! "
                "Выберите нужное действие ниже.",
                reply_markup=keyboard
            )
    else:
        # Проверяем, есть ли пользователь в базе данных
        client_info = None
        if db:
            try:
                client_info = db.get_client_contact_info(user_id)
                logger.info(f"Получена информация о клиенте: {client_info}")
            except Exception as e:
                logger.error(f"Ошибка при получении данных клиента: {e}")
        
        if client_info and client_info[0]:  # Если есть информация о клиенте и имя не пустое
            client_name = client_info[0]
            await message.answer(
                f"Здравствуйте, {client_name}! Рады видеть вас снова!\n"
                "Чем я могу вам помочь сегодня?",
                reply_markup=get_main_keyboard()
            )
            logger.info(f"Возвращающийся пользователь: {user_id}, имя: {client_name}")
        else:
            # Обычное меню для новых клиентов
            first_name = message.from_user.first_name
            greeting = f"Добро пожаловать, {first_name}!" if first_name else "Добро пожаловать!"
            await message.answer(
                f"{greeting} Я бот службы поддержки. Чтобы начать чат с менеджером, "
                "нажмите кнопку ниже.",
                reply_markup=get_main_keyboard()
            )
            logger.info(f"Новый пользователь: {user_id}")


async def handle_support_request(message: types.Message, bot: Bot, db: Database, config):
    """Обработка запроса на связь с менеджером"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    # Проверяем наличие свободных менеджеров
    available_managers = db.get_available_managers_count()
    logger.info(f"Available managers: {available_managers}")

    if available_managers <= 0:
        await message.answer(
            "К сожалению, все менеджеры сейчас заняты. "
            "Пожалуйста, попробуйте обратиться чуть позже.",
            reply_markup=get_main_keyboard()
        )
        return

    # Проверяем, не находится ли пользователь уже в чате
    if db.is_client_in_active_chat(user_id):
        await message.answer(
            "У вас уже есть активный чат с менеджером.",
            reply_markup=get_chat_keyboard()
        )
        return

    # Проверяем, есть ли у пользователя контактные данные в базе
    client_info = db.get_client_contact_info(user_id)
    
    if client_info and client_info[0] and client_info[1]:  # Если есть имя и телефон
        # Создаем чат без запроса контактных данных
        if not db.create_chat(user_id, username):
            logger.error(f"Не удалось создать чат для пользователя {user_id}")
            await message.answer(
                "Произошла ошибка при создании чата. Пожалуйста, попробуйте позже.",
                reply_markup=get_main_keyboard()
            )
            return
        
        # Информируем пользователя
        await message.answer(
            "Ваш запрос отправлен менеджерам. Пожалуйста, ожидайте ответа.",
            reply_markup=get_chat_keyboard()
        )
        
        # Получаем доступного менеджера с наименьшей нагрузкой
        manager_id = db.get_available_manager()
        
        # Получаем данные клиента
        client_name = client_info[0]
        client_phone = client_info[1]
        
        # Формируем сообщение с данными клиента
        client_info_text = (
            f"Новый запрос в чат от пользователя {username}\n"
            f"Имя: {client_name}\n"
            f"Телефон: {client_phone}"
        )
        
        # Создаем клавиатуру для менеджера с информацией о клиенте
        manager_keyboard = get_manager_keyboard(username, client_name, client_phone)
        
        # Отправляем уведомление менеджеру(ам)
        if manager_id > 0:
            # Уведомляем конкретного менеджера
            await bot.send_message(
                manager_id,
                client_info_text,
                reply_markup=manager_keyboard
            )
            logger.info(f"Запрос на чат отправлен менеджеру {manager_id}")
        else:
            # Уведомляем всех менеджеров
            notification_sent = False
            for mgr_id in config.config.managers:
                try:
                    await bot.send_message(
                        mgr_id,
                        client_info_text,
                        reply_markup=manager_keyboard
                    )
                    notification_sent = True
                except Exception as e:
                    logger.error(f"Ошибка отправки уведомления менеджеру {mgr_id}: {e}")
            
            if notification_sent:
                logger.info("Запрос на чат отправлен всем менеджерам")
            else:
                logger.error("Не удалось уведомить ни одного менеджера")
                await message.answer(
                    "Произошла ошибка при отправке запроса менеджерам. "
                    "Пожалуйста, попробуйте позже.",
                    reply_markup=get_main_keyboard()
                )
    else:
        # Просим пользователя поделиться контактом
        await message.answer(
            "Перед тем, как связаться с менеджером, поделитесь вашими контактными данными.",
            reply_markup=get_share_contact_keyboard()
        )


async def handle_share_contact(message: types.Message, bot: Bot, db: Database, config):
    """Обработка нажатия на кнопку 'Поделиться контактом'"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    # Создаем или обновляем запись в базе данных 
    if not db.create_chat(user_id, username):
        logger.error(f"Failed to create chat record for user {user_id}")
        await message.answer(
            "Произошла ошибка при подготовке чата. Пожалуйста, попробуйте позже.",
            reply_markup=get_main_keyboard()
        )
        return
    
    await message.answer(
        "Пожалуйста, нажмите кнопку 'Поделиться контактом' для автоматической передачи "
        "вашего имени и номера телефона из профиля Telegram.",
        reply_markup=get_share_contact_keyboard()
    )


async def process_contact_data(message: types.Message, bot: Bot, db: Database, config):
    """Обработка полученных контактных данных"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    # Извлекаем данные из контакта
    phone = message.contact.phone_number
    name = message.contact.first_name
    if message.contact.last_name:
        name += f" {message.contact.last_name}"
    
    logger.info(f"Получен контакт от пользователя {user_id}: имя={name}, телефон={phone}")
    
    # Перезагружаем базу данных перед дальнейшими операциями
    # для применения возможных изменений структуры таблиц
    try:
        if "_create_tables" in dir(db):
            db._create_tables()
            logger.info("Структура базы данных обновлена")
    except Exception as e:
        logger.error(f"Ошибка при обновлении структуры базы данных: {e}")
    
    # Проверяем существование таблицы и полей для отладки
    try:
        conn, cursor = db._get_connection()
        cursor.execute("PRAGMA table_info(chats)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        logger.info(f"Структура таблицы chats: {column_names}")
        
        # Проверяем запись для текущего пользователя
        cursor.execute("SELECT * FROM chats WHERE client_id = ?", (user_id,))
        user_record = cursor.fetchone()
        if user_record:
            logger.info(f"Найдена запись для пользователя: {user_record}")
        else:
            logger.info(f"Запись для пользователя {user_id} не найдена")
    except Exception as e:
        logger.error(f"Ошибка при проверке структуры базы данных: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
            delattr(db._local, 'connection')
    
    # Проверяем, существует ли запись в базе данных для этого пользователя
    # и создаем ее, если она отсутствует
    chat_info = db.get_client_contact_info(user_id)
    if not chat_info:
        logger.info(f"Не найдена существующая запись для пользователя {user_id}, создаем новую")
        if not db.create_chat(user_id, username):
            logger.error(f"Не удалось создать запись чата для пользователя {user_id}")
            await message.answer(
                "Произошла ошибка при создании чата. Пожалуйста, попробуйте позже.",
                reply_markup=get_main_keyboard()
            )
            return
        logger.info(f"Запись чата создана для пользователя {user_id}")
    else:
        logger.info(f"Найдена существующая запись для пользователя {user_id}: {chat_info}")
    
    # Сохраняем данные клиента
    try:
        logger.info(f"Попытка сохранить контактные данные: user_id={user_id}, name={name}, phone={phone}")
        success = db.save_client_contact_info(user_id, name, phone, username)
        if not success:
            logger.error(f"Не удалось сохранить контактные данные для пользователя {user_id}")
            await message.answer(
                "Произошла ошибка при сохранении данных. Пожалуйста, попробуйте позже.",
                reply_markup=get_main_keyboard()
            )
            return
        logger.info(f"Контактные данные успешно сохранены для пользователя {user_id}")
    except Exception as e:
        logger.error(f"Исключение при сохранении контактных данных: {str(e)}", exc_info=True)
        await message.answer(
            "Произошла ошибка при сохранении данных. Пожалуйста, попробуйте позже.",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Проверяем, сохранились ли данные
    try:
        updated_info = db.get_client_contact_info(user_id)
        logger.info(f"Проверка после сохранения: {updated_info}")
    except Exception as e:
        logger.error(f"Ошибка при проверке сохраненных данных: {e}")
    
    # Информируем пользователя
    logger.info(f"Контактные данные сохранены для пользователя {username} (ID: {user_id})")
    await message.answer(
        "Ваш запрос отправлен менеджерам. Пожалуйста, ожидайте ответа.",
        reply_markup=get_chat_keyboard()
    )
    
    # Получаем доступного менеджера с наименьшей нагрузкой
    manager_id = db.get_available_manager()
    logger.info(f"Available manager for user {user_id}: {manager_id}")
    
    # Формируем сообщение с данными клиента
    client_info = (
        f"Новый запрос в чат от пользователя {username}\n"
        f"Имя: {name}\n"
        f"Телефон: {phone}"
    )
    
    # Создаем клавиатуру для менеджера с информацией о клиенте
    manager_keyboard = get_manager_keyboard(username, name, phone)
    
    # Определяем вспомогательную функцию для отправки уведомлений всем менеджерам
    async def send_to_all_managers():
        notification_sent = False
        for mgr_id in config.config.managers:
            try:
                await bot.send_message(
                    mgr_id,
                    client_info,
                    reply_markup=manager_keyboard
                )
                notification_sent = True
                logger.info(f"Chat request sent to manager {mgr_id}")
            except Exception as e:
                logger.error(f"Error sending notification to manager {mgr_id}: {e}")
        
        if not notification_sent:
            logger.error(f"Failed to notify any manager for user {user_id}")
            await message.answer(
                "Произошла ошибка при отправке запроса менеджерам. "
                "Пожалуйста, попробуйте позже.",
                reply_markup=get_main_keyboard()
            )
    
    if manager_id > 0:
        # Уведомляем конкретного менеджера
        try:
            await bot.send_message(
                manager_id,
                client_info,
                reply_markup=manager_keyboard
            )
            logger.info(f"Chat request sent to manager {manager_id}")
        except Exception as e:
            logger.error(f"Error sending message to manager {manager_id}: {str(e)}")
            # Если не удалось отправить конкретному менеджеру, отправляем всем
            await send_to_all_managers()
    else:
        # Уведомляем всех менеджеров
        await send_to_all_managers()


async def handle_chat_history(message: types.Message, db: Database):
    """Отображение истории сообщений для пользователя"""
    user_id = message.from_user.id
    
    # Проверяем, есть ли у пользователя активный чат
    if not db.is_client_in_active_chat(user_id):
        await message.answer(
            "У вас нет активного чата с менеджером.",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Получаем историю сообщений
    messages = db.get_chat_history(user_id)
    
    if not messages:
        await message.answer(
            "История сообщений пуста.",
            reply_markup=get_chat_keyboard()
        )
        return
    
    # Форматируем сообщения для вывода
    history_text = "📋 История сообщений:\n\n"
    
    for msg in messages:
        msg_id, sender_id, msg_text, msg_type, file_id, timestamp, is_read = msg
        
        # Преобразуем timestamp в читаемый формат
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_str = dt.strftime("%d.%m.%Y %H:%M")
        except Exception as e:
            logger.error(f"Error parsing timestamp: {e}")
            time_str = str(timestamp)
        
        # Определяем отправителя
        if sender_id == user_id:
            sender = "Вы"
        else:
            sender = "Менеджер"
        
        # Добавляем информацию о типе сообщения
        type_icon = "💬"
        view_command = ""
        
        if msg_type != 'text' and file_id:
            if msg_type == 'photo':
                type_icon = "🖼️"
            elif msg_type == 'video':
                type_icon = "🎬"
            elif msg_type == 'document':
                type_icon = "📎"
            elif msg_type == 'audio':
                type_icon = "🎵"
            elif msg_type == 'voice':
                type_icon = "🎤"
                
            view_command = f"\nПросмотреть: /view_{msg_id}"
        
        # Добавляем форматированное сообщение
        history_text += f"{time_str} - {sender} {type_icon}:\n{msg_text}{view_command}\n\n"
    
    # Отправляем историю
    await message.answer(
        history_text,
        reply_markup=get_chat_keyboard()
    )


async def handle_view_media(message: types.Message, db: Database, bot: Bot):
    """Отображение медиа-файла из истории по ID сообщения"""
    user_id = message.from_user.id
    
    # Проверяем, является ли сообщение командой просмотра медиа
    if not message.text.startswith("/view_"):
        return
    
    try:
        # Извлекаем ID сообщения из команды
        msg_id = int(message.text.replace("/view_", ""))
        logger.info(f"User {user_id} requested media view for message ID: {msg_id}")
        
        # Получаем историю сообщений
        messages = db.get_chat_history(user_id)
        
        # Ищем нужное сообщение
        target_msg = None
        for msg in messages:
            if msg[0] == msg_id:
                target_msg = msg
                break
        
        if not target_msg:
            logger.warning(f"Message ID {msg_id} not found for user {user_id}")
            await message.answer("Сообщение не найдено")
            return
        
        # Распаковываем данные сообщения
        msg_id, sender_id, msg_text, msg_type, file_id, timestamp, is_read = target_msg
        
        if not file_id:
            logger.warning(f"No file_id found in message {msg_id}")
            await message.answer("К этому сообщению не прикреплен файл")
            return
        
        logger.info(f"Attempting to send media file, type: {msg_type}, file_id: {file_id[:15] if file_id else 'None'}...")
        
        try:
            # Отправляем файл в зависимости от типа
            if msg_type == 'photo':
                await bot.send_photo(user_id, file_id, caption=msg_text)
            elif msg_type == 'video':
                await bot.send_video(user_id, file_id, caption=msg_text)
            elif msg_type == 'document':
                await bot.send_document(user_id, file_id, caption=msg_text)
            elif msg_type == 'audio':
                await bot.send_audio(user_id, file_id, caption=msg_text)
            elif msg_type == 'voice':
                await bot.send_voice(user_id, file_id, caption=msg_text)
            elif msg_type == 'sticker':
                await bot.send_sticker(user_id, file_id)
            elif msg_type == 'animation':
                await bot.send_animation(user_id, file_id, caption=msg_text)
            else:
                logger.warning(f"Unsupported media type: {msg_type}")
                # Если тип не распознан, пробуем отправить как документ
                try:
                    await bot.send_document(user_id, file_id, caption=f"{msg_text} (Неизвестный тип файла)")
                    logger.info(f"Sent unknown media as document")
                except Exception as doc_err:
                    logger.error(f"Failed to send as document: {doc_err}")
                    await message.answer(f"Тип файла '{msg_type}' не поддерживается")
                return
                
            logger.info(f"Successfully sent media file to user {user_id}")
        except Exception as e:
            logger.error(f"Error sending media file: {e}")
            # Пытаемся отправить как документ в случае ошибки
            try:
                await bot.send_document(user_id, file_id, caption=f"{msg_text} (Отправлено как документ)")
                logger.info(f"Sent media as document after error")
            except Exception as fallback_err:
                logger.error(f"Fallback send failed: {fallback_err}")
                await message.answer(
                    "Произошла ошибка при отправке медиафайла. Возможно, "
                    "файл был удален с серверов Telegram или ID файла недействителен."
                )
            
    except ValueError:
        logger.error(f"Invalid command format: {message.text}")
        await message.answer("Неверный формат команды")
    except Exception as e:
        logger.error(f"Error viewing media: {e}")
        await message.answer("Произошла ошибка при загрузке файла")


async def handle_rate_chat_request(message: types.Message, db: Database):
    """Отправляет запрос на оценку чата"""
    user_id = message.from_user.id
    
    await message.answer(
        "Пожалуйста, оцените качество обслуживания:",
        reply_markup=get_rating_keyboard()
    )


async def handle_rating(message: types.Message, db: Database):
    """Обработка оценки чата"""
    user_id = message.from_user.id
    
    # Проверяем, что сообщение содержит оценку
    if not message.text.startswith("Оценка: "):
        return
    
    try:
        # Извлекаем оценку из сообщения
        rating = int(message.text.replace("Оценка: ", ""))
        
        if rating < 1 or rating > 5:
            await message.answer("Оценка должна быть от 1 до 5")
            return
        
        # Получаем информацию о чате для логирования
        active_chat = db.get_active_chat_by_client_id(user_id)
        last_chat = None
        
        # Если чат все еще активен, используем его для логирования
        if active_chat and active_chat[1]:
            manager_id = active_chat[1]
            
            # Логируем оценку
            try:
                from utils.logger import ManagerMetrics
                ManagerMetrics.log_rating_received(
                    client_id=user_id,
                    manager_id=manager_id,
                    rating=rating
                )
            except Exception as e:
                logger.error(f"Error logging rating: {e}")
        else:
            # Чат завершен, нужно найти последний чат пользователя
            try:
                # Получаем историю сообщений для определения менеджера
                chat_history = db.get_chat_history(user_id, limit=10)
                if chat_history:
                    # Ищем сообщения от менеджера
                    manager_ids = set()
                    for msg in chat_history:
                        sender_id = msg[2]
                        if sender_id != user_id:  # Если отправитель не клиент, это менеджер
                            manager_ids.add(sender_id)
                    
                    if manager_ids:
                        # Берем первого найденного менеджера
                        manager_id = next(iter(manager_ids))
                        
                        # Логируем оценку
                        try:
                            from utils.logger import ManagerMetrics
                            ManagerMetrics.log_rating_received(
                                client_id=user_id,
                                manager_id=manager_id,
                                rating=rating
                            )
                        except Exception as e:
                            logger.error(f"Error logging rating for closed chat: {e}")
            except Exception as e:
                logger.error(f"Error finding manager for rating: {e}")
        
        # Сохраняем оценку
        if db.save_chat_rating(user_id, rating):
            await message.answer(
                f"Спасибо за вашу оценку: {rating}/5!\n"
                "Если у вас есть комментарий, отправьте его следующим сообщением "
                "или нажмите кнопку 'Пропустить'.",
                reply_markup=types.ReplyKeyboardMarkup(
                    keyboard=[[types.KeyboardButton(text="Пропустить")]],
                    resize_keyboard=True
                )
            )
        else:
            await message.answer(
                "Произошла ошибка при сохранении оценки.",
                reply_markup=get_main_keyboard()
            )
    except ValueError:
        await message.answer("Некорректная оценка", reply_markup=get_rating_keyboard())


async def handle_rating_comment(message: types.Message, db: Database):
    """Обработка комментария к оценке"""
    user_id = message.from_user.id
    
    if message.text == "Пропустить":
        await message.answer(
            "Спасибо за оценку!",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Получаем текущую оценку
    rating_data = db.get_chat_rating(user_id)
    
    if not rating_data:
        await message.answer(
            "Сначала нужно оценить чат.",
            reply_markup=get_rating_keyboard()
        )
        return
    
    rating = rating_data[0]
    comment = message.text
    
    # Получаем информацию о чате для логирования
    try:
        # Получаем историю сообщений для определения менеджера
        chat_history = db.get_chat_history(user_id, limit=10)
        if chat_history:
            # Ищем сообщения от менеджера
            manager_ids = set()
            for msg in chat_history:
                sender_id = msg[2]
                if sender_id != user_id:  # Если отправитель не клиент, это менеджер
                    manager_ids.add(sender_id)
            
            if manager_ids:
                # Берем первого найденного менеджера
                manager_id = next(iter(manager_ids))
                
                # Логируем комментарий к оценке
                try:
                    from utils.logger import ManagerMetrics
                    ManagerMetrics.log_rating_received(
                        client_id=user_id,
                        manager_id=manager_id,
                        rating=rating,
                        comment=comment
                    )
                except Exception as e:
                    logger.error(f"Error logging rating comment: {e}")
    except Exception as e:
        logger.error(f"Error finding manager for rating comment: {e}")
    
    # Обновляем запись с комментарием
    if db.save_chat_rating(user_id, rating, comment):
        await message.answer(
            "Спасибо за ваш отзыв!",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer(
            "Произошла ошибка при сохранении комментария.",
            reply_markup=get_main_keyboard()
        )
