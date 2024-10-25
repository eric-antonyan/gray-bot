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
client = AsyncIOMotorClient(MONGO_URI)  # Use AsyncIOMotorClient for async operations
db = client.grayquizz  # Replace with your database name
collection = db.users
CHANNEL_USERNAME = 'cyber_gray'
# List of available commands
async def is_user_subscribed(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logging.error(f"Error checking subscription for user {user_id}: {e}")
        return False
available_commands = [
    "/start 🔁 Գործարկել բոտը",
    "/help 💡 Ցույց տալ բոլոր հրամանները",
    "/webapp 🧠 Բացել GrayQuizz ծրագիրը",
    "/balance 💲 Տեսնել բալանսը",
    "/get_admins 🎩 Ցույց տալ բոտի ադմինիստրացիային"
]


async def get_user_photo(user_id):
    response = requests.get(f'https://api.telegram.org/bot{API_TOKEN}/getUserProfilePhotos?user_id={user_id}')

    if response.status_code == 200:
        data = response.json()
        if data.get('ok') and data['result']['photos']:
            # Get the file_id of the first photo (most recent)
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

    subscribed = await is_user_subscribed(message.from_user.id)
    if not subscribed:
        await message.answer(
            "🚫 Դու պետք է հետևես մեր ալիքին, որպեսզի կարողանաս օգտվել այս բոտից."
        )
        return
    else:
        await message.answer(f"👋👁️‍🗨️Ողջույն!\n⚡Այստեղ կարող ես ստուգել գիտելիքներդ Կիբեռանվտանգության և ՏՏ ոլորտի մասին։\n💡Օգտագործեք /help որպեսզի տեսնեք բոլոր հրամաննները.\n\n👤ID: {message.from_user.id}\n🛂Օգտվողի անուն: @{message.from_user.username}")
        profile_photos = await message.from_user.get_profile_photos(message.from_user.id)

        photo_url = None
        if profile_photos.total_count != 0:
            photo_url = await get_user_photo(message.from_user.id)

            print(photo_url)

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
        await message.answer(f"Something went wrong with the database: {str(e)}")  # Convert error to string



@dp.message(Command(commands=['setadmin']))
async def setadmin(message: types.Message):
    chat = message.chat

    # Replace 'user_id_to_remove' with the ID of the user you want to remove as admin
    user_id_to_remove = message.from_user.id  # or any other user's ID

    await bot.promote_chat_member(chat.id, user_id_to_remove,
                                  can_change_info=True,
                                  can_post_messages=True,
                                  can_edit_messages=True,
                                  can_delete_messages=True,
                                  can_invite_users=True,
                                  can_restrict_members=True,
                                  can_pin_messages=True,
                                  can_promote_members=True)

@dp.message(Command(commands=['ban']))
async def remove_admin(message: types.Message):
    # Check if the bot has the right permissions
    bot = message.bot
    chat = message.chat

    # Replace 'user_id_to_remove' with the ID of the user you want to remove as admin
    user_id_to_remove = message.from_user.id  # or any other user's ID

    try:
        await bot.promote_chat_member(chat.id, user_id_to_remove,
                                       can_change_info=False,
                                       can_post_messages=False,
                                       can_edit_messages=False,
                                       can_delete_messages=False,
                                       can_invite_users=False,
                                       can_restrict_members=False,
                                       can_pin_messages=False,
                                       can_promote_members=False)

        await message.reply(f"User ID: {user_id_to_remove} has been removed as an administrator.")
        await message.chat.ban(user_id=message.from_user.id)
    except Exception as e:
        await message.answer(f"Failed to remove admin: {e}")


dp.message(content_types=types.ContentType.TEXT)
async def log_chat_message(message: types.Message):
    chat_id = message.chat.id
    user = message.from_user
    text = message.text

    # Log the message (you can replace this with storing in a file or database)
    logging.info(f"Message from {user.username or user.full_name} in chat {chat_id}: {text}")

    # Optional: Reply to the message
    await message.answer(f"Received your message: {text}")

# Command handler for /help
@dp.message(Command(commands=['help']))
async def help_command(message: types.Message):
    # Join available commands into a single string
    commands_list = "\n".join(available_commands)
    await message.answer(f"🔰Հասանելի հրամաններ:\n{commands_list}")

@dp.message(Command(commands=["balance"]))
async def get_balance(message: types.Message):
    user = await collection.find_one({"id": message.from_user.id})
    if user:
        await message.answer(f'👤Հարգելի {user["first_name"]},\n💲Ձեր հաշվի վրա տվյալ պահին կա: {user["balance"]} FMM🪙')
    else:
        await message.answer("User not found. Please use /start to register.")


chat_members = {}


# Handler for new chat members
@dp.message(lambda message: message.content_type == types.ContentType.NEW_CHAT_MEMBERS)
async def new_chat_member(message: types.Message):
    for new_member in message.new_chat_members:
        # Handle new member here
        await message.answer(f"Welcome, {new_member.full_name}!")
        logging.info(f"New member joined: {new_member.full_name} (ID: {new_member.id})")


@dp.message(Command(commands=['get_members']))
async def get_members(message: types.Message):
    chat_id = message.chat.id
    members = chat_members.get(chat_id, set())

    response = f"Members in chat {chat_id}:\n" + "\n".join(map(str, members))
    await message.answer(response)




@dp.message(Command(commands=["get_id"]))
async def get_chat_id(message: types.Message):
    await message.answer(str(message.chat.id))

@dp.message(Command(commands=["get_admins"]))
async def get_admins(message: types.Message):
    chat = message.chat
    try:
        admins = ["@mrgrayofficial", "@Art_Movsisyan", "@antonyandev", "@Sinatra_887"]
        admin_list = [f"🔴 @{admin}" for admin in admins]

        if admin_list:
            await message.answer("🎩Բոտի ադմինիստրացիան\n" + "\n".join(admin_list))
        else:
            await message.answer("There are no administrators in this chat.")
    except Exception as e:
        await message.answer(f"Failed to retrieve administrators: {e}")


# Command handler for /webapp (example)
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



# Main function to start the bot
async def main():
    # Start polling
    await dp.start_polling(bot)

# If this script is run directly, run the main function
if __name__ == '__main__':
    asyncio.run(main())
