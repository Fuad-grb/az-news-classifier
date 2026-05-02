# az-news-classifier

Multi-class news classifier for Azerbaijani: scrapes raw articles, fine-tunes XLM-RoBERTa, serves via FastAPI on Kubernetes with Prometheus/Grafana monitoring. Built end-to-end as a portfolio project to cover the full lifecycle from data collection to deployment.

Live demo: [news.fuadgurbanov.com](https://news.fuadgurbanov.com)

## Overview

Azerbaijani is a low-resource language with no publicly available labeled datasets for news classification. The project covers the full pipeline: scraping about 12K articles from three news sites, cleaning down to ~10K, fine-tuning XLM-RoBERTa-base, ONNX export for CPU inference, and deployment on k3s with Helm and monitoring.

Categories:

- siyasət (politics)
- iqtisadiyyat (economy)
- idman (sports)
- dünya (world news)
- sosial (social/society)

## Results

- 93% weighted F1 on held-out test set
- ~20ms inference latency (CPU, 6-core VPS)
- Dataset: 11,589 raw → 10,148 cleaned → 7,102 train / 1,522 val / 1,524 test

Per-class observations: idman has the most distinctive vocabulary and is classified most reliably. siyaset and sosial overlap the most — political and social news share a lot of language. dunya and iqtisadiyyat get confused on articles where world news is primarily about economic events.

## Architecture
Scraping (3 sites) → Cleaning + Dedup → Train/Val/Test Split;

XLM-RoBERTa Fine-tuning → ONNX Export;

FastAPI + ONNX Runtime → Docker;

k3s + Helm → Traefik Ingress → HPA;

Prometheus + Grafana (custom ML metrics);

React Frontend

## Stack

- **ML**: XLM-RoBERTa-base, HuggingFace Transformers, ONNX Runtime, scikit-learn
- **Serving**: FastAPI, Uvicorn, prometheus-client
- **Infrastructure**: Docker, k3s, Helm, Traefik, HPA
- **Monitoring**: Prometheus, Grafana with custom ML metrics (confidence distribution, prediction counts by category, latency histograms)
- **Frontend**: React, TypeScript, Axios
- **Data**: BeautifulSoup, requests, pandas

## Data pipeline

No existing dataset, so I built one.

**Scraping**: abstract base scraper class with site-specific implementations for report.az, sonxeber.az, qafqazinfo.az. Checkpointing to avoid re-downloading, retry with exponential backoff, randomized delays between requests.

**Cleaning**: category name normalization across sites (siyasi-xeberler / siyaset-xeberleri / siyaset-2 → siyaset), removal of articles under 50 words, title-based deduplication for cross-site duplicates (one of the sources aggregates from others).

**Split**: temporal split where dates are available, stratified random for undated articles.

## Monitoring

The interesting part of this project wasn't the model — it was instrumenting the service properly. Standard infra metrics (latency, error rate, CPU/memory) catch infrastructure issues but miss model degradation, since a model can serve 200 OK at low latency while quietly drifting.

Custom metrics exposed at `/metrics`:

- `predictions_total{category}` — counter per class. Distribution shifts signal input drift.
- `prediction_latency_seconds` — histogram for p50/p95/p99.
- `prediction_confidence` — histogram across all predictions. Confidence drops before accuracy does, so it's a leading indicator for drift. Cheap to compute, not a substitute for proper drift detection (PSI, KL-divergence, Evidently) against a reference set.

## Running locally

### Prerequisites

- Python 3.11+
- Docker
- k3s (for Kubernetes deployment)
- Helm 3
- Node.js 18+ (for frontend)

### Training

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Scrape data (takes hours)
python main.py

# Clean and split
python src/cleaning/cleaner.py
python src/cleaning/splitter.py

# Train
cd src/training
python train.py

# Export to ONNX
python export_onnx.py
```

### Serving (Docker)

```bash
docker build -f docker/serving.Dockerfile -t az-classifier:v1 .
docker run -p 8000:8000 az-classifier:v1
```

Test:

```bash
curl http://localhost:8000/health

curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Qarabağ FK Çempionlar Liqasında qalib gəldi"}'
```

### Kubernetes (k3s + Helm)

```bash
# Push image
docker tag az-classifier:v1 <registry>/az-classifier:v1
docker push <registry>/az-classifier:v1

# Deploy
helm install az-classifier helm/az-classifier/

# Add to /etc/hosts
# 127.0.0.1 az-classifier.local prometheus.local grafana.local

# Deploy monitoring
kubectl apply -f k8s/monitoring/

# Test
curl http://az-classifier.local/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Neft qiymətləri dünya bazarında artıb"}'
```

### Frontend

```bash
cd frontend
npm install
npm start
```

Opens at http://localhost:3000.

## API endpoints

- `POST /predict` — classify text. Returns category, confidence, full probability distribution, and inference latency.
- `GET /health` — returns 200 if model loaded, 503 otherwise. Used by Kubernetes liveness/readiness probes.
- `GET /metrics` — Prometheus format metrics (predictions_total, latency histogram, confidence histogram).
- `GET /api/stats` — prediction counts by category (JSON, frontend).
- `GET /api/model-info` — model metadata (JSON, frontend).

## Limitations

This is a portfolio project, not production infrastructure. Things missing for real production use, in rough order of priority:

- **Retraining pipeline** — model is static. A real deployment needs scheduled retraining (Airflow / Prefect) gated on validation metrics.
- **Real drift detection** — confidence histograms are a proxy. Production needs distribution comparison (PSI, KL-divergence) against a stored reference set, e.g. Evidently AI.
- **INT8 quantization** — current ONNX export uses FP16, which doesn't help much on x86 CPU. Dynamic INT8 quantization would give a real latency win.
- **Multi-node cluster** — single-node k3s means no HA. Restart = downtime.
- **Experiment tracking** — MLflow is set up but not integrated into a real training workflow.

## License

MIT
