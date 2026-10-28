import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.fsm.context import FSMContext

# Твои настройки
TOKEN = "8960731368:AAFv4fxvidBHA2OdqhZfdTyU0IebvvBMvSM"
GROUP_ID = -1004353925400  # ID твоей группы для саппорта

bot = Bot(token=TOKEN)
dp = Dispatcher()

USERS_FILE = "users.txt"

# Проверка, есть ли пользователь в базе
def is_user_registered(user_id: int) -> bool:
    if not os.path.exists(USERS_FILE):
        return False
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        users = f.read().splitlines()
        return str(user_id) in users

# Сохранение нового пользователя
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
    
    # Если пользователь пишет впервые — регистрируем и шлем красивое уведомление в группу
    if not registered:
        register_user(user_id)
        await bot.send_message(
            GROUP_ID, 
            f"🔔 **[LIVEGRAM] НОВЫЙ ПОЛЬЗОВАТЕЛЬ**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **Имя:** {user_name}\n"
            f"🔗 **Юзернейм:** @{username if username else 'отсутствует'}\n"
            f"🆔 **ID:** `{user_id}`\n"
            f"━━━━━━━━━━━━━━━━━━━",
            parse_mode="Markdown"
        )
    
    # Формируем красивую шапку сообщения в стиле Livegram
    header = (
        f"📩 **СООБЩЕНИЕ В ПОДДЕРЖКУ**\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **От:** {user_name} (@{username if username else 'нет'})\n"
        f"🆔 **ID:** `{user_id}`\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
    )

    # Пересылаем контент в зависимости от его типа (текст, фото, видео, документ и т.д.)
    if message.text:
        await bot.send_message(
            chat_id=GROUP_ID,
            text=header + f"💬 **Текст:**\n{message.text}",
            parse_mode="Markdown"
        )
    elif message.photo:
        # Берем фото наилучшего качества
        await bot.send_photo(
            chat_id=GROUP_ID,
            photo=message.photo[-1].file_id,
            caption=header + (f"💬 **Подпись:**\n{message.caption}" if message.caption else ""),
            parse_mode="Markdown"
        )
    elif message.video:
        await bot.send_video(
            chat_id=GROUP_ID,
            video=message.video.file_id,
            caption=header + (f"💬 **Подпись:**\n{message.caption}" if message.caption else ""),
            parse_mode="Markdown"
        )
    elif message.document:
        await bot.send_document(
            chat_id=GROUP_ID,
            document=message.document.file_id,
            caption=header + (f"💬 **Подпись:**\n{message.caption}" if message.caption else ""),
            parse_mode="Markdown"
        )
    elif message.voice:
        await bot.send_voice(
            chat_id=GROUP_ID,
            voice=message.voice.file_id,
            caption=header + "🎤 *Голосовое сообщение*",
            parse_mode="Markdown"
        )
    elif message.video_note:
        await bot.send_message(chat_id=GROUP_ID, text=header + "📹 *Видеосообщение (кружок)*", parse_mode="Markdown")
        await bot.send_video_note(chat_id=GROUP_ID, video_note=message.video_note.file_id)
    else:
        # Для любых других типов файлов
        await bot.send_message(
            chat_id=GROUP_ID,
            text=header + "📎 *Медиафайл*",
            parse_mode="Markdown"
        )

# 2. Обработка ответов администратора в группе (через Reply)
@dp.message(F.chat.id == GROUP_ID, F.reply_to_message)
async def admin_reply(message: types.Message):
    reply_msg = message.reply_to_message
    target_user_id = None

    # Достаем ID из текста сообщения (шапки), на которое ответил админ
    if reply_msg.text or reply_msg.caption:
        text = reply_msg.text or reply_msg.caption
        for line in text.split("\n"):
            if "🆔" in line or "ID:" in line:
                clean_id = ''.join(filter(str.isdigit, line))
                if clean_id:
                    target_user_id = int(clean_id)
                    break

    if target_user_id:
        try:
            # Отправляем ответ пользователю в личку
            await bot.send_message(
                chat_id=target_user_id,
                text=f"👨‍💻 **Ответ от администрации:**\n\n{message.text}",
                parse_mode="Markdown"
            )
            # Ставим лайк-реакцию в группе, подтверждая успешную отправку
            await message.react([types.ReactionTypeEmoji(emoji="👍")])
        except Exception as e:
            await message.reply(f"❌ Не удалось доставить сообщение пользователю (возможно, заблокировал бота).\nОшибка: {e}")
    else:
        await message.reply("⚠️ Не удалось определить ID пользователя. Убедитесь, что отвечаете именно на блок сообщения от бота с указанием ID.")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
