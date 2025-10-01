import os
import logging
import json
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, Application, CommandHandler, ContextTypes, CallbackQueryHandler
from fastapi import FastAPI, Request, HTTPException

# Configura o logger para vermos mensagens no terminal
logging.basicConfig(format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
                    level=logging.INFO,)

# Carrega variáveis do arquivo .env
load_dotenv()

# Lê o token do bot (pego com o BotFather) do .env
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("O token do Telegram não foi encontrado no arquivo .env. Verifique se a variável TELEGRAM_TOKEN está configurada corretamente.")

def criar_teclado(node_key: str) -> InlineKeyboardMarkup:
    """
    Cria um teclado de navegação com as opções do nó especificado e botões de navegação.
    """
    # copia os botões que já existem no nó
    base_rows = MAPA[node_key]["opcoes"].inline_keyboard
    rows = [[InlineKeyboardButton(btn.text, callback_data=btn.callback_data) for btn in row] for row in base_rows]

    # acrescenta navegação (exceto no ROOT)
    if node_key != "ROOT":
        rows.append([InlineKeyboardButton("Voltar", callback_data="VOLTAR")])
        rows.append([InlineKeyboardButton("Home", callback_data="HOME")])

    return InlineKeyboardMarkup(rows)

def criar_mapa(opcoes: list) -> InlineKeyboardMarkup:
    """
    Constrói um teclado com as opções fornecidas.
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(txt, callback_data=data)] 
        for txt, data in opcoes
    ])

with open("mapa.json", "r", encoding="utf-8") as f:
    mapa_json = json.load(f)

MAPA = {}
IDX = {}

for chave, item in mapa_json.items():
    MAPA[chave] = {"texto": item["texto"], "opcoes": criar_mapa(item["opcoes"])}
    for txt, data in item["opcoes"]:
        IDX[data] = txt

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Envia a mensagem inicial do bot com o menu principal.
    """
    context.user_data["stack"] = ["ROOT"]
    user = update.effective_user  # pega os dados do usuário que chamou o comando
    item = MAPA["ROOT"]
    await update.message.reply_text(f"Olá, {user.first_name or 'aluno(a)'}! 👋 " + item["texto"], reply_markup=item["opcoes"])

async def tratar_clique(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Gerencia a navegação entre os nós do mapa com base nos cliques do usuário.
    """
    q = update.callback_query
    await q.answer()
    chave = q.data

    if chave not in ("HOME", "VOLTAR"):
        rotulo = IDX.get(chave, chave)
        await q.message.chat.send_message(f"Sua escolha: {rotulo}")

    stack = context.user_data.get("stack", ["ROOT"])

    if chave == "HOME":
        stack = ["ROOT"]
        context.user_data["stack"] = stack
        item = MAPA["ROOT"]
        await q.message.reply_text(item["texto"], reply_markup=criar_teclado("ROOT"))
        return

    if chave == "VOLTAR":
        if len(stack) > 1:
            stack.pop()
        chave = stack[-1]
        context.user_data["stack"] = stack
        item = MAPA[chave]
        await q.message.reply_text(item["texto"], reply_markup=criar_teclado(chave))
        return

    if chave in MAPA:
        stack.append(chave)
        context.user_data["stack"] = stack
        item = MAPA[chave]
        await q.message.reply_text(item["texto"], reply_markup=criar_teclado(chave))
        return
    
    else:
        # nó não existe → mostra aviso
        stack.append(chave)
        context.user_data["stack"] = stack
        logging.warning(f"Nó ainda não implementado: {chave}")
        await q.message.reply_text("Ops! Ainda não implementamos esta opção. Você pode voltar.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Voltar", callback_data="VOLTAR")],
            [InlineKeyboardButton("Home", callback_data="HOME")]
        ])
        )

def main():
    """
    Inicializa o bot, registra os handlers e inicia o polling.
    """
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(tratar_clique))
    app.run_polling(close_loop=False)

if __name__ == "__main__":
    main()