"""Tests for the raspberry-flash command line interface."""

from collections.abc import Iterator
from pathlib import Path
from unittest import mock

from click.testing import CliRunner, Result
import pytest

from raspberry_flash.card_flasher.rpi_imager_flasher import RpiImagerParameters
from raspberry_flash.cli import (
    HOSTNAME,
    USER_PASSWORD_ENV_VAR,
    USERNAME,
    WIFI_PASSWORD_ENV_VAR,
    main,
)

USER_PASSWORD: str = "user-secret"
WIFI_PASSWORD: str = "wifi-secret"

ALL_ARGUMENTS: list[str] = [
    "--log-level",
    "DEBUG",
    "--device",
    "/dev/sdz",
    "--image",
    "/tmp/raspios.img.xz",
    "--hostname",
    "my-pi",
    "--username",
    "bob",
    "--wifi-ssid",
    "my-ssid",
    "--wifi-country",
    "FR",
    "--timezone",
    "Europe/Paris",
    "--keymap",
    "FR",
    "--ssh-pubkey",
    "ssh-ed25519 AAAA bob@host",
]


@pytest.fixture
def flasher_class() -> Iterator[mock.MagicMock]:
    """Replace the RpiImagerFlasher class used by the CLI with a mock whose flash()
    succeeds."""
    with mock.patch("raspberry_flash.cli.RpiImagerFlasher") as mocked_class:
        mocked_class.return_value.flash.return_value = True
        yield mocked_class


def invoke_main(
    arguments: list[str],
    user_password: str | None = USER_PASSWORD,
    wifi_password: str | None = WIFI_PASSWORD,
) -> Result:
    """Invoke the CLI with the given arguments and password environment variables.

    :param arguments: the command line arguments.
    :param user_password: the value of the user password environment variable, None to
        leave it unset.
    :param wifi_password: the value of the WiFi password environment variable, None to
        leave it unset.
    :return: the invocation result.
    """
    runner = CliRunner()
    return runner.invoke(
        main,
        arguments,
        prog_name="raspberry-flash",
        env={
            USER_PASSWORD_ENV_VAR: user_password,
            WIFI_PASSWORD_ENV_VAR: wifi_password,
        },
    )


def test_main_whenHelpOption_expectUsage() -> None:
    """Invoked with --help, the command shows its usage."""
    runner = CliRunner()

    result = runner.invoke(main, ["--help"], prog_name="raspberry-flash")

    assert result.exit_code == 0
    assert "Usage: raspberry-flash" in result.output


def test_main_whenAllArguments_expectFlasherCalledWithThem(
    flasher_class: mock.MagicMock,
) -> None:
    """Every argument and both environment variables reach the flasher."""
    result = invoke_main(ALL_ARGUMENTS)

    assert result.exit_code == 0
    flasher_class.assert_called_once_with(
        Path("/dev/sdz"),
        RpiImagerParameters(
            image=Path("/tmp/raspios.img.xz"),
            hostname="my-pi",
            username="bob",
            password=USER_PASSWORD,
            wifi_ssid="my-ssid",
            wifi_password=WIFI_PASSWORD,
            wifi_country="FR",
            timezone="Europe/Paris",
            keymap="FR",
            ssh_pubkey="ssh-ed25519 AAAA bob@host",
        ),
    )
    flasher_class.return_value.flash.assert_called_once_with()


def test_main_whenNoArguments_expectFlasherCalledWithDefaults(
    flasher_class: mock.MagicMock,
) -> None:
    """Without arguments, the flasher receives the default values."""
    result = invoke_main([])

    assert result.exit_code == 0
    flasher_class.assert_called_once_with(
        Path(),
        RpiImagerParameters(
            image=Path(),
            hostname=HOSTNAME,
            username=USERNAME,
            password=USER_PASSWORD,
            wifi_ssid="",
            wifi_password=WIFI_PASSWORD,
            wifi_country="",
            timezone="",
            keymap="",
            ssh_pubkey="",
        ),
    )
    flasher_class.return_value.flash.assert_called_once_with()


def test_main_whenLogLevelOption_expectLoggingConfiguredWithIt(
    flasher_class: mock.MagicMock,
) -> None:
    """The --log-level value is used to configure the logging, upper-cased."""
    with mock.patch("raspberry_flash.cli.logging.basicConfig") as basic_config:
        result = invoke_main(["--log-level", "debug"])

    assert result.exit_code == 0
    basic_config.assert_called_once()
    assert basic_config.call_args.kwargs["level"] == "DEBUG"


def test_main_whenInvalidLogLevel_expectUsageError(
    flasher_class: mock.MagicMock,
) -> None:
    """An unknown --log-level value is rejected and nothing is flashed."""
    result = invoke_main(["--log-level", "LOUD"])

    assert result.exit_code == 2
    flasher_class.assert_not_called()


def test_main_whenFlashFails_expectExitCode1(flasher_class: mock.MagicMock) -> None:
    """A failed flash is reported through the exit code."""
    flasher_class.return_value.flash.return_value = False

    result = invoke_main(ALL_ARGUMENTS)

    assert result.exit_code == 1
    flasher_class.return_value.flash.assert_called_once_with()


@pytest.mark.parametrize("user_password", [None, ""])
def test_main_whenUserPasswordMissing_expectExitCode1AndNoFlash(
    flasher_class: mock.MagicMock, user_password: str | None
) -> None:
    """Without a user password (unset or empty), nothing is flashed."""
    result = invoke_main(ALL_ARGUMENTS, user_password=user_password)

    assert result.exit_code == 1
    flasher_class.assert_not_called()


@pytest.mark.parametrize("wifi_password", [None, ""])
def test_main_whenWifiPasswordMissing_expectExitCode1AndNoFlash(
    flasher_class: mock.MagicMock, wifi_password: str | None
) -> None:
    """Without a WiFi password (unset or empty), nothing is flashed."""
    result = invoke_main(ALL_ARGUMENTS, wifi_password=wifi_password)

    assert result.exit_code == 1
    flasher_class.assert_not_called()
