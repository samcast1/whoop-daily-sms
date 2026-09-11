# app/service.py

import logging
import time

from app.whoop_client import WhoopClient
from app.formatter import format_whoop_sms
from app.daily_formatter import format_daily_update

RETRY_DELAY = 10 * 60
MAX_ATTEMPTS = 6


def get_ready_data(whoop):
    cycle = whoop.get_cycles()["records"][0]
    sleep = whoop.get_sleep()["records"][0]
    recovery = whoop.get_recovery()["records"][0]

    states = {
        "cycle": cycle["score_state"],
        "sleep": sleep["score_state"],
        "recovery": recovery["score_state"],
    }

    logging.info("WHOOP score states: %s", states)

    if all(state == "SCORED" for state in states.values()):
        return cycle, sleep, recovery

    return None


def get_morning():
    whoop = WhoopClient()

    for attempt in range(1, MAX_ATTEMPTS + 1):
        logging.info(
            "Checking WHOOP data (attempt %d/%d)",
            attempt,
            MAX_ATTEMPTS,
        )

        try:
            data = get_ready_data(whoop)

            if data:
                cycle, sleep, recovery = data

                return format_whoop_sms(
                    cycle,
                    sleep,
                    recovery,
                )

        except Exception:
            logging.exception("Error checking WHOOP data")

        if attempt < MAX_ATTEMPTS:
            logging.info("Data not ready. Retrying in 10 minutes.")
            time.sleep(RETRY_DELAY)

    raise RuntimeError("WHOOP data still not ready after one hour")


def get_evening():
    whoop = WhoopClient()
    data = whoop.get_daily_update()
    return format_daily_update(data)