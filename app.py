from __future__ import annotations

import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional

from flask import Flask, jsonify, request, abort

app = Flask(__name__)

# In-memory store (good for demo & CI). In real systems, use a DB.
@dataclass
class User:
    id: int
    name: str
    email: str
    created_at: str

_USERS: Dict[int, User] = {}
_NEXT_ID: int = 1


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@app.get("/")
def root():
    return jsonify({
        "service": "flask-user-health-api",
        "version": os.getenv("APP_VERSION", "dev"),
        "docs": {
            "health": "/health",
            "users": "/users"
        }
    })


@app.get("/health")
def health():
    # Health endpoint for monitoring checks
    return jsonify({
        "status": "ok",
        "time_utc": _utc_now_iso()
    })


@app.get("/users")
def list_users():
    users = [asdict(u) for u in _USERS.values()]
    return jsonify({"count": len(users), "users": users})


@app.post("/users")
def create_user():
    global _NEXT_ID

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()

    if not name or not email or "@" not in email:
        return jsonify({
            "error": "ValidationError",
            "message": "Provide valid 'name' and 'email'."
        }), 400

    user = User(
        id=_NEXT_ID,
        name=name,
        email=email,
        created_at=_utc_now_iso(),
    )
    _USERS[_NEXT_ID] = user
    _NEXT_ID += 1
    return jsonify(asdict(user)), 201


@app.get("/users/<int:user_id>")
def get_user(user_id: int):
    user = _USERS.get(user_id)
    if not user:
        return jsonify({"error": "NotFound", "message": "User not found"}), 404
    return jsonify(asdict(user))


@app.delete("/users/<int:user_id>")
def delete_user(user_id: int):
    user = _USERS.pop(user_id, None)
    if not user:
        return jsonify({"error": "NotFound", "message": "User not found"}), 404
    return jsonify({"deleted": user_id})


if __name__ == "__main__":
    # For local dev only. In Docker we use gunicorn.
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
