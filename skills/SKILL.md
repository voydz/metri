# metri CLI usage skill

## Purpose
Use this skill when helping users operate the finished `metri` CLI. It focuses on commands, options, and output expectations. It does not cover development, testing, or release tasks.

## Scope
- How to log metrics
- How to query and delete data
- Output formats
- Database location and overrides
- Common usage patterns

## Key constraints
- Keep existing CLI flags and semantics intact.
- Default database path: `~/.local/share/metri/metrics.db`
- Output format is command-local (`--format table|json` on each command, no global `--format`)

## Quick start
```bash
metri --help
metri today
```

## Common usage patterns
```bash
# Log a metric
metri log --key weight_kg --value 70.5
metri log --key ftp_watts --value 280 --source manual --date 2026-02-24 --time 07:15:00

# Show today
metri today
metri today --format json

# Query last 7 days
metri query --last 7d

# Query averages
metri query --last 30d --avg

# Query trend
metri query --last 30d --trend

# Delete
metri delete 12
metri delete 12 --format json
```

## Commands and flags (current CLI)
- `log`: `--key` `--value` `--source` `--date` `--time` `--format`
- `delete`: `id` `--format`
- `today`: `--format`
- `query`: `--last` `--avg` `--trend` `--format`

## Output format
- `table` (default):
  - `log`/`delete`: compact status messages
  - `today`/`query`: human-friendly table output
- `json`:
  - `log`: single object
  - `delete`: status object
  - `today`/`query`: arrays of records

## Database location
- Default: `~/.local/share/metri/metrics.db`
- Override: set `METRI_DB_PATH=/path/to/metrics.db`
