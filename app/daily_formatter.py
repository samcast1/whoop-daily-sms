import os
from datetime import datetime
from zoneinfo import ZoneInfo


TIMEZONE = ZoneInfo(os.getenv("TIMEZONE", "America/New_York"))


def format_duration(milliseconds):
    minutes = round(milliseconds / 60_000)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m"


def format_time(timestamp):
    dt = datetime.fromisoformat(timestamp)
    dt = dt.astimezone(TIMEZONE)
    return dt.strftime("%-I:%M %p")


def format_daily_update(data):
    cycle = data["cycle"]
    workouts = data["workouts"]
    sleep = data["sleep"]

    lines = [
        "WHOOP — Daily Update",
        "",
        f"Strain: {cycle['score']['strain']:.1f}",
    ]

    if workouts:
        lines.extend(["", "Activities:"])

        for workout in workouts:
            start = datetime.fromisoformat(workout["start"])
            end = datetime.fromisoformat(workout["end"])

            duration = end - start
            total_minutes = round(duration.total_seconds() / 60)
            hours, minutes = divmod(total_minutes, 60)

            if hours:
                duration_text = f"{hours}h {minutes}m"
            else:
                duration_text = f"{minutes}m"

            lines.append(
                f"• {workout['sport_name']} — "
                f"{format_time(workout['start'])} — "
                f"{duration_text} — "
                f"{workout['score']['strain']:.1f} strain"
            )
    else:
        lines.extend(["", "Activities: None"])

    if sleep and sleep["score_state"] == "SCORED":
        sleep_needed = sleep["score"]["sleep_needed"]

        total_needed = (
            sleep_needed["baseline_milli"]
            + sleep_needed["need_from_sleep_debt_milli"]
            + sleep_needed["need_from_recent_strain_milli"]
            + sleep_needed["need_from_recent_nap_milli"]
        )

        lines.extend([
            "",
            f"Recommended sleep: {format_duration(total_needed)}",
        ])

    return "\n".join(lines)