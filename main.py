import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
API_TOKEN = '7943946022:AAE45JUbp_36N2LinQqgZ_OMOLd7ul-oAqo'
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

MONGO_URI = "mongodb+srv://antonyaneric:Erik$2008@cluster0.hfvu6sp.mongodb.net/grayquizz?retryWrites=true&w=majority&appName=Cluster0"
client = AsyncIOMotorClient(MONGO_URI)
db = client.grayquizz
collection = db.users

# Your channel username (without @)
CHANNEL_USERNAME = 'cyber_gray'


# Function to check if a user is a member of the channel
async def is_user_subscribed(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        logging.info(f"Checked subscription for user_id {user_id}: {member.status}")
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logging.error(f"Error checking subscription for user {user_id}: {e}")
        return False



# Command handler for /start
@dp.message(Command(commands=['start']))
async def start(message: types.Message):
    # Check subscription
    subscribed = await is_user_subscribed(message.from_user.id)
    if not subscribed:
        await message.answer(
            "🚫 You need to subscribe to our channel to use this bot. Please subscribe and then use /start again."
        )
        return

    last_name = message.from_user.last_name if message.from_user.last_name is not None else ''
    await message.answer(
        f"👋👁️‍🗨️Ողջույն!\n⚡Այստեղ կարող եք ստուգել գիտելիքներդ Կիբեռանվտանգության և ՏՏ ոլորտի մասին։\n💡 օգտագործեք /help որպեսզի տեսնեք բոլոր հրամանները.\n\n👤ID: {message.from_user.id}\n🛂 Օգտվողի անուն: @{message.from_user.username}")

    profile_photos = await message.from_user.get_profile_photos(message.from_user.id)

    photo_url = None
    if profile_photos.total_count != 0:
        photo_url = await get_user_photo(message.from_user.id)

    user_data = {
        "id": message.from_user.id,
        "first_name": message.from_user.first_name,
        "last_name": message.from_user.last_name,
        "username": message.from_user.username,
        "balance": 0,
        "photo_url": photo_url
    }

    try:
        existing_user = await collection.find_one({"id": message.from_user.id})
        if existing_user is None:
            await collection.insert_one(user_data)
            logging.info(f"New user added: {user_data}")
            await message.reply(f"Դուք հաջողությամբ գրանցվեցիք հարգելի {message.from_user.first_name}")
    except Exception as e:
        logging.error(f"Error accessing MongoDB: {e}")
        await message.answer(f"Something went wrong with the database: {str(e)}")


# Command handler for /help
@dp.message(Command(commands=['help']))
async def help_command(message: types.Message):
    # Check subscription
    if not await is_user_subscribed(message.from_user.id):
        await message.answer(
            "🚫 You need to subscribe to our channel to use this bot. Please subscribe and then use /help again."
        )
        return

    commands_list = "\n".join([
        "/start 🔁 Գործարկել բոտը",
        "/help 💡 Ցույց տալ բոլոր հրամանները",
        "/webapp 🧠 Բացել GrayQuizz ծրագիրը",
        "/balance 💲 Տեսնել բալանսը",
        "/get_admins 🎩 Ցույց տալ բոտի ադմինիստրացիային"
    ])
    await message.answer(f"🔰 Հասանելի հրամաններ:\n{commands_list}")


@dp.message(Command(commands=["balance"]))
async def get_balance(message: types.Message):
    # Check subscription
    if not await is_user_subscribed(message.from_user.id):
        await message.answer(
            "🚫 You need to subscribe to our channel to use this bot. Please subscribe and then use /balance again."
        )
        return

    user = await collection.find_one({"id": message.from_user.id})
    if user:
        await message.answer(f'👤 Հարգելի {user["first_name"]},\n💲 Ձեր հաշվի վրա տվյալ պահին կա: {user["balance"]} FMM🪙')
    else:
        await message.answer("User not found. Please use /start to register.")


# Other command handlers with subscription check
@dp.message(Command(commands=['get_admins']))
async def get_admins(message: types.Message):
    # Check subscription
    if not await is_user_subscribed(message.from_user.id):
        await message.answer(
            "🚫 You need to subscribe to our channel to use this bot. Please subscribe and then use /get_admins again."
        )
        return

    try:
        admins = ["@mrgrayofficial", "@Art_Movsisyan", "@antonyandev", "@Sinatra_887"]
        admin_list = [f"🔴 @{admin}" for admin in admins]

        if admin_list:
            await message.answer("🎩 Բոտի ադմինիստրացիան\n" + "\n".join(admin_list))
        else:
            await message.answer("There are no administrators in this chat.")
    except Exception as e:
        await message.answer(f"Failed to retrieve administrators: {e}")


@dp.message(Command(commands=['webapp']))
async def webapp_command(message: types.Message):
    # Check subscription
    if not await is_user_subscribed(message.from_user.id):
        await message.answer(
            "🚫 You need to subscribe to our channel to use this bot. Please subscribe and then use /webapp again."
        )
        return

    web_app = WebAppInfo(url="https://gray-quiz.vercel.app/account")
    button = InlineKeyboardButton(text="Բացել խաղը", web_app=web_app)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])

    bot_link_button = InlineKeyboardButton(text="Բացել bot-ը", url="https://t.me/GrayQuizz_bot")
    bot_link_keyboard = InlineKeyboardMarkup(inline_keyboard=[[bot_link_button]])

    try:
        await message.answer("🤖 Սեղմեք կոճակին որպեսզի սկսեք խաղը:", reply_markup=keyboard)
    except Exception as e:
        logging.error(f"Failed to send message with web app button: {e}")
        await message.answer("➡️ Խնդրում ենք բացել bot֊ով", reply_markup=bot_link_keyboard)


# Other existing handlers...
@dp.message(lambda message: message.content_type == types.ContentType.NEW_CHAT_MEMBERS)
async def new_chat_member(message: types.Message):
    for new_member in message.new_chat_members:
        await message.answer(f"Welcome, {new_member.full_name}!")
        logging.info(f"New member joined: {new_member.full_name} (ID: {new_member.id})")


# Function to retrieve user profile photo
async def get_user_photo(user_id):
    response = requests.get(f'https://api.telegram.org/bot{API_TOKEN}/getUserProfilePhotos?user_id={user_id}')
    if response.status_code == 200:
        data = response.json()
        if data.get('ok') and data['result']['photos']:
            photo_file_id = data['result']['photos'][0][0]['file_id']
            file_response = requests.get(f'https://api.telegram.org/bot{API_TOKEN}/getFile?file_id={photo_file_id}')
            if file_response.status_code == 200:
                file_data = file_response.json()
                file_url = f'https://api.telegram.org/file/bot{API_TOKEN}/{file_data["result"]["file_path"]}'
                return file_url
    return None


# Main function to start the bot
async def main():
    await dp.start_polling(bot)


# If this script is run directly, run the main function
if __name__ == '__main__':
    asyncio.run(main())
