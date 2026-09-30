from typing import Literal

from fastapi import FastAPI

from app.models import PaymentEvent
from app.database import (
    create_table,
    save_payment_event,
    get_all_payment_events,
    get_filtered_payment_metrics,
    get_processor_metrics,
    get_terminal_metrics,
    get_transaction_trends,
    get_revenue_risk,
)
from app.incident_service import detect_incidents


Period = Literal[
    "today",
    "yesterday",
    "7_days",
    "all_time",
]


app = FastAPI(
    title="Payment API Monitoring Platform",
    version="0.3.0",
)

create_table()


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/events", status_code=201)
def create_payment_event(event: PaymentEvent):
    save_payment_event(event)

    return {
        "accepted": True,
        "event_id": event.event_id,
    }


@app.get("/events")
def read_payment_events():
    events = get_all_payment_events()

    return {
        "total": len(events),
        "events": events,
    }


@app.get("/metrics")
def read_payment_metrics(
    period: Period = "all_time",
):
    return get_filtered_payment_metrics(period=period)


@app.get("/metrics/trends")
def read_transaction_trends(
    period: Period = "7_days",
):
    return get_transaction_trends(period=period)


@app.get("/metrics/revenue-risk")
def read_revenue_risk(
    period: Period = "today",
):
    return get_revenue_risk(period=period)


@app.get("/metrics/processors")
def read_processor_metrics(
    period: Period = "all_time",
):
    processors = get_processor_metrics(period=period)

    return {
        "period": period,
        "total_processors": len(processors),
        "processors": processors,
    }


@app.get("/metrics/terminals")
def read_terminal_metrics(minutes: int = 15):
    terminals = get_terminal_metrics(minutes=minutes)

    return {
        "window_minutes": minutes,
        "total_terminal_groups": len(terminals),
        "terminals": terminals,
    }


@app.get("/incidents")
def read_incidents():
    incidents = detect_incidents()

    return {
        "total_incidents": len(incidents),
        "incidents": incidents,
    }