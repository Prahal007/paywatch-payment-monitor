from app.database import get_processor_metrics


ERROR_RATE_THRESHOLD = 5.0
DECLINE_RATE_THRESHOLD = 15.0
LATENCY_THRESHOLD_MS = 800.0


def detect_incidents():
    processor_metrics = get_processor_metrics()
    incidents = []

    for processor in processor_metrics:
        processor_name = processor["processor"]

        if processor["error_rate"] >= ERROR_RATE_THRESHOLD:
            incidents.append(
                {
                    "processor": processor_name,
                    "severity": "critical",
                    "metric": "error_rate",
                    "reason": "Processor error rate is too high",
                    "current_value": processor["error_rate"],
                    "threshold": ERROR_RATE_THRESHOLD,
                }
            )

        if processor["decline_rate"] >= DECLINE_RATE_THRESHOLD:
            incidents.append(
                {
                    "processor": processor_name,
                    "severity": "warning",
                    "metric": "decline_rate",
                    "reason": "Processor decline rate is too high",
                    "current_value": processor["decline_rate"],
                    "threshold": DECLINE_RATE_THRESHOLD,
                }
            )

        if processor["average_latency_ms"] >= LATENCY_THRESHOLD_MS:
            incidents.append(
                {
                    "processor": processor_name,
                    "severity": "warning",
                    "metric": "average_latency_ms",
                    "reason": "Processor average latency is too high",
                    "current_value": processor["average_latency_ms"],
                    "threshold": LATENCY_THRESHOLD_MS,
                }
            )

    return incidents