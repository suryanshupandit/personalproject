"""Amazon Lex V2 fulfillment code for a hotel room booking bot.

The bot supports the BookHotel intent and guides the user through:
1. Choosing a room category.
2. Providing the number of nights.
3. Providing the check-in date.
4. Returning the booking summary with price and stay duration.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, cast


ROOM_CATALOG: Dict[str, Dict[str, Any]] = {
    "Classic": {
        "price": 1500,
        "description": "Comfortable standard room for a budget-friendly stay.",
    },
    "Duplex": {
        "price": 3000,
        "description": "Two-level room with extra space for families or groups.",
    },
    "Suite": {
        "price": 5000,
        "description": "Premium room with enhanced comfort and amenities.",
    },
    "Deluxe": {
        "price": 4000,
        "description": "Spacious upgraded room with modern facilities.",
    },
    "Family": {
        "price": 4500,
        "description": "Designed for family stays with extra bedding space.",
    },
    "Executive": {
        "price": 6000,
        "description": "Executive-class stay for business and premium guests.",
    },
}

DEFAULT_INTENT = "BookHotel"


def _as_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        typed_value = cast(Dict[object, Any], value)
        return {str(k): v for k, v in typed_value.items()}
    return {}


def _as_session_attributes(value: Any) -> Dict[str, str]:
    if not isinstance(value, dict):
        return {}

    typed_value = cast(Dict[object, Any], value)
    result: Dict[str, str] = {}
    for key, item in typed_value.items():
        result[str(key)] = str(item)
    return result


def get_slot_value(slots: Dict[str, Any], slot_name: str) -> Optional[str]:
    """Extract the interpreted value of a Lex slot safely."""

    slot = slots.get(slot_name)
    if not slot:
        return None

    value = slot.get("value")
    if not value:
        return None

    interpreted_value = value.get("interpretedValue")
    if interpreted_value is None:
        return None

    return str(interpreted_value).strip()


def room_options_text() -> str:
    """Return a compact description of all available room categories."""

    lines = ["Available room types:"]
    for room_name, details in ROOM_CATALOG.items():
        lines.append(f"- {room_name}: Rs. {details['price']} per night")
    return "\n".join(lines)


def build_message(content: str) -> Dict[str, str]:
    return {"contentType": "PlainText", "content": content}


def elicit_slot(
    intent_name: str,
    slots: Dict[str, Any],
    slot_to_elicit: str,
    message: str,
    session_attributes: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    return {
        "sessionState": {
            "dialogAction": {
                "type": "ElicitSlot",
                "slotToElicit": slot_to_elicit,
            },
            "intent": {
                "name": intent_name,
                "slots": slots,
                "state": "InProgress",
            },
            "sessionAttributes": session_attributes or {},
        },
        "messages": [build_message(message)],
    }


def close(
    intent_name: str,
    message: str,
    session_attributes: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    return {
        "sessionState": {
            "dialogAction": {"type": "Close"},
            "intent": {
                "name": intent_name,
                "state": "Fulfilled",
            },
            "sessionAttributes": session_attributes or {},
        },
        "messages": [build_message(message)],
    }


def validate_booking(room_type: Optional[str], num_nights: Optional[str]) -> Optional[str]:
    """Validate booking inputs and return an error message if something is wrong."""

    if room_type and room_type not in ROOM_CATALOG:
        return (
            f"Please choose a valid room type. {room_options_text()}"
        )

    if num_nights is not None:
        try:
            nights = int(num_nights)
        except ValueError:
            return "Please enter the number of nights as a whole number."

        if nights <= 0:
            return "The number of nights must be at least 1."

        if nights > 30:
            return "For this booking flow, the maximum stay is 30 nights."

    return None


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Entry point used by Amazon Lex V2."""

    session_state = _as_dict(event.get("sessionState", {}))
    intent = _as_dict(session_state.get("intent", {}))
    slots = _as_dict(intent.get("slots") or {})
    intent_name = str(intent.get("name", DEFAULT_INTENT))
    invocation_source = str(event.get("invocationSource", "FulfillmentCodeHook"))
    session_attributes = _as_session_attributes(session_state.get("sessionAttributes", {}))

    room_type = get_slot_value(slots, "RoomType")
    num_nights = get_slot_value(slots, "Nights")
    check_in = get_slot_value(slots, "CheckInDate")

    if intent_name != DEFAULT_INTENT:
        return close(
            intent_name,
            "I can only handle the hotel booking flow in this project.",
            session_attributes,
        )

    if invocation_source == "DialogCodeHook":
        validation_error = validate_booking(room_type, num_nights)
        if validation_error:
            if room_type and room_type not in ROOM_CATALOG:
                return elicit_slot(
                    intent_name,
                    slots,
                    "RoomType",
                    validation_error,
                    session_attributes,
                )

            if num_nights is not None:
                try:
                    nights = int(num_nights)
                except ValueError:
                    nights = None

                if nights is None or nights <= 0 or nights > 30:
                    return elicit_slot(
                        intent_name,
                        slots,
                        "Nights",
                        validation_error,
                        session_attributes,
                    )

            return elicit_slot(
                intent_name,
                slots,
                "RoomType",
                validation_error,
                session_attributes,
            )

        if not room_type:
            return elicit_slot(
                intent_name,
                slots,
                "RoomType",
                f"Please choose a room type. {room_options_text()}",
                session_attributes,
            )

        if not num_nights:
            return elicit_slot(
                intent_name,
                slots,
                "Nights",
                "How many nights would you like to stay?",
                session_attributes,
            )

        if not check_in:
            return elicit_slot(
                intent_name,
                slots,
                "CheckInDate",
                "What is your check-in date?",
                session_attributes,
            )

        return {
            "sessionState": {
                "dialogAction": {"type": "Delegate"},
                "intent": {
                    "name": intent_name,
                    "slots": slots,
                    "state": "InProgress",
                },
                "sessionAttributes": session_attributes,
            }
        }

    if room_type not in ROOM_CATALOG:
        return elicit_slot(
            intent_name,
            slots,
            "RoomType",
            f"Please choose a valid room type. {room_options_text()}",
            session_attributes,
        )

    if not num_nights:
        return elicit_slot(
            intent_name,
            slots,
            "Nights",
            "How many nights would you like to stay?",
            session_attributes,
        )

    if not check_in:
        return elicit_slot(
            intent_name,
            slots,
            "CheckInDate",
            "What is your check-in date?",
            session_attributes,
        )

    validation_error = validate_booking(room_type, num_nights)
    if validation_error:
        return close(intent_name, validation_error, session_attributes)

    nights = int(num_nights)
    price_per_night = ROOM_CATALOG[room_type]["price"]
    total_cost = price_per_night * nights

    message = (
        f"Booking confirmed. Your {room_type} room is reserved from {check_in} for {nights} day(s). "
        f"Price per night is Rs. {price_per_night}, so the total cost is Rs. {total_cost}. "
        f"Thank you for choosing our hotel."
    )

    return close(intent_name, message, session_attributes)