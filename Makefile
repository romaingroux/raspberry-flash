VERSION := $(shell cat VERSION)
DEB_ROOT := build/deb

.PHONY: install-deps
install-deps:
	uv sync

.PHONY: lint
lint: install-deps
	uv run docformatter --check --diff -r src/ tests/
	uv run black --diff --check .
	uv run ruff check .
	uv run mypy src/
	uv run bandit -r src/ -c pyproject.toml
	uv run vulture --min-confidence 100 src/ tests/

.PHONY: format
format: install-deps  ## Run all code formatters
	uv run docformatter --in-place -r src/ tests/ || [ $$? -eq 3 ]
	uv run black .
	uv run ruff check . --fix

.PHONY: test
test: install-deps
	uv run pytest -s -v --cov=src/raspberry_flash tests/

.PHONY: build
build: install-deps  ## Build a standalone Debian package in dist/
	uv sync --reinstall-package raspberry-flash
	uv run pyinstaller --onedir --clean --noconfirm \
		--name raspberry-flash \
		--copy-metadata raspberry-flash \
		--distpath build/pyinstaller \
		--workpath build/pyinstaller-work \
		--specpath build \
		src/raspberry_flash/cli.py
	rm -rf $(DEB_ROOT)
	mkdir -p $(DEB_ROOT)/DEBIAN $(DEB_ROOT)/opt $(DEB_ROOT)/usr/bin dist \
		$(DEB_ROOT)/usr/share/doc/raspberry-flash
	cp -r build/pyinstaller/raspberry-flash $(DEB_ROOT)/opt/raspberry-flash
	ln -s /opt/raspberry-flash/raspberry-flash $(DEB_ROOT)/usr/bin/raspberry-flash
	gzip -9nc CHANGELOG.md > $(DEB_ROOT)/usr/share/doc/raspberry-flash/changelog.gz
	sed 's/@VERSION@/$(VERSION)/' packaging/deb/control > $(DEB_ROOT)/DEBIAN/control
	chmod -R u=rwX,go=rX $(DEB_ROOT)
	dpkg-deb --root-owner-group --build $(DEB_ROOT) dist/

.PHONY: clean
clean:
	rm -rf .mypy_cache .pytest_cache .ruff_cache $(DEB_ROOT)