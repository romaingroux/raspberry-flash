from pathlib import Path
import subprocess
import tempfile
from unittest import mock

import pytest

from nas_flash.card_flasher.rpi_imager_flasher import (
    RpiImagerFlasher,
    RpiImagerParameters,
)
from nas_flash.utils.shell import ShellReturn


def run_shell_which_rpi_imager_success(command):
    if command == ["which", "rpi-imager"]:
        return ShellReturn(0, "/usr/bin/rpi-imager\n", "")
    raise RuntimeError("unexpected call")


def run_shell_which_rpi_imager_failure(command):
    if command == ["which", "rpi-imager"]:
        return ShellReturn(1, "", "")
    raise RuntimeError("unexpected call")


def run_shell_flash_success(command):
    if command == ["which", "rpi-imager"]:
        return run_shell_which_rpi_imager_success(command)
    if command[0] == "/usr/bin/rpi-imager":
        return ShellReturn(0, "", "")
    raise RuntimeError("unexpected call")


def run_shell_flash_failure(command):
    if command == ["which", "rpi-imager"]:
        return run_shell_which_rpi_imager_success(command)
    if command[0] == "/usr/bin/rpi-imager":
        return ShellReturn(1, "error\n", "error\n")
    print(command)
    raise RuntimeError("unexpected call")


@mock.patch("nas_flash.card_flasher.rpi_imager_flasher.ICardFlasher.__init__")
class TestRpiImagerFlasher:

    device = Path("/dev/my-device")
    parameters = RpiImagerParameters(
        image=Path("/my/image"),
        username="my-username",
        hostname="my-hostname",
        password="my-password",
        wifi_ssid="my-wifi-ssid",
        wifi_password="my-wifi-password",
        wifi_country="my-wifi-country",
        timezone="my-timezone",
        keymap="my-keymap",
        ssh_pubkey="my-pub-key",
    )

    @mock.patch(
        "nas_flash.card_flasher.rpi_imager_flasher.run_shell",
        side_effect=run_shell_which_rpi_imager_success,
    )
    @mock.patch(
        "nas_flash.card_flasher.rpi_imager_flasher.Path.exists", return_value=True
    )
    def test_ctor_when_everything_is_found_expect_to_work(
        self, _mock_path_exists, mock_run_shell, mock_init
    ):

        mock_return = mock.Mock()
        mock_return.return_code = 0
        mock_return.stdout = "/usr/bin/rpi-imager\n"
        mock_return.stderr = ""
        mock_run_shell.return_value = mock_return

        flasher = RpiImagerFlasher(
            TestRpiImagerFlasher.device, TestRpiImagerFlasher.parameters
        )

        mock_init.assert_called_once_with(device=Path("/dev/my-device"))
        assert flasher._binary == Path("/usr/bin/rpi-imager")
        assert flasher._hostname == TestRpiImagerFlasher.parameters.hostname
        assert flasher._username == TestRpiImagerFlasher.parameters.username
        assert flasher._password == TestRpiImagerFlasher.parameters.password
        assert flasher._wifi_ssid == TestRpiImagerFlasher.parameters.wifi_ssid
        assert flasher._wifi_password == TestRpiImagerFlasher.parameters.wifi_password
        assert flasher._wifi_country == TestRpiImagerFlasher.parameters.wifi_country
        assert flasher._timezone == TestRpiImagerFlasher.parameters.timezone
        assert flasher._keymap == TestRpiImagerFlasher.parameters.keymap
        assert flasher._ssh_pubkey == TestRpiImagerFlasher.parameters.ssh_pubkey

    @mock.patch(
        "nas_flash.card_flasher.rpi_imager_flasher.Path.exists", return_value=False
    )
    def test_ctor_when_image_not_found_expect_error(self, _mock_path_exists, mock_init):
        with pytest.raises(ValueError, match="image not found"):
            RpiImagerFlasher(
                TestRpiImagerFlasher.device, TestRpiImagerFlasher.parameters
            )

    @mock.patch(
        "nas_flash.card_flasher.rpi_imager_flasher.run_shell",
        side_effect=run_shell_which_rpi_imager_failure,
    )
    @mock.patch(
        "nas_flash.card_flasher.rpi_imager_flasher.Path.exists", return_value=True
    )
    def test_ctor_when_rpi_imager_not_found_expect_error(
        self, _mock_path_exists, _mock_shell_run, _mock_init
    ):
        with pytest.raises(FileNotFoundError, match="rpi-imager binary not found"):
            RpiImagerFlasher(
                TestRpiImagerFlasher.device, TestRpiImagerFlasher.parameters
            )

    @mock.patch.object(RpiImagerFlasher, "generate_first_run_script")
    @mock.patch(
        "nas_flash.card_flasher.rpi_imager_flasher.run_shell",
        side_effect=run_shell_flash_success,
    )
    @mock.patch(
        "nas_flash.card_flasher.rpi_imager_flasher.Path.exists", return_value=True
    )
    def test_flash_when_no_error_expect_true(
        self, _mock_path_exists, _mock_shell_run, mock_generate, _mock_init
    ):
        flasher = RpiImagerFlasher(
            TestRpiImagerFlasher.device, TestRpiImagerFlasher.parameters
        )
        # the mocked ICardFlasher.__init__ does not set _device: inject it
        flasher._device = Path("/dev/my-device")

        assert flasher.flash() is True
        mock_generate.assert_called_once()

    @mock.patch.object(RpiImagerFlasher, "generate_first_run_script")
    @mock.patch(
        "nas_flash.card_flasher.rpi_imager_flasher.run_shell",
        side_effect=run_shell_flash_failure,
    )
    @mock.patch(
        "nas_flash.card_flasher.rpi_imager_flasher.Path.exists", return_value=True
    )
    def test_flash_when_error_expect_false(
        self, _mock_path_exists, _mock_shell_run, mock_generate, _mock_init
    ):
        flasher = RpiImagerFlasher(
            TestRpiImagerFlasher.device, TestRpiImagerFlasher.parameters
        )
        # the mocked ICardFlasher.__init__ does not set _device: inject it
        flasher._device = Path("/dev/my-device")

        assert flasher.flash() is False
        mock_generate.assert_called_once()

    def test_compute_password_hash_when_given_password_expect_hash(self, _mock_init):
        password = "my-password"

        result = RpiImagerFlasher.compute_password_hash(password)

        # shape: $6$<salt>$<digest>
        fields = result.split("$")
        assert len(fields) == 4
        assert fields[0] == ""
        assert fields[1] == "6"  # SHA-512-crypt
        assert 1 <= len(fields[2]) <= 16  # salt
        assert len(fields[3]) == 86  # digest

        # the hash must be the hash OF THE PASSWORD: re-derive it with
        # the same salt using the reference implementation.
        expected = (
            subprocess.run(
                ["openssl", "passwd", "-6", "-stdin", "-salt", fields[2]],
                input=password.encode(),
                capture_output=True,
                check=True,
            )
            .stdout.decode()
            .rstrip()
        )
        assert result == expected

    @pytest.mark.parametrize(
        "ssh_key,ssh_opt", ((None, ""), ("my-pub-key", " -k my-pub-key"))
    )
    @mock.patch.object(
        RpiImagerFlasher,
        "compute_password_hash",
        return_value="$6$testsalt$testdigest",
    )
    def test_generate_first_run_script_when_params_expect_file(
        self, mock_hash, _mock_init, ssh_key, ssh_opt
    ):
        user = TestRpiImagerFlasher.parameters.username
        host = TestRpiImagerFlasher.parameters.hostname
        psw = TestRpiImagerFlasher.parameters.password
        ssid = TestRpiImagerFlasher.parameters.wifi_ssid
        wifi_pwd = TestRpiImagerFlasher.parameters.wifi_password
        wifi_cty = TestRpiImagerFlasher.parameters.wifi_country
        timezone = TestRpiImagerFlasher.parameters.timezone
        keym = TestRpiImagerFlasher.parameters.keymap

        with tempfile.NamedTemporaryFile(mode="w+t") as file_out:
            returned = RpiImagerFlasher.generate_first_run_script(
                file_out,
                host,
                user,
                psw,
                ssid,
                wifi_pwd,
                wifi_cty,
                timezone,
                keym,
                ssh_key,
            )
            content = Path(file_out.name).read_text()

        assert returned is file_out
        mock_hash.assert_called_once_with(psw)

        expected_lines = [
            f"/usr/lib/raspberrypi-sys-mods/imager_custom set_hostname '{host}'",
            f"/usr/lib/raspberrypi-sys-mods/imager_custom enable_ssh{ssh_opt}",
            f"/usr/lib/userconf-pi/userconf '{user}' '$6$testsalt$testdigest'",
            "/usr/lib/raspberrypi-sys-mods/imager_custom"
            f" set_wlan -p '{ssid}' '{wifi_pwd}' '{wifi_cty}'",
            f"/usr/lib/raspberrypi-sys-mods/imager_custom set_keymap '{keym}'",
            "/usr/lib/raspberrypi-sys-mods/imager_custom" f" set_timezone '{timezone}'",
            "rfkill unblock wifi",
            "rm -f /boot/firstrun.sh",
            "sed -i 's| systemd.run.*||g' /boot/cmdline.txt",
        ]
        for line in expected_lines:
            assert line in content
