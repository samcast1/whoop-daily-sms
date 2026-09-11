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
def morning():
    return {
        "success": True,
        "message": get_morning(),
    }


@app.post("/evening")
def evening():
    return {
        "success": True,
        "message": get_evening(),
    }