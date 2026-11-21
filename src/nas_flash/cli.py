"""Command line interface to flash Raspberry Pi OS onto an SD card."""

import logging
import os
from pathlib import Path
import sys

import click

from nas_flash.card_flasher.rpi_imager_flasher import (
    RpiImagerFlasher,
    RpiImagerParameters,
)

HOSTNAME: str = "raspberry-pi"
USERNAME: str = "ansible"
WIFI_COUNTRY: str = "CH"
TIMEZONE: str = "Europe/Zurich"
KEYMAP: str = "CH"
LOG_LEVELS: list[str] = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LOG_LEVEL: str = "INFO"

USER_PASSWORD_ENV_VAR: str = "RASPBERRY_FLASH_PASSWORD_USER"
WIFI_PASSWORD_ENV_VAR: str = "RASPBERRY_FLASH_PASSWORD_WIFI"


@click.group(invoke_without_command=True)
@click.option(
    "--log-level",
    type=click.Choice(LOG_LEVELS, case_sensitive=False),
    default=LOG_LEVEL,
    show_default=True,
    help="Verbosity of the logs written to stderr.",
)
@click.option("--device", default="", help="Path to the SD card device to flash")
@click.option("--image", default="", help="Path to the image to flash")
@click.option("--hostname", default=HOSTNAME, help="The Raspberry Pi future hostname")
@click.option("--username", default=USERNAME, help="The Raspberry Pi future username")
@click.option("--wifi-ssid", default="", help="The Raspberry Pi future WiFi SSID.")
@click.option(
    "--wifi-country", default="", help="The Raspberry Pi future WiFi country."
)
@click.option("--timezone", default="", help="The Raspberry Pi future timezone.")
@click.option("--keymap", default="", help="The Raspberry Pi future keyboard keymap.")
@click.option(
    "--ssh-pubkey",
    default="",
    help="A public key (not a path) to use for SSH connection.",
)
@click.version_option(package_name="nas-flash")
def main(  # noqa: PLR0913, PLR0917
    log_level: str,
    device: str,
    image: str,
    hostname: str,
    username: str,
    wifi_ssid: str,
    wifi_country: str,
    timezone: str,
    keymap: str,
    ssh_pubkey: str,
) -> None:
    """Flash Raspberry Pi OS onto an SD card and sets the Raspberry Pi OS using the
    following given parameters.

    :param log_level: the verbosity of the logs, one of DEBUG, INFO, WARNING, ERROR,
        CRITICAL.
    :param device: the path to the SD card device to flash, e.g /dev/sda1
    :param image: the path to the image to flash on the SD card
    :param hostname: the future hostname.
    :param username: the future username. The corresponding username password is passed
        through the RASPBERRY_FLASH_PASSWORD_USER environment variable.
    :param wifi_ssid: the future Wifi SSD to connect to. The corresponding password is
        passed through the RASPBERRY_FLASH_PASSWORD_WIFI environment variable.
    :param wifi_country: the future Wifi country.
    :param timezone: the future timezone.
    :param keymap: the future keyboard key map.
    :param ssh_pubkey: a public SSH key (not a path to a file) to enable SSH connection
        using a key rather than a username / password.
    """
    logging.basicConfig(
        level=log_level.upper(),
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    user_password: str | None = os.environ.get(USER_PASSWORD_ENV_VAR)
    if user_password is None or user_password == "":  # nosec B105
        logging.critical(f"user password not provided: {USER_PASSWORD_ENV_VAR}")
        sys.exit(1)

    wifi_password: str | None = os.environ.get(WIFI_PASSWORD_ENV_VAR)
    if wifi_password is None or wifi_password == "":  # nosec B105
        logging.critical(f"WiFi password not provided: {WIFI_PASSWORD_ENV_VAR}")
        sys.exit(1)

    card_flasher = RpiImagerFlasher(
        Path(device),
        RpiImagerParameters(
            Path(image),
            hostname,
            username,
            user_password,
            wifi_ssid,
            wifi_password,
            wifi_country,
            timezone,
            keymap,
            ssh_pubkey,
        ),
    )
    suceeded = card_flasher.flash()
    sys.exit(0 if suceeded else 1)


if __name__ == "__main__":
    main()
