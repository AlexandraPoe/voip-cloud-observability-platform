import pandas as pd

REQUIRED_COLUMNS = {
    "call_id", "timestamp", "route", "destination", "status",
    "duration_seconds", "pdd_seconds", "packet_loss_percent",
    "latency_ms", "rbt_status", "sip_code"
}

def load_calls(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    numeric_columns = ["duration_seconds", "pdd_seconds", "packet_loss_percent", "latency_ms", "sip_code"]
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df

def route_summary(df: pd.DataFrame) -> pd.DataFrame:
    grouped = df.groupby("route").agg(
        total_calls=("call_id", "count"),
        answered_calls=("status", lambda s: (s == "answered").sum()),
        failed_calls=("status", lambda s: (s != "answered").sum()),
        avg_pdd_seconds=("pdd_seconds", "mean"),
        avg_latency_ms=("latency_ms", "mean"),
        avg_packet_loss_percent=("packet_loss_percent", "mean"),
        no_rbt_calls=("rbt_status", lambda s: (s == "missing").sum()),
    ).reset_index()

    grouped["asr_percent"] = (grouped["answered_calls"] / grouped["total_calls"] * 100).round(2)
    grouped["avg_pdd_seconds"] = grouped["avg_pdd_seconds"].round(2)
    grouped["avg_latency_ms"] = grouped["avg_latency_ms"].round(2)
    grouped["avg_packet_loss_percent"] = grouped["avg_packet_loss_percent"].round(2)

    grouped["health"] = grouped.apply(classify_route_health, axis=1)
    return grouped.sort_values(by=["health", "asr_percent", "avg_pdd_seconds"], ascending=[True, True, False])

def classify_route_health(row) -> str:
    if row["asr_percent"] < 45 or row["avg_pdd_seconds"] > 8 or row["avg_packet_loss_percent"] > 3:
        return "critical"
    if row["asr_percent"] < 60 or row["avg_pdd_seconds"] > 5 or row["avg_packet_loss_percent"] > 1.5:
        return "warning"
    return "healthy"

def detect_fas_suspects(df: pd.DataFrame) -> pd.DataFrame:
    # Simple heuristic:
    # answered calls with very short duration, missing RBT, or suspiciously low PDD
    suspects = df[
        (df["status"] == "answered") &
        (
            (df["duration_seconds"] <= 3) |
            (df["rbt_status"] == "missing") |
            (df["pdd_seconds"] < 0.7)
        )
    ].copy()

    suspects["reason"] = suspects.apply(_fas_reason, axis=1)
    return suspects[[
        "call_id", "timestamp", "route", "destination", "duration_seconds",
        "pdd_seconds", "rbt_status", "sip_code", "reason"
    ]]

def _fas_reason(row) -> str:
    reasons = []
    if row["duration_seconds"] <= 3:
        reasons.append("very short answered call")
    if row["rbt_status"] == "missing":
        reasons.append("missing ringback tone")
    if row["pdd_seconds"] < 0.7:
        reasons.append("abnormally low PDD")
    return ", ".join(reasons)

def global_summary(df: pd.DataFrame) -> dict:
    total = len(df)
    answered = int((df["status"] == "answered").sum())
    failed = total - answered
    return {
        "total_calls": total,
        "answered_calls": answered,
        "failed_calls": failed,
        "asr_percent": round(answered / total * 100, 2) if total else 0,
        "avg_pdd_seconds": round(float(df["pdd_seconds"].mean()), 2) if total else 0,
        "avg_latency_ms": round(float(df["latency_ms"].mean()), 2) if total else 0,
        "avg_packet_loss_percent": round(float(df["packet_loss_percent"].mean()), 2) if total else 0,
        "fas_suspects": int(len(detect_fas_suspects(df))),
    }
