import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
    texto = f"Olá, {user.first_name or 'aluno(a)'}! 👋 Eu sou o assistente FGV.\n" "Minha função é tirar suas dúvidas sobre os processos internos da FGV.\n\n""Para começar, sobre o que é sua dúvida?"
    botoes = [[InlineKeyboardButton("Financeiro", callback_data="FINANCEIRO")],
        [InlineKeyboardButton("Acadêmico", callback_data="ACADEMICO")],
        [InlineKeyboardButton("Administrativo", callback_data="ADMIN")],
        [InlineKeyboardButton("Estágio", callback_data="ESTAGIO")],
        [InlineKeyboardButton("Outros", callback_data="OUTROS")],
        [InlineKeyboardButton("Falar com a secretaria", callback_data="SECRETARIA")]]
    teclado = InlineKeyboardMarkup(botoes)
    await update.message.reply_text(texto, reply_markup=teclado)

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling(close_loop=False)

if __name__ == "__main__":
    main()