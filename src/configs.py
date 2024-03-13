from os import getenv, path
from dotenv import load_dotenv

load_dotenv()
PROJECT_NAME = path.dirname(path.abspath(__file__)).split("/")[-2]

# CONFIGURE THIS
# DEBUG = True if getenv("debug") == "1" else False
DEBUG = 1
FETCH_TOTAL_SCROLL = int(getenv("FETCH_TOTAL_SCROLL", 30))
FETCH_VIDEO_MAX_SEC = 40
FETCH_VIDEO_MIN_SEC = 5


SOCIAL_MAPS = {
    "facebook": {
        "login": "https://m.facebook.com/login",
        "filename": "facebook-cookies.json",
    },
    "instagram": {
        "login": "https://www.instagram.com/accounts/login/",
        "filename": "instagram-cookies.json",
    },
}


def get_project_root():
    cwd = path.dirname(path.abspath(__file__))
    return cwd[: cwd.find(PROJECT_NAME) + len(PROJECT_NAME)]


PROJECT_ROOT = get_project_root()
STATIC_ROOT = path.join(get_project_root(), "static")
FINAL_ROOT = path.join(get_project_root(), "final")
DISCORD_TOKEN = getenv("DISCORD_TOKEN", "")
DISCORD_CHANNEL = int(getenv("DISCORD_RANDOM_DUDES_CHANNEL", ""))
