import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import requests

TOKEN_FILE = Path("/app/data/whoop_token.json")

API_BASE = "https://api.prod.whoop.com/developer/v2"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"


class WhoopClient:
    def __init__(self):
        self.client_id = os.environ["WHOOP_CLIENT_ID"]
        self.client_secret = os.environ["WHOOP_CLIENT_SECRET"]

        self.token = self._load_token()
        self.access_token = self.token["access_token"]

    def _load_token(self):
        with TOKEN_FILE.open() as f:
            return json.load(f)

    def _save_token(self):
        with TOKEN_FILE.open("w") as f:
            json.dump(self.token, f)

    def _refresh_token(self):
        response = requests.post(
            TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.token["refresh_token"],
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )
        response.raise_for_status()

        self.token = response.json()
        self.access_token = self.token["access_token"]
        self._save_token()

    def _get(self, path, params=None):
        response = requests.get(
            f"{API_BASE}{path}",
            headers={
                "Authorization": f"Bearer {self.access_token}",
            },
            params=params,
        )

        # Access token expired — refresh and retry once.
        if response.status_code == 401:
            self._refresh_token()

            response = requests.get(
                f"{API_BASE}{path}",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                },
                params=params,
            )

        response.raise_for_status()
        return response.json()

    def get_cycles(self):
        return self._get(
            "/cycle",
            params={"limit": 1},
        )

    def get_sleep(self):
        return self._get(
            "/activity/sleep",
            params={"limit": 1},
        )

    def get_recovery(self):
        return self._get(
            "/recovery",
            params={"limit": 1},
        )
    def get_daily_update(self):
        now = datetime.now().astimezone()

        start = now.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        end = start + timedelta(days=1)

        # Current cycle = today's accumulated strain
        cycle_data = self._get(
            "/cycle",
            params={
                "limit": 1,
                "start": start.isoformat(),
                "end": end.isoformat(),
            },
        )

        cycle = cycle_data["records"][0] if cycle_data["records"] else None

        # Workouts performed today
        workout_data = self._get(
            "/activity/workout",
            params={
                "limit": 25,
                "start": start.isoformat(),
                "end": end.isoformat(),
            },
        )

        workouts = workout_data.get("records", [])

        # Latest sleep contains WHOOP's calculated sleep need.
        sleep_data = self._get(
            "/activity/sleep",
            params={"limit": 1},
        )

        sleep = sleep_data["records"][0] if sleep_data["records"] else None

        return {
            "cycle": cycle,
            "workouts": workouts,
            "sleep": sleep,
        }