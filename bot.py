import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.fsm.context import FSMContext

# Твои настройки
TOKEN = "8960731368:AAFv4fxvidBHA2OdqhZfdTyU0IebvvBMvSM"
GROUP_ID = -1004353925400  # ID твоей группы для саппорта

bot = Bot(token=TOKEN)
dp = Dispatcher()

USERS_FILE = "users.txt"

def is_user_registered(user_id: int) -> bool:
    if not os.path.exists(USERS_FILE):
        return False
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        users = f.read().splitlines()
        return str(user_id) in users

def register_user(user_id: int):
    with open(USERS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{user_id}\n")

# 1. Обработка входящих сообщений от пользователей в личке
@dp.message(F.chat.type == "private")
async def handle_user_message(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    username = message.from_user.username
    
    registered = is_user_registered(user_id)
    
    if not registered:
        register_user(user_id)
        await bot.send_message(
            GROUP_ID, 
            f"🔔 **Новый пользователь зарегистрировался в боте!**\n"
            f"👤 Имя: {user_name}\n"
            f"🔗 Юзернейм: @{username if username else 'немає'}\n"
            f"🆔 ID: `{user_id}`",
            parse_mode="Markdown"
        )
    
    # Вместо forward_message отправляем текст с четким указанием ID и сообщения
    user_text = message.text or message.caption or "[Медиафайл без текста]"
    
    await bot.send_message(
        chat_id=GROUP_ID,
        text=f"📩 **Сообщение от пользователя:**\n"
             f"👤 Имя: {user_name} (@{username if username else 'нет'})\n"
             f"🆔 ID: `{user_id}`\n\n"
             f"💬 Текст:\n{user_text}",
        parse_mode="Markdown"
    )

# 2. Обработка ответов администратора в группе
@dp.message(F.chat.id == GROUP_ID, F.reply_to_message)
async def admin_reply(message: types.Message):
    reply_msg = message.reply_to_message
    target_user_id = None

    # Достаем ID прямо из текста сообщения, на которое ответил админ
    if reply_msg.text or reply_msg.caption:
        text = reply_msg.text or reply_msg.caption
        for line in text.split("\n"):
            if "🆔 ID:" in line or "ID:" in line:
                clean_id = ''.join(filter(str.isdigit, line))
                if clean_id:
                    target_user_id = int(clean_id)
                    break

    if target_user_id:
        try:
            await bot.send_message(
                chat_id=target_user_id,
                text=f"👨‍💻 **Ответ от администрации:**\n\n{message.text}",
                parse_mode="Markdown"
            )
            await message.react([types.ReactionTypeEmoji(emoji="👍")])
        except Exception as e:
            await message.reply(f"Не удалось отправить сообщение пользователю. Возможно, он заблокировал бота. Ошибка: {e}")
    else:
        await message.reply("Не удалось определить ID пользователя. Убедитесь, что отвечаете на отчетное сообщение бота с указанием ID.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
