import os
import logging
import json
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
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
    Monta o teclado do nó a partir de opcoes_raw e acrescenta Voltar/Home
    para todos os nós exceto ROOT.
    Suporta tanto callback_data quanto botões de URL.
    """
    rows = []
    for label, target in MAPA[node_key].get("opcoes_raw", []):
        if isinstance(target, dict) and "url" in target:
            rows.append([InlineKeyboardButton(label, url=target["url"])])
        else:
            # aceita string direta ("FIN_COBR") ou dict com action/goto
            if isinstance(target, str):
                data = target
            else:
                data = target.get("action") or target.get("goto") or "ROOT"
            rows.append([InlineKeyboardButton(label, callback_data=data)])

    if node_key != "ROOT":
        rows.append([InlineKeyboardButton("Voltar", callback_data="VOLTAR")])
        rows.append([InlineKeyboardButton("Home", callback_data="HOME")])

    return InlineKeyboardMarkup(rows)

with open("mapa.json", "r", encoding="utf-8") as f:
    mapa_json = json.load(f)

MAPA = {}
IDX = {}

for chave, item in mapa_json.items():
    MAPA[chave] = {
        "texto": item["texto"],
        "itens": item.get("itens", []),
        "opcoes_raw": item.get("opcoes", [])  # <- guardamos as opções cruas
    }
    # popular índice de rótulos (só para callbacks; URLs não entram aqui)
    for opt in MAPA[chave]["opcoes_raw"]:
        label, target = opt
        if isinstance(target, str):
            IDX[target] = label
        elif isinstance(target, dict):
            cb = target.get("action") or target.get("goto")
            if cb:
                IDX[cb] = label

async def enviar_node(chat, node_key):
    """
    Envia todo o conteúdo de um nó (texto, notas, links, arquivos, etc.)
    seguido do teclado de navegação.
    """
    if node_key not in MAPA:
        await chat.send_message("Ops! Essa opção ainda não está disponível.")
        return

    item = MAPA[node_key]

    # Texto principal do nó
    await chat.send_message(item["texto"])

    # Conteúdo complementar (itens)
    for bloco in item.get("itens", []):
        tipo = bloco.get("tipo")

        if tipo == "nota":
            await chat.send_message(bloco["conteudo"])

        elif tipo == "link":
            kb = InlineKeyboardMarkup(
                [[InlineKeyboardButton(bloco["titulo"], url=bloco["url"])]]
            )
            await chat.send_message("Link:", reply_markup=kb)

    # Botões de navegação no final
    await chat.send_message(
        "Escolha uma opção:", reply_markup=criar_teclado(node_key)
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Envia a mensagem inicial do bot com o menu principal.
    """
    context.user_data["stack"] = ["ROOT"]
    user = update.effective_user  # pega os dados do usuário que chamou o comando
    await update.message.reply_text(f"Olá, {user.first_name or 'aluno(a)'}! 👋")
    await enviar_node(update.message.chat, "ROOT")

async def qualquer_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Para qualquer mensagem de texto que NÃO seja comando (/algo),
    se o usuário ainda não passou pelo /start, iniciamos o fluxo.
    """
    # Garante que só trata mensagens normais (não callback, etc.)
    if update.message is None:
        return

    # Se o usuário ainda não tem stack, é como se fosse o /start
    if "stack" not in context.user_data:
        await start(update, context)
    else:
        # Aqui você decide o que fazer com mensagens depois de já ter iniciado.
        # Pode só avisar que é pra usar o menu:
        await update.message.reply_text(
            "Use os botões do menu abaixo pra navegar"
        )
    
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
        await enviar_node(q.message.chat, "ROOT")
        return

    if chave == "VOLTAR":
        if len(stack) > 1:
            stack.pop()
        chave = stack[-1]
        context.user_data["stack"] = stack
        item = MAPA[chave]
        await enviar_node(q.message.chat, chave)
        return

    if chave == "SECRETARIA":
        await q.message.reply_text("Ok! Vou te conectar com a secretaria. Envie seu nome completo e R.A. aqui que eu repasso.")
        return

    if chave in MAPA:
        stack.append(chave)
        context.user_data["stack"] = stack
        item = MAPA[chave]
        await enviar_node(q.message.chat, chave)
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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, qualquer_mensagem))
    app.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
