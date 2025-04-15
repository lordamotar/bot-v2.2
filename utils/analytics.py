import asyncio
from datetime import datetime, timedelta
import json
from aiogram import Bot, types
from .logger import (
    AnalyticsReporter, 
    logger, 
    ManagerMetrics, 
    BotMonitoring
)
from database import Database


class ManagerAnalytics:
    """Класс для управления аналитикой работы менеджеров"""
    
    def __init__(self, db: Database, bot: Bot, config):
        self.db = db
        self.bot = bot
        self.config = config
        self.report_chat_id = config.config.admin_manager_id

    async def generate_daily_report(self):
        """Генерация ежедневного отчета по работе менеджеров"""
        try:
            # Получаем отчет о работе менеджеров за последние 24 часа
            manager_report = AnalyticsReporter.get_manager_performance_report(
                self.config.db.database, days=1
            )
            
            # Получаем отчет о времени отклика
            response_report = AnalyticsReporter.get_response_time_report(days=1)
            
            # Формируем текст отчета
            report_text = "📊 *Ежедневный отчет по работе менеджеров*\n\n"
            
            if manager_report:
                report_text += "*Обслуживание клиентов:*\n"
                for manager in manager_report:
                    report_text += (
                        f"👨‍💼 {manager['manager_name']} (ID: {manager['manager_id']})\n"
                        f"   - Чатов: {manager['total_chats']}\n"
                        f"   - Рейтинг: {manager['avg_rating']}/5.0 ({manager['rating_count']} оценок)\n"
                        f"   - 👍 Положительных: {manager['positive_ratings']}\n"
                        f"   - 👎 Отрицательных: {manager['negative_ratings']}\n\n"
                    )
            else:
                report_text += "*Нет данных по обслуживанию клиентов за сегодня*\n\n"
            
            if response_report:
                report_text += "*Время отклика:*\n"
                for manager in response_report:
                    manager_name = self.db.get_manager_name(manager['manager_id']) or f"Менеджер {manager['manager_id']}"
                    report_text += (
                        f"👨‍💼 {manager_name} (ID: {manager['manager_id']})\n"
                        f"   - Среднее время: {manager['avg_response_time']} сек\n"
                        f"   - Мин. время: {manager['min_response_time']} сек\n"
                        f"   - Макс. время: {manager['max_response_time']} сек\n"
                        f"   - Всего ответов: {manager['response_count']}\n\n"
                    )
            else:
                report_text += "*Нет данных по времени отклика за сегодня*\n\n"
            
            # Добавляем общую статистику
            stats = self.db.get_dashboard_stats()
            report_text += (
                "*Общая статистика:*\n"
                f"👥 Всего менеджеров: {stats['total_managers']}\n"
                f"✅ Доступно менеджеров: {stats['available_managers']}\n"
                f"⏳ Ожидающих чатов: {stats['pending_chats']}\n"
                f"💬 Активных чатов: {stats['active_chats']}\n"
            )
            
            # Отправляем отчет администратору
            if self.report_chat_id:
                await self.bot.send_message(
                    self.report_chat_id,
                    report_text,
                    parse_mode="Markdown"
                )
                logger.info(f"Daily report sent to admin (ID: {self.report_chat_id})")
            else:
                logger.warning("No admin ID configured to send daily report")
        
        except Exception as e:
            logger.error(f"Error generating daily report: {e}")

    async def start_scheduler(self):
        """Запускает планировщик для регулярных отчетов"""
        while True:
            try:
                # Получаем текущее время
                now = datetime.now()
                
                # Вычисляем время до следующего отчета (9:00 утра)
                target_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
                if now >= target_time:
                    target_time += timedelta(days=1)
                
                # Вычисляем сколько секунд нужно ждать
                seconds_to_wait = (target_time - now).total_seconds()
                
                # Ждем до времени отчета
                logger.info(f"Scheduled next daily report in {seconds_to_wait/3600:.2f} hours")
                await asyncio.sleep(seconds_to_wait)
                
                # Генерируем и отправляем отчет
                await self.generate_daily_report()
            
            except Exception as e:
                logger.error(f"Error in report scheduler: {e}")
                await asyncio.sleep(3600)  # В случае ошибки ждем 1 час

    async def send_manager_report(self, manager_id: int, chat_id: int, days: int = 7):
        """Отправляет отчет о работе конкретного менеджера"""
        try:
            # Получаем отчет о работе менеджера
            manager_report = AnalyticsReporter.get_manager_performance_report(
                self.config.db.database, manager_id=manager_id, days=days
            )
            
            if not manager_report:
                await self.bot.send_message(
                    chat_id,
                    "Нет данных для формирования отчета за указанный период."
                )
                return
            
            # Берем первый (и единственный) элемент отчета
            report = manager_report[0]
            
            # Формируем текст отчета
            report_text = (
                f"📊 *Отчет о работе менеджера {report['manager_name']}*\n"
                f"*Период:* {report['period']}\n\n"
                f"*Всего чатов:* {report['total_chats']}\n"
                f"*Средний рейтинг:* {report['avg_rating']}/5.0 ({report['rating_count']} оценок)\n"
                f"*Положительных оценок (4-5):* {report['positive_ratings']}\n"
                f"*Отрицательных оценок (1-2):* {report['negative_ratings']}\n"
            )
            
            # Отправляем отчет
            await self.bot.send_message(
                chat_id,
                report_text,
                parse_mode="Markdown"
            )
        
        except Exception as e:
            logger.error(f"Error sending manager report: {e}")
            await self.bot.send_message(
                chat_id,
                "Произошла ошибка при формировании отчета."
            )


class BotAnalytics:
    """Класс для анализа и мониторинга работы бота"""
    
    def __init__(self, db: Database, bot: Bot, config):
        self.db = db
        self.bot = bot
        self.config = config
        self.admin_id = config.config.admin_manager_id
    
    async def start_monitoring(self):
        """Запускает мониторинг состояния бота"""
        # Логируем запуск бота
        BotMonitoring.log_bot_start()
        
        # Запускаем фоновую задачу для мониторинга состояния бота
        asyncio.create_task(self._monitor_bot_health())
    
    async def _monitor_bot_health(self):
        """Фоновая задача для мониторинга состояния бота"""
        while True:
            try:
                # Проверяем состояние бота каждые 15 минут
                await asyncio.sleep(15 * 60)
                
                # Получаем статистику
                stats = self.db.get_dashboard_stats()
                
                # Проверяем критичные условия
                critical_issues = []
                
                # Проверка 1: Менее 1 доступного менеджера при наличии ожидающих чатов
                if stats['available_managers'] < 1 and stats['pending_chats'] > 0:
                    critical_issues.append(
                        f"⚠️ Нет доступных менеджеров, но есть {stats['pending_chats']} ожидающих чатов!"
                    )
                
                # Проверка 2: Большое количество ожидающих чатов (более 5)
                if stats['pending_chats'] >= 5:
                    critical_issues.append(
                        f"⚠️ Большая очередь чатов: {stats['pending_chats']} ожидающих обработки!"
                    )
                
                # Если есть критичные проблемы, отправляем уведомление
                if critical_issues and self.admin_id:
                    alert_text = "🚨 *ВНИМАНИЕ: Обнаружены проблемы в работе бота*\n\n"
                    alert_text += "\n".join(critical_issues)
                    alert_text += "\n\n*Текущая статистика:*\n"
                    alert_text += (
                        f"👥 Всего менеджеров: {stats['total_managers']}\n"
                        f"✅ Доступно менеджеров: {stats['available_managers']}\n"
                        f"⏳ Ожидающих чатов: {stats['pending_chats']}\n"
                        f"💬 Активных чатов: {stats['active_chats']}\n"
                    )
                    
                    await self.bot.send_message(
                        self.admin_id,
                        alert_text,
                        parse_mode="Markdown"
                    )
                    
                    logger.warning(
                        f"Bot health alert sent to admin. Issues: {', '.join(critical_issues)}"
                    )
            
            except Exception as e:
                logger.error(f"Error in bot health monitoring: {e}")
                await asyncio.sleep(60)  # В случае ошибки ждем 1 минуту
    
    def log_bot_stop(self):
        """Логирует остановку бота"""
        BotMonitoring.log_bot_stop() 