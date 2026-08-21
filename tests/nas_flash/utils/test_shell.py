from unittest import mock

from nas_flash.utils.shell import run_shell


class TestUtils:

    @mock.patch("nas_flash.utils.shell.sub.run")
    def test_run_shell_when_command_returns_expect_shell_return(self, mock_run):
        return_code_expected = 0
        stdout_expected = b"this is stdout"
        stderr_expected = b"this is stderr"

        mock_run.return_value = mock.Mock(
            returncode=return_code_expected,
            stdout=stdout_expected,
            stderr=stderr_expected,
        )

        result = run_shell(["cmd", "arg1", "arg2"])

        assert result.return_code == return_code_expected
        assert result.stdout == stdout_expected.decode()
        assert result.stderr == stderr_expected.decode()
