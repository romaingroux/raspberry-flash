from pathlib import Path
from unittest import mock

import pytest

from nas_flash.card_flasher.icard_flasher import ICardFlasher


class CardFlasherToy(ICardFlasher):
    """A test implementation."""

    def __init__(self, device: Path):
        super().__init__(device=device)

    def flash(self) -> bool:
        return True


class TestICardWriter:

    @mock.patch.object(Path, "exists", return_value=True)
    def test_ctor_when_device_exist_expect_to_work(self, _mock_path):

        CardFlasherToy(Path("/dev/my-dev"))

    @mock.patch.object(Path, "exists", return_value=False)
    def test_ctor_when_device_does_not_exist_expect_error(self, _mock_path):
        with pytest.raises(ValueError, match="given device does not exist:"):
            CardFlasherToy(Path("/dev/my-dev"))
