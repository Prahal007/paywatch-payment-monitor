import pandas as pd
import requests
import streamlit as st
from datetime import datetime


API_BASE_URL = "http://127.0.0.1:8000"


st.set_page_config(
    page_title="Payment Operations Center",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------- Styling ----------

st.markdown(
    """
    <style>
        .stApp {
            background-color: #080d16;
        }

        [data-testid="stSidebar"] {
            background-color: #0d1421;
            border-right: 1px solid #202b3c;
        }

        .block-container {
            max-width: 1500px;
            padding-top: 2rem;
            padding-bottom: 4rem;
        }

        .hero {
            padding: 1.5rem 1.7rem;
            margin-bottom: 1.5rem;
            border: 1px solid #202b3c;
            border-radius: 18px;
            background:
                radial-gradient(
                    circle at top right,
                    rgba(0, 209, 178, 0.18),
                    transparent 35%
                ),
                linear-gradient(135deg, #101827, #0b111c);
        }

        .hero-title {
            color: #ffffff;
            font-size: 2.3rem;
            font-weight: 750;
            margin: 0;
        }

        .hero-subtitle {
            color: #96a3b7;
            font-size: 1rem;
            margin-top: 0.5rem;
            margin-bottom: 0;
        }

        .section-label {
            color: #ffffff;
            font-size: 1.35rem;
            font-weight: 700;
            margin-top: 1.5rem;
            margin-bottom: 0.8rem;
        }

        div[data-testid="stMetric"] {
            background: linear-gradient(145deg, #111a29, #0d1420);
            border: 1px solid #243044;
            padding: 1.1rem;
            border-radius: 14px;
        }

        div[data-testid="stMetricLabel"] {
            color: #97a5ba;
        }

        div[data-testid="stMetricValue"] {
            color: #ffffff;
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid #243044;
            border-radius: 14px;
            overflow: hidden;
        }

        .status-online {
            display: inline-block;
            color: #2ee59d;
            background-color: rgba(46, 229, 157, 0.12);
            border: 1px solid rgba(46, 229, 157, 0.35);
            border-radius: 999px;
            padding: 0.35rem 0.8rem;
            font-weight: 600;
        }

        .status-offline {
            display: inline-block;
            color: #ff6b6b;
            background-color: rgba(255, 107, 107, 0.12);
            border: 1px solid rgba(255, 107, 107, 0.35);
            border-radius: 999px;
            padding: 0.35rem 0.8rem;
            font-weight: 600;
        }

        .incident-card {
            background-color: rgba(255, 82, 82, 0.09);
            border: 1px solid rgba(255, 82, 82, 0.35);
            border-left: 5px solid #ff5252;
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 0.8rem;
        }

        .healthy-card {
            background-color: rgba(46, 229, 157, 0.08);
            border: 1px solid rgba(46, 229, 157, 0.30);
            border-left: 5px solid #2ee59d;
            border-radius: 12px;
            padding: 1rem;
        }

        .footer-text {
            color: #64748b;
            text-align: center;
            padding-top: 2rem;
            font-size: 0.85rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- API functions ----------

def get_api_data(endpoint, show_error=True):
    try:
        response = requests.get(
            f"{API_BASE_URL}{endpoint}",
            timeout=5,
        )
        response.raise_for_status()
        return response.json()

    except requests.RequestException as error:
        if show_error:
            st.error(f"Could not load {endpoint}: {error}")
        return None


def calculate_rate(value, total):
    if total == 0:
        return 0.0

    return round((value / total) * 100, 2)


# ---------- Sidebar ----------

with st.sidebar:
    st.title("💳 PayWatch")
    st.caption("Payment operations console")

    period_labels = {
        "Today": "today",
        "Yesterday": "yesterday",
        "Last 7 Days": "7_days",
        "All Time": "all_time",
    }

    selected_period_label = st.selectbox(
        "Monitoring period",
        options=list(period_labels.keys()),
        index=2,
    )

    selected_period = period_labels[selected_period_label]

    st.divider()

    health_data = get_api_data("/health", show_error=False)

    if health_data:
        st.markdown(
            '<span class="status-online">● API connected</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="status-offline">● API disconnected</span>',
            unsafe_allow_html=True,
        )

    st.divider()

    if st.button("↻ Refresh dashboard", width="stretch"):
        st.rerun()

    st.caption(
        "API address\n\n"
        "`http://127.0.0.1:8000`"
    )

    st.divider()

    st.caption(
        "This dashboard monitors payment outcomes, "
        "processor performance, latency and incidents."
    )


# ---------- Header ----------

st.markdown(
    """
    <div class="hero">
        <p class="hero-title">Payment Operations Center</p>
        <p class="hero-subtitle">
            Monitor transaction outcomes, processor reliability,
            response time and active payment incidents.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

last_updated = datetime.now().strftime("%B %d, %Y · %I:%M:%S %p")
st.caption(f"Last refreshed: {last_updated}")


# ---------- Load API data ----------

metrics = get_api_data(
    f"/metrics?period={selected_period}"
)

trend_data = get_api_data(
    f"/metrics/trends?period={selected_period}"
)

revenue_risk_data = get_api_data(
    f"/metrics/revenue-risk?period={selected_period}"
)

processor_data = get_api_data(
    f"/metrics/processors?period={selected_period}"
)

incident_data = get_api_data("/incidents")

if metrics is None:
    st.warning(
        "The dashboard cannot reach the FastAPI server. "
        "Start the API in Terminal 1 and refresh this page."
    )
    st.code(
        "source .venv/bin/activate\n"
        "python -m uvicorn app.main:app --reload",
        language="bash",
    )
    st.stop()


# ---------- Main metrics ----------

total_transactions = metrics.get("total_transactions", 0)
approved_transactions = metrics.get("approved_transactions", 0)
declined_transactions = metrics.get("declined_transactions", 0)
error_transactions = metrics.get("error_transactions", 0)

approval_rate = calculate_rate(
    approved_transactions,
    total_transactions,
)

decline_rate = calculate_rate(
    declined_transactions,
    total_transactions,
)

error_rate = calculate_rate(
    error_transactions,
    total_transactions,
)

st.markdown(
    (
        '<div class="section-label">'
        f'Transaction Overview · {selected_period_label}'
        '</div>'
    ),
    unsafe_allow_html=True,
)

column1, column2, column3, column4, column5 = st.columns(5)

column1.metric(
    label="Total Transactions",
    value=f"{total_transactions:,}",
)

column2.metric(
    label="Approved",
    value=f"{approved_transactions:,}",
    delta=f"{approval_rate}% approval rate",
)

column3.metric(
    label="Declined",
    value=f"{declined_transactions:,}",
    delta=f"{decline_rate}% decline rate",
    delta_color="inverse",
)

column4.metric(
    label="Processing Errors",
    value=f"{error_transactions:,}",
    delta=f"{error_rate}% error rate",
    delta_color="inverse",
)

column5.metric(
    label="Payment Volume",
    value=f"${metrics.get('total_payment_volume', 0):,.2f}",
)
# ---------- Revenue at risk ----------

st.markdown(
    '<div class="section-label">Revenue at Risk</div>',
    unsafe_allow_html=True,
)

if revenue_risk_data:
    total_revenue_at_risk = (
        revenue_risk_data.get("total_revenue_at_risk", 0) or 0
    )

    total_failed_transactions = (
        revenue_risk_data.get("total_failed_transactions", 0) or 0
    )

    total_payment_volume = (
        metrics.get("total_payment_volume", 0) or 0
    )

    if total_payment_volume > 0:
        revenue_risk_rate = round(
            (total_revenue_at_risk / total_payment_volume) * 100,
            2,
        )
    else:
        revenue_risk_rate = 0.0

    risk_column1, risk_column2, risk_column3 = st.columns(3)

    risk_column1.metric(
        label="Potential Revenue at Risk",
        value=f"${total_revenue_at_risk:,.2f}",
    )

    risk_column2.metric(
        label="Failed Transactions",
        value=f"{total_failed_transactions:,}",
    )

    risk_column3.metric(
        label="At-Risk Volume Rate",
        value=f"{revenue_risk_rate:.2f}%",
    )

    risk_processors = revenue_risk_data.get("processors", [])

    if risk_processors:
        risk_dataframe = pd.DataFrame(risk_processors)

        highest_risk_processor = max(
            risk_processors,
            key=lambda processor: processor.get(
                "revenue_at_risk",
                0,
            ) or 0,
        )

        highest_processor_name = highest_risk_processor.get(
            "processor",
            "Unknown processor",
        )

        highest_processor_value = highest_risk_processor.get(
            "revenue_at_risk",
            0,
        ) or 0

        st.warning(
            f"{highest_processor_name} currently has the highest "
            f"potential revenue impact: "
            f"${highest_processor_value:,.2f}"
        )

        risk_chart_dataframe = risk_dataframe.set_index("processor")[
            ["revenue_at_risk"]
        ]

        st.bar_chart(
            risk_chart_dataframe,
            color="#ff6b6b",
            height=320,
        )

        with st.expander("View processor revenue-risk details"):
            st.dataframe(
                risk_dataframe,
                width="stretch",
                hide_index=True,
            )

    elif total_failed_transactions == 0:
        st.success(
            "No payment revenue is currently at risk "
            f"for {selected_period_label}."
        )

else:
    st.info("Revenue-risk information is currently unavailable.")




# ---------- Transaction trends ----------

st.markdown(
    '<div class="section-label">Transaction Trends</div>',
    unsafe_allow_html=True,
)

if trend_data and trend_data.get("trends"):
    trend_dataframe = pd.DataFrame(trend_data["trends"])

    trend_dataframe["time_bucket"] = pd.to_datetime(
        trend_dataframe["time_bucket"]
    )

    trend_dataframe = trend_dataframe.set_index("time_bucket")

    trend_tab1, trend_tab2, trend_tab3 = st.tabs(
        [
            "Transaction volume",
            "Payment outcomes",
            "Latency",
        ]
    )

    with trend_tab1:
        st.line_chart(
            trend_dataframe[["total_transactions"]],
            height=360,
        )

        st.caption(
            "Shows how many payment attempts were received "
            f"for each {trend_data.get('grouped_by', 'time')} period."
        )

    with trend_tab2:
        st.line_chart(
            trend_dataframe[
                [
                    "approved_transactions",
                    "declined_transactions",
                    "error_transactions",
                ]
            ],
            height=360,
        )

    with trend_tab3:
        st.line_chart(
            trend_dataframe[["average_latency_ms"]],
            height=360,
        )

    st.markdown(
        '<div class="section-label">Payment Volume Trend</div>',
        unsafe_allow_html=True,
    )

    st.bar_chart(
        trend_dataframe[["payment_volume"]],
        color="#21c7a8",
        height=320,
    )

else:
    st.info(
        f"No transaction trend data is available for {selected_period_label}. "
        "Run the synthetic event generator to create recent transactions."
    )


# ---------- Outcome and latency summary ----------

summary_column, latency_column = st.columns([1.3, 1])

with summary_column:
    st.markdown(
        '<div class="section-label">Payment Outcomes</div>',
        unsafe_allow_html=True,
    )

    outcome_dataframe = pd.DataFrame(
        {
            "Outcome": ["Approved", "Declined", "Error"],
            "Transactions": [
                approved_transactions,
                declined_transactions,
                error_transactions,
            ],
        }
    ).set_index("Outcome")

    st.bar_chart(
        outcome_dataframe,
        color="#21c7a8",
        height=320,
    )

with latency_column:
    st.markdown(
        '<div class="section-label">Latency Health</div>',
        unsafe_allow_html=True,
    )

    average_latency = metrics.get("average_latency_ms", 0) or 0
    maximum_latency = metrics.get("maximum_latency_ms", 0) or 0

    latency_metric1, latency_metric2 = st.columns(2)

    latency_metric1.metric(
        "Average",
        f"{average_latency} ms",
    )

    latency_metric2.metric(
        "Maximum",
        f"{maximum_latency} ms",
    )

    if average_latency < 500:
        st.success("Average response time is within the healthy range.")
    elif average_latency < 1000:
        st.warning("Average response time requires attention.")
    else:
        st.error("Average response time is critically high.")

    if maximum_latency >= 2000:
        st.warning(
            "Some transactions experienced latency above 2 seconds."
        )


# ---------- Processor performance ----------

st.markdown(
    '<div class="section-label">Processor Performance</div>',
    unsafe_allow_html=True,
)

if processor_data and processor_data.get("processors"):
    processor_dataframe = pd.DataFrame(
        processor_data["processors"]
    )

    display_columns = [
        "processor",
        "total_transactions",
        "approval_rate",
        "decline_rate",
        "error_rate",
        "average_latency_ms",
        "maximum_latency_ms",
    ]

    available_columns = [
        column
        for column in display_columns
        if column in processor_dataframe.columns
    ]

    st.dataframe(
        processor_dataframe[available_columns],
        width="stretch",
        hide_index=True,
        column_config={
            "processor": "Processor",
            "total_transactions": "Transactions",
            "approval_rate": st.column_config.NumberColumn(
                "Approval Rate",
                format="%.2f%%",
            ),
            "decline_rate": st.column_config.NumberColumn(
                "Decline Rate",
                format="%.2f%%",
            ),
            "error_rate": st.column_config.NumberColumn(
                "Error Rate",
                format="%.2f%%",
            ),
            "average_latency_ms": st.column_config.NumberColumn(
                "Average Latency",
                format="%d ms",
            ),
            "maximum_latency_ms": st.column_config.NumberColumn(
                "Maximum Latency",
                format="%d ms",
            ),
        },
    )

    chart_tab1, chart_tab2 = st.tabs(
        [
            "Payment success rates",
            "Processor latency",
        ]
    )

    with chart_tab1:
        rate_columns = [
            "approval_rate",
            "decline_rate",
            "error_rate",
        ]

        if all(
            column in processor_dataframe.columns
            for column in rate_columns
        ):
            rate_dataframe = processor_dataframe.set_index("processor")[
                rate_columns
            ]

            st.bar_chart(
                rate_dataframe,
                stack=False,
                height=400,
            )

    with chart_tab2:
        latency_columns = [
            "average_latency_ms",
            "maximum_latency_ms",
        ]

        if all(
            column in processor_dataframe.columns
            for column in latency_columns
        ):
            latency_dataframe = processor_dataframe.set_index("processor")[
                latency_columns
            ]

            st.bar_chart(
                latency_dataframe,
                stack=False,
                height=400,
            )

else:
    st.info("No processor performance data is available.")


# ---------- Incidents ----------

st.markdown(
    '<div class="section-label">Active Incidents · Last 15 Minutes</div>',
    unsafe_allow_html=True,
)

if incident_data:
    incidents = incident_data.get("incidents", [])
    total_incidents = incident_data.get(
        "total_incidents",
        len(incidents),
    )

    if total_incidents == 0:
        st.markdown(
            """
            <div class="healthy-card">
                <strong>✓ All systems operational</strong><br>
                No payment processor incidents are currently active.
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:
        st.error(
            f"{total_incidents} active payment incident(s) detected"
        )

        for incident in incidents:
            processor = incident.get("processor", "Unknown processor")
            severity = incident.get("severity", "warning")
            reason = incident.get("reason", "Performance issue")
            metric = incident.get("metric", "metric")
            current_value = incident.get("current_value", 0)
            threshold = incident.get("threshold", 0)

            st.markdown(
                f"""
                <div class="incident-card">
                    <strong>{processor}</strong>
                    &nbsp;·&nbsp; {severity.upper()}<br>
                    {reason}<br><br>
                    Current {metric}: <strong>{current_value}%</strong>
                    &nbsp;·&nbsp;
                    Alert threshold: <strong>{threshold}%</strong>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with st.expander("View technical incident details"):
            incident_dataframe = pd.DataFrame(incidents)

            st.dataframe(
                incident_dataframe,
                width="stretch",
                hide_index=True,
            )

else:
    st.info("Incident information is currently unavailable.")


# ---------- Footer ----------

st.markdown(
    """
    <div class="footer-text">
        PayWatch · Payment API Monitoring Platform · Synthetic demonstration data
    </div>
    """,
    unsafe_allow_html=True,
)
