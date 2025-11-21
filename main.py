import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ============================
# CONFIG DESDE VARIABLES ENTORNO (Render)
# ============================
TOKEN = os.getenv("8415374580:AAEpnVwlX2cmI6MK18wdRcZ3vwzMFoR9454")
GROUP_ID = os.getenv("-5031243712")
CHANNEL_ID = os.getenv("-5031243712")
OWNER_ID = os.getenv("8471103011")  # Tu ID de Telegram autorizado para controlar el bot

if not TOKEN or not GROUP_ID or not CHANNEL_ID or not OWNER_ID:
    raise ValueError("Faltan variables de entorno necesarias")

GROUP_ID = int(GROUP_ID)
CHANNEL_ID = int(CHANNEL_ID)
OWNER_ID = int(OWNER_ID)

# ============================
# Memoria temporal
# ============================
user_signals = {}
user_round = {}
bot_active = True  # Estado del bot: encendido / apagado

logging.basicConfig(level=logging.INFO)

# ============================
# COMANDOS
# ============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hola, soy JEISON BOT.\nEnvíame señales por privado (solo números)."
    )

async def bot_control(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para encender/apagar el bot"""
    global bot_active

    if update.message.from_user.id != OWNER_ID:
        await update.message.reply_text("❌ No tienes permiso para usar este comando.")
        return

    if not context.args:
        await update.message.reply_text("Usa /bot on o /bot off")
        return

    cmd = context.args[0].lower()
    if cmd == "on":
        bot_active = True
        await update.message.reply_text("✅ Bot activado")
    elif cmd == "off":
        bot_active = False
        await update.message.reply_text("⛔ Bot desactivado")
    else:
        await update.message.reply_text("Usa /bot on o /bot off")

# ===============================
# PROCESAR SEÑALES PRIVADAS
# ===============================
async def handle_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    if not bot_active:
        return

    if update.message.chat.type != "private":
        return

    text = update.message.text.strip()
    try:
        value = float(text)
    except:
        return

    user_id = update.message.from_user.id
    lst = user_signals.setdefault(user_id, [])
    lst.append(value)

    if len(lst) > 2:
        lst.pop(0)

    if len(lst) == 1:
        user_round[user_id] = {"waiting_result": False, "martin": False}
        if value > 2:
            await context.bot.send_message(chat_id=GROUP_ID, text="⏳ Esperando confirmación para iniciar la apuesta…")
        else:
            await context.bot.send_message(chat_id=GROUP_ID, text="❌ La primera señal NO superó 2.00 — No abrir apuestas.")
        return

    if len(lst) == 2:
        first, second = lst
        if first > 2 and second > 2:
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"✅ ENTRADA CONFIRMADA — JEISON BOT ✅\n\n👉 Entrar después de {second}\n💰 RETIRAR EN: 1.50x\n♟️ MÁXIMO 1 GALES"
            )
            user_round[user_id]["waiting_result"] = True
        else:
            await context.bot.send_message(chat_id=GROUP_ID, text="❌ No abrir ninguna apuesta — la segunda señal no superó 2.00")
            user_signals[user_id] = []

# ===============================
# PROCESAR RESULTADOS
# ===============================
async def handle_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    if not bot_active:
        return

    if update.message.chat.type != "private":
        return

    try:
        value = float(update.message.text.strip())
    except:
        return

    user_id = update.message.from_user.id
    if user_id not in user_round:
        return

    state = user_round[user_id]

    if state["waiting_result"] and not state["martin"]:
        if value >= 2:
            await context.bot.send_message(chat_id=CHANNEL_ID, text=f"🍀🍀🍀 GREEN!!! 🍀🍀🍀\n\n✅ Resultado: {value}x")
        else:
            await context.bot.send_message(chat_id=CHANNEL_ID, text="⚠️ Resultado menor de 2.00 — ABRIR MARTIN GALA X1")
            state["martin"] = True
        state["waiting_result"] = False
        return

    if state["martin"]:
        if value >= 2:
            await context.bot.send_message(chat_id=CHANNEL_ID, text=f"🍀🍀🍀 GREEN!!! (Martin Gala) 🍀🍀🍀\n\n✅ Resultado: {value}x")
        else:
            await context.bot.send_message(chat_id=CHANNEL_ID, text="⛔ OPERACION PERDIDA ⛔")
        user_signals[user_id] = []
        user_round[user_id] = {}

# ============================
# MAIN Render
# ============================
if __name__ == "__main__":
    print("JEISON BOT corriendo…")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("bot", bot_control))  # Comando de encendido/apagado
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_signal))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_result))

    app.run_polling()