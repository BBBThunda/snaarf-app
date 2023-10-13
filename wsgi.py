import os
from dotenv import load_dotenv
from snaarf_app.server import app

load_dotenv()

if __name__ == "__main__":
    app.run(host=os.getenv("PROD_HOST"), port=os.getenv("PROD_PORT"))
else:
    app.run(host=os.getenv("DEV_HOST"), port=os.getenv("DEV_PORT"))
