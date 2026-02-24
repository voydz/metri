# metri

`metri` is a small CLI for logging and querying health/fitness metrics (e.g., FTP, weight, body fat) in a local append-only SQLite database. It is heavily inspired by and fully aligned with the architecture of [nutri](https://github.com/voydz/nutri).

## Installation

Install `metri` via Homebrew using the custom tap:

```bash
brew install voydz/tap/metri
```

## Setup (Development)

This project uses `uv` for dependency management and `PyInstaller` for standalone binaries.

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
```

### Output Formats
All commands support `--format json` for integration with other tools (like OpenClaw or jq):
```bash
metri today --format json
```

## Build & Release
- `make build` compiles a standalone `arm64` macOS binary using `PyInstaller`.
- `make package` creates a `.tar.gz` archive with the binary and a sha256 checksum.
- A GitHub Action automatically builds the binary on release and triggers `brew bump-formula-pr` in the `voydz/homebrew-tap`.
