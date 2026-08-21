# Changelog

All notable changes to nas-flash are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). The version
itself lives in the `VERSION` file at the repository root.

## [Unreleased]

## [0.1.0] - 2026-08-11

### Added

- Development environment: uv with a pinned, uv-managed CPython 3.13, hatchling build
  backend and a `Makefile` exposing `install-deps`, `lint`, `format`, `test`, `deb` and
  `clean`.
- Debian packaging: `make deb` freezes the application with PyInstaller and builds a
  standalone `.deb` with `dpkg-deb`. The bundled interpreter means the target needs no
  system Python.
- `nas-flash` command line entry point with `--help` and `--version`.
