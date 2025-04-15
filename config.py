from dataclasses import dataclass
from environs import Env
from typing import List


@dataclass
class Config:
    token: str
    managers: List[int]     # Список ID всех менеджеров
    admin_manager_id: int   # ID главного менеджера (администратора)


@dataclass
class DatabaseConfig:
    database: str = "support_bot.db"


@dataclass
class TgBot:
    config: Config
    db: DatabaseConfig


def load_config() -> TgBot:
    env = Env()
    env.read_env()

    # Получаем список ID менеджеров из переменной окружения
    # Формат: "ID1,ID2,ID3"
    managers_str = env.str("MANAGERS_IDS", "")
    managers_ids = [int(manager_id.strip()) for manager_id in managers_str.split(",") if manager_id.strip()]
    
    # Если список менеджеров пуст, используем значение MANAGER_ID
    if not managers_ids:
        try:
            manager_id = env.int("MANAGER_ID")
            managers_ids = [manager_id]
        except Exception:
            managers_ids = []
        
    # ID главного менеджера (администратора)
    admin_id = env.int("ADMIN_MANAGER_ID", managers_ids[0] if managers_ids else 0)

    return TgBot(
        config=Config(
            token=env.str("BOT_TOKEN"),
            managers=managers_ids,
            admin_manager_id=admin_id
        ),
        db=DatabaseConfig()
    )