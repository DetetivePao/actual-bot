from flask import Flask
from threading import Thread
from bot import run_bot

app = Flask('')

@app.route('/')
def home():
    return "Bot ativo!"

def manter_vivo():
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

if __name__ == "__main__":
    manter_vivo()
    run_bot()
