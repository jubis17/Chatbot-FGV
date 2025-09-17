import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# Configura o logger para vermos mensagens no terminal
logging.basicConfig(format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
                    level=logging.INFO,)

# Carrega variáveis do arquivo .env
load_dotenv()

# Lê o token do bot (pego com o BotFather) do .env
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("Faltou TELEGRAM_TOKEN no arquivo .env")

def criar_teclado(opcoes):
    return InlineKeyboardMarkup([[InlineKeyboardButton(txt, callback_data=data)] for txt, data in opcoes])

MAPA = {
    "ROOT": {
        "texto": (
            "Eu sou o assistente FGV.\n"
            "Minha função é tirar suas dúvidas sobre os processos internos da FGV.\n\n"
            "Para começar, sobre o que é sua dúvida?"
        ),
        "teclado": criar_teclado([
            ("Financeiro", "FINANCEIRO"),
            ("Acadêmico", "ACADEMICO"),
            ("Administrativo", "ADMIN"),
            ("Estágio", "ESTAGIO"),
            ("Outros", "OUTROS"),
            ("Falar com a secretaria", "SECRETARIA"),
        ])
    },
    "FINANCEIRO": {
        "texto": (
            "Ok, sua dúvida é sobre 'Financeiro'. O que você quer saber, mais especificamente?"
        ),
        "teclado": criar_teclado([
            ("Pagamento de boleto", "FINANCEIRO/BOLETO"),
            ("Solicitação de bolsa de estudos", "FINANCEIRO/BOLSA"),
            ("Bilhete de transporte", "FINANCEIRO/BILHETE"),
            ("Voltar", "ROOT"),
        ])
    },
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user  # pega os dados do usuário que chamou o comando
    item = MAPA["ROOT"]
    await update.message.reply_text(f"Olá, {user.first_name or 'aluno(a)'}! 👋 " + item["texto"], reply_markup=item["teclado"])

def buscar_rotulo(callback):
    for chave, item in MAPA.items():
        for linha in item["teclado"].inline_keyboard:
            for botao in linha:
                if botao.callback_data == callback:
                    return botao.text
    return callback 

async def tratar_clique(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    chave = q.data

    rotulo = buscar_rotulo(chave)
    await q.message.chat.send_message(f"Sua escolha: {rotulo}")

    if chave in MAPA:
        item = MAPA[chave]
        
        await q.message.reply_text(item["texto"], reply_markup=item["teclado"])
        return

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(tratar_clique))
    app.run_polling(close_loop=False)

if __name__ == "__main__":
    main()