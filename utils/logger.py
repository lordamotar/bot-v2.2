import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import os
from datetime import datetime, timedelta
import json
import sqlite3
from pathlib import Path
import inspect


def setup_logger():
    # Создаем директорию для логов, если её нет
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Настраиваем разные уровни логирования
    log_levels = {
        'bot': logging.INFO,
        'db': logging.INFO,
        'handlers': logging.INFO,
        'analytics': logging.INFO,
        'performance': logging.INFO,
    }

    # Настраиваем формат логирования
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)

    # Создаем файловые обработчики для разных типов логов
    handlers = {}
    
    # Основной лог бота с ежедневной ротацией
    current_date = datetime.now().strftime('%Y-%m-%d')
    handlers['bot'] = TimedRotatingFileHandler(
        f'logs/bot_{current_date}.log',
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    
    # Лог для аналитики взаимодействий
    handlers['analytics'] = RotatingFileHandler(
        f'logs/analytics.log',
        maxBytes=10485760,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    
    # Лог для производительности и мониторинга
    handlers['performance'] = RotatingFileHandler(
        f'logs/performance.log',
        maxBytes=5242880,  # 5MB
        backupCount=5,
        encoding='utf-8'
    )
    
    # Лог для базы данных
    handlers['db'] = RotatingFileHandler(
        f'logs/database.log',
        maxBytes=5242880,  # 5MB
        backupCount=5,
        encoding='utf-8'
    )
    
    # Лог для обработчиков сообщений
    handlers['handlers'] = RotatingFileHandler(
        f'logs/handlers.log',
        maxBytes=5242880,  # 5MB
        backupCount=5,
        encoding='utf-8'
    )
    
    # Настраиваем логгеры
    loggers = {}
    for name, level in log_levels.items():
        logger = logging.getLogger(name)
        logger.setLevel(level)
        handlers[name].setFormatter(formatter)
        logger.addHandler(handlers[name])
        loggers[name] = logger
    
    return loggers


# Инициализация логгеров
loggers = setup_logger()
logger = loggers['bot']
db_logger = loggers['db']
handlers_logger = loggers['handlers']
analytics_logger = loggers['analytics']
performance_logger = loggers['performance']


class ManagerMetrics:
    """Класс для работы с метриками работы менеджеров"""
    
    @staticmethod
    def log_chat_started(client_id, timestamp=None):
        """Логирует начало чата"""
        timestamp = timestamp or datetime.now().isoformat()
        analytics_logger.info(json.dumps({
            'event': 'chat_started',
            'client_id': client_id,
            'timestamp': timestamp
        }))
    
    @staticmethod
    def log_chat_accepted(client_id, manager_id, response_time=None, timestamp=None):
        """Логирует принятие чата менеджером с временем отклика"""
        timestamp = timestamp or datetime.now().isoformat()
        analytics_logger.info(json.dumps({
            'event': 'chat_accepted',
            'client_id': client_id,
            'manager_id': manager_id,
            'response_time_seconds': response_time,
            'timestamp': timestamp
        }))
    
    @staticmethod
    def log_chat_closed(client_id, manager_id, duration=None, timestamp=None):
        """Логирует завершение чата с его продолжительностью"""
        timestamp = timestamp or datetime.now().isoformat()
        analytics_logger.info(json.dumps({
            'event': 'chat_closed',
            'client_id': client_id,
            'manager_id': manager_id,
            'duration_seconds': duration,
            'timestamp': timestamp
        }))
    
    @staticmethod
    def log_rating_received(client_id, manager_id, rating, comment=None, timestamp=None):
        """Логирует получение оценки за чат"""
        timestamp = timestamp or datetime.now().isoformat()
        analytics_logger.info(json.dumps({
            'event': 'rating_received',
            'client_id': client_id,
            'manager_id': manager_id,
            'rating': rating,
            'comment': comment,
            'timestamp': timestamp
        }))
    
    @staticmethod
    def log_message_sent(chat_id, sender_id, is_manager, message_type, timestamp=None):
        """Логирует отправку сообщения"""
        timestamp = timestamp or datetime.now().isoformat()
        analytics_logger.info(json.dumps({
            'event': 'message_sent',
            'chat_id': chat_id,
            'sender_id': sender_id,
            'is_manager': is_manager,
            'message_type': message_type,
            'timestamp': timestamp
        }))
    
    @staticmethod
    def log_manager_status_change(manager_id, status, timestamp=None):
        """Логирует изменение статуса менеджера"""
        timestamp = timestamp or datetime.now().isoformat()
        analytics_logger.info(json.dumps({
            'event': 'manager_status_change',
            'manager_id': manager_id,
            'status': status,
            'timestamp': timestamp
        }))


class BotMonitoring:
    """Класс для мониторинга состояния бота"""
    
    @staticmethod
    def log_bot_start(timestamp=None):
        """Логирует запуск бота"""
        timestamp = timestamp or datetime.now().isoformat()
        performance_logger.info(json.dumps({
            'event': 'bot_start',
            'timestamp': timestamp
        }))
    
    @staticmethod
    def log_bot_stop(timestamp=None):
        """Логирует остановку бота"""
        timestamp = timestamp or datetime.now().isoformat()
        performance_logger.info(json.dumps({
            'event': 'bot_stop',
            'timestamp': timestamp
        }))
    
    @staticmethod
    def log_request_processing_time(handler_name, processing_time, timestamp=None):
        """Логирует время обработки запроса"""
        timestamp = timestamp or datetime.now().isoformat()
        performance_logger.info(json.dumps({
            'event': 'request_processed',
            'handler': handler_name,
            'processing_time_ms': processing_time,
            'timestamp': timestamp
        }))
    
    @staticmethod
    def log_error(error_message, handler_name=None, user_id=None, timestamp=None):
        """Логирует ошибку бота"""
        timestamp = timestamp or datetime.now().isoformat()
        performance_logger.error(json.dumps({
            'event': 'error',
            'handler': handler_name,
            'user_id': user_id,
            'error': error_message,
            'timestamp': timestamp
        }))
    
    @staticmethod
    def log_db_performance(operation, execution_time, query=None, timestamp=None):
        """Логирует производительность базы данных"""
        timestamp = timestamp or datetime.now().isoformat()
        db_logger.info(json.dumps({
            'event': 'db_operation',
            'operation': operation,
            'execution_time_ms': execution_time,
            'query': query if query and len(query) < 500 else None,
            'timestamp': timestamp
        }))


class AnalyticsReporter:
    """Класс для генерации аналитических отчетов"""
    
    @staticmethod
    def get_manager_performance_report(db_path, manager_id=None, days=7):
        """Получает отчет о производительности менеджеров за указанный период"""
        try:
            # Подключаемся к базе данных
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Определяем период отчета
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Строим запрос в зависимости от того, запрашиваются ли данные по конкретному менеджеру
            if manager_id:
                query = """
                SELECT 
                    m.id as manager_id,
                    m.name as manager_name,
                    COUNT(c.client_id) as total_chats,
                    AVG(r.rating) as avg_rating,
                    COUNT(r.rating) as rating_count,
                    SUM(CASE WHEN r.rating >= 4 THEN 1 ELSE 0 END) as positive_ratings,
                    SUM(CASE WHEN r.rating <= 2 THEN 1 ELSE 0 END) as negative_ratings
                FROM 
                    managers m
                LEFT JOIN 
                    chats c ON m.id = c.manager_id
                LEFT JOIN 
                    ratings r ON c.client_id = r.chat_id
                WHERE 
                    m.id = ? AND
                    c.status = 'closed' AND
                    r.timestamp BETWEEN ? AND ?
                GROUP BY 
                    m.id
                """
                cursor.execute(query, (manager_id, start_date.isoformat(), end_date.isoformat()))
            else:
                query = """
                SELECT 
                    m.id as manager_id,
                    m.name as manager_name,
                    COUNT(c.client_id) as total_chats,
                    AVG(r.rating) as avg_rating,
                    COUNT(r.rating) as rating_count,
                    SUM(CASE WHEN r.rating >= 4 THEN 1 ELSE 0 END) as positive_ratings,
                    SUM(CASE WHEN r.rating <= 2 THEN 1 ELSE 0 END) as negative_ratings
                FROM 
                    managers m
                LEFT JOIN 
                    chats c ON m.id = c.manager_id
                LEFT JOIN 
                    ratings r ON c.client_id = r.chat_id
                WHERE 
                    c.status = 'closed' AND
                    r.timestamp BETWEEN ? AND ?
                GROUP BY 
                    m.id
                ORDER BY 
                    avg_rating DESC
                """
                cursor.execute(query, (start_date.isoformat(), end_date.isoformat()))
            
            # Получаем результаты
            results = cursor.fetchall()
            
            # Преобразуем результаты в словарь для удобства
            report = []
            for row in results:
                manager_data = {
                    'manager_id': row[0],
                    'manager_name': row[1] or f"Manager {row[0]}",
                    'total_chats': row[2],
                    'avg_rating': round(row[3], 2) if row[3] is not None else 0,
                    'rating_count': row[4],
                    'positive_ratings': row[5] or 0,
                    'negative_ratings': row[6] or 0,
                    'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
                }
                report.append(manager_data)
            
            return report
        except Exception as e:
            db_logger.error(f"Error generating manager performance report: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def get_response_time_report(log_path="logs/analytics.log", days=7):
        """Анализирует время отклика менеджеров из лог-файла аналитики"""
        try:
            # Определяем период отчета
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Словари для хранения данных
            chat_started = {}  # client_id -> timestamp
            manager_response_times = {}  # manager_id -> [response_times]
            
            # Читаем лог-файл
            log_file = Path(log_path)
            if not log_file.exists():
                return {}
            
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        # Извлекаем JSON из строки лога
                        parts = line.strip().split(' - ')
                        if len(parts) >= 4:
                            try:
                                log_data = json.loads(parts[3])
                            except:
                                continue
                            
                            # Парсим временную метку
                            log_timestamp = datetime.fromisoformat(log_data.get('timestamp', '').replace('Z', '+00:00'))
                            
                            # Проверяем, входит ли запись в анализируемый период
                            if not (start_date <= log_timestamp <= end_date):
                                continue
                            
                            # Обрабатываем события
                            event = log_data.get('event')
                            
                            if event == 'chat_started':
                                client_id = log_data.get('client_id')
                                chat_started[client_id] = log_timestamp
                            
                            elif event == 'chat_accepted':
                                client_id = log_data.get('client_id')
                                manager_id = log_data.get('manager_id')
                                
                                # Если есть запись о начале чата, вычисляем время отклика
                                if client_id in chat_started:
                                    start_time = chat_started[client_id]
                                    response_time = (log_timestamp - start_time).total_seconds()
                                    
                                    # Добавляем в статистику менеджера
                                    if manager_id not in manager_response_times:
                                        manager_response_times[manager_id] = []
                                    
                                    manager_response_times[manager_id].append(response_time)
                    except Exception as e:
                        continue
            
            # Готовим отчет
            report = []
            for manager_id, response_times in manager_response_times.items():
                if response_times:
                    avg_response_time = sum(response_times) / len(response_times)
                    min_response_time = min(response_times)
                    max_response_time = max(response_times)
                    
                    report.append({
                        'manager_id': manager_id,
                        'avg_response_time': round(avg_response_time, 2),
                        'min_response_time': round(min_response_time, 2),
                        'max_response_time': round(max_response_time, 2),
                        'response_count': len(response_times),
                        'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
                    })
            
            # Сортируем по среднему времени отклика (от наименьшего к наибольшему)
            report.sort(key=lambda x: x['avg_response_time'])
            
            return report
        except Exception as e:
            logger.error(f"Error generating response time report: {e}")
            return []


# Класс-декоратор для измерения времени выполнения
class PerformanceMonitor:
    """Декоратор для измерения производительности функций"""
    
    @staticmethod
    def measure(handler_name=None):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                start_time = datetime.now()
                try:
                    # Отфильтровываем неожиданные аргументы
                    sig = inspect.signature(func)
                    allowed_kwargs = {}
                    for param_name, param in sig.parameters.items():
                        if param_name in kwargs:
                            allowed_kwargs[param_name] = kwargs[param_name]
                        elif param.kind == inspect.Parameter.VAR_KEYWORD:
                            # Если функция принимает **kwargs, передаем все
                            allowed_kwargs = kwargs
                            break
                    
                    result = await func(*args, **allowed_kwargs)
                    elapsed_time = (datetime.now() - start_time).total_seconds() * 1000  # мс
                    
                    # Логируем время выполнения
                    func_name = handler_name or func.__name__
                    BotMonitoring.log_request_processing_time(func_name, elapsed_time)
                    
                    return result
                except Exception as e:
                    elapsed_time = (datetime.now() - start_time).total_seconds() * 1000  # мс
                    func_name = handler_name or func.__name__
                    
                    # Определяем user_id из аргументов, если возможно
                    user_id = None
                    for arg in args:
                        if hasattr(arg, 'from_user') and hasattr(arg.from_user, 'id'):
                            user_id = arg.from_user.id
                            break
                    
                    # Логируем ошибку
                    BotMonitoring.log_error(str(e), func_name, user_id)
                    
                    # Пробрасываем исключение дальше
                    raise
            return wrapper
        return decorator
