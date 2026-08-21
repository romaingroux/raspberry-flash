from dataclasses import dataclass
import logging
from pathlib import Path
import subprocess  # nosec B404
import tempfile
from typing import IO

from nas_flash.card_flasher.icard_flasher import ICardFlasher
from nas_flash.utils.shell import ShellReturn, run_shell

logger = logging.getLogger(__name__)


@dataclass
class RpiImagerParameters:
    """The RpiImagerParameters stores the parameters needed to flash a SD card using
    rpi-imager.

    :param image: the path to the image to flash
    :param hostname: the future hostname.
    :param username: the future username
    :param password: the future user <username> password, the hash will be used, not the
        password.
    :param wifi_ssid: the future WiFi SSID to connect to.
    :param wifi_password: the password to connect to the WiFi SSD <wifi_ssid>.
    :param wifi_country: the future WiFi country.
    :param timezone: the future timezone.
    :param keymap: the future keyboard key map.
    :param ssh_pubkey: a public SSH key (not a path to a file) to enable SSH connection
        using a key rather than a username / password. None means no key given
        (default).
    """

    image: Path
    hostname: str
    username: str
    password: str
    wifi_ssid: str
    wifi_password: str
    wifi_country: str = "CH"
    timezone: str = "Europe/Zurich"
    keymap: str = "CH"
    ssh_pubkey: str | None = None


class RpiImagerFlasher(ICardFlasher):
    """The RpiImagerFlasher class allows to flash a SD card using rpi-imager.

    This requires rpi-imager to be installed.

    :param device: the path to the SD card device to flash, e.g /dev/sda1
    :param rpi_imager_parameters: the parameters to pass to rpi-imager to flash the SD
        card.
    """

    def __init__(self, device: Path, parameters: RpiImagerParameters) -> None:
        super().__init__(device=device)

        if not parameters.image.exists():
            raise ValueError(f"image not found: {parameters.image}")

        self._image: Path = parameters.image
        """The image to flash."""
        self._hostname: str = parameters.hostname
        """The hostname value that will be set."""
        self._username: str = parameters.username
        """The username  value that will be set."""
        self._password: str = parameters.password
        """The username password value that will be set."""
        self._wifi_ssid: str = parameters.wifi_ssid
        """The WiFi SSID  value that will be set."""
        self._wifi_password: str = parameters.wifi_password
        """The future password corresponding to the WiFi SSID that will be set."""
        self._wifi_country: str = parameters.wifi_country
        """The future WiFi country value that will be set."""
        self._timezone: str = parameters.timezone
        """The future timezone value that will be set."""
        self._keymap: str = parameters.keymap
        """The future keyboard keymap value that will be set."""
        self._ssh_pubkey: str | None = parameters.ssh_pubkey
        """A public key to use for SSH that will be set."""
        self._binary: Path = self._find_rpi_imager_binary()
        """The path to rpi-imager binary."""

    def _find_rpi_imager_binary(self) -> Path:
        """Finds the rpi-imager binary and returns its path.

        :returns: the path to the rpi-imager binary.
        :raises: FileNotFoundError if rpi-imager cannot be found
        """
        result: ShellReturn = run_shell(["which", "rpi-imager"])
        if result.return_code != 0:
            raise FileNotFoundError("rpi-imager binary not found")
        binary = Path(result.stdout.rstrip())
        logger.debug("rpi-imager binary found: %s", binary)
        return binary

    def flash(self) -> bool:
        """Placeholder implementation, returns True.

        :return: True
        """
        with tempfile.NamedTemporaryFile(
            mode="wt", delete=True, delete_on_close=True
        ) as file_first_run:
            RpiImagerFlasher.generate_first_run_script(
                file_first_run,
                self._hostname,
                self._username,
                self._password,
                self._wifi_ssid,
                self._wifi_password,
                self._wifi_country,
                self._timezone,
                self._keymap,
                self._ssh_pubkey,
            )
            cmd = [
                str(self._binary),
                "--cli",
                "--first-run-script",
                file_first_run.name,
                str(self._image),
                str(self._device),
            ]
            logger.info("flashing %s", self._device)
            logger.debug("running: %s", " ".join(str(arg) for arg in cmd))
            result: ShellReturn = run_shell(cmd)
            if result.return_code:
                logger.error("flashing error")
                logger.error("rpi-image exit code: %d", result.return_code)
                logger.error("rpi-image stdout: %s", result.stdout.strip())
                logger.error("rpi-image stderr: %s", result.stderr.strip())
                return False
        logger.info("flashing succeeded")
        return True

    @staticmethod
    def generate_first_run_script(  # noqa: PLR0913, PLR0917
        file_out: IO[str],
        hostname: str,
        username: str,
        password: str,
        wifi_ssid: str,
        wifi_password: str,
        wifi_country: str = "CH",
        timezone: str = "Europe/Zurich",
        keymap: str = "CH",
        ssh_pubkey: str | None = None,
    ) -> IO[str]:
        """Generates the first run shell script that will configure the rasperry pi on
        its first run.

        :param file_out: a handle to the file where the script should be written.
        :param hostname: the future hostname.
        :param username: the future username
        :param password: the future user <username> password, the hash will be used, not
            the password.
        :param wifi_ssid: the future WiFi SSID to connect to.
        :param wifi_password: the password to connect to the Wifi SSID <wifi_ssid>.
        :param wifi_country: the future Wifi country.
        :param timezone: the future timezone.
        :param keymap: the future keyboard key map.
        :param ssh_pubkey: a public SSH key (not a path to a file) to enable SSH
            connection using a key rather than a username / password. None means no key
            given (default).
        :returns: <file_out>
        """
        ssh_option = f"-k {ssh_pubkey}" if ssh_pubkey else ""
        password_hash = RpiImagerFlasher.compute_password_hash(password)

        script: str = rf"""
                #!/bin/sh

                set +e

                CURRENT_HOSTNAME=$(cat /etc/hostname | tr -d " \t\n\r")
                if [ -f /usr/lib/raspberrypi-sys-mods/imager_custom ]; then
                    /usr/lib/raspberrypi-sys-mods/imager_custom set_hostname '{hostname}'
                else
                    echo '{hostname}' >/etc/hostname
                    sed -i "s/127.0.1.1.*$CURRENT_HOSTNAME/127.0.1.1\t{hostname}/g" /etc/hosts
                fi

                FIRSTUSER=$(getent passwd 1000 | cut -d: -f1)
                FIRSTUSERHOME=$(getent passwd 1000 | cut -d: -f6)

                if [ -f /usr/lib/raspberrypi-sys-mods/imager_custom ]; then
                    /usr/lib/raspberrypi-sys-mods/imager_custom enable_ssh {ssh_option}
                else
                   systemctl enable ssh
                fi

                if [ -f /usr/lib/userconf-pi/userconf ]; then
                   /usr/lib/userconf-pi/userconf '{username}' '{password_hash}'
                else
                   echo "$FIRSTUSER:"'{password_hash}' | chpasswd -e
                   if [ "$FIRSTUSER" != '{username}' ]; then
                      usermod -l '{username}' "$FIRSTUSER"
                      usermod -m -d '/home/{username}' '{username}'
                      groupmod -n '{username}' "$FIRSTUSER"
                   fi
                fi

                if [ -f /usr/lib/raspberrypi-sys-mods/imager_custom ]; then
                   /usr/lib/raspberrypi-sys-mods/imager_custom set_wlan -p '{wifi_ssid}' '{wifi_password}' '{wifi_country}'
                   /usr/lib/raspberrypi-sys-mods/imager_custom set_keymap '{keymap}'
                   /usr/lib/raspberrypi-sys-mods/imager_custom set_timezone '{timezone}'
                fi
                rfkill unblock wifi

                rm -f /boot/firstrun.sh
                sed -i 's| systemd.run.*||g' /boot/cmdline.txt
                exit 0
            """

        file_out.write(script)
        file_out.flush()
        logger.debug(
            "first run script written to %s (hostname=%s, username=%s, wifi_ssid=%s)",
            file_out.name,
            hostname,
            username,
            wifi_ssid,
        )
        return file_out

    @staticmethod
    def compute_password_hash(password: str) -> str:
        """Computes the given password openssl passwd -6 hash and returns it.

        :param: password
        :returns: the password hash.
        """
        # the password is fed through stdin, never through argv, so that
        # it does not show up in the process list.
        result = subprocess.run(  # nosec B603, B607
            ["openssl", "passwd", "-6", "-stdin"],
            input=password.encode(),
            capture_output=True,
            check=True,
        )
        return result.stdout.decode().rstrip()
