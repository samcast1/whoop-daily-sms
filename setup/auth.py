import os

from dotenv import load_dotenv
from whoopy import WhoopClient

load_dotenv()

client = WhoopClient.auth_flow(
    os.environ["WHOOP_CLIENT_ID"],
    os.environ["WHOOP_CLIENT_SECRET"],
    os.environ["WHOOP_REDIRECT_URI"],
)

client.save_token("data/whoop_token.json")

print("WHOOP authentication successful!")