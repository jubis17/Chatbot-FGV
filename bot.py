import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Configura o logger para vermos mensagens no terminal
logging.basicConfig(
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    level=logging.INFO,
)

# Carrega variáveis do arquivo .env
load_dotenv()

# Lê o token do bot (pego com o BotFather) do .env
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("Faltou TELEGRAM_TOKEN no arquivo .env")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user  # pega os dados do usuário que chamou o comando
    await update.message.reply_text(f"Olá, {user.first_name or 'aluno(a)'}! 👋 Eu sou o assistente FGV.\n" 
                                    "Use /help para ver os comandos disponíveis.")
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling(close_loop=False)

if __name__ == "__main__":
    main()