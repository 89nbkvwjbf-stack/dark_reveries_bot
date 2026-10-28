import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

# Твои данные
BOT_TOKEN = "8960731368:AAFv4fxvidBHA2OdqhZfdTyU0IebvvBMvSM"
GROUP_ID = -1004353925400

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Словарь для связи сообщений в группе с ID пользователя
msg_map = {}

# Хранилище временных выборов пользователя
user_temp_data = {}

# Настройка базы
USERS_FILE = "users.txt"
BASE_TOTAL_USERS = 240
BASE_BLOCKED_USERS = 64


def load_users():
  """Загружает уникальные ID пользователей из файла"""
  try:
    with open(USERS_FILE, "r", encoding="utf-8") as f:
      return set(int(line.strip()) for line in f if line.strip().isdigit())
  except FileNotFoundError:
    return set()


def save_user(user_id):
  """Сохраняет нового пользователя в файл"""
  users = load_users()
  if user_id not in users:
    with open(USERS_FILE, "a", encoding="utf-8") as f:
      f.write(f"{user_id}\n")


# Главная клавиатура внизу экрана
user_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✍️ Написать в поддержку")],
        [KeyboardButton(text="ℹ️ Информация / FAQ")],
    ],
    resize_keyboard=True,
)


# Кнопки выбора пола администратора
def get_gender_kb():
  return InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(text="👨 Парень", callback_data="gender_male"),
              InlineKeyboardButton(
                  text="👩 Девушка", callback_data="gender_female"
              ),
          ],
          [
              InlineKeyboardButton(
                  text="🌐 Не важно", callback_data="gender_any"
              )
          ],
      ]
  )


# Кнопки выбора категории
def get_category_kb():
  return InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="💬 Общение", callback_data="cat_communication"
              ),
              InlineKeyboardButton(
                  text="🛠 Поддержка", callback_data="cat_support"
              ),
          ],
          [
              InlineKeyboardButton(
                  text="⭐ Универсал", callback_data="cat_universal"
              )
          ],
      ]
  )


@dp.message(CommandStart())
async def start_cmd(message: Message):
  if message.chat.type == "private":
    save_user(message.from_user.id)
    welcome_text = (
        f"👋 **Приветствуем, {message.from_user.first_name}!**\n\n"
        f"🤖 Это официальный бот обратной связи проекта **Dark Reveries**.\n"
        f"Здесь вы можете пообщаться, задать вопрос администрации или получить"
        f" необходимую помощь.\n\n"
        f"👇 Для начала выберите, **пол администратора**, с которым вы хотели"
        f" бы общаться:"
    )
    await message.answer(
        welcome_text,
        reply_markup=get_gender_kb(),
        parse_mode=ParseMode.MARKDOWN,
    )


# Обработка выбора пола администратора
@dp.callback_query(F.data.startswith("gender_"))
async def process_gender(callback: CallbackQuery):
  user_id = callback.from_user.id
  gender_map = {
      "gender_male": "👨 Парень",
      "gender_female": "👩 Девушка",
      "gender_any": "🌐 Не важно",
  }
  selected_gender = gender_map.get(callback.data, "Не указан")

  if user_id not in user_temp_data:
    user_temp_data[user_id] = {}
  user_temp_data[user_id]["gender"] = selected_gender

  await callback.message.edit_text(
      f"✅ Выбран пол администратора: **{selected_gender}**\n\n👇 Теперь"
      f" выберите **категорию** обращения:",
      reply_markup=get_category_kb(),
      parse_mode=ParseMode.MARKDOWN,
  )
  await callback.answer()


# Обработка выбора категории, сохранение маппинга и отправка анкеты в группу
@dp.callback_query(F.data.startswith("cat_"))
async def process_category(callback: CallbackQuery):
  user_id = callback.from_user.id
  user = callback.from_user

  cat_map = {
      "cat_communication": "💬 Общение",
      "cat_support": "🛠 Поддержка",
      "cat_universal": "⭐ Универсал",
  }
  selected_cat = cat_map.get(callback.data, "Не указана")

  if user_id not in user_temp_data:
    user_temp_data[user_id] = {}
  user_temp_data[user_id]["category"] = selected_cat

  data = user_temp_data[user_id]
  gender = data.get("gender", "Не указан")
  category = data.get("category", "Не указана")

  card_text = (
      f"📌 **НОВАЯ АНКЕТА ПОЛЬЗОВАТЕЛЯ**\n"
      f"━━━━━━━━━━━━━━━━━━\n"
      f"👤 **Имя:** {user.full_name}\n"
      f"🔗 **Юзернейм:** @{user.username or 'нет'}\n"
      f"🆔 **ID:** `{user.id}`\n"
      f"👨‍💻 **Желаемый пол админа:** {gender}\n"
      f"📁 **Категория:** {category}\n"
      f"━━━━━━━━━━━━━━━━━━\n"
      f"👇 *Отвечайте через Reply на это сообщение, чтобы написать пользователю!*"
  )

  # Отправляем карточку в группу
  info_msg = await bot.send_message(
      chat_id=GROUP_ID, text=card_text, parse_mode=ParseMode.MARKDOWN
  )

  # Привязываем ID анкеты к ID пользователя, чтобы администратор мог сразу сделать Reply
  msg_map[info_msg.message_id] = user.id

  # Завершаем для пользователя
  await callback.message.edit_text(
      f"🎉 **Регистрация завершена!**\n\n"
      f"• Желаемый пол админа: {gender}\n"
      f"• Категория: {category}\n\n"
      f"💬 Теперь отправьте ваше сообщение или вопрос прямо сюда, и он"
      f" отправится администраторам!",
      parse_mode=ParseMode.MARKDOWN,
  )

  await callback.message.answer(
      "Главное меню:", reply_markup=user_keyboard
  )
  await callback.answer()


# Информационная кнопка
@dp.message(F.chat.type == "private", F.text == "ℹ️ Информация / FAQ")
async def info_btn(message: Message):
  info_text = (
      "📌 **Справка:**\n\n"
      "• Время работы: 24/7\n"
      "• Среднее время ответа: от 5 до 15 минут\n"
      "• Пишите ваш вопрос четко и в одном сообщении."
  )
  await message.answer(info_text, parse_mode=ParseMode.MARKDOWN)


# Команда рассылки для админов в группе: /broadcast Текст
@dp.message(F.chat.id == GROUP_ID, Command("broadcast"))
async def broadcast_cmd(message: Message):
  command_parts = message.text.split(maxsplit=1)
  if len(command_parts) < 2:
    await message.reply(
        "❌ **Ошибка!** Укажите текст для рассылки.\nПример: `/broadcast"
        " Привет всем!`",
        parse_mode=ParseMode.MARKDOWN,
    )
    return

  broadcast_text = command_parts[1]
  users = load_users()

  status_msg = await message.reply("🚀 Начинаю рассылку сообщения пользователям...")

  success_count = 0
  fail_count = 0

  for user_id in users:
    try:
      await bot.send_message(
          chat_id=user_id, text=broadcast_text, parse_mode=ParseMode.MARKDOWN
      )
      success_count += 1
      await asyncio.sleep(0.05)
    except Exception:
      fail_count += 1

  await status_msg.edit_text(
      f"📢 **РАССЫЛКА ЗАВЕРШЕНА**\n"
      f"━━━━━━━━━━━━━━━━━━\n"
      f"✅ Успешно отправлено: `{success_count}`\n"
      f"❌ Ошибок (заблокировали): `{fail_count}`\n"
      f"━━━━━━━━━━━━━━━━━━",
      parse_mode=ParseMode.MARKDOWN,
  )


# Статистика /stats (без слова "визуальная")
@dp.message(F.chat.id == GROUP_ID, Command("stats"))
async def stats_cmd(message: Message):
  users = load_users()
  file_users_count = len(users)

  status_msg = await message.reply("🔄 Подсчитываю статистику...")

  file_blocked = 0
  file_active = 0

  for user_id in users:
    try:
      await bot.send_chat_action(chat_id=user_id, action="typing")
      file_active += 1
    except Exception:
      file_blocked += 1

  total_users = BASE_TOTAL_USERS + file_users_count
  total_blocked = BASE_BLOCKED_USERS + file_blocked
  total_active = total_users - total_blocked

  if total_users > 0:
    active_percent = int((total_active / total_users) * 100)
    blocked_percent = 100 - active_percent
    bar_blocks = 10
    active_blocks = int((total_active / total_users) * bar_blocks)
    blocked_blocks = bar_blocks - active_blocks
    visual_bar = "🟩" * active_blocks + "🟥" * blocked_blocks
  else:
    active_percent, blocked_percent = 100, 0
    visual_bar = "🟩" * 10

  stats_text = (
      f"📊 **СТАТИСТИКА БОТА**\n"
      f"━━━━━━━━━━━━━━━━━━\n"
      f"👥 **Всего пользователей:** `{total_users}`\n\n"
      f"🟢 **Активные:** `{total_active}` ({active_percent}%)\n"
      f"🔴 **Заблокировали:** `{total_blocked}` ({blocked_percent}%)\n\n"
      f"📈 **Соотношение:**\n"
      f"{visual_bar}\n"
      f"━━━━━━━━━━━━━━━━━━"
  )

  await status_msg.edit_text(stats_text, parse_mode=ParseMode.MARKDOWN)


# Обработка обычных сообщений от пользователей в личке
@dp.message(F.chat.type == "private", F.from_user.id != GROUP_ID)
async def handle_user_message(message: Message):
  if message.text == "✍️ Написать в поддержку":
    await message.answer(
        "Напишите ваше сообщение ниже, и мы сразу передадим его в"
        " администрацию! 👇"
    )
    return

  user = message.from_user
  save_user(user.id)

  card_text = (
      f"📩 **НОВОЕ СООБЩЕНИЕ**\n"
      f"👤 **От:** {user.full_name}\n"
      f"🔗 **Юзернейм:** @{user.username or 'нет'}\n"
      f"🆔 **ID:** `{user.id}`\n"
      f"━━━━━━━━━━━━━━━━━━\n"
      f"👇 *Отвечайте через Reply на это или пересланное сообщение!*"
  )

  forwarded = await message.forward(chat_id=GROUP_ID)
  info_msg = await bot.send_message(
      chat_id=GROUP_ID, text=card_text, parse_mode=ParseMode.MARKDOWN
  )

  msg_map[forwarded.message_id] = user.id
  msg_map[info_msg.message_id] = user.id

  await message.answer(
      "✅ **Сообщение доставлено!** Ожидайте ответа.",
      parse_mode=ParseMode.MARKDOWN,
  )


# Ответ администраторов в группе через Reply
@dp.message(F.chat.id == GROUP_ID)
async def handle_admin_reply(message: Message):
  if not message.reply_to_message:
    return

  reply_id = message.reply_to_message.message_id
  target_user_id = msg_map.get(reply_id)

  if target_user_id:
    try:
      await bot.copy_message(
          chat_id=target_user_id,
          from_chat_id=message.chat.id,
          message_id=message.message_id,
      )
      await message.reply("📬 Ответ успешно отправлен пользователю!")
    except Exception as e:
      await message.reply(
          f"❌ Не удалось отправить (возможно, пользователь заблокировал"
          f" бота): {e}"
      )


async def main():
  logging.basicConfig(level=logging.INFO)
  await bot.delete_webhook(drop_pending_updates=True)
  print("Бот успешно запущен и работает!")
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
