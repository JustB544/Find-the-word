"""File containing all constants that are useful between modules"""
from datetime import timedelta, timezone, datetime
from secret import auth_key

HEADERS = {
        "X-RapidAPI-Key": auth_key,
        "X-RapidAPI-Host": "wordsapiv1.p.rapidapi.com"
}
URL_BASE = "https://wordsapiv1.p.rapidapi.com/words"

# TZ is a timezone set specifically to when the API changes day
TZ = timezone(
    offset=-timedelta(
        hours=3,
        minutes=19
    )
)
TZ_NOW = lambda: datetime.now(TZ).strftime("%b %d %Y")

# Must change create_data() in app, models, and root.html as well
GAME_TYPES = ["Sentence", "Definition", "Synonym", "Antonym"]