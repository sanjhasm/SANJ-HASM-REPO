\
from __future__ import annotations
from fastapi import Request, HTTPException

def require_user(request: Request):
    if not request.session.get("user"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return request.session["user"]

def check_login(username: str, password: str, cfg: dict) -> bool:
    auth = cfg.get("auth", {})
    return username == auth.get("username") and password == auth.get("password")
