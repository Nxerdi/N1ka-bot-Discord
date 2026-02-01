import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
TG_LINK = os.getenv("TG_LINK")
ZAPRET_LINK = os.getenv("ZAPRET_LINK")
AFK_CHANNEL_NAME = "🚽 Уборная"
DRUNK_ROLE_NAME = "🤪 Напился"
LOG_CHANNEL_NAME = "n1ka-log"
ENABLE_LOGGING = True

ROLE_NAMES = [
    "🎲 За игровым столом",
    "🍺 У барной стойки",
    "🎥 В киноуголке",
    "🧙 Завсегдатай",
    "🪖В танке"
]

VOICE_ROLE_MAP = {
    "🎲 Игровой стол": "🎲 За игровым столом",
    "🍺 Барная стойка": "🍺 У барной стойки",
    "🎥 Кинотеатр": "🎥 В киноуголке",
    "🪖Танки":"🪖В танке"
}