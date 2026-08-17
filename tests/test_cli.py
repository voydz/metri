import json
import re
import sys

import pytest

from metricli.__main__ import main

ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


@pytest.fixture(autouse=True)
def plain_wide_output(monkeypatch):
    """Keep help rendering independent of the terminal rich thinks it is writing to.

    Rich styles and hard-wraps its help output when colour is forced (FORCE_COLOR is
    set in CI), which otherwise breaks substring assertions.
    """
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setenv("TERM", "dumb")
    monkeypatch.setenv("COLUMNS", "200")


def test_main_prints_help_when_no_arguments(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["metri"])

    main()

    captured = ANSI_ESCAPE.sub("", capsys.readouterr().out)
    assert "Usage: metri" in captured
    assert "Log and query health/fitness metrics." in captured
    assert "log" in captured
    assert "Log a new metric entry." in captured
    assert "delete" in captured
    assert "Delete a metric by id." in captured
    assert "today" in captured
    assert "Show metrics logged today." in captured
    assert "query" in captured
    assert "Query metric history with optional aggregations." in captured


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
