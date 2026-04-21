# az-news-classifier

End-to-end ML platform for classifying Azerbaijani news articles into 5 categories. This is a full pipeline from data collection to Kubernetes deployment with monitoring.

Azerbaijani is a low-resource language with no existing labeled datasets for text classification. I built everything from scratch: scraped nearly 11500 articles from three news sites, cleaned and deduplicated down to 10000, fine-tuned XLM-RoBERTa, exported to ONNX, containerized, deployed on k3s with Helm, and set up Prometheus + Grafana monitoring with custom ML metrics.
What it does
You give it a news article in Azerbaijani, it tells you the category:

siyasət (politics)
iqtisadiyyat (economy)
idman (sports)
dünya (world news)
sosial (social/society)

93% F1 score on held-out test set. 20ms inference latency.

## Architecture

Scraping Pipeline (3 sites):

Cleaning and Dedup
Temporal Train/Val/Test Split
XLM-RoBERTa Fine-tuning
ONNX Export
FastAPI Serving (ONNX Runtime)
Docker Container
k3s Kubernetes (Helm)
Prometheus + Grafana Monitoring
React Dashboard
    
### Tech stack

ML: XLM-RoBERTa-base, HuggingFace Transformers, ONNX Runtime, scikit-learn
Serving: FastAPI, Uvicorn, prometheus-client

Infrastructure: Docker, k3s (Kubernetes), Helm, Traefik Ingress, HPA

Monitoring: Prometheus, Grafana, custom ML metrics (confidence distribution, prediction counts by category, latency histograms)

Frontend: React, TypeScript, Axios

Data: BeautifulSoup, requests, pandas

idman (sports) performs best, because the sports vocabulary is highly distinctive. siyaset and sosial overlap the most, which makes sense, political and social news share a lot of language. dunya and iqtisadiyyat sometimes get confused because world news is often about economics.

### Data pipeline

No existing dataset, so I built one:

Scraping: abstract base scraper class with site-specific implementations for report.az, sonxeber.az, qafqazinfo.az. Checkpointing (don't re-download), retry with exponential backoff, random delay between requests.
Cleaning: category name normalization across sites (siyasi-xeberler = siyaset-xeberleri = siyaset-2 → siyaset), remove articles under 50 words, title-based deduplication for cross-site duplicates.
Split: temporal for articles with dates, stratified random for undated articles. Not random — news data has leakage through recurring stories and same-day paraphrases.

Raw: 11,589 articles → Cleaned: 10,148 → Train: 7,102 / Val: 1,522 / Test: 1,524

Running locally

### Prerequisites

Python 3.11+
Docker
k3s (for Kubernetes deployment)
Helm 3
Node.js 18+ (for frontend)

### Training
bashpython -m venv venv
source venv/bin/activate
pip install -r requirements.txt

### Scrape data (takes hours)
python main.py

### Clean and split
python src/cleaning/cleaner.py
python src/cleaning/splitter.py

### Train
cd src/training
python train.py

### Export to ONNX
python export_onnx.py
Serving (Docker)
bashdocker build -f docker/serving.Dockerfile -t az-classifier:v1 .
docker run -p 8000:8000 az-classifier:v1

### Test
curl http://localhost:8000/health
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Qarabağ FK Çempionlar Liqasında qalib gəldi"}'
Kubernetes (k3s + Helm)
bash# Push image
docker tag az-classifier:v1 <your-dockerhub>/az-classifier:v1
docker push <your-dockerhub>/az-classifier:v1

### Deploy
helm install az-classifier helm/az-classifier/

### Add to /etc/hosts
# 127.0.0.1 az-classifier.local prometheus.local grafana.local

### Deploy monitoring
kubectl apply -f k8s/monitoring/

### Test
curl http://az-classifier.local/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Neft qiymətləri dünya bazarında artıb"}'
Frontend
bashcd frontend
npm install
npm start

### Opens at http://localhost:3000

API endpoints
POST /predict — classify text, returns category + confidence + probabilities + latency
GET /health — returns 200 if model loaded, 503 if not. Used by k8s probes.
GET /metrics — Prometheus format metrics (predictions_total, latency histogram, confidence histogram)
GET /api/stats — prediction counts by category (JSON, for frontend)
GET /api/model-info — model metadata (JSON, for frontend)
