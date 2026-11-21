from dataclasses import dataclass
import subprocess as sub  # nosec B404


@dataclass
class ShellReturn:
    """A class to hold the return values of a shell command."""

    return_code: int
    stdout: str
    stderr: str


def run_shell(command: list[str]) -> ShellReturn:
    """Runs the given command in a shell and returns its restult.

    :param command: the command to execute, e.g. ["ls", "-hl", "."]
    :return: an object with the return value, stdout and stderr.
    """
    result = sub.run(
        command, shell=False, capture_output=True, check=False  # nosec B603
    )
    return ShellReturn(
        stdout=result.stdout.decode(),
        stderr=result.stderr.decode(),
        return_code=result.returncode,
    )
