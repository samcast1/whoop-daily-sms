# whoop-daily-sms

A small Dockerized service that sends daily WHOOP metrics via SMS, designed for living without a smartphone.

The service pulls data directly from the WHOOP API and sends two messages each day:

* **6:30 AM** — sleep, recovery, HRV, resting heart rate, sleep stages, and sleep debt
* **9:00 PM** — daily strain, activities/workouts, and recommended sleep duration

Messages can also be printed to the console instead of being sent via Twilio for testing.

## Architecture

```text
                  ┌──────────────┐
                  │  WHOOP API   │
                  └──────┬───────┘
                         │
                         ▼
                ┌─────────────────┐
                │ Python service  │
                │                 │
                │ WHOOP client    │
                │ Formatters      │
                │ Twilio client   │
                └────────┬────────┘
                         │
                    ┌────┴────┐
                    │         │
                    ▼         ▼
                 Twilio    Console
                    │
                    ▼
                   SMS
```

The application itself is intentionally small. Cron handles scheduling, Docker handles the runtime environment, and WHOOP/Twilio handle the external services.

---

## Requirements

* Docker
* Docker Compose
* A WHOOP account
* A WHOOP Developer application
* A Twilio account and phone number
* A host capable of running cron

The intended deployment is a small always-on machine such as a Raspberry Pi.

---

## 1. Clone the repository

```bash
git clone https://github.com/samcast1/whoop-daily-sms.git
cd whoop-daily-sms
```

---

## 2. Create the WHOOP Developer App

Create an application in the [WHOOP Developer Dashboard](https://developer.whoop.com/).

Configure the application with:

```text
Redirect URI:
http://localhost:1234
```

The application requires these scopes:

```text
offline
read:recovery
read:cycles
read:sleep
read:workout
read:profile
read:body_measurement
```

You will need the application's:

* Client ID
* Client Secret

---

## 3. Configure environment variables

Copy the example environment file:

```bash
cp .env.example .env
```

Populate `.env`:

```env
WHOOP_CLIENT_ID=your_whoop_client_id
WHOOP_CLIENT_SECRET=your_whoop_client_secret
WHOOP_REDIRECT_URI=http://localhost:1234

TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_FROM_NUMBER=+1xxxxxxxxxx
TWILIO_TO_NUMBER=+1xxxxxxxxxx
```

Do **not** commit `.env`. It is included in `.gitignore`.

---

## 4. Authenticate with WHOOP

The initial WHOOP authorization is handled separately from the Dockerized application using `setup/auth.py`.

Install the Python dependencies locally:

```bash
pip install -r requirements.txt
```

Then run:

```bash
python setup/auth.py
```

This uses [`whoopy`](https://github.com/felixnext/whoopy) to perform the WHOOP OAuth flow.

A browser window will open for WHOOP authorization. After approving access, the browser will redirect to:

```text
http://localhost:1234
```

The page itself does not need to load successfully. Copy the **entire URL from the browser's address bar** and paste it into the terminal when prompted.

The authentication script saves the resulting OAuth token to:

```text
data/whoop_token.json
```

The token file is intentionally excluded from Git.

The application later uses this persisted token and refreshes the access token when necessary.

### Why authenticate outside Docker?

The OAuth flow requires interactive browser authorization, so it is simplest to perform this one-time step directly on the machine where the repository is being configured.

Once `data/whoop_token.json` exists, the normal application runs entirely inside Docker.

---

## 5. Configure Twilio

Create a Twilio account and obtain a Twilio phone number capable of sending SMS.

You will need:

```text
Account SID
Auth Token
Twilio phone number
Destination phone number
```

Put these values in `.env`.

### US 10DLC registration

If sending SMS from a US local 10-digit Twilio number to a US phone number, Twilio requires **A2P 10DLC registration**, including for individuals and hobby projects.

For a personal project without an EIN, Twilio supports registering as a **Sole Proprietor**.

The basic process is:

1. Upgrade the Twilio account from trial.
2. Purchase a US 10DLC phone number.
3. Create/complete the Twilio compliance profile.
4. Register the account as a Sole Proprietor Brand if applicable.
5. Create the messaging Campaign.
6. Associate the Twilio phone number with the Campaign.
7. Wait for the registration to be approved.

Twilio currently notes that campaign reviews can take approximately 10–15 days.

---

## 6. Build the Docker image

Build the application:

```bash
docker compose build
```

The Compose configuration:

* builds the Python image
* loads `.env`
* mounts `./data` into `/app/data`
* sets `app.main` as the container entrypoint

This allows the job to be selected simply by passing `morning` or `evening`.

---

## 7. Test the morning job

Run:

```bash
docker compose run --rm whoop-daily-sms morning
```

The morning job checks whether the WHOOP cycle, sleep, and recovery data have been scored.

If the data is not ready yet, it waits 10 minutes and tries again, up to six times.

The resulting message looks approximately like:

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

---

## 8. Test the evening job

Run:

```bash
docker compose run --rm whoop-daily-sms evening
```

The evening message contains the day's strain and recorded activities, along with recommended sleep duration.

Example:

```text
WHOOP — Daily Update

Strain: 0.6

Activities:
• yard-work — 11:44 PM — 26m — 6.1 strain

Recommended sleep: 8h 51m
```

---

## 9. Console vs. SMS mode

The application supports a simple test mode so messages can be verified without sending SMS.

In `app/main.py`:

```python
SEND_SMS = False
```

With this setting, the formatted message is printed to the console.

Once Twilio is ready:

```python
SEND_SMS = True
```

The same commands will then send the message through Twilio instead.

No other part of the scheduling configuration needs to change.

---

# Deployment

The application is designed to run as a short-lived Docker container rather than as a continuously running service.

Cron starts a fresh container for each scheduled job.

## Cron schedule

Edit the host's crontab:

```bash
crontab -e
```

Add:

```cron
30 6 * * * cd /path/to/whoop-daily-sms && docker compose run --rm whoop-daily-sms morning >> data/cron.log 2>&1
0 21 * * * cd /path/to/whoop-daily-sms && docker compose run --rm whoop-daily-sms evening >> data/cron.log 2>&1
```

This produces:

| Time    | Job                         |
| ------- | --------------------------- |
| 6:30 AM | Morning recovery/sleep SMS  |
| 9:00 PM | Evening strain/activity SMS |

### Cron timezone

Cron uses the **host system's timezone**.

Make sure the deployment host is configured for the desired timezone:

```bash
timedatectl
```

For example:

```text
Time zone: America/New_York
```

If the host is configured correctly, the cron schedule above will run at 6:30 AM and 9:00 PM local time.

This is particularly worth checking when deploying to a Raspberry Pi or another machine that may have been configured with UTC.

---

## Cron logging

The cron entries redirect output to:

```text
data/cron.log
```

View the log with:

```bash
tail -f data/cron.log
```

This captures both normal application output and errors:

```cron
>> data/cron.log 2>&1
```

---

# Updating the application

Pull the latest code:

```bash
git pull
```

Rebuild the image:

```bash
docker compose build
```

The next scheduled job will use the newly built image.

You can also test immediately:

```bash
docker compose run --rm whoop-daily-sms morning
```

or:

```bash
docker compose run --rm whoop-daily-sms evening
```

---

# Project Structure

```text
whoop-daily-sms/
├── app/
│   ├── __init__.py
│   ├── daily_formatter.py
│   ├── formatter.py
│   ├── main.py
│   ├── twilio_client.py
│   └── whoop_client.py
│
├── data/
│   └── .gitkeep
│
├── setup/
│   └── auth.py
│
├── .env
├── .env.example
├── .gitignore
├── compose.yml
├── Dockerfile
└── requirements.txt
```

### Components

**`setup/auth.py`**

Performs the one-time interactive WHOOP OAuth authorization using `whoopy` and persists the resulting token.

**`app/whoop_client.py`**

Communicates directly with the WHOOP API and handles access-token refresh.

**`app/formatter.py`**

Formats the morning recovery and sleep data into an SMS.

**`app/daily_formatter.py`**

Formats the evening strain and activity data.

**`app/twilio_client.py`**

Sends formatted messages through Twilio.

**`app/main.py`**

Dispatches the requested job:

```text
morning
evening
```

and handles the morning retry behavior.

**`compose.yml`**

Provides the container runtime configuration and mounts the persistent WHOOP token into the container.

---

## Design Philosophy

This project deliberately keeps the architecture simple:

* WHOOP is the source of truth.
* No database is required.
* No web server is required.
* No continuously running application process is required.
* Cron provides scheduling.
* Docker provides isolation and reproducibility.
* Twilio provides SMS delivery.
* The application only formats and delivers the metrics needed.
* No AI, recommendations, or additional processing are involved.

The end result is a tiny service that can quietly run on an always-on machine and provide the useful parts of WHOOP without requiring a smartphone.
