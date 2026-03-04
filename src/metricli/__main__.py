from __future__ import annotations

import json
import sys
from collections.abc import Iterable
from dataclasses import asdict
from datetime import date, datetime, timedelta
from enum import StrEnum
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from metricli import db


class OutputFormat(StrEnum):
    table = "table"
    json = "json"


app = typer.Typer(
    help="Log and query health/fitness metrics.",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()


@app.command(
    "log",
    help="Log a new metric entry.",
)
def cmd_log(
    key: Annotated[str, typer.Option("--key", help="Metric key, e.g. ftp_watts")],
    value: Annotated[float, typer.Option("--value", help="Metric value")],
    source: Annotated[
        str,
        typer.Option("--source", help="Source of data (default: manual)"),
    ] = "manual",
    metric_date: Annotated[
        str | None,
        typer.Option("--date", help="Date in YYYY-MM-DD (default: today)"),
    ] = None,
    metric_time: Annotated[
        str | None,
        typer.Option("--time", help="Time in HH:MM:SS (default: now)"),
    ] = None,
    output_format: Annotated[
        OutputFormat,
        typer.Option(
            "--format",
            case_sensitive=False,
            help="Output format (default: table).",
        ),
    ] = OutputFormat.table,
) -> None:
    conn = db.connect()
    try:
        date_value = metric_date or date.today().isoformat()
        time_value = metric_time or datetime.now().time().replace(microsecond=0).isoformat()

        _validate_date(date_value)
        _validate_time(time_value)

        metric_id = db.insert_metric(
            conn,
            metric_date=date_value,
            metric_time=time_value,
            metric_key=key,
            value=value,
            source=source,
        )
    finally:
        conn.close()

    format_value = output_format.value
    payload = {
        "id": metric_id,
        "date": date_value,
        "time": time_value,
        "metric_key": key,
        "value": value,
        "source": source,
    }
    if format_value == OutputFormat.json.value:
        _print_json(payload)
        return
    console.print(f"Metric #{metric_id} logged: {key}={value:g} ({source})")


@app.command(
    "delete",
    help="Delete a metric by id.",
)
def cmd_delete(
    metric_id: Annotated[int, typer.Argument(help="Metric id to delete")],
    output_format: Annotated[
        OutputFormat,
        typer.Option(
            "--format",
            case_sensitive=False,
            help="Output format (default: table).",
        ),
    ] = OutputFormat.table,
) -> None:
    format_value = output_format.value

    conn = db.connect()
    try:
        deleted = db.delete_metric(conn, metric_id)
    finally:
        conn.close()

    if deleted == 0:
        if format_value == OutputFormat.json.value:
            _print_json({"deleted": None, "id": metric_id, "found": False})
            return
        console.print(f"No entry found with id {metric_id}.")
        return
    if format_value == OutputFormat.json.value:
        _print_json({"deleted": metric_id, "found": True})
        return
    console.print(f"Metric #{metric_id} deleted.")


@app.command(
    "today",
    help="Show metrics logged today.",
)
def cmd_today(
    output_format: Annotated[
        OutputFormat,
        typer.Option(
            "--format",
            case_sensitive=False,
            help="Output format (default: table).",
        ),
    ] = OutputFormat.table,
) -> None:
    conn = db.connect()
    try:
        metric_date = db.iso_today()
        records = db.fetch_by_date(conn, metric_date)
    finally:
        conn.close()

    _render(output_format.value, [asdict(record) for record in records])


@app.command(
    "query",
    help="Query metric history with optional aggregations.",
)
def cmd_query(
    last: Annotated[
        str | None,
        typer.Option("--last", help="Range window like 7d (last N days, including today)"),
    ] = None,
    avg: Annotated[
        bool,
        typer.Option("--avg", help="Return average by metric_key instead of raw rows"),
    ] = False,
    trend: Annotated[
        bool,
        typer.Option("--trend", help="Return trend by metric_key over the selected range"),
    ] = False,
    output_format: Annotated[
        OutputFormat,
        typer.Option(
            "--format",
            case_sensitive=False,
            help="Output format (default: table).",
        ),
    ] = OutputFormat.table,
) -> None:
    start_date = None
    if last:
        start_date = _parse_last_days(last)

    conn = db.connect()
    try:
        if trend:
            rows = db.fetch_trends_range(conn, start_date=start_date)
            _render(output_format.value, rows)
        elif avg:
            rows = db.fetch_avg_range(conn, start_date=start_date)
            _render(output_format.value, rows)
        else:
            records = db.fetch_range(conn, start_date=start_date)
            _render(
                output_format.value,
                [asdict(record) for record in records],
            )
    finally:
        conn.close()


def _parse_last_days(value: str) -> str:
    raw = value.strip().lower()
    if not raw.endswith("d"):
        _exit_with_error("--last must be in the form '<N>d', e.g. 7d")
    number = raw[:-1]
    if not number.isdigit():
        _exit_with_error("--last must be in the form '<N>d', e.g. 7d")
    days = int(number)
    if days < 1:
        _exit_with_error("--last must be >= 1")
    start = date.today() - timedelta(days=days - 1)
    return start.isoformat()


def _validate_date(value: str) -> None:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        _exit_with_error("--date must be YYYY-MM-DD")


def _validate_time(value: str) -> None:
    try:
        datetime.strptime(value, "%H:%M:%S")
    except ValueError:
        _exit_with_error("--time must be HH:MM:SS")


def _render(output_format: str, rows: Iterable[dict]) -> None:
    rows_list = list(rows)
    if not rows_list:
        console.print("No entries.")
        return
    if output_format == "json":
        _print_json(rows_list)
        return
    console.print(_build_table(rows_list))


def _print_json(data: object) -> None:
    console.print_json(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def _exit_with_error(message: str) -> None:
    typer.echo(message, err=True)
    raise typer.Exit(code=1)


def _build_table(rows: list[dict]) -> Table:
    headers = list(rows[0].keys())
    table = Table(show_header=True, box=None, pad_edge=False, collapse_padding=True)

    for key in headers:
        justify = "right" if _is_numeric_column(rows, key) else "left"
        table.add_column(key, justify=justify)

    for row in rows:
        table.add_row(*[_format_cell(row.get(key)) for key in headers])

    return table


def _is_numeric_column(rows: list[dict], key: str) -> bool:
    seen_numeric = False
    for row in rows:
        value = row.get(key)
        if value is None:
            continue
        if isinstance(value, bool):
            return False
        if isinstance(value, int | float):
            seen_numeric = True
            continue
        return False
    return seen_numeric


def _format_cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def main() -> None:
    try:
        app(prog_name="metri")
    except SystemExit as exc:
        if exc.code == 2 and len(sys.argv) <= 1:
            return
        if exc.code not in (None, 0):
            raise


if __name__ == "__main__":
    main()
