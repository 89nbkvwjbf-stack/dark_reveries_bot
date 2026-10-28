import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.fsm.context import FSMContext

# Твои настройки
TOKEN = "8960731368:AAFv4fxvidBHA2OdqhZfdTyU0IebvvBMvSM"
GROUP_ID = -1004353925400  # ID твоей группы для саппорта

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Путь к файлу базы данных пользователей
USERS_FILE = "users.txt"

# Функция проверки: есть ли пользователь в файле
def is_user_registered(user_id: int) -> bool:
    if not os.path.exists(USERS_FILE):
        return False
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        users = f.read().splitlines()
        return str(user_id) in users

# Функция для сохранения нового пользователя
def register_user(user_id: int):
    with open(USERS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{user_id}\n")

# 1. Обработка сообщений от пользователей в личке бота
@dp.message(F.chat.type == "private")
async def handle_user_message(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    username = message.from_user.username
    
    # Проверяем, регистрировался ли пользователь ранее
    registered = is_user_registered(user_id)
    
    if not registered:
        # ПЕРВЫЙ РАЗ (РЕГИСТРАЦИЯ) — сохраняем и шлем уведомление в группу
        register_user(user_id)
        
        await bot.send_message(
            GROUP_ID, 
            f"🔔 **Новый пользователь зарегистрировался в боте!**\n"
            f"👤 Имя: {user_name}\n"
            f"🔗 Юзернейм: @{username if username else 'немає'}\n"
            f"🆔 ID: `{user_id}`",
            parse_mode="Markdown"
        )
    
    # ВСЕ РАЗЫ (И ПЕРВЫЙ, И ПОСЛЕДУЮЩИЕ) — пересылаем сообщение в группу
    await bot.forward_message(
        chat_id=GROUP_ID,
        from_chat_id=message.chat.id,
        message_id=message.message_id
    )
    # Текст "Ваше сообщение передано..." удален, бот больше ничего не пишет в ответ.

# 2. Обработка ответов от администраторов в группе (через Reply на сообщение)
@dp.message(F.chat.id == GROUP_ID, F.reply_to_message)
async def admin_reply(message: types.Message):
    reply_msg = message.reply_to_message
    target_user_id = None

    # Сначала пробуем найти ID через forward_from (если сообщение было переслано)
    if reply_msg.forward_from:
        target_user_id = reply_msg.forward_from.id
    
    # Если это не сработало, пытаемся вытащить ID из текста сообщения (если там сохранился ID)
    elif reply_msg.text or reply_msg.caption:
        text = reply_msg.text or reply_msg.caption
        for line in text.split("\n"):
            if "ID:" in line:
                # Очищаем строку от лишних символов, чтобы достать чистые цифры ID
                clean_id = ''.join(filter(str.isdigit, line))
                if clean_id:
                    target_user_id = int(clean_id)
                    break

    # Если ID пользователя успешно найден — отправляем ему ответ от админа
    if target_user_id:
        try:
            await bot.send_message(
                chat_id=target_user_id,
                text=f"👨‍💻 **Ответ от администрации:**\n\n{message.text}",
                parse_mode="Markdown"
            )
            # Ставим галочку в группе, что ответ успешно отправлен
            await message.react([types.ReactionTypeEmoji(emoji="👍")])
        except Exception as e:
            await message.reply(f"Не удалось отправить сообщение пользователю (возможно, он заблокировал бота). Ошибка: {e}")
    else:
        await message.reply("Не удалось определить ID пользователя для ответа. Убедитесь, что отвечаете на пересланное сообщение.")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
