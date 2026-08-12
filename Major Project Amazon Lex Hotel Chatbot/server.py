from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, cast

from flask import Flask, jsonify, request, send_from_directory

from python import ROOM_CATALOG, lambda_handler, validate_booking

BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path="")


def _build_lex_event(room_type: str, nights: int, check_in_date: str) -> Dict[str, Any]:
    return {
        "invocationSource": "FulfillmentCodeHook",
        "sessionState": {
            "intent": {
                "name": "BookHotel",
                "slots": {
                    "RoomType": {"value": {"interpretedValue": room_type}},
                    "Nights": {"value": {"interpretedValue": str(nights)}},
                    "CheckInDate": {"value": {"interpretedValue": check_in_date}},
                },
            },
            "sessionAttributes": {},
        },
    }


def _validate_payload(payload: Dict[str, Any]) -> str | None:
    room_type = str(payload.get("roomType", "")).strip()
    nights_raw = payload.get("nights", "")
    check_in_date = str(payload.get("checkInDate", "")).strip()

    if room_type not in ROOM_CATALOG:
        return "Invalid room type selected."

    try:
        nights = int(str(nights_raw).strip())
    except (TypeError, ValueError):
        return "Nights must be a whole number."

    validation_error = validate_booking(room_type, str(nights))
    if validation_error:
        return validation_error

    try:
        parsed_date = datetime.strptime(check_in_date, "%Y-%m-%d").date()
    except ValueError:
        return "Check-in date must be in YYYY-MM-DD format."

    if parsed_date < datetime.now().date():
        return "Check-in date cannot be in the past."

    return None


@app.get("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


@app.get("/<path:path>")
def static_files(path: str):
    return send_from_directory(BASE_DIR, path)


@app.post("/api/book")
def book_hotel():
    raw_payload = request.get_json(silent=True)
    payload = cast(Dict[str, Any], raw_payload) if isinstance(raw_payload, dict) else {}
    error = _validate_payload(payload)
    if error:
        return jsonify({"ok": False, "message": error}), 400

    room_type = str(payload["roomType"]).strip()
    nights = int(payload["nights"])
    check_in_date = str(payload["checkInDate"]).strip()

    event = _build_lex_event(room_type, nights, check_in_date)
    lex_response = lambda_handler(event, None)

    message = "Booking could not be completed."
    raw_messages = lex_response.get("messages", [])
    if isinstance(raw_messages, list) and raw_messages and isinstance(raw_messages[0], dict):
        first_message = cast(Dict[str, Any], raw_messages[0])
        message = str(first_message.get("content", message))

    return jsonify({"ok": True, "message": message, "lexResponse": lex_response})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
