import os

from fastapi import FastAPI, Header, HTTPException

from app.service import get_morning_poll, get_evening

app = FastAPI(title="WHOOP API")

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/morning")
def morning():
    return {
        "success": True,
        "message": get_morning_poll(),
    }


@app.post("/evening")
def evening():
    return {
        "success": True,
        "message": get_evening(),
    }