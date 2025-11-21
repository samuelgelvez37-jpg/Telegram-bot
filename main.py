import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ============================
# CONFIG DESDE VARIABLES ENTORNO (Render)
# ============================
import os
TOKEN = os.getenv("8415374580:AAEpnVwlX2cmI6MK18wdRcZ3vwzMFoR9454")
GROUP_ID = int(os.getenv("-5031243712"))
CHANNEL_ID = int(os.getenv("-5031243712"))

# Memoria temporal por usuario
user_signals = {}
user_round = {}   # Para controlar green / martin gala
logging.basicConfig(level=logging.INFO)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hola, soy JEISON BOT.\nEnvíame señales por privado (solo números)."
    )

# ===============================
# PROCESAR SEÑALES PRIVADAS
# ===============================
async def handle_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Solo aceptar en privado
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

    # Mantener solo 2 señales
    if len(lst) > 2:
        lst.pop(0)

    # =========================
    # PRIMERA SEÑAL
    # =========================
    if len(lst) == 1:

        # Reiniciar estado
        user_round[user_id] = {
            "waiting_result": False,
            "martin": False
        }

        if value > 2:
            await context.bot.send_message(
                chat_id=GROUP_ID,
                text="⏳ Esperando confirmación para iniciar la apuesta…"
            )
        else:
            await context.bot.send_message(
                chat_id=GROUP_ID,
                text="❌ La primera señal NO superó 2.00 — No abrir apuestas."
            )
        return

    # =========================
    # SEGUNDA SEÑAL
    # =========================
    if len(lst) == 2:

        first, second = lst

        # Ambas señales > 2 → APUESTA ABIERTA
        if first > 2 and second > 2:

            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=(
                    "✅ ENTRADA CONFIRMADA — JEISON BOT ✅\n\n"
                    f"👉 Entrar después de {second}\n"
                    "💰 RETIRAR EN: 1.50x\n♟️ MÁXIMO 1 GALES"
                )
            )

            # Activar modo espera de resultado
            user_round[user_id]["waiting_result"] = True
            return

        else:
            await context.bot.send_message(
                chat_id=GROUP_ID,
                text="❌ No abrir ninguna apuesta — la segunda señal no superó 2.00"
            )

            user_signals[user_id] = []
            return

# ============================================================
# PROCESAR RESULTADOS (después de confirmada la apuesta)
# ============================================================
async def handle_result(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.chat.type != "private":
        return

    msg = update.message.text.strip()

    try:
        value = float(msg)
    except:
        return

    user_id = update.message.from_user.id

    # El usuario debe haber activado una apuesta
    if user_id not in user_round:
        return

    state = user_round[user_id]

    # Si estamos esperando resultado de la entrada
    if state["waiting_result"] and not state["martin"]:

        if value >= 2:
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"🍀🍀🍀 GREEN!!! 🍀🍀🍀\n\n✅ Resultado: {value}x"
            )
        else:
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text="⚠️ Resultado menor de 2.00 — ABRIR MARTIN GALA X1"
            )
            state["martin"] = True

        state["waiting_result"] = False
        return

    # Segundo resultado (Martin Gala)
    if state["martin"]:
        if value >= 2:
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"🍀🍀🍀 GREEN!!! (Martin Gala) 🍀🍀🍀\n\n✅ Resultado: {value}x"
            )
        else:
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text="⛔ OPERACION PERDIDA ⛔"
            )

        # Reset total
        user_signals[user_id] = []
        user_round[user_id] = {}
        return


# ============================
# MAIN Render
# ============================
if __name__ == "__main__":
    print("JEISON BOT corriendo…")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_signal))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_result))

    app.run_polling()