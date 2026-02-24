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
- Output format: `table` or `json`

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

# Query last 7 days
metri query --last 7d

# Query averages
metri query --last 30d --avg

# Delete
metri delete 12
```

## Commands and flags (current CLI)
- `log`: `--key` `--value` `--source` `--date` `--time` `--format`
- `delete`: `id`
- `today`: `--format`
- `query`: `--last` `--avg` `--format`

## Output format
- `table` (default): human-friendly rows
- `json`: machine-readable records

## Database location
- Default: `~/.local/share/metri/metrics.db`
- Override: set `METRI_DB_PATH=/path/to/metrics.db`
