import os

from fastapi import FastAPI, Header, HTTPException

from app.service import get_morning, get_evening

app = FastAPI(title="WHOOP API")

API_TOKEN = os.environ["WHOOP_API_TOKEN"]


def authenticate(authorization: str | None):
    expected = f"Bearer {API_TOKEN}"

    if authorization != expected:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
        )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/morning")
def morning(authorization: str | None = Header(default=None)):
    authenticate(authorization)

    message = get_morning()

    return {
        "success": True,
        "message": message,
    }


@app.post("/evening")
def evening(authorization: str | None = Header(default=None)):
    authenticate(authorization)

    message = get_evening()

    return {
        "success": True,
        "message": message,
    }