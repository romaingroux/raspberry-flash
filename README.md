# nas-flash

Command line application to flash Raspberry Pi OS onto an SD card, for the Raspberry Pi
NAS project.

It runs on an **amd64 Linux laptop** and is shipped as a standalone Debian package: the
Python runtime is bundled, so the machine installing it needs no Python.

## Requirements

Runtime:

- `rpi-imager` (>= 1.7) — available from the Ubuntu universe repository

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
| `make test`         | Run the unit tests with coverage of `src/nas_flash`               |
| `make build`        | Build `dist/nas-flash_<version>_amd64.deb`                       |

Every target depends on `install-deps`, so any of them bootstraps the environment.

## Packaging

`make build` freezes the application with PyInstaller, assembles a package tree under
`build/deb/` from `packaging/deb/control`, and builds the archive with `dpkg-deb`. The
package also installs `CHANGELOG.md` as `/usr/share/doc/nas-flash/changelog.gz`.

Install and remove it with:

```
sudo apt install ./dist/nas-flash_0.1.0_amd64.deb
sudo apt remove nas-flash
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
reported by `nas-flash --version` cannot drift from the version in the package name.

## Usage

```
nas-flash --help
```
