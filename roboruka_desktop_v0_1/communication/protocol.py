import json
from communication.messages import DeviceMessage


PROTOCOL_VERSION = 1


class ProtocolError(ValueError):
    pass


def parse_message(line: str) -> DeviceMessage:
    try:
        raw = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ProtocolError(f"Invalid JSON: {exc}") from exc
    if not isinstance(raw, dict):
        raise ProtocolError("Message must be a JSON object")
    version = raw.get("version")
    msg_type = raw.get("type")
    if version != PROTOCOL_VERSION:
        raise ProtocolError(f"Unsupported protocol version: {version}")
    if not isinstance(msg_type, str):
        raise ProtocolError("Missing or invalid message type")
    position = raw.get("position")
    if position is not None:
        if not isinstance(position, dict):
            raise ProtocolError("position must be an object")
        for axis in ("x", "y"):
            value = position.get(axis)
            if not isinstance(value, (int, float)) or not 0.0 <= value <= 1.0:
                raise ProtocolError(f"position.{axis} must be between 0 and 1")
    return DeviceMessage(
        version=version,
        type=msg_type,
        seq=raw.get("seq"),
        timestamp_ms=raw.get("timestamp_ms"),
        position=position,
        orientation=raw.get("orientation"),
        buttons=raw.get("buttons"),
    )


def encode_message(message: dict) -> bytes:
    message = dict(message)
    message.setdefault("version", PROTOCOL_VERSION)
    return (json.dumps(message, separators=(",", ":")) + "\n").encode("utf-8")
