from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import sqlite3
import time

API_TOKEN = "7961024836:AAG2CdnIw0ZIFHpIPbYkn2b2_X7yVxFlqGQ"
ESCROW_TON_ADDRESS = "UQBtClvwxxsjEpig1jPb-VSpxi3DinSyEq3mchLM0ONd-YKm"
ESCROW_TRC20_ADDRESS = "TNiFv8226EQn1HsQZKkewd7tzEVofXaFH6"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

conn = sqlite3.connect("deals.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS deals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id INTEGER,
    buyer_id INTEGER,
    asset TEXT,
    amount REAL,
    status TEXT,
    timestamp INTEGER
)
""")
conn.commit()

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("/create_deal"), KeyboardButton("/status"))
    await message.answer("🤖 Привет! Я OTC бот-гарант. Используй /create_deal, чтобы начать.", reply_markup=kb)

@dp.message_handler(commands=["create_deal"])
async def create_deal(message: types.Message):
    await message.answer("✍️ Введите данные сделки в формате:

asset amount buyer_id

Пример:
TON 50 8110009397")

@dp.message_handler(lambda message: len(message.text.split()) == 3 and message.text.split()[0].upper() in ["TON", "USDT"])
async def parse_deal(message: types.Message):
    try:
        asset, amount, buyer_id = message.text.split()
        amount = float(amount)
        buyer_id = int(buyer_id)
        cursor.execute("INSERT INTO deals (seller_id, buyer_id, asset, amount, status, timestamp) VALUES (?, ?, ?, ?, ?, ?)", (
            message.from_user.id, buyer_id, asset.upper(), amount, "waiting_payment", int(time.time())
        ))
        conn.commit()
        pay_address = ESCROW_TON_ADDRESS if asset.upper() == "TON" else ESCROW_TRC20_ADDRESS
        await message.answer(f"✅ Сделка создана!

Отправьте {amount} {asset.upper()} на адрес:

{pay_address}")
    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {str(e)}. Убедитесь, что вы ввели: asset amount buyer_id")

@dp.message_handler(commands=["release"])
async def release(message: types.Message):
    if message.from_user.id not in [8110009397]:  
        return await message.answer("⛔ Только гарант может использовать эту команду.")
    await message.answer("Введите ID сделки для перевода средств покупателю.")

@dp.message_handler(commands=["cancel"])
async def cancel(message: types.Message):
    if message.from_user.id not in [8110009397]: 
        return await message.answer("⛔ Только гарант может использовать эту команду.")
    await message.answer("Введите ID сделки для отмены и возврата продавцу.")

@dp.message_handler(commands=["status"])
async def status(message: types.Message):
    cursor.execute("SELECT * FROM deals WHERE seller_id=? OR buyer_id=? ORDER BY id DESC LIMIT 5", (
        message.from_user.id, message.from_user.id
    ))
    deals = cursor.fetchall()
    if not deals:
        return await message.answer("❌ У вас нет активных сделок.")
    msg = ""
    for deal in deals:
        msg += f"ID {deal[0]} | {deal[3]} {deal[4]} | Статус: {deal[5]}
"
    await message.answer(msg)

if name == "__main__":
    executor.start_polling(dp, skip_updates=True)
