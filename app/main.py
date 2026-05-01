from fastapi import FastAPI, UploadFile, File
from fastapi.responses import PlainTextResponse
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST
from pathlib import Path
import shutil
import tempfile

from app.analyzer import load_calls, route_summary, detect_fas_suspects, global_summary

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_calls.csv"

app = FastAPI(title="VoIP Cloud Observability Platform")

total_calls_gauge = Gauge("voip_total_calls", "Total VoIP calls analyzed")
asr_gauge = Gauge("voip_asr_percent", "Answer-Seizure Ratio percentage")
avg_pdd_gauge = Gauge("voip_avg_pdd_seconds", "Average post-dial delay in seconds")
avg_latency_gauge = Gauge("voip_avg_latency_ms", "Average latency in milliseconds")
avg_packet_loss_gauge = Gauge("voip_avg_packet_loss_percent", "Average packet loss percentage")
fas_suspects_gauge = Gauge("voip_fas_suspects", "Potential False Answer Supervision suspects")
route_health_gauge = Gauge("voip_route_health_status", "Route health: 0 healthy, 1 warning, 2 critical", ["route"])

HEALTH_MAP = {"healthy": 0, "warning": 1, "critical": 2}

def refresh_metrics(csv_path=DATA_PATH):
    df = load_calls(str(csv_path))
    summary = global_summary(df)
    routes = route_summary(df)

    total_calls_gauge.set(summary["total_calls"])
    asr_gauge.set(summary["asr_percent"])
    avg_pdd_gauge.set(summary["avg_pdd_seconds"])
    avg_latency_gauge.set(summary["avg_latency_ms"])
    avg_packet_loss_gauge.set(summary["avg_packet_loss_percent"])
    fas_suspects_gauge.set(summary["fas_suspects"])

    for _, row in routes.iterrows():
        route_health_gauge.labels(route=row["route"]).set(HEALTH_MAP[row["health"]])

    return df, summary, routes

@app.get("/")
def home():
    return {
        "project": "VoIP Cloud Observability Platform",
        "description": "Python analyzer exposing VoIP KPIs as Prometheus metrics for Grafana dashboards.",
        "endpoints": ["/summary", "/routes", "/fas-suspects", "/metrics", "/upload"]
    }

@app.get("/summary")
def get_summary():
    _, summary, _ = refresh_metrics()
    return summary

@app.get("/routes")
def get_routes():
    _, _, routes = refresh_metrics()
    return routes.to_dict(orient="records")

@app.get("/fas-suspects")
def get_fas_suspects():
    df, _, _ = refresh_metrics()
    return detect_fas_suspects(df).head(100).to_dict(orient="records")

@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    df = load_calls(tmp_path)
    summary = global_summary(df)
    routes = route_summary(df)
    return {
        "summary": summary,
        "routes": routes.to_dict(orient="records"),
        "note": "Upload analyzed successfully. The demo Prometheus metrics still use data/sample_calls.csv."
    }

@app.get("/metrics")
def metrics():
    refresh_metrics()
    return PlainTextResponse(generate_latest().decode("utf-8"), media_type=CONTENT_TYPE_LATEST)
