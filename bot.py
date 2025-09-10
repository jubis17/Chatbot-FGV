import os
import logging
from dotenv import load_dotenv

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

print("TOKEN carregado:", TELEGRAM_TOKEN)