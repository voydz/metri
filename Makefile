.PHONY: setup run lint lint-fix test build smoke package

setup:
	uv sync

run:
	uv run python -m metricli $(ARGS)

lint:
	uv run ruff check src tests

lint-fix:
	uv run ruff check --fix src tests
	uv run ruff format src tests

test:
	uv run pytest

build:
	uv run pyinstaller --onefile --name metri --target-arch arm64 src/metricli/__main__.py

smoke: build
	@tmp=$$(mktemp -d); \
	env -i HOME="$$tmp" PATH="$$PATH" ./dist/metri --help >/dev/null; \
	rm -rf "$$tmp"

package: build
	@tarball=dist/metri-macos-arm64.tar.gz; \
	rm -f "$$tarball" "$$tarball.sha256"; \
	tar -czf "$$tarball" -C dist metri; \
	shasum -a 256 "$$tarball" > "$$tarball.sha256"
