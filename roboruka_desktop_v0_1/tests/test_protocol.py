import pytest
from communication.protocol import parse_message, ProtocolError, encode_message


def test_parse_state():
    msg = parse_message('{"version":1,"type":"state","position":{"x":0.2,"y":0.8}}')
    assert msg.type == "state"
    assert msg.position["x"] == 0.2


def test_reject_bad_coordinate():
    with pytest.raises(ProtocolError):
        parse_message('{"version":1,"type":"state","position":{"x":2,"y":0.8}}')


def test_encode_adds_version_and_newline():
    encoded = encode_message({"type": "ping"})
    assert encoded.endswith(b"\\n")
    assert b'"version":1' in encoded
