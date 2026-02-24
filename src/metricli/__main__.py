from __future__ import annotations

import argparse
import json
from collections.abc import Iterable
from dataclasses import asdict
from datetime import date, datetime, timedelta

from tabulate import tabulate

from metricli import db


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="metri",
        description="Log and query health/fitness metrics.",
    )
    parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table).",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    log_parser = subparsers.add_parser("log", help="Log a metric value.")
    log_parser.add_argument("--key", required=True, help="Metric key, e.g. ftp_watts")
    log_parser.add_argument("--value", required=True, type=float, help="Metric value")
    log_parser.add_argument(
        "--source",
        default="manual",
        help="Source of data (default: manual)",
    )
    log_parser.add_argument("--date", help="Date in YYYY-MM-DD (default: today)")
    log_parser.add_argument("--time", help="Time in HH:MM:SS (default: now)")

    delete_parser = subparsers.add_parser("delete", help="Delete a metric by id.")
    delete_parser.add_argument("id", type=int, help="Metric id to delete")

    subparsers.add_parser("today", help="Show metrics logged today.")

    query_parser = subparsers.add_parser("query", help="Query historical metrics.")
    query_parser.add_argument(
        "--last",
        help="Range window like 7d (last N days, including today)",
    )
    query_parser.add_argument(
        "--avg",
        action="store_true",
        help="Return average by metric_key instead of raw rows",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    conn = db.connect()
    try:
        if args.command == "log":
            handle_log(conn, args)
        elif args.command == "delete":
            handle_delete(conn, args)
        elif args.command == "today":
            handle_today(conn, args)
        elif args.command == "query":
            handle_query(conn, args)
        else:
            parser.error("Unknown command")
    finally:
        conn.close()


def handle_log(conn, args) -> None:
    metric_date = args.date or date.today().isoformat()
    metric_time = args.time or datetime.now().time().replace(microsecond=0).isoformat()

    _validate_date(metric_date)
    _validate_time(metric_time)

    metric_id = db.insert_metric(
        conn,
        metric_date=metric_date,
        metric_time=metric_time,
        metric_key=args.key,
        value=args.value,
        source=args.source,
    )

    _render(
        args.format,
        [
            {
                "id": metric_id,
                "date": metric_date,
                "time": metric_time,
                "metric_key": args.key,
                "value": args.value,
                "source": args.source,
            }
        ],
    )


def handle_delete(conn, args) -> None:
    deleted = db.delete_metric(conn, args.id)
    if deleted == 0:
        print(f"No entry found with id {args.id}.")
        return
    print(f"Deleted entry {args.id}.")


def handle_today(conn, args) -> None:
    metric_date = db.iso_today()
    records = db.fetch_by_date(conn, metric_date)
    _render(args.format, [asdict(record) for record in records])


def handle_query(conn, args) -> None:
    start_date = None
    if args.last:
        start_date = _parse_last_days(args.last)
    if args.avg:
        rows = db.fetch_avg_range(conn, start_date=start_date)
        _render(args.format, rows)
    else:
        records = db.fetch_range(conn, start_date=start_date)
        _render(args.format, [asdict(record) for record in records])


def _parse_last_days(value: str) -> str:
    raw = value.strip().lower()
    if not raw.endswith("d"):
        raise SystemExit("--last must be in the form '<N>d', e.g. 7d")
    number = raw[:-1]
    if not number.isdigit():
        raise SystemExit("--last must be in the form '<N>d', e.g. 7d")
    days = int(number)
    if days < 1:
        raise SystemExit("--last must be >= 1")
    start = date.today() - timedelta(days=days - 1)
    return start.isoformat()


def _validate_date(value: str) -> None:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise SystemExit("--date must be YYYY-MM-DD") from exc


def _validate_time(value: str) -> None:
    try:
        datetime.strptime(value, "%H:%M:%S")
    except ValueError as exc:
        raise SystemExit("--time must be HH:MM:SS") from exc


def _render(output_format: str, rows: Iterable[dict]) -> None:
    rows_list = list(rows)
    if not rows_list:
        print("No entries.")
        return
    if output_format == "json":
        print(json.dumps(rows_list, indent=2))
        return
    print(tabulate(rows_list, headers="keys", tablefmt="plain"))


if __name__ == "__main__":
    main()
