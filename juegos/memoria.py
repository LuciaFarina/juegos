import random
from typing import Any


WORDS = [
    "Eclipse", "Montaña", "Relámpago", "Almohada", "Laberinto",
    "Espejo", "Cactus", "Horizonte", "Guitarra", "Reloj",
    "Papel", "Murmullo", "Abismo", "Cometa", "Cosecha",
    "Tinta", "Susurro", "Escalera", "Nube", "Travesía",
    "Cascada", "Sombrero", "Destello", "Caracola", "Amanecer",
    "Ceniza", "Brújula", "Mariposa", "Cristal", "Viento"
]


def make_round(level: int) -> dict[str, Any]:
    shown = random.sample(WORDS, 5 * level)
    shuffled = shown[:]
    random.shuffle(shuffled)
    return {"shown": shown, "shuffled": shuffled}


def public_state(state: dict[str, Any], session_id: int | None = None) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "status": state["status"],
        "level": state.get("level", 1),
        "shown": state.get("shown", []),
        "shuffled": state.get("shuffled", []),
        "message": state.get("message", "Recordá el orden de las palabras."),
        "correctAnswer": state.get("correctAnswer") if state["status"] in {"failed", "lost", "won"} else None,
    }


def start(level: int = 1) -> dict[str, Any]:
    return {
        "status": "active", "level": level, **make_round(level),
        "message": "Recordá las palabras en orden.",
    }


def action(state: dict[str, Any], data: dict[str, Any]) -> tuple[dict[str, Any], str | None, int, str]:
    requested_action = str(data.get("action", "submit"))
    if requested_action == "continue" and state["status"] == "passed":
        next_level = state["level"] + 1
        new_state = start(next_level)
        new_state["message"] = f"Nivel {next_level}/4. Recordá el nuevo orden."
        return new_state, None, 0, new_state["message"]
    if requested_action == "retry" and state["status"] == "failed":
        new_state = start(state["level"])
        new_state["message"] = f"Reintentá el nivel {state['level']}."
        return new_state, None, 0, new_state["message"]
    if requested_action == "finish_after_pass" and state["status"] == "passed":
        state["status"] = "won"
        detail = f"Terminaste el juego de memoria luego de superar el nivel {state['level']}."
        return state, "won", state["level"], detail
    if requested_action == "finish_after_fail" and state["status"] == "failed":
        state["status"] = "lost"
        detail = f"Finalizaste luego de fallar el nivel {state['level']}."
        return state, "lost", state["level"] - 1, detail
    if state["status"] != "active":
        return state, None, 0, "La partida no está esperando respuesta."

    parts = str(data.get("order", "")).strip().split()
    shown = state["shown"]
    shuffled = state["shuffled"]
    correct = len(parts) == len(shown)
    if correct:
        for index, part in enumerate(parts):
            if not part.isdigit():
                correct = False
                break
            position = int(part)
            if position < 1 or position > len(shuffled) or shuffled[position - 1] != shown[index]:
                correct = False
                break
    correct_answer = [str(shuffled.index(word) + 1) for word in shown]

    if correct:
        if state["level"] >= 4:
            state["status"] = "won"
            state["message"] = "¡Completaste todos los niveles!"
            return state, "won", 4, "Completaste los 4 niveles del juego de memoria."
        state["status"] = "passed"
        state["message"] = f"¡Correcto! Superaste el nivel {state['level']}."
        return state, None, 0, state["message"]

    state["status"] = "failed"
    state["correctAnswer"] = " ".join(correct_answer)
    state["message"] = f"Orden incorrecto. Podés reintentar el nivel {state['level']} o terminar."
    return state, None, 0, state["message"]
