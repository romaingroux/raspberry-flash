# raspberry-flash

Command line application to flash Raspberry Pi OS onto an SD card, for the Raspberry Pi
NAS project.

It runs on an **amd64 Linux laptop** and is shipped as a standalone Debian package: the
Python runtime is bundled, so the machine installing it needs no Python.

## Requirements

Runtime:

- `rpi-imager` (>= 1.8.1) — writes the image, its `--first-run-script` option is used to
  configure the Raspberry Pi. Ubuntu 22.04 ships an older version: install a recent
  package from <https://github.com/raspberrypi/rpi-imager/releases>.
- `openssl` — hashes the user password
- `libc6` (>= 2.17) and `zlib1g` — needed by the bundled Python runtime

The Debian package declares all of them, so `apt` installs or checks them.

Development:

- [uv](https://docs.astral.sh/uv/) — manages both the dependencies and the interpreter
- `make`, `dpkg-deb`

Python itself does not need to be installed: `uv` downloads the CPython version pinned in
`.python-version`.

## Development

| Target              | Purpose                                                          |
| ------------------- | ---------------------------------------------------------------- |
| `make install-deps` | Sync the virtual environment from `uv.lock`                      |
| `make lint`         | Run `docformatter`, `black`, `ruff`, `mypy`, `bandit`, `vulture`  |
| `make format`       | Apply `docformatter`, `black` and `ruff --fix` in place           |
| `make test`         | Run the unit tests with coverage of `src/raspberry_flash`        |
| `make build`        | Build `dist/raspberry-flash_<version>_amd64.deb`                 |

Every target depends on `install-deps`, so any of them bootstraps the environment.

## Packaging

`make build` freezes the application with PyInstaller, assembles a package tree under
`build/deb/` from `packaging/deb/control`, and builds the archive with `dpkg-deb`. The
package also installs `CHANGELOG.md` as
`/usr/share/doc/raspberry-flash/changelog.gz`.

Install and remove it with:

```
sudo apt install ./dist/raspberry-flash_0.1.0_amd64.deb
sudo apt remove raspberry-flash
```

## Releasing

The version lives in the `VERSION` file at the repository root, and nothing else records
it: `pyproject.toml` declares `dynamic = ["version"]` and hatchling reads `VERSION`, while
the Makefile reads it for the package name and control file.

To cut a release:

1. Edit `VERSION`.
2. Move the `CHANGELOG.md` entries from `Unreleased` into a section for the new version.
3. Run `make build`.

`make build` reinstalls the project into the virtual environment first, so the version
reported by `raspberry-flash --version` cannot drift from the version in the package
name.

## Usage

```
raspberry-flash --help
```

Passwords are never given on the command line, where they would be visible in the
process list and in the shell history. They are read from environment variables:

| Variable                        | Purpose                                          |
| ------------------------------- | ------------------------------------------------ |
| `RASPBERRY_FLASH_PASSWORD_USER` | Password of the future user. Always required.    |
| `RASPBERRY_FLASH_PASSWORD_WIFI` | WiFi password. Required only with `--wifi-ssid`. |

Writing to the SD card needs root, and `sudo` only passes the environment along when
asked to:

```
read -rs RASPBERRY_FLASH_PASSWORD_USER
read -rs RASPBERRY_FLASH_PASSWORD_WIFI
export RASPBERRY_FLASH_PASSWORD_USER RASPBERRY_FLASH_PASSWORD_WIFI
sudo --preserve-env=RASPBERRY_FLASH_PASSWORD_USER,RASPBERRY_FLASH_PASSWORD_WIFI \
    raspberry-flash --device /dev/sdX --image raspios.img.xz --wifi-ssid my-ssid
```

`--device` is the whole card (check with `lsblk`), never one of its partitions.

## License

raspberry-flash is free software, distributed under the terms of the GNU General Public
License, version 3 or later. See `LICENSE`.
