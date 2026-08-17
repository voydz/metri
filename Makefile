.PHONY: setup run lint lint-fix test build smoke package clean

UNAME_S := $(shell uname -s)
UNAME_M := $(shell uname -m)

ifeq ($(UNAME_S),Darwin)
OS := darwin
SHA256 := shasum -a 256
else
OS := linux
SHA256 := sha256sum
endif

ifneq (,$(filter $(UNAME_M),arm64 aarch64))
ARCH := arm64
else
ARCH := x86_64
endif

# Overridable so the release workflow can make the git tag authoritative.
VERSION ?= $(shell sed -n 's/^__version__ = "\(.*\)"/\1/p' src/metricli/__init__.py)
TARBALL := dist/metri-$(VERSION)-$(OS)-$(ARCH).tar.gz

setup:
	uv sync

run:
	uv run python -m metricli $(ARGS)

lint:
	uv run ruff check src tests packaging

lint-fix:
	uv run ruff check --fix src tests packaging
	uv run ruff format src tests packaging

test:
	uv run pytest

# No --target-arch: it is macOS-only (Mach-O slice selection) and every release
# runner builds natively for its own architecture.
build:
	uv run pyinstaller --onefile --name metri \
		--distpath dist --workpath build/pyinstaller --specpath build \
		src/metricli/__main__.py

smoke: build
	@tmp=$$(mktemp -d); \
	env -i HOME="$$tmp" PATH="$$PATH" ./dist/metri --help >/dev/null; \
	env -i HOME="$$tmp" PATH="$$PATH" ./dist/metri log --key weight_kg --value 82.7 >/dev/null; \
	env -i HOME="$$tmp" PATH="$$PATH" ./dist/metri today >/dev/null; \
	test -f "$$tmp/.local/share/metri/metrics.db"; \
	status=$$?; rm -rf "$$tmp"; exit $$status

package: build
	@rm -f "$(TARBALL)" "$(TARBALL).sha256"
	@tar -czf "$(TARBALL)" -C dist metri
	@$(SHA256) "$(TARBALL)" > "$(TARBALL).sha256"
	@echo "$(TARBALL)"

clean:
	rm -rf dist build
