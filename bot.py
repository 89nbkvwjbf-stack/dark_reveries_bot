import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.fsm.context import FSMContext

# Твои настройки (можешь заменить или подтянуть из переменных окружения)
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

@dp.message(F.chat.type == "private")
async def handle_user_message(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    username = message.from_user.username
    
    # Проверяем, регистрировался ли пользователь ранее
    registered = is_user_registered(user_id)
    
    if not registered:
        # --- ПЕРВЫЙ РАЗ (РЕГИСТРАЦИЯ) ---
        register_user(user_id) # Записываем ID в users.txt
        
        # Отправляем в группу уведомление о новом пользователе
        await bot.send_message(
            GROUP_ID, 
            f"🔔 **Новый пользователь зарегистрировался в боте!**\n"
            f"👤 Имя: {user_name}\n"
            f"🔗 Юзернейм: @{username if username else 'немає'}\n"
            f"🆔 ID: `{user_id}`",
            parse_mode="Markdown"
        )
    
    # --- ВСЕ ПОСЛЕДУЮЩИЕ РАЗЫ (ИЛИ САМО ОБРАЩЕНИЕ) ---
    # Просто пересылаем сообщение пользователя в группу без лишних уведомлений
    await bot.forward_message(
        chat_id=GROUP_ID,
        from_chat_id=message.chat.id,
        message_id=message.message_id
    )
    
    # Ответ пользователю, что его сообщение принято
    await message.answer("Ваше сообщение передано администрации! Ожидайте ответа.")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
