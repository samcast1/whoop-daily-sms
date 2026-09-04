def format_duration(milliseconds):
    minutes = round(milliseconds / 60_000)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m"


def format_whoop_sms(cycle, sleep, recovery):
    cycle_score = cycle["score"]
    sleep_score = sleep["score"]
    recovery_score = recovery["score"]

    sleep_stages = sleep_score["stage_summary"]

    sleep_duration = (
        sleep_stages["total_light_sleep_time_milli"]
        + sleep_stages["total_slow_wave_sleep_time_milli"]
        + sleep_stages["total_rem_sleep_time_milli"]
    )

    sleep_debt = sleep_score["sleep_needed"]["need_from_sleep_debt_milli"]

    return (
        f"WHOOP — {sleep['start'][:10]}\n"
        f"Recovery: {recovery_score['recovery_score']:.0f}%\n"
        f"HRV: {recovery_score['hrv_rmssd_milli']:.0f} ms\n"
        f"Resting HR: {recovery_score['resting_heart_rate']:.0f} bpm\n"
        f"Sleep: {sleep_score['sleep_performance_percentage']:.0f}%\n"
        f"Total Duration: {format_duration(sleep_duration)}\n"
        f"REM: {format_duration(sleep_stages['total_rem_sleep_time_milli'])}\n"
        f"Deep: {format_duration(sleep_stages['total_slow_wave_sleep_time_milli'])}\n"
        f"Light: {format_duration(sleep_stages['total_light_sleep_time_milli'])}\n"
        f"Sleep debt: {format_duration(sleep_debt)}\n"
    )