from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "I am alive and running 24/7!"

def run():
    # Render requires port 10000 or dynamically assigns one via environment variables
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()