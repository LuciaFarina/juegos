from __future__ import annotations

import json
import re
import sys
from http import HTTPStatus
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from app import (  # noqa: E402
    ACTIONS,
    ApiError,
    GAMES,
    PUBLIC,
    STARTERS,
    check_password,
    connect_db,
    create_game_session,
    create_login_session,
    find_user_by_username,
    hash_password,
    init_db,
    load_game_session,
    normalize_username,
    record_score,
    save_state,
    STATIC_DIR,
    user_from_token,
    validate_password,
)

init_db()

app = FastAPI(title="Los Idos Arcade", version="1.0.0")


async def read_json(request: Request) -> dict[str, Any]:
    body = await request.body()
    if not body:
        return {}
    try:
        data = json.loads(body.decode("utf-8"))
    except Exception as exc:
        raise ApiError("El body debe ser JSON válido.") from exc
    if not isinstance(data, dict):
        raise ApiError("El body debe ser un objeto JSON.")
    return data


def make_json_response(payload: dict[str, Any], status: int = 200, cookie: str | None = None, clear_cookie: bool = False) -> JSONResponse:
    response = JSONResponse(content=payload, status_code=status)
    if cookie:
        response.set_cookie(key="session_token", value=cookie, httponly=True, samesite="lax", path="/")
    if clear_cookie:
        response.delete_cookie(key="session_token", path="/")
    return response


def cookie_token(request: Request) -> str | None:
    return request.cookies.get("session_token")


def current_user(store: Any, request: Request) -> Any:
    return user_from_token(store, cookie_token(request))


def require_user(store: Any, request: Request) -> Any:
    user = current_user(store, request)
    if not user:
        raise ApiError("Tenés que iniciar sesión.", HTTPStatus.UNAUTHORIZED)
    return user


@app.get("/")
async def index() -> HTMLResponse:
    content = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(content=content)


@app.get("/static/{file_path:path}")
async def static_files(file_path: str) -> FileResponse:
    safe_path = (STATIC_DIR / file_path).resolve()
    if not safe_path.exists() or not safe_path.is_file() or STATIC_DIR.resolve() not in safe_path.parents:
        raise ApiError("Archivo no encontrado", HTTPStatus.NOT_FOUND)
    return FileResponse(safe_path)


@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def api_router(request: Request, path: str) -> Response:
    method = request.method.upper()
    try:
        data = await read_json(request) if method in {"POST", "PUT", "PATCH"} else {}
        with connect_db() as store:
            if store.backend == "sqlite":
                store.sqlite_conn.execute("PRAGMA foreign_keys = ON")

            if path == "register" and method == "POST":
                username = normalize_username(str(data.get("username", "")))
                password = str(data.get("password", ""))
                validate_password(password)

                existing_user = find_user_by_username(store, username)
                if existing_user:
                    user_id = int(existing_user["id"]) if store.backend == "sqlite" else int(existing_user["_id"])
                    stored_hash = existing_user["password_hash"]
                    if check_password(password, stored_hash):
                        token = create_login_session(store, user_id)
                        if store.backend == "sqlite":
                            store.sqlite_conn.commit()
                        return make_json_response(
                            {
                                "ok": True,
                                "mode": "login",
                                "message": "Ese usuario ya existía, entonces se inició sesión normalmente.",
                                "user": {"id": user_id, "username": existing_user["username"]},
                            },
                            cookie=token,
                        )
                    raise ApiError("Ese usuario ya existe. Usá Ingresar con su contraseña correcta.", HTTPStatus.CONFLICT)

                if store.backend == "sqlite":
                    cur = store.sqlite_conn.execute(
                        "INSERT INTO users(username, password_hash, created_at) VALUES (?, ?, ?)",
                        (username, hash_password(password), ""),
                    )
                    user_id = int(cur.lastrowid)
                else:
                    user_id = 1
                    store.mongo_db.users.insert_one(
                        {
                            "_id": user_id,
                            "username": username,
                            "password_hash": hash_password(password),
                            "created_at": "",
                        }
                    )

                token = create_login_session(store, user_id)
                if store.backend == "sqlite":
                    store.sqlite_conn.commit()
                return make_json_response(
                    {
                        "ok": True,
                        "mode": "register",
                        "message": "Cuenta creada correctamente.",
                        "user": {"id": user_id, "username": username},
                    },
                    cookie=token,
                )

            if path == "login" and method == "POST":
                username = normalize_username(str(data.get("username", "")))
                password = str(data.get("password", ""))
                row = find_user_by_username(store, username)
                if not row:
                    raise ApiError("Ese usuario no existe. Primero creá la cuenta.", HTTPStatus.UNAUTHORIZED)
                stored_hash = row["password_hash"]
                if not check_password(password, stored_hash):
                    raise ApiError("Contraseña incorrecta para ese usuario.", HTTPStatus.UNAUTHORIZED)
                token = create_login_session(store, int(row["id"]) if store.backend == "sqlite" else int(row["_id"]))
                if store.backend == "sqlite":
                    store.sqlite_conn.commit()
                return make_json_response(
                    {
                        "ok": True,
                        "mode": "login",
                        "message": "Sesión iniciada correctamente.",
                        "user": {"id": row["id"] if store.backend == "sqlite" else row["_id"], "username": row["username"]},
                    },
                    cookie=token,
                )

            if path == "users" and method == "GET":
                if store.backend == "sqlite":
                    rows = store.sqlite_conn.execute(
                        "SELECT id, username, created_at FROM users ORDER BY username COLLATE NOCASE"
                    ).fetchall()
                    return make_json_response({"ok": True, "users": [dict(r) for r in rows]})
                rows = list(store.mongo_db.users.find({}, {"_id": 1, "username": 1, "created_at": 1}).sort("username", 1))
                users = []
                for row in rows:
                    users.append({"id": row["_id"], "username": row["username"], "created_at": row.get("created_at")})
                return make_json_response({"ok": True, "users": users})

            if path == "logout" and method == "POST":
                token = cookie_token(request)
                if token:
                    if store.backend == "sqlite":
                        store.sqlite_conn.execute("DELETE FROM login_sessions WHERE token = ?", (token,))
                        store.sqlite_conn.commit()
                    else:
                        store.mongo_db.login_sessions.delete_one({"token": token})
                return make_json_response({"ok": True}, clear_cookie=True)

            if path == "me" and method == "GET":
                user = current_user(store, request)
                if store.backend == "sqlite":
                    store.sqlite_conn.commit()
                if not user:
                    return make_json_response({"ok": True, "user": None})
                return make_json_response({"ok": True, "user": {"id": user["id"], "username": user["username"]}})

            if path == "games" and method == "GET":
                require_user(store, request)
                return make_json_response({"ok": True, "games": [{"key": k, "title": v} for k, v in GAMES.items()]})

            if path == "scores" and method == "GET":
                user = require_user(store, request)
                if store.backend == "sqlite":
                    rows = store.sqlite_conn.execute(
                        "SELECT game_key, result, score, detail, created_at FROM scores WHERE user_id = ? ORDER BY id DESC LIMIT 50",
                        (user["id"],),
                    ).fetchall()
                    summary_rows = store.sqlite_conn.execute(
                        "SELECT game_key, SUM(CASE WHEN result = 'won' THEN 1 ELSE 0 END) AS won, SUM(CASE WHEN result = 'lost' THEN 1 ELSE 0 END) AS lost, MAX(score) AS best_score FROM scores WHERE user_id = ? AND result IN ('won','lost') GROUP BY game_key",
                        (user["id"],),
                    ).fetchall()
                    return make_json_response({"ok": True, "scores": [dict(r) for r in rows], "summary": [dict(r) for r in summary_rows], "gameTitles": GAMES})

                rows = list(store.mongo_db.scores.find({"user_id": user["id"]}, {"_id": 0, "game_key": 1, "result": 1, "score": 1, "detail": 1, "created_at": 1}).sort("created_at", -1).limit(50))
                summary_rows = list(store.mongo_db.scores.aggregate([
                    {"$match": {"user_id": user["id"], "result": {"$in": ["won", "lost"]}}},
                    {"$group": {"_id": "$game_key", "won": {"$sum": {"$cond": [{"$eq": ["$result", "won"]}, 1, 0] }}, "lost": {"$sum": {"$cond": [{"$eq": ["$result", "lost"]}, 1, 0] }}, "best_score": {"$max": "$score"}}},
                    {"$project": {"game_key": "$_id", "won": 1, "lost": 1, "best_score": 1, "_id": 0}},
                    {"$sort": {"game_key": 1}},
                ]))
                return make_json_response({"ok": True, "scores": rows, "summary": summary_rows, "gameTitles": GAMES})

            start_match = re.fullmatch(r"games/([^/]+)/start", path)
            if start_match and method == "POST":
                game_key = start_match.group(1)
                if game_key not in GAMES:
                    raise ApiError("Juego inválido.", HTTPStatus.NOT_FOUND)
                user = require_user(store, request)
                state = STARTERS[game_key](data)
                session_id = create_game_session(store, int(user["id"]), game_key, state)
                if store.backend == "sqlite":
                    store.sqlite_conn.commit()
                return make_json_response({"ok": True, "game": game_key, "title": GAMES[game_key], "state": PUBLIC[game_key](state, session_id)})

            action_match = re.fullmatch(r"games/([^/]+)/action", path)
            if action_match and method == "POST":
                game_key = action_match.group(1)
                if game_key not in GAMES:
                    raise ApiError("Juego inválido.", HTTPStatus.NOT_FOUND)
                user = require_user(store, request)
                try:
                    session_id = int(data.get("session_id"))
                except Exception as exc:
                    raise ApiError("Falta session_id de la partida.") from exc
                row = load_game_session(store, int(user["id"]), session_id, game_key)
                state = json.loads(row["state_json"])
                state, result, score, detail = ACTIONS[game_key](state, data)
                status_for_db = state["status"] if state["status"] in {"won", "lost", "cancelled"} else "active"
                save_state(store, session_id, state, status_for_db)
                if result in {"won", "lost"}:
                    record_score(store, int(user["id"]), session_id, game_key, result, score, detail)
                if store.backend == "sqlite":
                    store.sqlite_conn.commit()
                return make_json_response({"ok": True, "game": game_key, "title": GAMES[game_key], "state": PUBLIC[game_key](state, session_id)})

            raise ApiError("Endpoint no encontrado", HTTPStatus.NOT_FOUND)
    except ApiError as exc:
        return make_json_response({"ok": False, "error": exc.message}, status=exc.status)
    except ValueError as exc:
        return make_json_response({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
    except Exception as exc:
        return make_json_response({"ok": False, "error": f"Error interno: {exc}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)


@app.get("/health")
async def health() -> JSONResponse:
    return make_json_response({"ok": True, "status": "ok"})
