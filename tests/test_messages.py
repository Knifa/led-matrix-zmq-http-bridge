from lmz.control import BrightnessArgs, SetBrightnessRequest


def test_message_serde_identity():
    message = SetBrightnessRequest(BrightnessArgs(50))

    assert message == SetBrightnessRequest.from_bytes(message.to_bytes())
