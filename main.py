import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from motor.motor_asyncio import AsyncIOMotorClient
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
API_TOKEN = '7943946022:AAE45JUbp_36N2LinQqgZ_OMOLd7ul-oAqo'
CHANNEL_ID = "@cyber_gray"  # Your channel's username
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

MONGO_URI = "mongodb+srv://antonyaneric:Erik$2008@cluster0.hfvu6sp.mongodb.net/grayquizz?retryWrites=true&w=majority&appName=Cluster0"
client = AsyncIOMotorClient(MONGO_URI)
db = client.grayquizz
collection = db.users

# List of available commands
available_commands = [
    "/start 🔁 Գործարկել բոտը",
    "/help 💡 Ցույց տալ բոլոր հրամանները",
    "/webapp 🧠 Բացել GrayQuizz ծրագիրը",
    "/balance 💲 Տեսնել բալանսը",
    "/get_admins 🎩 Ցույց տալ բոտի ադմինիստրացիային"
]


async def check_subscription(user_id):
    """Check if a user is subscribed to the channel."""
    chat_member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
    return chat_member.status != 'left'


async def get_user_photo(user_id):
    """Fetch the user's profile photo URL, if available."""
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


# Command handler for /start
@dp.message(Command(commands=['start']))
async def start(message: types.Message):
    user_id = message.from_user.id
    is_subscribed = await check_subscription(user_id)

    if not is_subscribed:

        subscribe_button = InlineKeyboardButton("Հետևել➡️", url="https://t.me/cyber_gray")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[subscribe_button]])
        await message.answer("⚠️ Բոտից օգտվելու համար անհրաժեշտ է հետևել մեր ալիքին.", reply_markup=keyboard)
        return

    last_name = message.from_user.last_name or ''
    await message.answer(
        f"👋👁️‍🗨️Ողջույն!\n⚡Այստեղ կարող ես ստուգել գիտելիքներդ Կիբեռանվտանգության և ՏՏ ոլորտի մասին։\n💡 Օգտագործեք /help որպեսզի տեսնեք բոլոր հրամաննները.\n\n👤ID: {user_id}\n🛂Օգտվողի անուն: @{message.from_user.username}")

    photo_url = await get_user_photo(user_id)
    user_data = {
        "id": user_id,
        "first_name": message.from_user.first_name,
        "last_name": last_name,
        "username": message.from_user.username,
        "balance": 0,
        "photo_url": photo_url
    }

    existing_user = await collection.find_one({"id": user_id})
    if existing_user is None:
        await collection.insert_one(user_data)
        logging.info(f"New user added: {user_data}")
        await message.reply(f"Դուք հաջողությամբ գրանցվեցիք հարգելի {message.from_user.first_name}")


@dp.message(Command(commands=['help']))
async def help_command(message: types.Message):
    commands_list = "\n".join(available_commands)
    await message.answer(f"🔰Հասանելի հրամաններ:\n{commands_list}")


@dp.message(Command(commands=['balance']))
async def get_balance(message: types.Message):
    user = await collection.find_one({"id": message.from_user.id})
    if user:
        await message.answer(f'👤Հարգելի {user["first_name"]},\n💲Ձեր հաշվի վրա տվյալ պահին կա: {user["balance"]} FMM🪙')
    else:
        await message.answer("User not found. Please use /start to register.")


@dp.message(Command(commands=['webapp']))
async def webapp_command(message: types.Message):
    web_app = WebAppInfo(url="https://gray-quiz.vercel.app/account")
    button = InlineKeyboardButton(text="Բացել խաղը", web_app=web_app)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])

    bot_link_button = InlineKeyboardButton(text="Բացել bot-ը", url="https://t.me/GrayQuizz_bot")
    bot_link_keyboard = InlineKeyboardMarkup(inline_keyboard=[[bot_link_button]])

    try:
        await message.answer("🤖Սեղմեք կոճակին որպեսզի սկսեք խաղը:", reply_markup=keyboard)
    except Exception as e:
        logging.error(f"Failed to send message with web app button: {e}")
        await message.answer("➡️Խնդրում ենք բացել bot֊ով", reply_markup=bot_link_keyboard)


@dp.message(Command(commands=['get_admins']))
async def get_admins(message: types.Message):
    admins = ["@mrgrayofficial", "@Art_Movsisyan", "@antonyandev", "@Sinatra_887"]
    admin_list = [f"🔴 @{admin}" for admin in admins]
    await message.answer("🎩Բոտի ադմինիստրացիան\n" + "\n".join(admin_list))


# Main function to start the bot
async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
