"""Command line interface to flash Raspberry Pi OS onto an SD card."""

import click


@click.group(invoke_without_command=True)
@click.version_option(package_name="nas-flash")
def main() -> None:
    """Flash Raspberry Pi OS onto an SD card."""
    print("Hello!!!")


if __name__ == "__main__":
    main()
