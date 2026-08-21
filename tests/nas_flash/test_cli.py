"""Tests for the nas-flash command line interface."""

from click.testing import CliRunner

from nas_flash.cli import main


def test_main_whenNoSubcommand_expectGreeting() -> None:
    """Invoked without a subcommand, the command runs its callback."""
    runner = CliRunner()

    result = runner.invoke(main, [], prog_name="nas-flash")

    assert result.exit_code == 0
    assert "Hello!!!" in result.output


def test_main_whenHelpOption_expectUsage() -> None:
    """Invoked with --help, the command shows its usage."""
    runner = CliRunner()

    result = runner.invoke(main, ["--help"], prog_name="nas-flash")

    assert result.exit_code == 0
    assert "Usage: nas-flash" in result.output
