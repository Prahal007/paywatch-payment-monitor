import sqlite3
from datetime import datetime, timedelta, timezone

from app.models import PaymentEvent


DATABASE_NAME = "payment_monitor.db"


def create_table():
    connection = sqlite3.connect(DATABASE_NAME)

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS payment_events (
            event_id TEXT PRIMARY KEY,
            occurred_at TEXT NOT NULL,
            merchant_id TEXT NOT NULL,
            terminal_id TEXT NOT NULL,
            processor TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT NOT NULL,
            status TEXT NOT NULL,
            response_code TEXT NOT NULL,
            latency_ms INTEGER NOT NULL
        )
        """
    )

    connection.commit()
    connection.close()


def save_payment_event(event: PaymentEvent):
    connection = sqlite3.connect(DATABASE_NAME)

    connection.execute(
        """
        INSERT INTO payment_events (
            event_id,
            occurred_at,
            merchant_id,
            terminal_id,
            processor,
            amount,
            currency,
            status,
            response_code,
            latency_ms
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event.event_id,
            event.occurred_at.isoformat(),
            event.merchant_id,
            event.terminal_id,
            event.processor,
            event.amount,
            event.currency,
            event.status.value,
            event.response_code,
            event.latency_ms,
        ),
    )

    connection.commit()
    connection.close()


def get_all_payment_events():
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row

    rows = connection.execute(
        """
        SELECT *
        FROM payment_events
        ORDER BY occurred_at DESC
        """
    ).fetchall()

    connection.close()

    return [dict(row) for row in rows]


def get_payment_metrics():
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row

    row = connection.execute(
        """
        SELECT
            COUNT(*) AS total_transactions,

            SUM(
                CASE WHEN status = 'approved' THEN 1 ELSE 0 END
            ) AS approved_transactions,

            SUM(
                CASE WHEN status = 'declined' THEN 1 ELSE 0 END
            ) AS declined_transactions,

            SUM(
                CASE WHEN status = 'error' THEN 1 ELSE 0 END
            ) AS error_transactions,

            ROUND(AVG(latency_ms), 2) AS average_latency_ms,
            MAX(latency_ms) AS maximum_latency_ms

        FROM payment_events
        """
    ).fetchone()

    connection.close()

    return dict(row)


def get_processor_metrics(period: str = "all_time"):
    start_time, end_time = get_period_boundaries(period)

    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row

    query = """
        SELECT
            processor,
            COUNT(*) AS total_transactions,

            SUM(
                CASE WHEN status = 'approved' THEN 1 ELSE 0 END
            ) AS approved_transactions,

            SUM(
                CASE WHEN status = 'declined' THEN 1 ELSE 0 END
            ) AS declined_transactions,

            SUM(
                CASE WHEN status = 'error' THEN 1 ELSE 0 END
            ) AS error_transactions,

            ROUND(
                100.0 * SUM(
                    CASE WHEN status = 'approved' THEN 1 ELSE 0 END
                ) / COUNT(*),
                2
            ) AS approval_rate,

            ROUND(
                100.0 * SUM(
                    CASE WHEN status = 'declined' THEN 1 ELSE 0 END
                ) / COUNT(*),
                2
            ) AS decline_rate,

            ROUND(
                100.0 * SUM(
                    CASE WHEN status = 'error' THEN 1 ELSE 0 END
                ) / COUNT(*),
                2
            ) AS error_rate,

            ROUND(AVG(latency_ms), 2) AS average_latency_ms,
            MAX(latency_ms) AS maximum_latency_ms

        FROM payment_events
    """

    parameters = ()

    if start_time is not None:
        query += """
            WHERE occurred_at >= ?
            AND occurred_at < ?
        """
        parameters = (start_time, end_time)

    query += """
        GROUP BY processor
        ORDER BY processor
    """

    rows = connection.execute(query, parameters).fetchall()

    connection.close()

    return [dict(row) for row in rows]

def get_terminal_metrics(minutes: int = 15):
    cutoff_time = datetime.now(timezone.utc) - timedelta(
        minutes=minutes
    )
    cutoff_iso = cutoff_time.isoformat()

    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row

    rows = connection.execute(
        """
        SELECT
            terminal_id,
            merchant_id,
            processor,
            COUNT(*) AS total_transactions,

            SUM(
                CASE WHEN status = 'approved' THEN 1 ELSE 0 END
            ) AS approved_transactions,

            SUM(
                CASE WHEN status = 'declined' THEN 1 ELSE 0 END
            ) AS declined_transactions,

            SUM(
                CASE WHEN status = 'error' THEN 1 ELSE 0 END
            ) AS error_transactions,

            ROUND(
                100.0 * SUM(
                    CASE WHEN status = 'declined' THEN 1 ELSE 0 END
                ) / COUNT(*),
                2
            ) AS decline_rate,

            ROUND(
                100.0 * SUM(
                    CASE WHEN status = 'error' THEN 1 ELSE 0 END
                ) / COUNT(*),
                2
            ) AS error_rate,

            ROUND(AVG(latency_ms), 2) AS average_latency_ms,
            MAX(latency_ms) AS maximum_latency_ms

        FROM payment_events
        WHERE occurred_at >= ?
        GROUP BY terminal_id, merchant_id, processor
        ORDER BY terminal_id, merchant_id, processor
        """,
        (cutoff_iso,),
    ).fetchall()

    connection.close()

    return [dict(row) for row in rows]


def get_period_boundaries(period: str):
    now = datetime.now(timezone.utc)

    today_start = now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    if period == "today":
        return today_start.isoformat(), now.isoformat()

    if period == "yesterday":
        yesterday_start = today_start - timedelta(days=1)

        return (
            yesterday_start.isoformat(),
            today_start.isoformat(),
        )

    if period == "7_days":
        seven_days_ago = now - timedelta(days=7)

        return seven_days_ago.isoformat(), now.isoformat()

    return None, None


def get_filtered_payment_metrics(period: str = "all_time"):
    start_time, end_time = get_period_boundaries(period)

    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row

    if start_time is None:
        row = connection.execute(
            """
            SELECT
                COUNT(*) AS total_transactions,

                SUM(
                    CASE WHEN status = 'approved' THEN 1 ELSE 0 END
                ) AS approved_transactions,

                SUM(
                    CASE WHEN status = 'declined' THEN 1 ELSE 0 END
                ) AS declined_transactions,

                SUM(
                    CASE WHEN status = 'error' THEN 1 ELSE 0 END
                ) AS error_transactions,

                ROUND(SUM(amount), 2) AS total_payment_volume,
                ROUND(AVG(latency_ms), 2) AS average_latency_ms,
                MAX(latency_ms) AS maximum_latency_ms

            FROM payment_events
            """
        ).fetchone()

    else:
        row = connection.execute(
            """
            SELECT
                COUNT(*) AS total_transactions,

                SUM(
                    CASE WHEN status = 'approved' THEN 1 ELSE 0 END
                ) AS approved_transactions,

                SUM(
                    CASE WHEN status = 'declined' THEN 1 ELSE 0 END
                ) AS declined_transactions,

                SUM(
                    CASE WHEN status = 'error' THEN 1 ELSE 0 END
                ) AS error_transactions,

                ROUND(SUM(amount), 2) AS total_payment_volume,
                ROUND(AVG(latency_ms), 2) AS average_latency_ms,
                MAX(latency_ms) AS maximum_latency_ms

            FROM payment_events
            WHERE occurred_at >= ?
              AND occurred_at < ?
            """,
            (
                start_time,
                end_time,
            ),
        ).fetchone()

    connection.close()

    result = dict(row)

    result["approved_transactions"] = (
        result["approved_transactions"] or 0
    )
    result["declined_transactions"] = (
        result["declined_transactions"] or 0
    )
    result["error_transactions"] = (
        result["error_transactions"] or 0
    )
    result["total_payment_volume"] = (
        result["total_payment_volume"] or 0
    )
    result["average_latency_ms"] = (
        result["average_latency_ms"] or 0
    )
    result["maximum_latency_ms"] = (
        result["maximum_latency_ms"] or 0
    )

    result["period"] = period

    return result


def get_transaction_trends(period: str = "7_days"):
    start_time, end_time = get_period_boundaries(period)

    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row

    if period in ("today", "yesterday"):
        rows = connection.execute(
            """
            SELECT
                substr(occurred_at, 1, 13) || ':00:00'
                    AS time_bucket,

                COUNT(*) AS total_transactions,

                SUM(
                    CASE WHEN status = 'approved' THEN 1 ELSE 0 END
                ) AS approved_transactions,

                SUM(
                    CASE WHEN status = 'declined' THEN 1 ELSE 0 END
                ) AS declined_transactions,

                SUM(
                    CASE WHEN status = 'error' THEN 1 ELSE 0 END
                ) AS error_transactions,

                ROUND(SUM(amount), 2) AS payment_volume,
                ROUND(AVG(latency_ms), 2) AS average_latency_ms

            FROM payment_events
            WHERE occurred_at >= ?
              AND occurred_at < ?

            GROUP BY substr(occurred_at, 1, 13)
            ORDER BY time_bucket
            """,
            (
                start_time,
                end_time,
            ),
        ).fetchall()

        grouped_by = "hour"

    elif period == "7_days":
        rows = connection.execute(
            """
            SELECT
                substr(occurred_at, 1, 10) AS time_bucket,
                COUNT(*) AS total_transactions,

                SUM(
                    CASE WHEN status = 'approved' THEN 1 ELSE 0 END
                ) AS approved_transactions,

                SUM(
                    CASE WHEN status = 'declined' THEN 1 ELSE 0 END
                ) AS declined_transactions,

                SUM(
                    CASE WHEN status = 'error' THEN 1 ELSE 0 END
                ) AS error_transactions,

                ROUND(SUM(amount), 2) AS payment_volume,
                ROUND(AVG(latency_ms), 2) AS average_latency_ms

            FROM payment_events
            WHERE occurred_at >= ?
              AND occurred_at < ?

            GROUP BY substr(occurred_at, 1, 10)
            ORDER BY time_bucket
            """,
            (
                start_time,
                end_time,
            ),
        ).fetchall()

        grouped_by = "day"

    else:
        rows = connection.execute(
            """
            SELECT
                substr(occurred_at, 1, 10) AS time_bucket,
                COUNT(*) AS total_transactions,

                SUM(
                    CASE WHEN status = 'approved' THEN 1 ELSE 0 END
                ) AS approved_transactions,

                SUM(
                    CASE WHEN status = 'declined' THEN 1 ELSE 0 END
                ) AS declined_transactions,

                SUM(
                    CASE WHEN status = 'error' THEN 1 ELSE 0 END
                ) AS error_transactions,

                ROUND(SUM(amount), 2) AS payment_volume,
                ROUND(AVG(latency_ms), 2) AS average_latency_ms

            FROM payment_events
            GROUP BY substr(occurred_at, 1, 10)
            ORDER BY time_bucket
            """
        ).fetchall()

        grouped_by = "day"

    connection.close()

    return {
        "period": period,
        "grouped_by": grouped_by,
        "total_buckets": len(rows),
        "trends": [dict(row) for row in rows],
    }


def get_revenue_risk(period: str = "today"):
    start_time, end_time = get_period_boundaries(period)

    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row

    query = """
        SELECT
            processor,
            COUNT(*) AS total_transactions,

            SUM(
                CASE
                    WHEN status IN ('declined', 'error')
                    THEN 1
                    ELSE 0
                END
            ) AS failed_transactions,

            ROUND(SUM(amount), 2) AS attempted_payment_volume,

            ROUND(
                SUM(
                    CASE
                        WHEN status IN ('declined', 'error')
                        THEN amount
                        ELSE 0
                    END
                ),
                2
            ) AS revenue_at_risk

        FROM payment_events
    """

    parameters = ()

    if start_time is not None:
        query += """
            WHERE occurred_at >= ?
              AND occurred_at < ?
        """
        parameters = (start_time, end_time)

    query += """
        GROUP BY processor
        ORDER BY revenue_at_risk DESC
    """

    rows = connection.execute(
        query,
        parameters,
    ).fetchall()

    connection.close()

    processors = [dict(row) for row in rows]

    total_revenue_at_risk = round(
        sum(row["revenue_at_risk"] or 0 for row in processors),
        2,
    )

    total_failed_transactions = sum(
        row["failed_transactions"] or 0 for row in processors
    )

    return {
        "period": period,
        "total_failed_transactions": total_failed_transactions,
        "total_revenue_at_risk": total_revenue_at_risk,
        "processors": processors,
    }