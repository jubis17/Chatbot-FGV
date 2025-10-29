import os
from pyngrok import ngrok, conf
from dotenv import load_dotenv

load_dotenv()

AUTHTOKEN = os.getenv("NGROK_AUTH_TOKEN")

# 1) cole seu token aqui
conf.get_default().auth_token = AUTHTOKEN


# 2) abre túnel HTTPS para o FastAPI em 8000
tunnel = ngrok.connect(8000, bind_tls=True)
print("PUBLIC URL:", tunnel.public_url)

input("\nPressione Enter para encerrar o túnel...")
ngrok.disconnect(tunnel.public_url)
ngrok.kill()