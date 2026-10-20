import asyncio
import os
import pandas as pd
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.filters import CommandStart
from scraper import parser_pravda_news

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# User language memory (user_id -> lang_code)
user_langs = {}

# Dictionary with all translations
TEXTS = {
    'en': {
        'welcome': "👋 Welcome! Please choose your language:",
        'main_menu': "Language selected: English! 🇬🇧\nChoose an action from the menu below:",
        'btn_scrape': "📥 Scrape Data",
        'btn_change_lang': "⚙️ Change Language",
        'loading': "⏳ Running the scraper... Gathering the latest news, please wait...",
        'error': "❌ Failed to retrieve data. The website might be down.",
        'success': "✅ Done! Total records collected: {}",
        'col_title': 'Title', 'col_link': 'Link', 'col_date': 'Date'
    },
    'uk': {
        'welcome': "👋 Вітаю! Будь ласка, оберіть мову:",
        'main_menu': "Мову обрано: Українська! 🇺🇦\nОберіть дію в меню нижче:",
        'btn_scrape': "📥 Зібрати дані",
        'btn_change_lang': "⚙️ Змінити мову",
        'loading': "⏳ Запускаю скрапер... Збираю свіжі новини, зачекайте...",
        'error': "❌ Не вдалося отримати дані. Можливо, сайт недоступний.",
        'success': "✅ Готово! Зібрано новин: {}",
        'col_title': 'Заголовок', 'col_link': 'Посилання', 'col_date': 'Дата'
    },
    'ru': {
        'welcome': "👋 Добро пожаловать! Пожалуйста, выберите язык:",
        'main_menu': "Язык выбран: Русский! 🇷🇺\nВыберите действие в меню ниже:",
        'btn_scrape': "📥 Собрать данные",
        'btn_change_lang': "⚙️ Сменить язык",
        'loading': "⏳ Запускаю парсер... Собираю свежие новости, подождите...",
        'error': "❌ Не удалось получить данные. Возможно, сайт недоступен.",
        'success': "✅ Готово! Собрано новостей: {}",
        'col_title': 'Заголовок', 'col_link': 'Ссылка', 'col_date': 'Дата'
    }
}

# Helper function to create language selection keyboard
def get_lang_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇬🇧 English"), KeyboardButton(text="🇺🇦 Українська"), KeyboardButton(text="🇷🇺 Русский")]
        ],
        resize_keyboard=True, # Makes buttons smaller and neat
        input_field_placeholder="Choose language..."
    )

# Helper function to create main menu keyboard based on language
def get_main_keyboard(lang):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=TEXTS[lang]['btn_scrape'])],
            [KeyboardButton(text=TEXTS[lang]['btn_change_lang'])]
        ],
        resize_keyboard=True
    )

# Handle /start command
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    # Send welcome text and show language buttons at the bottom
    await message.answer(TEXTS['en']['welcome'], reply_markup=get_lang_keyboard())

# Handle language selection
@dp.message(F.text.in_(["🇬🇧 English", "🇺🇦 Українська", "🇷🇺 Русский"]))
async def set_language(message: types.Message):
    # Determine which language code corresponds to the pressed button
    if message.text == "🇬🇧 English":
        lang = 'en'
    elif message.text == "🇺🇦 Українська":
        lang = 'uk'
    else:
        lang = 'ru'
        
    # Save user language
    user_langs[message.from_user.id] = lang
    
    # Show main menu with new language buttons
    await message.answer(TEXTS[lang]['main_menu'], reply_markup=get_main_keyboard(lang))

# Handle 'Change Language' button
@dp.message(F.text.in_([TEXTS['en']['btn_change_lang'], TEXTS['uk']['btn_change_lang'], TEXTS['ru']['btn_change_lang']]))
async def change_language(message: types.Message):
    # Bring back the language selection keyboard
    await message.answer(TEXTS['en']['welcome'], reply_markup=get_lang_keyboard())

# Handle 'Scrape Data' button
@dp.message(F.text.in_([TEXTS['en']['btn_scrape'], TEXTS['uk']['btn_scrape'], TEXTS['ru']['btn_scrape']]))
async def handle_scraping(message: types.Message):
    # Get user language (default to English if not set)
    lang = user_langs.get(message.from_user.id, 'en')
    texts = TEXTS[lang]
    
    # Notify user that parsing has started
    status_msg = await message.answer(texts['loading'])

    # 1. Run the parser
    news_data = parser_pravda_news()

    # Check for errors
    if not news_data:
        await status_msg.edit_text(texts['error'])
        return

    # 2. Create DataFrame and rename columns based on language
    df = pd.DataFrame(news_data)
    df.rename(columns={
        'title': texts['col_title'], 
        'link': texts['col_link'], 
        'date': texts['col_date']
    }, inplace=True)

    # 3. Save to Excel with auto-width columns
    file_name = "parsed_news.xlsx"
    with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Latest News')
        worksheet = writer.sheets['Latest News']
        worksheet.column_dimensions['A'].width = 80
        worksheet.column_dimensions['B'].width = 60
        worksheet.column_dimensions['C'].width = 15

    # 4. Send the file
    document = FSInputFile(file_name)
    await message.answer_document(document, caption=texts['success'].format(len(news_data)))
    
    # 5. Delete temporary status message and file
    await status_msg.delete()
    os.remove(file_name)

# Main launch function
async def main():
    print("Bot is successfully running and waiting for messages...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())