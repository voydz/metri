# metri

`metri` is a small CLI for logging and querying health/fitness metrics (FTP, weight, body fat) in a local SQLite database.

## Quickstart

```sh
make setup
make run ARGS="--help"
```

## Examples

```sh
metri log --key weight_kg --value 70.5
metri today
metri query --last 7d
metri query --last 30d --avg
```
