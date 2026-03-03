from metricli import db


def test_insert_and_fetch_by_date(tmp_path):
    db_path = tmp_path / "metrics.db"
    conn = db.connect(db_path)
    try:
        metric_id = db.insert_metric(
            conn,
            metric_date="2024-01-01",
            metric_time="06:30:00",
            metric_key="weight_kg",
            value=70.5,
            source="manual",
        )
        records = db.fetch_by_date(conn, "2024-01-01")
        assert len(records) == 1
        assert records[0].id == metric_id
        assert records[0].metric_key == "weight_kg"
        assert records[0].value == 70.5
    finally:
        conn.close()


def test_delete_metric(tmp_path):
    db_path = tmp_path / "metrics.db"
    conn = db.connect(db_path)
    try:
        metric_id = db.insert_metric(
            conn,
            metric_date="2024-01-02",
            metric_time="07:00:00",
            metric_key="ftp_watts",
            value=280,
            source="manual",
        )
        deleted = db.delete_metric(conn, metric_id)
        assert deleted == 1
        assert db.fetch_by_date(conn, "2024-01-02") == []
    finally:
        conn.close()


def test_fetch_trends_range(tmp_path):
    db_path = tmp_path / "metrics.db"
    conn = db.connect(db_path)
    try:
        db.insert_metric(
            conn,
            metric_date="2024-01-01",
            metric_time="07:00:00",
            metric_key="weight_kg",
            value=80.0,
            source="manual",
        )
        db.insert_metric(
            conn,
            metric_date="2024-01-10",
            metric_time="07:00:00",
            metric_key="weight_kg",
            value=78.5,
            source="manual",
        )
        db.insert_metric(
            conn,
            metric_date="2024-01-01",
            metric_time="06:00:00",
            metric_key="ftp_watts",
            value=250.0,
            source="manual",
        )
        db.insert_metric(
            conn,
            metric_date="2024-01-10",
            metric_time="06:00:00",
            metric_key="ftp_watts",
            value=265.0,
            source="manual",
        )

        rows = db.fetch_trends_range(conn)
        assert rows == [
            {
                "metric_key": "ftp_watts",
                "first_value": 250.0,
                "last_value": 265.0,
                "delta": 15.0,
                "percent_change": 6.0,
                "direction": "up",
                "count": 2,
            },
            {
                "metric_key": "weight_kg",
                "first_value": 80.0,
                "last_value": 78.5,
                "delta": -1.5,
                "percent_change": -1.875,
                "direction": "down",
                "count": 2,
            },
        ]
    finally:
        conn.close()


def test_fetch_trends_range_respects_start_date_and_zero_baseline(tmp_path):
    db_path = tmp_path / "metrics.db"
    conn = db.connect(db_path)
    try:
        db.insert_metric(
            conn,
            metric_date="2024-01-01",
            metric_time="07:00:00",
            metric_key="effort",
            value=0.0,
            source="manual",
        )
        db.insert_metric(
            conn,
            metric_date="2024-01-03",
            metric_time="07:00:00",
            metric_key="effort",
            value=10.0,
            source="manual",
        )
        db.insert_metric(
            conn,
            metric_date="2024-01-04",
            metric_time="07:00:00",
            metric_key="effort",
            value=10.0,
            source="manual",
        )

        rows = db.fetch_trends_range(conn, start_date="2024-01-03")
        assert rows == [
            {
                "metric_key": "effort",
                "first_value": 10.0,
                "last_value": 10.0,
                "delta": 0.0,
                "percent_change": 0.0,
                "direction": "flat",
                "count": 2,
            }
        ]

        rows = db.fetch_trends_range(conn)
        assert rows == [
            {
                "metric_key": "effort",
                "first_value": 0.0,
                "last_value": 10.0,
                "delta": 10.0,
                "percent_change": None,
                "direction": "up",
                "count": 3,
            }
        ]
    finally:
        conn.close()
