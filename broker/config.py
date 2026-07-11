import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GITHUB_APP_ID = os.environ["BROKER_GITHUB_APP_ID"]
GITHUB_INSTALLATION_ID = os.environ["BROKER_GITHUB_INSTALLATION_ID"]
GITHUB_PRIVATE_KEY_PATH = os.environ["BROKER_GITHUB_PEM_PATH"]

def load_private_key() -> str:
    return Path(GITHUB_PRIVATE_KEY_PATH).read_text(encoding="utf-8")