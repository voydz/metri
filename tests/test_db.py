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
