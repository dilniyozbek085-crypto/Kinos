import os
import re
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import telebot
from telebot import types

TOKEN = "9092555570:AAFGUoEPzBDPND_graumNr4jOXNjz_lfoFA"
ADMIN_ID = 8657503976  # O'z Telegram ID raqamingiz

bot = telebot.TeleBot(TOKEN)


def init_db():
  conn = sqlite3.connect("movies.db")
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            code TEXT PRIMARY KEY,
            file_id TEXT,
            caption TEXT
        )
    """)
  conn.commit()
  conn.close()


init_db()


# Kengaytirilgan Super Admin Paneli (10 ta tugma - 2 tadan qator bo'lib chiqadi)
def main_admin_keyboard():
  markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
  btn1 = types.KeyboardButton("🎦 Medialarni boshqarish")
  btn2 = types.KeyboardButton("📊 Statistika")
  btn3 = types.KeyboardButton("✉️ Xabar yuborish")
  btn4 = types.KeyboardButton("📋 Barcha kodlar ro'yxati")
  btn5 = types.KeyboardButton("🔍 Kino qidirish")
  btn6 = types.KeyboardButton("🗑 Bitta kinoni o'chirish")
  btn7 = types.KeyboardButton("🧹 Bazani tozalash")
  btn8 = types.KeyboardButton("👑 Admin ma'lumoti")
  btn9 = types.KeyboardButton("🚀 Bot holati")
  btn10 = types.KeyboardButton("⚙️ Tizim sozlamalari")
  markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7, btn8, btn9, btn10)
  return markup


def media_inline_keyboard():
  markup = types.InlineKeyboardMarkup(row_width=1)
  btn1 = types.InlineKeyboardButton(
      "🎬 Kino yuklash (Video + Kod)", callback_data="sodda_yuklash"
  )
  btn2 = types.InlineKeyboardButton(
      "📋 Barcha medialar ro'yxati", callback_data="barcha_medialar"
  )
  btn3 = types.InlineKeyboardButton("⬅️ Orqaga", callback_data="orqaga")
  markup.add(btn1, btn2, btn3)
  return markup


# Start komandasi
@bot.message_handler(commands=["start", "admin"])
def send_welcome(message):
  if message.from_user.id == ADMIN_ID:
    bot.send_message(
        message.chat.id,
        "👑 **SUPER ADMIN PANELGA XUSH KELIBSIZ, XO'JAYIN!**\n\nKerakli bo'limni"
        " tanlang:",
        parse_mode="Markdown",
        reply_markup=main_admin_keyboard(),
    )
  else:
    bot.send_message(
        message.chat.id,
        "Assalomu alaykum! Menga kino kodini yuboring (masalan: 2), men sizga"
        " kinoni topib beraman.",
        reply_markup=types.ReplyKeyboardRemove(),
    )


# Matnli xabarlar va barcha admin funksiyalari
@bot.message_handler(content_types=["text"])
def handle_text_menu(message):
  user_id = message.from_user.id

  # Agar oddiy foydalanuvchi bo'lsa
  if user_id != ADMIN_ID:
    if not message.text.startswith("/"):
      code = message.text.strip()
      conn = sqlite3.connect("movies.db")
      cursor = conn.cursor()
      cursor.execute(
          "SELECT file_id, caption FROM movies WHERE code = ?", (code,)
      )
      movie = cursor.fetchone()
      conn.close()
      if movie:
        bot.send_video(message.chat.id, movie[0], caption=movie[1])
      else:
        bot.send_message(
            message.chat.id, f"Siz yuborgan kod: {code} bo'yicha kino topilmadi."
        )
    return

  # --- SUPER ADMIN MENYU AMALLARI ---
  text = message.text

  if text == "🎦 Medialarni boshqarish":
    bot.send_message(
        message.chat.id,
        "🎬 **MEDIA BOSHQARUV MARKAZI**\n\nQuyidagi amalni tanlang:",
        parse_mode="Markdown",
        reply_markup=media_inline_keyboard(),
    )
  elif text == "📊 Statistika":
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM movies")
    count = cursor.fetchone()[0]
    conn.close()
    bot.send_message(
        message.chat.id,
        f"📊 **Bot Statistikasi:**\n\n🎦 Bazadagi jami kinolar soni: `{count}`"
        " ta\n🟢 Holati: 100% Barqaror",
        parse_mode="Markdown",
    )
  elif text == "✉️ Xabar yuborish":
    bot.send_message(
        message.chat.id,
        "📢 Foydalanuvchilarga ommaviy xabar yuborish tizimi tayyorlanmoqda.",
    )
  elif text == "📋 Barcha kodlar ro'yxati":
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute("SELECT code FROM movies")
    movies = cursor.fetchall()
    conn.close()
    if movies:
      codes = ", ".join([row[0] for row in movies])
      bot.send_message(
          message.chat.id,
          f"📋 **Bazadagi barcha kino kodlari:**\n\n{codes}",
          parse_mode="Markdown",
      )
    else:
      bot.send_message(
          message.chat.id, "📋 Hozircha bazada birorta ham kino yo'q."
      )
  elif text == "🔍 Kino qidirish":
    bot.send_message(
        message.chat.id,
        "🔍 Kino topish uchun shunchaki uning **kodini** chatga yuboring.",
    )
  elif text == "🗑 Bitta kinoni o'chirish":
    bot.send_message(
        message.chat.id,
        "🗑 Kinoni o'chirish uchun menga shunday yozing: `/delete kod`"
        " (masalan: `/delete 2`)",
    )
  elif text.startswith("/delete"):
    parts = text.split()
    if len(parts) > 1:
      del_code = parts[1]
      conn = sqlite3.connect("movies.db")
      cursor = conn.cursor()
      cursor.execute("DELETE FROM movies WHERE code = ?", (del_code,))
      conn.commit()
      conn.close()
      bot.send_message(
          message.chat.id,
          f"✅ `{del_code}`-kodli kino bazadan muvaffaqiyatli o'chirildi!",
          parse_mode="Markdown",
      )
    else:
      bot.send_message(
          message.chat.id,
          "⚠️ Xato! Kodni ham yozing. Masalan: `/delete 2`",
          parse_mode="Markdown",
      )
  elif text == "🧹 Bazani tozalash":
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM movies")
    conn.commit()
    conn.close()
    bot.send_message(
        message.chat.id,
        "🧹 **Ogohlantirish!** Bazadagi hamma kinolar butunlay o'chirib"
        " tashlandi.",
        parse_mode="Markdown",
    )
  elif text == "👑 Admin ma'lumoti":
    bot.send_message(
        message.chat.id,
        "👑 **Bot egasi:** Siz\n🆔 **Admin ID:** `"
        f"{ADMIN_ID}`\n🛡️ **Huquqlar:** To'liq Super Admin",
        parse_mode="Markdown",
    )
  elif text == "🚀 Bot holati":
    bot.send_message(
        message.chat.id,
        "🚀 **Server holati:**\n• Hosting: Render (Online)\n• Ping: A'lo"
        " darajada\n• Xatoliklar: Yo'q",
        parse_mode="Markdown",
    )
  elif text == "⚙️ Tizim sozlamalari":
    bot.send_message(
        message.chat.id,
        "⚙️ **Tizim versiyasi:**\n• Bot turi: Kino qidiruv va himoyalangan"
        " baza\n• Ma'lumotlar bazasi: SQLite",
        parse_mode="Markdown",
    )
  else:
    # Admin matn yuborganda kino kodini tekshiradi
    code = text.strip()
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute("SELECT file_id, caption FROM movies WHERE code = ?", (code,))
    movie = cursor.fetchone()
    conn.close()
    if movie:
      bot.send_video(message.chat.id, movie[0], caption=movie[1])
    else:
      bot.send_message(
          message.chat.id, f"Siz yuborgan kod: {code} bo'yicha kino topilmadi."
      )


# Inline tugmalar (Faqat admin uchun)
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
  if call.from_user.id != ADMIN_ID:
    bot.answer_callback_query(call.id, "❌ Bu tugma faqat bot egasi uchun!")
    return

  if call.data == "sodda_yuklash":
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        "📥 **Kino yuklash tartibi:**\nMenga kino videosini yuboring va ostiga"
        " uning **kodini** yozib yuboring (masalan: `2`).",
        parse_mode="Markdown",
    )
  elif call.data == "barcha_medialar":
    bot.answer_callback_query(call.id)
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute("SELECT code FROM movies")
    movies = cursor.fetchall()
    conn.close()

    if movies:
      codes = ", ".join([row[0] for row in movies])
      bot.send_message(
          call.message.chat.id,
          f"📋 **Bazadagi mavjud kino kodlari:**\n\n{codes}",
          parse_mode="Markdown",
      )
    else:
      bot.send_message(
          call.message.chat.id, "📋 Hozircha bazada kinolar yo'q."
      )
  elif call.data == "orqaga":
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        "Bosh menyuga qaytdingiz.", call.message.chat.id, call.message.message_id
    )


# --- VIDEO YUBORISH (FAQAT ADMIN UCHUN) ---
@bot.message_handler(content_types=["video", "document"])
def save_movie_file(message):
  if message.from_user.id != ADMIN_ID:
    bot.reply_to(
        message,
        "❌ Kechirasiz, bu botga video yuklash taqiqlangan. Bot faqat kino"
        " qidirish uchun mo'ljallangan!",
    )
    return

  file_id = message.video.file_id if message.video else message.document.file_id
  raw_caption = message.caption or message.text or ""

  match = re.search(r"start=([a-zA-Z0-9_]+)", raw_caption)
  if match:
    code = match.group(1)
  else:
    parts = raw_caption.strip().split()
    code = parts[-1] if parts else "1"

  conn = sqlite3.connect("movies.db")
  cursor = conn.cursor()
  cursor.execute(
      """
        INSERT OR REPLACE INTO movies (code, file_id, caption)
        VALUES (?, ?, ?)
    """,
      (code, file_id, f"Kino kodi: {code}"),
  )
  conn.commit()
  conn.close()

  bot.reply_to(
      message,
      f"✅ **{code}**-kodli kino bazaga muvaffaqiyatli saqlandi!",
      parse_mode="Markdown",
  )


class SimpleHandler(BaseHTTPRequestHandler):

  def do_GET(self):
    self.send_response(200)
    self.end_headers()
    self.wfile.write(b"Bot is running!")


def run_server():
  port = int(os.environ.get("PORT", 10000))
  server = HTTPServer(("0.0.0.0", port), SimpleHandler)
  server.serve_forever()


threading.Thread(target=run_server, daemon=True).start()

bot.infinity_polling()
