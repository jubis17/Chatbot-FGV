import os
import asyncio
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from telegram import Update
from telegram.ext import Application, ApplicationBuilder, CommandHandler, CallbackQueryHandler
from contextlib import asynccontextmanager
import bot as mybot

load_dotenv()



WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
if not WEBHOOK_SECRET:
    raise RuntimeError("A variável de ambiente WEBHOOK_SECRET não foi encontrada.")

telegram_app: Application = ApplicationBuilder().token(mybot.TELEGRAM_TOKEN).build()

telegram_app.add_handler(CommandHandler("start", mybot.start))
telegram_app.add_handler(CallbackQueryHandler(mybot.tratar_clique))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializa e inicia o bot quando o FastAPI sobe
    await telegram_app.initialize()
    await telegram_app.start()

    try:
        yield
    finally:
        # Para e encerra limpo quando servidor desliga
        await telegram_app.stop()
        await telegram_app.shutdown()

api = FastAPI(lifespan=lifespan)

@api.get("/health")
def health():
    return {"status": "ok"}

@api.post("/webhook/{secret}")

async def telegram_webhook(request: Request, secret: str):
    if secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    try:
        data = await request.json()
        update = Update.de_json(data, telegram_app.bot)
        await telegram_app.process_update(update)
    except Exception as e:
        logging.error(f"Erro ao processar webhook: {e}")
        raise HTTPException(status_code=500, detail="Erro interno no servidor")