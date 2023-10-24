import os
from dotenv import load_dotenv
from flask import Flask, render_template

load_dotenv()

app = Flask(__name__)


@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html", title="SnaarfBot")


if __name__ == "__main__":
    app.run(host=os.getenv("DEV_HOST"), port=os.getenv("DEV_PORT"))
