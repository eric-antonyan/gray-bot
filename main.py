import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from motor.motor_asyncio import AsyncIOMotorClient
import requests
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
API_TOKEN = "7943946022:AAE45JUbp_36N2LinQqgZ_OMOLd7ul-oAqo"
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
    "/info ℹ️ Տեղեկություն բոտի մասին",
    "/help 💡 Ցույց տալ բոլոր հրամանները",
    "/webapp 🧠 Բացել GrayQuizz ծրագիրը",
    "/balance 💲 Տեսնել բալանսը",
    "/get_admins 🎩 Ցույց տալ բոտի ադմինիստրացիային",
    "/donate ☘️ Աջակցել մեզ",
    "/ref 🤝 Դարձիր գործընկեր",
    "/get_friends 🔑 Տեսնել միացած ընկերներին"
]

# Referral bonus
REFERRAL_BONUS = 10  # Amount to reward referrer for each successful referral

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

async def check_subscription(user_id):
    chat_member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
    return chat_member.status != 'left'

async def need_subscribe(message: types.Message):
    channel_link_button = InlineKeyboardButton(text="Հետևել➡️", url="https://t.me/cyber_gray")
    channel_link_keyboard = InlineKeyboardMarkup(inline_keyboard=[[channel_link_button]])
    await message.answer("⚠️ Բոտից օգտվելու համար անհրաժեշտ է հետևել մեր ալիքին.", reply_markup=channel_link_keyboard)

async def add_referral(user_id, referrer_id):
    referrer = await collection.find_one({"id": referrer_id})
    if referrer:
        # Update the referrer balance
        new_balance = referrer["balance"] + REFERRAL_BONUS
        await collection.update_one({"id": referrer_id}, {"$set": {"balance": new_balance}})
        logging.info(f"Referral bonus added to user {referrer_id}. New balance: {new_balance}")
        
        # Add the user to the referrer's referrals list
        await collection.update_one({"id": referrer_id}, {"$push": {"referrals": user_id}})
        logging.info(f"User {user_id} added to referrer {referrer_id}'s referral list.")

@dp.message(Command(commands=['ref']))
async def ref(message: types.Message):
    user_id = message.from_user.id
    is_subscribed = await check_subscription(user_id)

    if not is_subscribed:
        await need_subscribe(message)
    else:
        await message.answer(f"Հրավիրիր ընկերներիդ GrayQuizz🧠 և ստացիր հավելյալ 10FMM ամեն նոր մասնակցի համար \nԿիսվիր այս հղումով ➡️ https://t.me/GrayQuizz_Bot?start={user_id}")
        referral_link = f"https://t.me/GrayQuizz_Bot?start={user_id}"
        share_button = InlineKeyboardButton(text="Կիսվել", switch_inline_query=referral_link)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[share_button]])

        await message.reply(f"Կիսվիր ընկերոջդ հետ՝\n{referral_link}", reply_markup=keyboard)

@dp.message(Command(commands=['start']))
async def start(message: types.Message):
    user_id = message.from_user.id
    parts = message.text.split(maxsplit=1)
    referrer_id = parts[1] if len(parts) > 1 else None
    is_subscribed = await check_subscription(user_id)

    if not is_subscribed:
        await need_subscribe(message)
    else:
        last_name = message.from_user.last_name or ''


        photo_url = await get_user_photo(user_id)
        user_data = {
            "id": user_id,
            "first_name": message.from_user.first_name,
            "last_name": last_name,
            "username": message.from_user.username,
            "balance": 0,
            "photo_url": photo_url,
            "referrals": []  # Add referrals field to store referred users
        }

        existing_user = await collection.find_one({"id": user_id})
        if existing_user is None:
            await collection.insert_one(user_data)
            logging.info(f"New user added: {user_data}")
            await message.reply(f"Դուք հաջողությամբ գրանցվեցիք հարգելի {message.from_user.first_name}")
            if referrer_id:
                await add_referral(user_id, int(referrer_id))
        await message.answer(
            f"👋👁️‍🗨️Ողջույն!\n⚡Այստեղ կարող ես ստուգել գիտելիքներդ Կիբեռանվտանգության և ՏՏ ոլորտի մասին։\n💡 Օգտագործեք /help որպեսզի տեսնեք բոլոր հրամաննները.\n\n👤ID: {user_id}\n🛂Օգտվողի անուն: @{message.from_user.username}"
        )

@dp.message(Command(commands=['get_friends']))
async def get_friends(message: types.Message):
    user_id = message.from_user.id
    is_subscribed = await check_subscription(user_id)

    if not is_subscribed:
        await need_subscribe(message)
    else:
        user = await collection.find_one({"id": user_id})
        if user:
            referrals = user.get("referrals", [])
            if referrals:
                friends = await collection.find({"id": {"$in": list(set(referrals))}}).to_list(length=None)

                friend_names = [f"{friend['first_name']} {friend.get('last_name', '')}" for friend in friends]
                if friend_names:
                    await message.answer(f"🎉 Ձեր ընկերները, ովքեր գրանցվել են ձեր հղումով: \n\n" + "\n => ".join(friend_names))
                else:
                    await message.answer(f"Ձեր հղումով ոչ մի ընկեր չի գրանցվել.\n➡️ Կիսվիր այս հղումով ՝ https://t.me/GrayQuizz_Bot?start={user_id}")
            else:
                await message.answer(f"Ձեր հղումով ոչ մի ընկեր չի գրանցվել ➡️ Կիսվիր այս հղումով ՝ https://t.me/GrayQuizz_Bot?start={user_id}")
        else:
            await message.answer("User not found. Please use /start to register.")


@dp.message(Command(commands=['info']))
async def info_command(message: types.Message):
    user_id = message.from_user.id
    is_subscribed = await check_subscription(user_id)

    if not is_subscribed:
        await need_subscribe(message)
    else:
        commands_list = "\n".join(available_commands)
        await message.answer(f"ℹ️ Բոտի Մասին\n\n🔰Հասանելի հրամաններ:\n{commands_list}")

@dp.message(Command(commands=['help']))
async def help_command(message: types.Message):
    user_id = message.from_user.id
    is_subscribed = await check_subscription(user_id)

    if not is_subscribed:
        await need_subscribe(message)
    else:
        commands_list = "\n".join(available_commands)
        await message.answer(f"🔰Հասանելի հրամաններ:\n{commands_list}")

@dp.message(Command(commands=['balance']))
async def get_balance(message: types.Message):
    user_id = message.from_user.id
    is_subscribed = await check_subscription(user_id)

    if not is_subscribed:
        await need_subscribe(message)
    else:
        user = await collection.find_one({"id": user_id})
        if user:
            await message.answer(f'👤Հարգելի {user["first_name"]},\n💲Ձեր հաշվի վրա տվյալ պահին կա: {user["balance"]} FMM🪙')
        else:
            await message.answer("User not found. Please use /start to register.")

@dp.message(Command(commands=['webapp']))
async def webapp_command(message: types.Message):
    user_id = message.from_user.id
    is_subscribed = await check_subscription(user_id)

    if not is_subscribed:
        await need_subscribe(message)
    else:
        web_app = WebAppInfo(url="https://gray-quiz.vercel.app/account")
        button = InlineKeyboardButton(text="Բացել GrayQuizz-ը", web_app=web_app)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])

        bot_link_button = InlineKeyboardButton(text="Բացել bot-ը", url="https://t.me/GrayQuizz_bot")
        bot_link_keyboard = InlineKeyboardMarkup(inline_keyboard=[[bot_link_button]])
 
        try:
            await message.answer("🤖Սեղմեք կոճակին որպեսզի սկսեք GrayQuizz-ը:", reply_markup=keyboard)
        except Exception as e:
            logging.error(f"Failed to send message with web app button: {e}")
            await message.answer("➡️Խնդրում ենք բացել bot֊ով", reply_markup=bot_link_keyboard)

@dp.message(Command(commands=['get_admins']))
async def get_admins(message: types.Message):
    user_id = message.from_user.id
    is_subscribed = await check_subscription(user_id)

    if not is_subscribed:
        await need_subscribe(message)
    else:
        admins = ["@mrgrayofficial", "@Art_Movsisyan", "@netfaca", "@Sinatra_47"]
        admin_list = [f"🔴 {admin}" for admin in admins]
        await message.answer("🎩Բոտի ադմինիստրացիան\n" + "\n".join(admin_list))

@dp.message(Command(commands=['donate']))
async def donate_command(message: types.Message):
    user_id = message.from_user.id
    is_subscribed = await check_subscription(user_id)
    if not is_subscribed:
        await need_subscribe(message)
    else:
        await message.answer(
            "💖 Նպաստեք մեր բոտին\n\n📬 Կրիպտո հասցե\n\n"
            "Ethereum(BEP20): 0xd303f5d69ef6fa90ddbbe2d0f943175db40ecc1d\n\n"
            "Bitcoin(BEP20): 0xd303f5d69ef6fa90ddbbe2d0f943175db40ecc1d\n\n"
            "USDT(TRX20): TNwAA2qBC9Wirr5dfhwp12sii3wFwzCJHE\n"
            "\n🙏 Ձեր աջակցության շնորհիվ մենք կարող ենք շարունակել զարգացնել և բարելավել մեր բոտը"
        )

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
