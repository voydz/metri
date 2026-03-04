import json
import sys

import pytest

from metricli.__main__ import main


def test_main_prints_help_when_no_arguments(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["metri"])

    main()

    captured = capsys.readouterr()
    assert "Usage: metri" in captured.out
    assert "Log and query health/fitness metrics." in captured.out
    assert "log" in captured.out
    assert "Log a new metric entry." in captured.out
    assert "delete" in captured.out
    assert "Delete a metric by id." in captured.out
    assert "today" in captured.out
    assert "Show metrics logged today." in captured.out
    assert "query" in captured.out
    assert "Query metric history with optional aggregations." in captured.out


def test_command_local_format_option_is_supported(monkeypatch, capsys):
    monkeypatch.setenv("METRI_DB_PATH", ":memory:")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "metri",
            "log",
            "--key",
            "weight_kg",
            "--value",
            "82.7",
            "--date",
            "2026-03-01",
            "--time",
            "10:30:00",
            "--format",
            "json",
        ],
    )

    main()

    captured = capsys.readouterr()
    row = json.loads(captured.out)
    assert isinstance(row, dict)
    assert row["metric_key"] == "weight_kg"
    assert row["value"] == 82.7
    assert row["date"] == "2026-03-01"
    assert row["time"] == "10:30:00"


def test_global_format_option_is_not_supported(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["metri", "--format", "json", "today"])

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 2
