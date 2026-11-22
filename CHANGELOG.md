# Changelog

All notable changes to raspberry-flash are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). The version
itself lives in the `VERSION` file at the repository root.

## [Unreleased]

### Added

- `raspberry-flash` command line tool: writes a Raspberry Pi OS image (`--image`) onto an
  SD card (`--device`) with `rpi-imager`, and reports the outcome through its exit code.
- Configuration of the Raspberry Pi on its first boot, without screen nor keyboard:
  - hostname (`--hostname`);
  - user account (`--username`), replacing the default user of the image;
  - WiFi network (`--wifi-ssid`, `--wifi-country`), left unconfigured when no SSID is
    given;
  - timezone (`--timezone`) and keyboard layout (`--keymap`);
  - SSH server, enabled with password login, or restricted to a public key when one is
    given (`--ssh-pubkey`).
- Passwords read from the `RASPBERRY_FLASH_PASSWORD_USER` and
  `RASPBERRY_FLASH_PASSWORD_WIFI` environment variables, so that they never appear on a
  command line. The WiFi one is only required with `--wifi-ssid`. The user password is
  stored on the SD card as a SHA-512 hash, never in clear.
- `--log-level` to choose the verbosity of the logs written to stderr, `--help` and
  `--version`.
- Debian packaging: `make build` freezes the application with PyInstaller and builds a
  standalone `.deb` with `dpkg-deb`, for the architecture of the machine building it. The
  bundled interpreter means the target needs no system Python, and the package declares
  its runtime dependencies (`rpi-imager`, `openssl`, `libc6`, `zlib1g`).
- Development environment: uv with a pinned, uv-managed CPython 3.13, hatchling build
  backend and a `Makefile` exposing `install-deps`, `lint`, `format`, `test`, `build` and
  `clean`.
