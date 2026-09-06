import os

import requests
from dotenv import load_dotenv

load_dotenv()


class PushcutClient:
    def __init__(self):
        self.url = os.environ["PUSHCUT_URL"]

    def send_message(self, body):
        response = requests.post(
            self.url,
            json={"input": body},
            timeout=30,
        )
        response.raise_for_status()

        return response.text