# VoIP Cloud Observability Platform

Python + Docker + Kubernetes + Prometheus + Grafana

This project is a junior infrastructure / observability portfolio project designed to simulate how a telecom/IT team can monitor VoIP route quality using cloud-native tools.

## What it does

- Processes VoIP call logs from CSV files
- Calculates telecom KPIs:
  - ASR: Answer-Seizure Ratio
  - PDD: Post-Dial Delay
  - latency
  - packet loss
  - failed calls
- Detects possible False Answer Supervision patterns using simple heuristics
- Exposes metrics in Prometheus format
- Visualizes route quality in Grafana
- Includes Docker Compose and Kubernetes manifests

## Project structure

```text
voip-cloud-observability-platform/
├── app/
│   ├── main.py
│   └── analyzer.py
├── data/
│   └── sample_calls.csv
├── grafana/
│   ├── dashboards/
│   └── provisioning/
├── k8s/
├── prometheus/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Run locally with Python

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
# .venv\Scripts\activate  # Windows PowerShell

pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open:

- API: http://localhost:8000
- Summary: http://localhost:8000/summary
- Routes: http://localhost:8000/routes
- FAS suspects: http://localhost:8000/fas-suspects
- Prometheus metrics: http://localhost:8000/metrics

## Run with Docker Compose

```bash
docker compose up --build
```

Open:

- API: http://localhost:8000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

Grafana default login:

```text
username: admin
password: admin
```

The dashboard should be automatically provisioned.

## Run on Kubernetes with Minikube

Start Minikube:

```bash
minikube start
```

Build the Docker image inside Minikube:

```bash
eval $(minikube docker-env)        # Linux/Mac
# minikube docker-env | Invoke-Expression   # Windows PowerShell

docker build -t voip-cloud-observability:latest .
```

Apply Kubernetes manifests:

```bash
kubectl apply -f k8s/
```

Check pods and services:

```bash
kubectl get pods
kubectl get svc
```

Open the API:

```bash
minikube service voip-api
```

Open Prometheus:

```bash
minikube service prometheus
```

## Useful interview explanation

I built a small VoIP observability platform that analyzes call logs and exposes telecom KPIs as Prometheus metrics. The application is containerized with Docker and can be deployed locally or on Kubernetes using Minikube. Grafana visualizes route health, ASR, PDD, packet loss, latency, and potential FAS patterns. The goal was to connect my telecom support background with cloud infrastructure and observability tools.

## CV bullet

Built a containerized VoIP observability platform using Python, Docker, Kubernetes, Prometheus, and Grafana to analyze call logs, expose route-quality metrics, and visualize KPIs such as ASR, PDD, latency, packet loss, and potential False Answer Supervision patterns.
