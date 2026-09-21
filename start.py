import os
import asyncio
import random
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import psycopg2
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import BotCommand, BotCommandScopeAllGroupChats

# =====================================================================
# 🌐 ВЕБ-СЕРВЕР ДЛЯ ОБМАНА ХОСТИНГА RENDER (ЧТОБЫ БОТ НЕ ВЫКЛЮЧАЛСЯ)
# =====================================================================
class WebServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), WebServer)
    server.serve_forever()

# Запускаем сайт-обманку в отдельном фоновом потоке, чтобы он не блокировал бота
threading.Thread(target=run_web_server, daemon=True).start()

# ==========================================
# ⚙️ НАСТРОЙКИ И ПОДКЛЮЧЕНИЕ К БАЗЕ
# ==========================================
ADMIN_ID = 8754245670  # Твой Telegram ID
DB_URL = os.environ.get("DATABASE_URL")

bot = Bot(token="8948607951:AAHIwQ3eZPedZbLAfiBhBGNwZBi05hStkQo")
dp = Dispatcher()

# Инициализация базы PostgreSQL
conn = psycopg2.connect(DB_URL)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        chat_id BIGINT,
        user_id BIGINT,
        username TEXT,
        size INTEGER DEFAULT 0,
        last_grow TEXT,
        PRIMARY KEY (chat_id, user_id)
    )
''')
conn.commit()

def get_clean_args(message_text: str) -> list:
    parts = message_text.split()
    if len(parts) < 2:
        return []
    return parts[1:]
async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="my", description="📏 Узнать размер своего пениса"),
        BotCommand(command="grow", description="Вырасти пиписю!"),
        BotCommand(command="top", description="Узнай рейтинг самых больших волын в чате"),
        BotCommand(command="pvp", description="Сражайся с пипирками друзей!"),
        BotCommand(command="give", description="Передать свои см другу"),
        BotCommand(command="menu", description="📱 Открыть меню кнопками"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeAllGroupChats())

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.reply(
        "👋 Привет! Добавь меня в группу, чтобы играть вместе с друзьями!\n\n"
        "📜 **Команды в чате:**\n"
        "📏 `/my` — узнать свой текущий размер\n"
        "📈 `/grow` или через `/menu` — вырастить агрегат\n"
        "🏆 `/top` — топ-200 участников чата\n"
        "🤝 `/give [кол-во]` — передать см (ответом на сообщение)\n"
        "🎲 `/pvp [кол-во]` — открытое казино на кубиках для всех",
        parse_mode=ParseMode.MARKDOWN
    )

@dp.message(Command("menu"))
async def cmd_menu(message: types.Message):
    if message.chat.type == "private":
        await message.reply("❌ Меню доступно только в групповых чатах!")
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="📏 Мой размер", callback_data="btn_my")
    builder.button(text="📈 Вырастить пиписю", callback_data="btn_grow")
    builder.button(text="🏆 Топ чата (200)", callback_data="top_page:0")
    builder.adjust(1)

    await message.answer(
        "📱 **Главное меню игры**\n\nНажимай на кнопки ниже, чтобы играть!",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.MARKDOWN
    )

@dp.message(Command("my"))
@dp.callback_query(F.data == "btn_my")
async def my_size_handler(event: types.Message | types.CallbackQuery):
    is_callback = isinstance(event, types.CallbackQuery)
    message = event.message if is_callback else event
    chat_id, user_id, username = message.chat.id, event.from_user.id, event.from_user.first_name

    if message.chat.type == "private":
        if is_callback: await event.answer()
        return

    cursor.execute("SELECT size FROM users WHERE chat_id = %s AND user_id = %s", (chat_id, user_id))
    row = cursor.fetchone()
    current_size = row[0] if row else 0

    text = f"📏 {username}, на данный момент длина твоего агрегата: **{current_size} см** 🍆"
    await message.answer(text, parse_mode=ParseMode.MARKDOWN)
    if is_callback: await event.answer()
@dp.message(Command("grow"))
@dp.callback_query(F.data == "btn_grow")
async def grow_handler(event: types.Message | types.CallbackQuery):
    is_callback = isinstance(event, types.CallbackQuery)
    message = event.message if is_callback else event
    chat_id, user_id, username, now = message.chat.id, event.from_user.id, event.from_user.first_name, datetime.now()

    if message.chat.type == "private":
        await message.reply("❌ Эта команда работает только в групповых чатах!")
        return

    cursor.execute("SELECT size, last_grow FROM users WHERE chat_id = %s AND user_id = %s", (chat_id, user_id))
    row = cursor.fetchone()

    if row:
        current_size, last_grow_str = row[0], row[1]
        if last_grow_str:
            last_grow = datetime.fromisoformat(last_grow_str)
            if now - last_grow < timedelta(hours=10):
                time_left = timedelta(hours=10) - (now - last_grow)
                hours, remainder = divmod(time_left.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                if is_callback: await event.answer(f"⏳ КД! Приходи через {hours}ч {minutes}м.", show_alert=True)
                else: await message.reply(f"⏳ Твой инструмент отдыхает! Приходи через {hours}ч {minutes}м.")
                return
    else: current_size = 0

    change = random.randint(0, 50)
    new_size = current_size + change

    cursor.execute("INSERT INTO users (chat_id, user_id, username, size, last_grow) VALUES (%s, %s, %s, %s, %s) ON CONFLICT(chat_id, user_id) DO UPDATE SET username = EXCLUDED.username, size = EXCLUDED.size, last_grow = EXCLUDED.last_grow", (chat_id, user_id, username, new_size, now.isoformat()))
    conn.commit()

    text = f"📈 {username}, твой болт вырос на **+{change} см**!\nТеперь он: **{new_size} см** 📏" if change > 0 else f"😐 {username}, в этот раз ничего не выросло. Размер по-прежнему: **{new_size} см** 📏"
    await message.answer(text, parse_mode=ParseMode.MARKDOWN)
    if is_callback: await event.answer()

@dp.message(Command("top"))
@dp.callback_query(F.data.startswith("top_page:"))
async def top_handler(event: types.Message | types.CallbackQuery):
    is_callback = isinstance(event, types.CallbackQuery)
    message = event.message if is_callback else event
    chat_id = message.chat.id
    
    # ТУТ ТЕПЕРЬ ВСЁ СТОИТ СТРОГО ПРАВИЛЬНО И КНОПКА БОЛЬШЕ НЕ ОШИБЁТСЯ
    page = int(event.data.split(":")[1]) if is_callback else 0
    per_page = 10

    cursor.execute("SELECT username, size FROM users WHERE chat_id = %s ORDER BY size DESC LIMIT 200", (chat_id,))
    rows = cursor.fetchall()

    if not rows:
        if is_callback: await event.answer("🏆 Список лидеров пока пуст!", show_alert=True)
        else: await message.reply("🏆 Список лидеров чата пока пуст!")
        return

    total_players = len(rows)
    total_pages = (total_players + per_page - 1) // per_page
    page_rows = rows[page * per_page : (page + 1) * per_page]

    top_text = f"🏆 **ТОП ЧАТА (Страница {page + 1}/{total_pages})**\nВсего участников: **{total_players}**\n\n"
    for i, (username, size) in enumerate(page_rows, page * per_page + 1):
        top_text += f"{i}. {username} — **{size} см**\n"

    builder = InlineKeyboardBuilder()
    if page > 0: builder.button(text="⬅️ Назад", callback_data=f"top_page:{page - 1}")
    if page < total_pages - 1: builder.button(text="Вперед ➡️", callback_data=f"top_page:{page + 1}")
    builder.adjust(2)

    if is_callback:
        await message.edit_text(top_text, reply_markup=builder.as_markup(), parse_mode=ParseMode.MARKDOWN)
        await event.answer()
    else:
        await message.answer(top_text, reply_markup=builder.as_markup(), parse_mode=ParseMode.MARKDOWN)
@dp.message(Command("give"))
async def cmd_give(message: types.Message):
    if not message.reply_to_message:
        await message.reply("❌ Ответь этой командой на сообщение того, кому хочешь передать см!")
        return
    chat_id, from_id, to_id = message.chat.id, message.from_user.id, message.reply_to_message.from_user.id
    if from_id == to_id:
        await message.reply("❌ Нельзя передать см самому себе!")
        return
    args = get_clean_args(message.text)
    if not args or not args[0].isdigit():
        await message.reply("❌ Укажи целое число. Пример: `/give 5`", parse_mode=ParseMode.MARKDOWN)
        return
    amount = int(args[0])
    if amount <= 0:
        await message.reply("❌ Количество должно быть больше 0!")
        return
    cursor.execute("SELECT size FROM users WHERE chat_id = %s AND user_id = %s", (chat_id, from_id))
    from_row = cursor.fetchone()
    from_size = from_row[0] if from_row else 0
    if from_size < amount:
        await message.reply("❌ У тебя нет столько см!")
        return
    cursor.execute("SELECT size FROM users WHERE chat_id = %s AND user_id = %s", (chat_id, to_id))
    to_row = cursor.fetchone()
    to_size = (to_row[0] if to_row else 0) + amount
    to_username = message.reply_to_message.from_user.first_name
    cursor.execute("UPDATE users SET size = %s WHERE chat_id = %s AND user_id = %s", (from_size - amount, chat_id, from_id))
    cursor.execute("INSERT INTO users (chat_id, user_id, username, size) VALUES (%s, %s, %s, %s) ON CONFLICT(chat_id, user_id) DO UPDATE SET size = EXCLUDED.size", (chat_id, to_id, to_username, to_size))
    conn.commit()
    await message.reply(f"🤝 Ты успешно передал **{amount} см** игроку {to_username}!", parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("add_cm"))
async def cmd_add_cm(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    if not message.reply_to_message:
        await message.reply("❌ Ответь этой командой на сообщение того, кому хочешь выдать см!")
        return
    args = get_clean_args(message.text)
    if not args or not args[0].isdigit():
        await message.reply("❌ Использование: `/add_cm [число]`")
        return
    amount, chat_id, target_id, target_name = int(args[0]), message.chat.id, message.reply_to_message.from_user.id, message.reply_to_message.from_user.first_name
    cursor.execute("SELECT size FROM users WHERE chat_id = %s AND user_id = %s", (chat_id, target_id))
    row = cursor.fetchone()
    current_size = row[0] if row else 0
    new_size = current_size + amount
    cursor.execute("INSERT INTO users (chat_id, user_id, username, size) VALUES (%s, %s, %s, %s) ON CONFLICT(chat_id, user_id) DO UPDATE SET size = EXCLUDED.size", (chat_id, target_id, target_name, new_size))
    conn.commit()
    await message.reply(f"👑 **Админ-действие**: Выдано **+{amount} см** игроку {target_name}!\nБаланс: **{new_size} см**.")

@dp.message(Command("remove_cm"))
async def cmd_remove_cm(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    if not message.reply_to_message:
        await message.reply("❌ Ответь этой командой на сообщение того, у кого хочешь забрать см!")
        return
    args = get_clean_args(message.text)
    if not args or not args[0].isdigit():
        await message.reply("❌ Использование: `/remove_cm [число]`")
        return
    amount, chat_id, target_id, target_name = int(args[0]), message.chat.id, message.reply_to_message.from_user.id, message.reply_to_message.from_user.first_name
    cursor.execute("SELECT size FROM users WHERE chat_id = %s AND user_id = %s", (chat_id, target_id))
    row = cursor.fetchone()
    current_size = row[0] if row else 0
    new_size = max(0, current_size - amount)
    cursor.execute("INSERT INTO users (chat_id, user_id, username, size) VALUES (%s, %s, %s, %s) ON CONFLICT(chat_id, user_id) DO UPDATE SET size = EXCLUDED.size", (chat_id, target_id, target_name, new_size))
    conn.commit()
    await message.reply(f"👑 **Админ-действие**: Изъято **-{amount} см** у игрока {target_name}!\nБаланс: **{new_size} см**.")

@dp.message(Command("pvp"))
async def cmd_pvp(message: types.Message):
    if message.chat.type == "private":
        await message.reply("❌ Эта команда работает только в групповых чатах!")
        return
    args = get_clean_args(message.text)
    if not args or not args[0].isdigit():
        await message.reply("❌ Укажи ставку в см. Пример: `/pvp 10`")
        return
    bet, chat_id, p1_id, p1_name = int(args[0]), message.chat.id, message.from_user.id, message.from_user.first_name
    if bet <= 0:
        await message.reply("❌ Ставка должна быть больше 0!")
        return
    cursor.execute("SELECT size FROM users WHERE chat_id = %s AND user_id = %s", (chat_id, p1_id))
    p1_row = cursor.fetchone()
    p1_size = p1_row[0] if p1_row else 0
    if p1_size < bet:
        await message.reply("❌ У тебя самого недостаточно сантиметров для этой ставки!")
        return
    builder = InlineKeyboardBuilder()
    builder.button(text="🎲 Принять вызов", callback_data=f"pub_accept:{p1_id}:{bet}")
    builder.button(text="❌ Отменить", callback_data=f"pub_cancel:{p1_id}")
    builder.adjust(1)
    await message.answer(f"📣 **ОТКРЫТЫЙ ВЫЗОВ В КАЗИНО!**\n👤 Создатель: {p1_name}\n💰 Ставка: **{bet} см**\n\n👇 Кто угодно может принять вызов по кнопке ниже:", reply_markup=builder.as_markup(), parse_mode=ParseMode.MARKDOWN)

@dp.callback_query(F.data.startswith("pub_accept:"))
async def pub_accept(callback: types.CallbackQuery):
    _, p1_id, bet = callback.data.split(":")
    p1_id, bet, p2_id, chat_id = int(p1_id), int(bet), callback.from_user.id, callback.message.chat.id
    if p2_id == p1_id:
        await callback.answer("❌ Нельзя играть против самого себя!", show_alert=True)
        return
    cursor.execute("SELECT size, username FROM users WHERE chat_id = %s AND user_id = %s", (chat_id, p1_id))
    p1_data = cursor.fetchone()
    cursor.execute("SELECT size, username FROM users WHERE chat_id = %s AND user_id = %s", (chat_id, p2_id))
    p2_data = cursor.fetchone()
    p1_size, p1_name = (p1_data[0], p1_data[1]) if p1_data else (0, "Игрок 1")
    p2_size, p2_name = (p2_data[0], p2_data[1]) if p2_data else (0, callback.from_user.first_name)
    if p1_size < bet:
        await callback.message.edit_text("❌ Игра отменена: у создателя вызова больше нет нужной суммы!")
        await callback.answer()
        return
    if p2_size < bet:
        await callback.answer(f"❌ У тебя не хватает см! Твой баланс: {p2_size} см.", show_alert=True)
        return
    await callback.message.edit_text(f"⚔️ **Ставка принята!**\nДуэль: **{p1_name}** против **{p2_name}** на **{bet} см**.", parse_mode=ParseMode.MARKDOWN)
    await callback.answer()
    await callback.message.answer(f"🎲 Бросок для **{p1_name}**:")
    dice1 = await bot.send_dice(chat_id=chat_id)
    val1 = dice1.dice.value
    await asyncio.sleep(3.5)
    await callback.message.answer(f"🎲 Бросок для **{p2_name}**:")
    dice2 = await bot.send_dice(chat_id=chat_id)
    val2 = dice2.dice.value
    await asyncio.sleep(3.5)
    if val1 > val2:
        w_id, w_name, l_id, w_size, l_size = p1_id, p1_name, p2_id, p1_size + bet, p2_size - bet
        result_text = f"🏆 **{w_name}** выиграл дуэль (**{val1}** против **{val2}**) и забирает **{bet} см** у {p2_name}!"
    elif val2 > val1:
        w_id, w_name, l_id, w_size, l_size = p2_id, p2_name, p1_id, p2_size + bet, p1_size - bet
        result_text = f"🏆 **{w_name}** выиграл дуэль (**{val2}** против **{val1}**) и забирает **{bet} см** у {p1_name}!"
    else:
        await callback.message.answer(f"🤝 Ничья (**{val1}** : **{val2}**)! Все остались при своих сантиметрах.")
        return
    cursor.execute("UPDATE users SET size = %s WHERE chat_id = %s AND user_id = %s", (w_size, chat_id, w_id))
    cursor.execute("UPDATE users SET size = %s WHERE chat_id = %s AND user_id = %s", (l_size, chat_id, l_id))
    conn.commit()
    await callback.message.answer(result_text, parse_mode=ParseMode.MARKDOWN)

@dp.callback_query(F.data.startswith("pub_cancel:"))
async def pub_cancel(callback: types.CallbackQuery):
    _, p1_id = callback.data.split(":")
    p1_id = int(p1_id)
    if callback.from_user.id != p1_id:
        await callback.answer("❌ Только создатель может отменить этот вызов!", show_alert=True)
        return
    await callback.message.edit_text("❌ Вызов в казино был отозван создателем.")
    await callback.answer()

async def main():
    await set_bot_commands(bot)
    print("Бот успешно запущен со всеми обновлениями!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
