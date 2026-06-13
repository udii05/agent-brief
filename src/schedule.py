import time
from datetime import datetime, timedelta


def next_run_time(hour: int = 2, minute: int = 0):
    now = datetime.utcnow()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return target


def run_daily(hour: int = 2, minute: int = 0):
    from main import main

    print(f"Scheduled daily briefing at {hour:02d}:{minute:02d} UTC")

    while True:
        next_run = next_run_time(hour, minute)
        wait_seconds = (next_run - datetime.utcnow()).total_seconds()
        print(f"Next run at {next_run.isoformat()} (in {wait_seconds / 3600:.1f}h)")
        time.sleep(wait_seconds)
        print("Running scheduled briefing...")
        main(send_whatsapp=True)


if __name__ == "__main__":
    run_daily()
