from aiogram import types
from database import Database
from keyboards.reply import (
    get_main_keyboard,
    get_catalog_categories_keyboard,
    get_catalog_subcategories_keyboard,
    get_catalog_types_keyboard,
    get_catalog_sizes_keyboard
)
import logging
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)

# Словари для хранения выбранных значений пользователя
user_catalog_selections = {}  # user_id -> {category, subcategory, type}


async def handle_catalog(message: types.Message, db: Database):
    """Обработка нажатия на кнопку 'Каталог'"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    logger.info(f"User {username} (ID: {user_id}) requested catalog")

    # Очищаем предыдущие выборы пользователя, если есть
    if user_id in user_catalog_selections:
        del user_catalog_selections[user_id]

    # Получаем список категорий из базы данных
    categories = db.get_product_categories()
    
    if not categories:
        await message.answer(
            "В каталоге пока нет товаров. Пожалуйста, вернитесь позже.",
            reply_markup=get_main_keyboard()
        )
        return
    
    await message.answer(
        "Выберите категорию товаров:",
        reply_markup=get_catalog_categories_keyboard(categories)
    )


async def handle_category_selection(message: types.Message, db: Database):
    """Обработка выбора категории товаров"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    category = message.text

    logger.info(f"User {username} (ID: {user_id}) selected category: {category}")

    # Сохраняем выбранную категорию
    user_catalog_selections[user_id] = {"category": category}

    # Получаем список подкатегорий для выбранной категории
    subcategories = db.get_product_subcategories(category)
    
    if not subcategories:
        await message.answer(
            f"В категории {category} пока нет товаров. Пожалуйста, выберите другую категорию.",
            reply_markup=get_catalog_categories_keyboard(db.get_product_categories())
        )
        return
    
    await message.answer(
        f"Выберите подкатегорию в категории {category}:",
        reply_markup=get_catalog_subcategories_keyboard(subcategories)
    )


async def handle_subcategory_selection(message: types.Message, db: Database):
    """Обработка выбора подкатегории товаров"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    subcategory = message.text

    logger.info(f"User {username} (ID: {user_id}) selected subcategory: {subcategory}")

    # Проверяем, что категория была выбрана ранее
    if user_id not in user_catalog_selections:
        await handle_catalog(message, db)
        return

    category = user_catalog_selections[user_id].get("category")
    if not category:
        await handle_catalog(message, db)
        return

    # Сохраняем выбранную подкатегорию
    user_catalog_selections[user_id]["subcategory"] = subcategory

    # Для дисков проверяем, есть ли типы
    if category == "Диски":
        types = db.get_product_types(category, subcategory)
        if types:
            # Сохраняем информацию и показываем типы
            await message.answer(
                f"Выберите тип дисков в подкатегории {subcategory}:",
                reply_markup=get_catalog_types_keyboard(types)
            )
            return

    # Если это не диски или у дисков нет типов, показываем размеры
    sizes = db.get_product_sizes(category, subcategory)
    
    if not sizes:
        await message.answer(
            f"В подкатегории {subcategory} пока нет размеров. "
            "Пожалуйста, выберите другую подкатегорию.",
            reply_markup=get_catalog_subcategories_keyboard(
                db.get_product_subcategories(category)
            )
        )
        return
    
    await message.answer(
        f"Выберите размер в подкатегории {subcategory}:",
        reply_markup=get_catalog_sizes_keyboard(sizes)
    )


async def handle_type_selection(message: types.Message, db: Database):
    """Обработка выбора типа товаров (только для дисков)"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    type_name = message.text

    logger.info(f"User {username} (ID: {user_id}) selected type: {type_name}")

    # Проверяем, что категория и подкатегория были выбраны ранее
    if (user_id not in user_catalog_selections or 
        "category" not in user_catalog_selections[user_id] or 
        "subcategory" not in user_catalog_selections[user_id]):
        await handle_catalog(message, db)
        return

    category = user_catalog_selections[user_id]["category"]
    subcategory = user_catalog_selections[user_id]["subcategory"]

    # Сохраняем выбранный тип
    user_catalog_selections[user_id]["type"] = type_name

    # Получаем размеры для выбранного типа
    sizes = db.get_product_sizes(category, subcategory, type_name)
    
    if not sizes:
        await message.answer(
            f"Для типа {type_name} пока нет размеров. Пожалуйста, выберите другой тип.",
            reply_markup=get_catalog_types_keyboard(
                db.get_product_types(category, subcategory)
            )
        )
        return
    
    await message.answer(
        f"Выберите размер для типа {type_name}:",
        reply_markup=get_catalog_sizes_keyboard(sizes)
    )


async def handle_size_selection(message: types.Message, db: Database):
    """Обработка выбора размера товаров"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    size = message.text

    logger.info(f"User {username} (ID: {user_id}) selected size: {size}")

    # Проверяем, что необходимые данные были выбраны ранее
    if (user_id not in user_catalog_selections or 
        "category" not in user_catalog_selections[user_id] or 
        "subcategory" not in user_catalog_selections[user_id]):
        await handle_catalog(message, db)
        return

    category = user_catalog_selections[user_id]["category"]
    subcategory = user_catalog_selections[user_id]["subcategory"]
    type_name = user_catalog_selections[user_id].get("type")  # Может быть None

    # Получаем товары по выбранным параметрам
    products = db.get_products_by_params(category, subcategory, type_name, size)
    
    if not products:
        await message.answer(
            f"К сожалению, товары для размера {size} не найдены. Пожалуйста, выберите другой размер.",
            reply_markup=get_catalog_sizes_keyboard(
                db.get_product_sizes(category, subcategory, type_name)
            )
        )
        return

    # Если есть несколько товаров, показываем кнопки со ссылками на каждый товар
    if len(products) > 1:
        inline_buttons = []
        for product in products:
            product_id, product_name, description, price, external_url, image_url = product
            button_text = product_name if product_name else f"Товар {product_id}"
            inline_buttons.append([InlineKeyboardButton(text=button_text, url=external_url)])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=inline_buttons)
        await message.answer(
            "Перейдите на сайт для просмотра товаров:",
            reply_markup=keyboard
        )
    else:
        # Если только один товар, просто даем ссылку
        product_id, product_name, description, price, external_url, image_url = products[0]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Перейти на сайт", url=external_url)]
        ])
        await message.answer(
            "Перейдите на сайт для просмотра товара:",
            reply_markup=keyboard
        )
    
    # После отправки ссылки, отправляем сообщение с возможностью вернуться
    back_text = "Хотите посмотреть другие товары?"
    
    # В зависимости от уровня навигации определяем, куда вернуться
    if type_name:
        # Если был выбран тип, возвращаемся к выбору размера для того же типа
        sizes = db.get_product_sizes(category, subcategory, type_name)
        await message.answer(
            back_text,
            reply_markup=get_catalog_sizes_keyboard(sizes)
        )
    else:
        # Если тип не выбирался, возвращаемся к выбору размера для той же подкатегории
        sizes = db.get_product_sizes(category, subcategory)
        await message.answer(
            back_text,
            reply_markup=get_catalog_sizes_keyboard(sizes)
        )


async def handle_back_to_categories(message: types.Message, db: Database):
    """Обработка возврата к списку категорий"""
    user_id = message.from_user.id
    
    # Очищаем выбор пользователя
    if user_id in user_catalog_selections:
        del user_catalog_selections[user_id]
    
    # Возвращаемся к списку категорий
    await handle_catalog(message, db)


async def handle_back_to_subcategories(message: types.Message, db: Database):
    """Обработка возврата к списку подкатегорий"""
    user_id = message.from_user.id
    
    # Проверяем, что категория была выбрана
    if user_id not in user_catalog_selections or "category" not in user_catalog_selections[user_id]:
        await handle_catalog(message, db)
        return
    
    category = user_catalog_selections[user_id]["category"]
    
    # Удаляем выбор подкатегории и типа, если есть
    if "subcategory" in user_catalog_selections[user_id]:
        del user_catalog_selections[user_id]["subcategory"]
    if "type" in user_catalog_selections[user_id]:
        del user_catalog_selections[user_id]["type"]
    
    # Получаем список подкатегорий и отображаем их
    subcategories = db.get_product_subcategories(category)
    await message.answer(
        f"Выберите подкатегорию в категории {category}:",
        reply_markup=get_catalog_subcategories_keyboard(subcategories)
    )


async def handle_back_from_sizes(message: types.Message, db: Database):
    """Обработка возврата от выбора размера"""
    user_id = message.from_user.id
    
    # Проверяем, что необходимые данные были выбраны
    if user_id not in user_catalog_selections:
        await handle_catalog(message, db)
        return
    
    category = user_catalog_selections[user_id].get("category")
    subcategory = user_catalog_selections[user_id].get("subcategory")
    type_name = user_catalog_selections[user_id].get("type")
    
    if not category or not subcategory:
        await handle_catalog(message, db)
        return
    
    # Если был выбран тип, возвращаемся к выбору типа
    if type_name:
        types = db.get_product_types(category, subcategory)
        if types:
            await message.answer(
                f"Выберите тип дисков в подкатегории {subcategory}:",
                reply_markup=get_catalog_types_keyboard(types)
            )
            # Удаляем выбор типа
            del user_catalog_selections[user_id]["type"]
            return
    
    # В противном случае возвращаемся к выбору подкатегории
    await handle_back_to_subcategories(message, db) 