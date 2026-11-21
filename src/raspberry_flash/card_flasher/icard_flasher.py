from abc import ABC, abstractmethod
from pathlib import Path


class ICardFlasher(ABC):
    """The ICardFlasher class defines an interface for classes that flash the SD card.

    :param device: the path to the card device, e.g /dev/sda1.
    :raises: ValueError if the given device does not exist.
    """

    def __init__(self, device: Path) -> None:
        if not device.exists():
            raise ValueError(f"given device does not exist: {device}")
        self._device: Path = device
        """Where the device to write is located."""

    @abstractmethod
    def flash(self) -> bool:
        """Flashes the SD card and returns whether it worked.

        :returns: True if writing succeeded.
        """
        pass
