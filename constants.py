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
API_LIMIT = 2500
USER_API_LIMIT = 1000