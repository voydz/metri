from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path

DB_ENV_VAR = "METRI_DB_PATH"
DEFAULT_DB_PATH = Path.home() / ".local" / "share" / "metri" / "metrics.db"


@dataclass(frozen=True)
class MetricRecord:
    id: int
    date: str
    time: str
    metric_key: str
    value: float
    source: str | None
    created_at: str


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    metric_key TEXT NOT NULL,
    value REAL NOT NULL,
    source TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_metrics_date ON metrics(date);
CREATE INDEX IF NOT EXISTS idx_metrics_key ON metrics(metric_key);
"""


def get_db_path() -> Path:
    env_path = os.environ.get(DB_ENV_VAR)
    if env_path:
        return Path(env_path).expanduser()
    return DEFAULT_DB_PATH


def ensure_data_dir(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)


def connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    if db_path is None:
        path: Path | str = get_db_path()
    else:
        db_path_str = str(db_path)
        path = ":memory:" if db_path_str == ":memory:" else Path(db_path_str).expanduser()

    if isinstance(path, Path):
        ensure_data_dir(path)
        connect_target: str | Path = path
    else:
        connect_target = path

    conn = sqlite3.connect(connect_target)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    conn.commit()


def insert_metric(
    conn: sqlite3.Connection,
    *,
    metric_date: str,
    metric_time: str,
    metric_key: str,
    value: float,
    source: str | None,
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO metrics (date, time, metric_key, value, source)
        VALUES (?, ?, ?, ?, ?)
        """,
        (metric_date, metric_time, metric_key, value, source),
    )
    conn.commit()
    return int(cursor.lastrowid)


def delete_metric(conn: sqlite3.Connection, metric_id: int) -> int:
    cursor = conn.execute("DELETE FROM metrics WHERE id = ?", (metric_id,))
    conn.commit()
    return cursor.rowcount


def fetch_by_date(conn: sqlite3.Connection, metric_date: str) -> list[MetricRecord]:
    rows = conn.execute(
        """
        SELECT id, date, time, metric_key, value, source, created_at
        FROM metrics
        WHERE date = ?
        ORDER BY time ASC, id ASC
        """,
        (metric_date,),
    ).fetchall()
    return [_row_to_record(row) for row in rows]


def fetch_range(
    conn: sqlite3.Connection,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[MetricRecord]:
    clauses: list[str] = []
    params: list[str] = []
    if start_date:
        clauses.append("date >= ?")
        params.append(start_date)
    if end_date:
        clauses.append("date <= ?")
        params.append(end_date)
    where_sql = ""
    if clauses:
        where_sql = "WHERE " + " AND ".join(clauses)
    rows = conn.execute(
        f"""
        SELECT id, date, time, metric_key, value, source, created_at
        FROM metrics
        {where_sql}
        ORDER BY date ASC, time ASC, id ASC
        """,
        params,
    ).fetchall()
    return [_row_to_record(row) for row in rows]


def fetch_avg_range(
    conn: sqlite3.Connection,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict[str, str | float | int]]:
    clauses: list[str] = []
    params: list[str] = []
    if start_date:
        clauses.append("date >= ?")
        params.append(start_date)
    if end_date:
        clauses.append("date <= ?")
        params.append(end_date)
    where_sql = ""
    if clauses:
        where_sql = "WHERE " + " AND ".join(clauses)
    rows = conn.execute(
        f"""
        SELECT metric_key, AVG(value) AS avg_value, COUNT(*) AS count
        FROM metrics
        {where_sql}
        GROUP BY metric_key
        ORDER BY metric_key ASC
        """,
        params,
    ).fetchall()
    return [
        {
            "metric_key": row["metric_key"],
            "avg_value": float(row["avg_value"]),
            "count": int(row["count"]),
        }
        for row in rows
    ]


def _row_to_record(row: sqlite3.Row) -> MetricRecord:
    return MetricRecord(
        id=int(row["id"]),
        date=row["date"],
        time=row["time"],
        metric_key=row["metric_key"],
        value=float(row["value"]),
        source=row["source"],
        created_at=row["created_at"],
    )


def iso_today() -> str:
    return date.today().isoformat()
