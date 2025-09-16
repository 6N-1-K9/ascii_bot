import os
import random
import logging
import pyfiglet
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters
)

# Включим логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния диалога
TEXT, CHOICE, FONT_NUMBER = range(3)

# Глобальные переменные для хранения данных пользователя
user_data = {}

# Создаем папку для сохранения файлов
STYLED_TEXT_DIR = "styled_text"
os.makedirs(STYLED_TEXT_DIR, exist_ok=True)

async def send_examples_file(update: Update) -> None:
    """Отправляет файл examples.txt пользователю."""
    try:
        examples_file = "examples.txt"
        if os.path.exists(examples_file):
            with open(examples_file, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=examples_file,
                    caption="📋 Примеры текстов для ASCII-арта"
                )
        else:
            await update.message.reply_text(
                "❌ Файл examples.txt не найден в папке проекта."
            )
    except Exception as e:
        logger.error(f"Ошибка при отправке файла examples: {e}")
        await update.message.reply_text(
            "❌ Ошибка при отправке файла с примерами."
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает диалог и просит ввести текст."""
    await update.message.reply_text(
        "🎨 Добро пожаловать в ASCII Art Bot!\n\n"
        "📝 Введите текст, который хотите преобразовать в ASCII-арт:",
        reply_markup=ReplyKeyboardRemove()
    )
    
    return TEXT

async def save_and_send_ascii_art(update: Update, user_text: str, font_name: str, ascii_art: str) -> None:
    """Сохраняет ASCII-арт в файл и отправляет пользователю."""
    try:
        # Создаем имя файла
        filename = f"ascii_art_{random.randint(1000, 9999)}.txt"
        filepath = os.path.join(STYLED_TEXT_DIR, filename)
        
        # Сохраняем в файл
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Текст: {user_text}\n")
            f.write(f"Шрифт: {font_name}\n")
            f.write("=" * 50 + "\n")
            f.write(ascii_art)
            f.write("=" * 50 + "\n")
        
        # Отправляем текстовое сообщение (без parse_mode для избежания ошибок разметки)
        if len(ascii_art) > 1000:
            # Для длинных текстов отправляем только информацию о шрифте
            await update.message.reply_text(
                f"✅ Шрифт: {font_name}\n\n"
                f"📝 Ваш текст слишком длинный для отображения в сообщении, "
                f"но он сохранен в файле ниже 👇",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            # Для коротких текстов отправляем как есть
            await update.message.reply_text(
                f"✅ Шрифт: {font_name}\n\n"
                f"📝 Ваш текст:\n<pre>{ascii_art}</pre>",
                parse_mode='HTML',
                reply_markup=ReplyKeyboardRemove()
            )
        
        # Отправляем файл
        with open(filepath, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=filename,
                caption=f"📁 Файл с вашим ASCII-артом\nШрифт: {font_name}"
            )
            
        await update.message.reply_text(
            "Хотите преобразовать другой текст? Введите его или используйте /start"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при сохранении/отправке файла: {e}")
        # Отправляем без parse_mode чтобы избежать ошибок разметки
        await update.message.reply_text(
            f"❌ Ошибка при создании файла: {e}\n\n"
            f"Но вот ваш текст:\n\n{ascii_art}\n\n"
            f"Шрифт: {font_name}"
        )

    return TEXT

async def get_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получаем текст от пользователя."""
    user_text = update.message.text
    chat_id = update.message.chat_id

    user_data[chat_id] = {'text': user_text}
    all_fonts = pyfiglet.FigletFont.getFonts()
    user_data[chat_id]['fonts'] = all_fonts

    keyboard = [
        ['🎲 Случайный шрифт', '🔢 Выбрать номером'],
        ['📋 Отправить примеры']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    await update.message.reply_text(
        f"✅ Текст получен: '{user_text}'\n\n"
        f"📊 Доступно шрифтов: {len(all_fonts)}\n\n"
        "Выберите способ выбора шрифта:",
        reply_markup=reply_markup
    )

    return CHOICE

async def random_font(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатываем выбор случайного шрифта."""
    chat_id = update.message.chat_id
    user_text = user_data[chat_id]['text']
    all_fonts = user_data[chat_id]['fonts']

    font_name = random.choice(all_fonts)

    try:
        ascii_art = pyfiglet.figlet_format(user_text, font=font_name)
        await save_and_send_ascii_art(update, user_text, font_name, ascii_art)
        
    except Exception as e:
        logger.error(f"Ошибка в random_font: {e}")
        await update.message.reply_text(
            f"❌ Ошибка при создании ASCII-арта: {e}\n\n"
            "Попробуйте другой шрифт или текст."
        )

    return ConversationHandler.END


async def choose_font_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запрашиваем номер шрифта."""
    chat_id = update.message.chat_id
    all_fonts = user_data[chat_id]['fonts']

    await update.message.reply_text(
        f"🔢 Введите номер шрифта (от 1 до {len(all_fonts)}):\n\n"
        "Популярные номера:\n"
        "1 - standard\n"
        "3 - slant\n"
        "4 - 3-d\n"
        "5 - bubble\n"
        "6 - block\n"
        "7 - doom",
        reply_markup=ReplyKeyboardRemove()
    )

    return FONT_NUMBER

async def send_examples(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатываем запрос на отправку примеров."""
    await send_examples_file(update)
    
    # Возвращаемся к выбору шрифта
    chat_id = update.message.chat_id
    user_text = user_data[chat_id]['text']
    all_fonts = user_data[chat_id]['fonts']

    keyboard = [
        ['🎲 Случайный шрифт', '🔢 Выбрать номером'],
        ['📋 Отправить примеры']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    await update.message.reply_text(
        f"📝 Ваш текст: '{user_text}'\n\n"
        "Выберите способ выбора шрифта:",
        reply_markup=reply_markup
    )

    return CHOICE

async def get_font_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатываем введенный номер шрифта."""
    chat_id = update.message.chat_id
    user_text = user_data[chat_id]['text']
    all_fonts = user_data[chat_id]['fonts']

    try:
        font_number = int(update.message.text)
        if 1 <= font_number <= len(all_fonts):
            font_name = all_fonts[font_number - 1]
            ascii_art = pyfiglet.figlet_format(user_text, font=font_name)
            
            await save_and_send_ascii_art(update, user_text, font_name, ascii_art)
            
        else:
            await update.message.reply_text(
                f"❌ Неверный номер! Введите число от 1 до {len(all_fonts)}"
            )
            return FONT_NUMBER

    except ValueError:
        await update.message.reply_text(
            "❌ Пожалуйста, введите число!"
        )
        return FONT_NUMBER

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена диалога."""
    user = update.message.from_user
    logger.info(f"Пользователь {user.first_name} отменил диалог.")

    await update.message.reply_text(
        "Диалог отменен. Используйте /start чтобы начать заново.",
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда помощи."""
    help_text = (
        "🤖 ASCII Art Bot Help\n\n"
        "Команды:\n"
        "/start - Начать создание ASCII-арта\n"
        "/help - Показать эту справку\n"
        "/cancel - Отменить текущий диалог\n\n"
        "Как использовать:\n"
        "1. Используйте /start\n"
        "2. Введите текст\n"
        "3. Выберите шрифт (случайный или по номеру)\n"
        "4. Получите красивый ASCII-арт + текстовый файл!\n\n"
        "Доступно более 500 различных шрифтов!"
    )

    await update.message.reply_text(help_text)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок."""
    logger.error(f"Ошибка: {context.error}")
    if update and update.message:
        await update.message.reply_text(
            "❌ Произошла ошибка. Попробуйте еще раз или используйте /start"
        )

def main() -> None:
    """Запуск бота."""
    # ИСПРАВЛЕННАЯ СТРОКА - используйте один из вариантов:
    
    # Вариант 1: Прямое указание токена
    token = '7916292269:AAGwFzx2RGdGMOaQlFSQEGnSMQFCkMmug0o'
    
    # Вариант 2: Через переменную окружения (предварительно установите её)
    # token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        logger.error("Не задан TELEGRAM_BOT_TOKEN!")
        return

    application = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_text)],
            CHOICE: [
                MessageHandler(filters.Regex('^🎲 Случайный шрифт$'), random_font),
                MessageHandler(filters.Regex('^🔢 Выбрать номером$'), choose_font_number),
                MessageHandler(filters.Regex('^📋 Отправить примеры$'), send_examples)
            ],
            FONT_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_font_number)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('cancel', cancel))
    application.add_error_handler(error_handler)

    print("🤖 Бот запущен! Нажмите Ctrl+C для остановки.")
    application.run_polling()

if __name__ == '__main__':
    main()