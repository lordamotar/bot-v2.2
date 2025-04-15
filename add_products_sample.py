#!/usr/bin/env python
"""
Скрипт для добавления тестовых товаров в базу данных.
Запускать после создания базы данных.
"""

from database import Database
from config import load_config
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_sample_products():
    """Добавление тестовых товаров в базу данных"""
    # Загрузка конфигурации и инициализация базы данных
    config = load_config()
    db = Database(config.db.database)
    
    # Пример товаров для добавления
    products = [
        # Шины - Легковые
        {
            "category": "Шины",
            "subcategory": "Легковые",
            "type": None,
            "size": "R13",
            "product_name": "Летние шины R13",
            "description": "Качественные летние шины для легковых автомобилей",
            "price": "от 15 000 тг",
            "external_url": "https://example.com/tires/r13",
            "image_url": "https://i.ibb.co/k8HLmmR/tire-r13.jpg"
        },
        {
            "category": "Шины",
            "subcategory": "Легковые",
            "type": None,
            "size": "R14",
            "product_name": "Зимние шины R14",
            "description": "Зимние шины с шипами для повышенного сцепления с дорогой",
            "price": "от 18 000 тг",
            "external_url": "https://example.com/tires/r14",
            "image_url": "https://i.ibb.co/k8HLmmR/tire-r14.jpg"
        },
        {
            "category": "Шины",
            "subcategory": "Легковые",
            "type": None,
            "size": "R15",
            "product_name": "Всесезонные шины R15",
            "description": "Универсальные шины для любого сезона",
            "price": "от 20 000 тг",
            "external_url": "https://example.com/tires/r15",
            "image_url": "https://i.ibb.co/k8HLmmR/tire-r15.jpg"
        },
        
        # Шины - Грузовые
        {
            "category": "Шины",
            "subcategory": "Грузовые",
            "type": None,
            "size": "R17.5",
            "product_name": "Грузовые шины R17.5",
            "description": "Усиленные шины для малотоннажных грузовиков",
            "price": "от 45 000 тг",
            "external_url": "https://example.com/tires/truck/r17-5",
            "image_url": "https://i.ibb.co/k8HLmmR/truck-tire-r17-5.jpg"
        },
        {
            "category": "Шины",
            "subcategory": "Грузовые",
            "type": None,
            "size": "R22.5",
            "product_name": "Грузовые шины R22.5",
            "description": "Высокопрочные шины для большегрузных автомобилей",
            "price": "от 75 000 тг",
            "external_url": "https://example.com/tires/truck/r22-5",
            "image_url": "https://i.ibb.co/k8HLmmR/truck-tire-r22-5.jpg"
        },
        
        # Диски - Легкосплавные
        {
            "category": "Диски",
            "subcategory": "Легкосплавные",
            "type": None,
            "size": "R16",
            "product_name": "Легкосплавные диски R16",
            "description": "Стильные алюминиевые диски для легковых автомобилей",
            "price": "от 30 000 тг",
            "external_url": "https://example.com/wheels/alloy/r16",
            "image_url": "https://i.ibb.co/k8HLmmR/alloy-wheel-r16.jpg"
        },
        {
            "category": "Диски",
            "subcategory": "Легкосплавные",
            "type": None,
            "size": "R17",
            "product_name": "Легкосплавные диски R17",
            "description": "Премиальные алюминиевые диски",
            "price": "от 40 000 тг",
            "external_url": "https://example.com/wheels/alloy/r17",
            "image_url": "https://i.ibb.co/k8HLmmR/alloy-wheel-r17.jpg"
        },
        
        # Диски - Штампованные - Легковые
        {
            "category": "Диски",
            "subcategory": "Штампованные",
            "type": "Легковые",
            "size": "R14",
            "product_name": "Штампованные диски R14",
            "description": "Надежные штампованные диски для легковых автомобилей",
            "price": "от 12 000 тг",
            "external_url": "https://example.com/wheels/steel/car/r14",
            "image_url": "https://i.ibb.co/k8HLmmR/steel-wheel-r14.jpg"
        },
        {
            "category": "Диски",
            "subcategory": "Штампованные",
            "type": "Легковые",
            "size": "R15",
            "product_name": "Штампованные диски R15",
            "description": "Экономичное решение для большинства автомобилей",
            "price": "от 14 000 тг",
            "external_url": "https://example.com/wheels/steel/car/r15",
            "image_url": "https://i.ibb.co/k8HLmmR/steel-wheel-r15.jpg"
        },
        
        # Диски - Штампованные - Грузовые
        {
            "category": "Диски",
            "subcategory": "Штампованные",
            "type": "Грузовые",
            "size": "R17.5",
            "product_name": "Штампованные диски R17.5",
            "description": "Усиленные штампованные диски для малотоннажных грузовиков",
            "price": "от 25 000 тг",
            "external_url": "https://example.com/wheels/steel/truck/r17-5",
            "image_url": "https://i.ibb.co/k8HLmmR/steel-truck-wheel-r17-5.jpg"
        },
        {
            "category": "Диски",
            "subcategory": "Штампованные",
            "type": "Грузовые",
            "size": "R22.5",
            "product_name": "Штампованные диски R22.5",
            "description": "Прочные стальные диски для большегрузных автомобилей",
            "price": "от 40 000 тг",
            "external_url": "https://example.com/wheels/steel/truck/r22-5",
            "image_url": "https://i.ibb.co/k8HLmmR/steel-truck-wheel-r22-5.jpg"
        }
    ]
    
    # Добавление товаров в базу данных
    for product in products:
        try:
            success = db.add_product(
                category=product["category"],
                subcategory=product["subcategory"],
                type=product["type"],
                size=product["size"],
                product_name=product["product_name"],
                description=product["description"],
                price=product["price"],
                external_url=product["external_url"],
                image_url=product["image_url"]
            )
            if success:
                logger.info(f"Добавлен товар: {product['category']} {product['subcategory']} {product['size']}")
            else:
                logger.error(f"Ошибка добавления товара: {product['category']} {product['subcategory']} {product['size']}")
        except Exception as e:
            logger.error(f"Исключение при добавлении товара: {e}")
    
    logger.info("Добавление тестовых товаров завершено")


if __name__ == "__main__":
    add_sample_products() 