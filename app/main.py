import logging
import sys

from app.pushcut_client import PushcutClient
from app.service import get_morning, get_evening

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

SEND_MESSAGE = True


def deliver_message(message, label):
    if SEND_MESSAGE:
        pushcut = PushcutClient()
        pushcut.send_message(message)
        logging.info("%s message sent via Pushcut", label)
    else:
        print()
        print("=" * 40)
        print(f"{label.upper()} MESSAGE (TEST MODE)")
        print("=" * 40)
        print(message)
        print("=" * 40)


def main():
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python -m app.main [morning|evening]"
        )

    job = sys.argv[1]

    if job == "morning":
        deliver_message(get_morning(), "Morning")

    elif job == "evening":
        deliver_message(get_evening(), "Evening")

    else:
        raise SystemExit(f"Unknown job: {job}")


if __name__ == "__main__":
    main()