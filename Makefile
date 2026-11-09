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
	uv run pytest -s -v --cov=src/nas_flash tests/

.PHONY: build
build: install-deps  ## Build a standalone Debian package in dist/
	uv sync --reinstall-package nas-flash
	uv run pyinstaller --onedir --clean --noconfirm \
		--name nas-flash \
		--copy-metadata nas-flash \
		--distpath build/pyinstaller \
		--workpath build/pyinstaller-work \
		--specpath build \
		src/nas_flash/cli.py
	rm -rf $(DEB_ROOT)
	mkdir -p $(DEB_ROOT)/DEBIAN $(DEB_ROOT)/opt $(DEB_ROOT)/usr/bin dist \
		$(DEB_ROOT)/usr/share/doc/nas-flash
	cp -r build/pyinstaller/nas-flash $(DEB_ROOT)/opt/nas-flash
	ln -s /opt/nas-flash/nas-flash $(DEB_ROOT)/usr/bin/nas-flash
	gzip -9nc CHANGELOG.md > $(DEB_ROOT)/usr/share/doc/nas-flash/changelog.gz
	sed 's/@VERSION@/$(VERSION)/' packaging/deb/control > $(DEB_ROOT)/DEBIAN/control
	dpkg-deb --root-owner-group --build $(DEB_ROOT) dist/

.PHONY: clean
clean:
	rm -rf .mypy_cache .pytest_cache .ruff_cache $(DEB_ROOT)