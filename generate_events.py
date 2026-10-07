import random
from datetime import datetime, timedelta, timezone

import requests 
import time

API_URL = "http://127.0.0.1:8000/events"


MERCHANTS = [
    "merchant-001",
    "merchant-002",
    "merchant-003",
    "merchant-004",
    "merchant-005",
]

TERMINALS = [
    "terminal-001",
    "terminal-002",
    "terminal-003",
    "terminal-004",
]

PROCESSORS = [
    "processor-a",
    "processor-b",
    "processor-c",
]


def choose_payment_result():
    status = random.choices(
        population=["approved", "declined", "error"],
        weights=[85, 10, 5],
        k=1,
    )[0]

    if status == "approved":
        return status, "00"

    if status == "declined":
        return status, random.choice(["05", "51", "54"])

    return status, random.choice(["91", "96"])


def generate_random_timestamp():
    now = datetime.now(timezone.utc)

    random_seconds = random.randint(
        0,
        7 * 24 * 60 * 60,
    )

    occurred_at = now - timedelta(seconds=random_seconds)

    return occurred_at.isoformat()


def generate_payment_event():
    status, response_code = choose_payment_result()

    if status == "error":
        latency_ms = random.randint(1000, 3000)
    else:
        latency_ms = random.randint(80, 500)

    return {
        "occurred_at": generate_random_timestamp(),
        "merchant_id": random.choice(MERCHANTS),
        "terminal_id": random.choice(TERMINALS),
        "processor": random.choice(PROCESSORS),
        "amount": round(random.uniform(1.00, 500.00), 2),
        "currency": "USD",
        "status": status,
        "response_code": response_code,
        "latency_ms": latency_ms,
    }


def send_payment_events(number_of_events):
    successful_requests = 0
    failed_requests = 0

    for event_number in range(1, number_of_events + 1):
        payment_event = generate_payment_event()

        try:
            response = requests.post(
                API_URL,
                json=payment_event,
                timeout=5,
            )

            if response.status_code == 201:
                successful_requests += 1

                print(
                    f"Event {event_number}: "
                    f"{payment_event['status']} - "
                    f"{payment_event['occurred_at']} - saved"
                )
            else:
                failed_requests += 1

                print(
                    f"Event {event_number}: failed "
                    f"with status {response.status_code}"
                )
                print(response.text)

        except requests.RequestException as error:
            failed_requests += 1
            print(
                f"Event {event_number}: "
                f"connection failed - {error}"
            )

    print()
    print("Generation complete")
    print(f"Successful requests: {successful_requests}")
    print(f"Failed requests: {failed_requests}")




if __name__ == "__main__":
    print("Automatic payment event generator started")
    print("Press Control + C to stop")

    while True:
        number_of_events = random.randint(5, 25)

        print()
        print(f"Generating {number_of_events} payment events...")
        send_payment_events(number_of_events)

        wait_seconds = random.randint(30, 120)

        print(
            f"Waiting {wait_seconds} seconds "
            "before the next batch..."
        )

        time.sleep(wait_seconds)