# metri

`metri` is a small CLI for logging and querying health/fitness metrics (e.g., FTP, weight, body fat) in a local append-only SQLite database. It is heavily inspired by and fully aligned with the architecture of [nutri](https://github.com/voydz/nutri).

## Installation

Install `metri` via Homebrew using the custom tap:

```bash
brew install voydz/tap/metri
```

Prebuilt binaries are published for:

| Platform | Notes |
| --- | --- |
| macOS arm64 | Apple Silicon only |
| Linux x86_64 | Homebrew on Linux (Linuxbrew), glibc 2.35 or newer |
| Linux arm64 | Homebrew on Linux (Linuxbrew), glibc 2.35 or newer |

Metrics are stored at `~/.local/share/metri/metrics.db` on every platform. Override the
location with `METRI_DB_PATH`.

## Setup (Development)

This project uses `uv` for dependency management and `PyInstaller` for standalone binaries.
On Linux, PyInstaller additionally needs `objdump` (the `binutils` package).

```bash
# Clone the repository
git clone https://github.com/voydz/metri.git
cd metri

# Setup the uv environment
make setup

# Run the CLI
make run ARGS="--help"
```

## Usage Examples

### Log a metric
By default, `metri log` uses the current date and time.
```bash
# Log weight from Home Assistant
metri log --key weight_kg --value 82.7 --source home_assistant

# Log an FTP update from Garmin
metri log --key ftp_watts --value 215.0 --source garmin
```

### View Data
```bash
# See today's logged metrics
metri today

# View history over the last 7 days
metri query --last 7d

# Get average values over the last 30 days
metri query --last 30d --avg

# View trend (first vs last value) over the last 30 days
metri query --last 30d --trend
```

### Output Formats
All commands support `--format json` for integration with other tools (like OpenClaw or jq):
```bash
metri today --format json
```

## Build & Release
- `make build` compiles a standalone binary for the host platform using `PyInstaller`.
- `make smoke` builds the binary and exercises it against a throwaway `HOME`.
- `make package` creates `dist/metri-<version>-<os>-<arch>.tar.gz` plus a sha256 checksum.
- On release, a GitHub Action builds one binary per supported platform (`macos-14`,
  `ubuntu-22.04`, `ubuntu-22.04-arm`), uploads them as release assets, renders the tap
  formula from `packaging/metri.rb.tmpl`, and opens a pull request against
  `voydz/homebrew-tap`.

Linux binaries are built on `ubuntu-22.04` on purpose: a PyInstaller binary cannot run on a
host whose glibc is older than the build host's, so this sets the compatibility floor at
glibc 2.35 (Ubuntu 22.04, Debian 12, and newer).

The formula carries a separate `url`/`sha256` per platform, which `brew bump-formula-pr`
cannot express — it only rewrites a single pair. `packaging/render_formula.py` renders the
whole formula instead:

```bash
python3 packaging/render_formula.py --version 0.1.0 --repo voydz/metri \
  --sha256 darwin-arm64=... --sha256 linux-x86_64=... --sha256 linux-arm64=...
```
