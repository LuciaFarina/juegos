import random
from typing import Any


WORDS = [
    "perro", "gato", "libro", "escuela", "elefante", "mariposa", "dinosaurio",
    "helicoptero", "estrella", "computadora", "camioneta", "esmeralda",
    "catedral", "enciclopedia", "espejo", "telescopio", "refrigerador", "bicicleta", "paracaidas", "astronauta", "murcielago", "cangrejo", "jirafa", "hipopotamo", "cocodrilo", "serpiente", "tortuga", "camaleon", "ornitorrinco"
]


def public_state(state: dict[str, Any], session_id: int | None = None) -> dict[str, Any]:
    word = state["word"]
    guessed = set(state.get("guessed", []))
    return {
        "session_id": session_id,
        "status": state["status"],
        "masked": " ".join(ch if ch in guessed else "_" for ch in word),
        "used": state.get("guessed", []),
        "errors": state.get("errors", 0),
        "max_errors": 6,
        "message": state.get("message", ""),
        "word": word if state["status"] in {"won", "lost"} else None,
    }


def start() -> dict[str, Any]:
    return {
        "status": "active",
        "word": random.choice(WORDS),
        "guessed": [],
        "errors": 0,
        "message": "Ingresá una letra para jugar.",
    }


def action(state: dict[str, Any], data: dict[str, Any]) -> tuple[dict[str, Any], str | None, int, str]:
    if state["status"] != "active":
        return state, None, 0, "La partida ya terminó."
    letter = str(data.get("letter", "")).strip().lower()[:1]
    if not letter or not letter.isalpha():
        state["message"] = "Ingresá una letra válida."
        return state, None, 0, state["message"]
    if letter in state["guessed"]:
        state["message"] = f"Ya usaste la letra {letter}."
        return state, None, 0, state["message"]

    state["guessed"].append(letter)
    if letter not in state["word"]:
        state["errors"] += 1
        state["message"] = f"La letra {letter} no está en la palabra."
    else:
        state["message"] = f"Bien: la letra {letter} está en la palabra."

    if all(ch in state["guessed"] for ch in state["word"]):
        state["status"] = "won"
        score = max(0, 100 - state["errors"] * 10)
        detail = f"Adivinaste la palabra '{state['word']}' con {state['errors']} errores."
        return state, "won", score, detail
    if state["errors"] >= 6:
        state["status"] = "lost"
        detail = f"Se terminaron los intentos. La palabra era '{state['word']}'."
        return state, "lost", 0, detail
    return state, None, 0, state["message"]
