# WHOOP Daily SMS

A small Python service that sends twice-daily WHOOP metric summaries to a dumb phone via iMessage.

The project is designed for a setup where the primary phone can remain at home while a dumb phone receives the important daily WHOOP information.

## Architecture

```text
WHOOP API
    ↓
Python app on Raspberry Pi
    ↓
Pushcut HTTP API
    ↓
iPhone Pushcut Automation Server
    ↓
iOS Shortcut
    ↓
iMessage
    ↓
Dumb Phone 2 / OpenBubbles
```

The Raspberry Pi runs the WHOOP API integration and sends the formatted messages to Pushcut. Pushcut triggers an iOS Shortcut on an iPhone, which sends the message via iMessage.

## Messages

Two messages are sent each day.

### Morning — 6:30 AM

The morning update contains:

* Recovery score
* HRV
* Resting heart rate
* Total sleep
* Sleep performance
* Sleep debt
* REM sleep
* Deep sleep
* Light sleep

Example:

```text
WHOOP — 2026-09-04
Recovery: 88%
HRV: 80 ms
Resting HR: 51 bpm
Sleep: 6h 54m (86%)
Sleep debt: 1h 2m
REM: 1h 36m
Deep: 1h 50m
Light: 3h 44m
```

The morning job checks whether the WHOOP data has been scored. If it isn't ready yet, it retries every 10 minutes for up to one hour.

### Evening — 9:00 PM

The evening update contains:

* Daily strain
* Activities/workouts completed that day
* Activity start time
* Activity duration
* Activity strain
* Recommended sleep duration

Example:

```text
WHOOP — Daily Update

Strain: 0.6

Activities:
• yard-work — 7:44 PM — 26m — 6.1 strain

Recommended sleep: 8h 51m
```

Activity times are converted to the configured local timezone.

## Requirements

* Raspberry Pi or other always-on Linux host
* Docker and Docker Compose
* WHOOP Developer API application
* iPhone with the Pushcut app
* Pushcut Automation Server
* iOS Shortcuts
* Dumb Phone 2 (or another device capable of receiving the resulting iMessage)

The iPhone must remain powered on and connected to Wi-Fi.

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/samcast1/whoop-daily-sms.git
cd whoop-daily-sms
```

### 2. Configure environment variables

Create `.env`:

```env
WHOOP_CLIENT_ID=
WHOOP_CLIENT_SECRET=
WHOOP_REDIRECT_URI=http://localhost:1234

PUSHCUT_URL=

TIMEZONE=America/New_York
```

`PUSHCUT_URL` is the Pushcut Automation Server endpoint for the shortcut that sends the message.

### 3. Authenticate with WHOOP

The one-time OAuth setup is handled outside the Docker container:

```bash
python setup/auth.py
```

The resulting token is saved to:

```text
data/whoop_token.json
```

This file contains OAuth credentials and is intentionally excluded from Git.

The `data/` directory is mounted into the container so the token persists between container runs and WHOOP refresh tokens can be updated.

### 4. Configure Pushcut

Create an iOS Shortcut named:

```text
WHOOP Send
```

The Shortcut should contain:

```text
Shortcut Input
    ↓
Send Message
```

The **Message** field of `Send Message` must use the `Shortcut Input` variable.

Configure Pushcut Automation Server to execute the shortcut.

The Pushcut endpoint receives the formatted WHOOP message as shortcut input.

### 5. Test the containers

Morning:

```bash
docker compose run --rm whoop-daily-sms morning
```

Evening:

```bash
docker compose run --rm whoop-daily-sms evening
```

These commands execute the complete pipeline and send the resulting message through Pushcut and iMessage.

## Scheduled operation

The Raspberry Pi uses cron to run the two daily jobs.

Example:

```cron
30 6 * * * cd /opt/whoop-daily-sms && docker compose run --rm whoop-daily-sms morning >> data/cron.log 2>&1

0 21 * * * cd /opt/whoop-daily-sms && docker compose run --rm whoop-daily-sms evening >> data/cron.log 2>&1
```

The host timezone should be configured for the desired local timezone:

```bash
timedatectl
```

Logs are written to:

```text
data/cron.log
```

## Project structure

```text
whoop-daily-sms/
├── app/
│   ├── __init__.py
│   ├── daily_formatter.py
│   ├── formatter.py
│   ├── main.py
│   ├── pushcut_client.py
│   └── whoop_client.py
├── data/
│   └── .gitkeep
├── setup/
│   └── auth.py
├── .env
├── .env.example
├── .gitignore
├── Dockerfile
├── compose.yml
├── README.md
└── requirements.txt
```

## Deployment

After pulling changes on the Raspberry Pi:

```bash
cd /opt/whoop-daily-sms
git pull
docker compose build
```

Then verify both jobs:

```bash
docker compose run --rm whoop-daily-sms morning
docker compose run --rm whoop-daily-sms evening
```

Once verified, cron handles the scheduled execution.

## Notes

### WHOOP data availability

WHOOP may not have finalized the previous night's sleep, recovery, or cycle data by 6:30 AM. The morning job therefore waits for all three datasets to have a `SCORED` state and retries every 10 minutes.

### OAuth token persistence

The WHOOP OAuth token is stored in `data/whoop_token.json`. Because `data/` is bind-mounted into the container, refreshed tokens persist across container runs.

Do not commit the token or `.env` file to the repository.

### Pushcut / iPhone

The iPhone acts as the bridge between the Raspberry Pi and iMessage. It needs to remain powered on, connected to Wi-Fi, signed into iMessage, and running Pushcut Automation Server.

Pushcut Automation Server requires the Pushcut app to be available in the foreground in order to process incoming automation requests.

### No Twilio required

This project originally used an SMS provider, but the current implementation uses Pushcut and iMessage instead. No cellular service or SMS API is required on the Raspberry Pi.

The iPhone provides the actual iMessage connection while the Dumb Phone 2 receives the messages through OpenBubbles.
