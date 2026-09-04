import logging
import time
import sys

from app.whoop_client import WhoopClient
from app.twilio_client import TwilioClient
from app.formatter import format_whoop_sms
from app.daily_formatter import format_daily_update


# Set to True when you want to actually send SMS messages.
SEND_SMS = False


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

RETRY_DELAY = 10 * 60
MAX_ATTEMPTS = 6


def deliver_message(message, label):
    if SEND_SMS:
        twilio = TwilioClient()
        sid = twilio.send_sms(message)
        logging.info("%s SMS sent: %s", label, sid)
    else:
        print()
        print("=" * 40)
        print(f"{label.upper()} MESSAGE (TEST MODE)")
        print("=" * 40)
        print(message)
        print("=" * 40)
        print()


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

    if "UNSCORABLE" in states.values():
        logging.error("WHOOP returned UNSCORABLE: %s", states)
        return None

    return None


def morning():
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

                message = format_whoop_sms(
                    cycle,
                    sleep,
                    recovery,
                )

                deliver_message(message, "Morning")
                return

        except Exception:
            logging.exception("Error checking WHOOP data")

        if attempt < MAX_ATTEMPTS:
            logging.info("Data not ready. Retrying in 10 minutes.")
            time.sleep(RETRY_DELAY)

    logging.error("WHOOP data still not ready after one hour.")


def evening():
    whoop = WhoopClient()

    data = whoop.get_daily_update()
    message = format_daily_update(data)

    deliver_message(message, "Evening")


def main():
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python -m app.main [morning|evening]"
        )

    job = sys.argv[1]

    if job == "morning":
        morning()
    elif job == "evening":
        evening()
    else:
        raise SystemExit(f"Unknown job: {job}")


if __name__ == "__main__":
    main()