import asyncio
import json
import os
import time

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

# 🔑 Токен (лучше через переменные окружения)
TOKEN = os.getenv("BOT_TOKEN") or "ТВОЙ_ТОКЕН"

bot = Bot(token=TOKEN)
dp = Dispatcher()

DATA_FILE = "users.json"
COOLDOWN = 10  # секунд между заданиями

# 📡 Каналы
CHANNELS = [
    {"id": -1003877994893, "link": "https://t.me/+Hs8CEusLEvc1YjYx"},
    {"id": -1003981236439, "link": "https://t.me/+-gBUqAHwj7I4Y2My"},
]

# -------------------- 💾 ДАННЫЕ --------------------

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def get_user(user_id):
    data = load_data()
    user_id = str(user_id)

    if user_id not in data:
        data[user_id] = {
            "balance": 0,
            "last_claim": 0
        }
        save_data(data)

    return data[user_id]

def add_balance(user_id, amount):
    data = load_data()
    user_id = str(user_id)

    if user_id not in data:
        data[user_id] = {"balance": 0, "last_claim": 0}

    data[user_id]["balance"] += amount
    save_data(data)

def get_balance(user_id):
    return get_user(user_id)["balance"]

def set_last_claim(user_id):
    data = load_data()
    data[str(user_id)]["last_claim"] = time.time()
    save_data(data)

# -------------------- 🔐 ПОДПИСКА --------------------

async def check_sub(user_id):
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(channel["id"], user_id)
            if member.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True

def get_sub_keyboard():
    buttons = []

    for channel in CHANNELS:
        buttons.append([
            InlineKeyboardButton(text="📢 Подписаться", url=channel["link"])
        ])

    buttons.append([
        InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_sub")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.callback_query(F.data == "check_sub")
async def check_sub_handler(callback):
    if await check_sub(callback.from_user.id):
        await callback.message.answer("✅ Подписка подтверждена!")
    else:
        await callback.message.answer("❌ Подпишись на все каналы!")

# -------------------- 🧠 КНОПКИ --------------------

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💰 Заработать балл")],
        [KeyboardButton(text="💳 Мой баланс")],
        [KeyboardButton(text="🛒 Магазин")]
    ],
    resize_keyboard=True
)

# -------------------- 🚀 СТАРТ --------------------

@dp.message(Command("start"))
async def start(message: Message):
    if not await check_sub(message.from_user.id):
        await message.answer("❗ Подпишись на каналы:", reply_markup=get_sub_keyboard())
        return

    get_user(message.from_user.id)

    await message.answer(
        "Привет! Я Teen Money Star Bot!\nЗарабатывай баллы 👇",
        reply_markup=main_keyboard
    )

# -------------------- 💰 ЗАРАБОТОК --------------------

@dp.message(F.text == "💰 Заработать балл")
async def earn(message: Message):
    user = get_user(message.from_user.id)

    if not await check_sub(message.from_user.id):
        await message.answer("❗ Сначала подпишись!", reply_markup=get_sub_keyboard())
        return

    now = time.time()
    last = user.get("last_claim", 0)

    if now - last < COOLDOWN:
        wait = int(COOLDOWN - (now - last))
        await message.answer(f"⏳ Подожди {wait} сек")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📲 Перейти к заданию", url="ТВОЯ_ССЫЛКА")],
        [InlineKeyboardButton(text="✅ Я выполнил", callback_data="done_task")]
    ])

    await message.answer("📋 Выполни задание и нажми кнопку:", reply_markup=kb)

# -------------------- ✅ ВЫПОЛНИЛ --------------------

@dp.callback_query(F.data == "done_task")
async def done_task(callback):
    user_id = callback.from_user.id
    user = get_user(user_id)

    now = time.time()

    if now - user.get("last_claim", 0) < COOLDOWN:
        await callback.answer("⏳ Подожди!", show_alert=True)
        return

    add_balance(user_id, 1)
    set_last_claim(user_id)

    await callback.message.answer("⭐ Балл начислен!")

# -------------------- 💳 БАЛАНС --------------------

@dp.message(F.text == "💳 Мой баланс")
async def balance(message: Message):
    if not await check_sub(message.from_user.id):
        await message.answer("❗ Сначала подпишись!", reply_markup=get_sub_keyboard())
        return

    bal = get_balance(message.from_user.id)
    await message.answer(f"💰 Баланс: {bal}")

# -------------------- 🛒 МАГАЗИН --------------------

def shop_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Купить звезды", callback_data="stars")],
        [InlineKeyboardButton(text="💎 Telegram Premium", callback_data="premium")]
    ])

@dp.message(F.text == "🛒 Магазин")
async def shop(message: Message):
    if not await check_sub(message.from_user.id):
        await message.answer("❗ Сначала подпишись!", reply_markup=get_sub_keyboard())
        return

    await message.answer("🛒 Выбери:", reply_markup=shop_keyboard())

@dp.callback_query(F.data == "stars")
async def stars(callback):
    await callback.message.answer("⭐ В разработке")

@dp.callback_query(F.data == "premium")
async def premium(callback):
    await callback.message.answer("💎 В разработке")

# -------------------- ▶️ ЗАПУСК --------------------

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())