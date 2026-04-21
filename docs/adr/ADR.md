Architecture and Design Decisions


Notes on key decisions made throughout the project — what I chose, what I considered, and why.

Data Collection

As far as I searched, there is no labeled dataset for Azerbaijani news classification. I needed to build one from scratch.

I went with scraping news websites because editors already categorize articles into sections (İdman, Siyasət, etc.), so I get labels for free without manual annotation.

I considered generating synthetic articles with an LLM, but thats circular, if I train on GPT-generated text and test on GPT-generated text, I have proven nothing about real-world performance. Synthetic augmentation on top of real data is fine, synthetic as the primary source is not.

Built scrapers for three sites: report.az, sonxeber.az, qafqazinfo.az. Each site has different HTML structure, different pagination, different quirks. I wrote an abstract base class with the common logic (retry, checkpointing, saving) and site-specific child classes that only handle DOM parsing. Adding a fourth source would mean writing one file with CSS selectors, not touching anything else.

Some issues I faced:

report.az had infinite scroll - each "page" loaded all previous articles too, so page 50 returned 800 URLs with 784 already saved. Scraper ran forever. Fixed with a threshold: if less than 10% of articles on a page are new, stop.
Encoding broke Azerbaijani characters — requests guessed Latin-1 encoding instead of UTF-8, turning "ə" into "Ã¤". One-line fix: response.encoding = 'utf-8'.
qafqazinfo had two <h1> tags - one for the site logo, one for the article title. soup.find("h1") grabbed the logo (empty text). 4,854 articles had blank titles, and dedup treated them all as the same article. Lost almost half the dataset before I caught it.

Checkpointing was important - scraper saves each article as a JSON file, and checks if the file exists before re-downloading. If the script crashes at article 500, restart picks up at 501. Sounds obvious, but I have seen production pipelines that dont do this.

Train/Test Split

This one caused me some headaches. Two of three sources had publication dates. qafqazinfo didnt - the scraper missed the date field, and when I tried to re-scrape, the site kept timing out.
Random split on news data is a bad idea. "Bakının yollarında tıxac yaranıb" (traffic jam in Baku) gets published almost every day with the same headline. Random split puts mondays version in train and tuesdays in test — model "remembers" instead of "generalizes." Thats data leakage.

So I did a hybrid: temporal split for articles with dates (sort by date, oldest 70% train, next 15% val, newest 15% test), and stratified random split for the undated ones. Not ideal — the undated portion might still have leakage - but better than dropping 4,000 articles or making up fake dates.
I considered synthesizing dates from qafqazinfo's URL IDs (auto-increment numbers that roughly correlate with time), but there's no way to validate the mapping. Felt dishonest.

Model
Went with XLM-RoBERTa-base (280M parameters). Its pretrained on CommonCrawl data from 100 languages, including Azerbaijani, so it already understands the language. Im not teaching it Azerbaijani - I'm teaching it my classification task.
Why not an LLM (GPT-4, Claude)? For classification its not necessary. XLM-R gives me 20ms inference. GPT-3.5 through API is 500ms-2s, costs money per request, and creates vendor dependency. Fine-tuned encoder models match or beat LLMs on domain-specific classification, and they run on my own hardware.
Why not mBERT? Its pretrained on Wikipedia, and Azerbaijani Wikipedia is small (about 200K articles). XLM-R uses CommonCrawl which has significantly more Azerbaijani text. The XLM-R paper shows it outperforms mBERT on low-resource languages.

Why not train a language model from scratch? With 10K articles I would get garbage. Pretraining needs millions of texts. Transfer learning exists for exactly this situation.

Token Length (256)
XLM-R supports up to 512 tokens. I set max_length to 256. Here is why:
250 words is 500-750 tokens. Most articles get truncated regardless.
But news articles put the important stuff first (inverted pyramid). "Azərbaycan millisi UEFA turnirində..." - you know its sports from the first three words. Truncating at 256 tokens means the model sees about 100-130 words, which is the headline and first couple of paragraphs. That's where the category signal lives.
93% F1 on test set with 256 tokens tells me Im not losing much. Going to 512 would double memory usage and inference time for maybe 0.5% accuracy gain. Not worth it.

ONNX Export

I export the trained model to ONNX format and serve it with ONNX Runtime instead of PyTorch.
Main reason: Docker image drops from 5 GB to 2 GB. PyTorch is a massive dependency designed for training with GPU support. I dont need any of that for inference. ONNX Runtime also does graph optimization automatically (fusing operations, folding constants) which gives 20-30% speed improvement for free.
Had a bug here - PyTorch 2.x's new dynamo-based ONNX exporter silently produced a model without weights. 1.7 MB file instead of 1 GB. The model loaded fine, ran fine, and confidently predicted "sosial" for everything. Took me a while to notice. Switched to HuggingFaces optimum library which uses the older, stable exporter.

Serving

FastAPI with ONNX Runtime. Model loads once at startup (module-level), not per-request - loading a 1 GB model on every request would give multi-second latency.

I keep the serving dependencies separate from training dependencies (serving-requirements.txt vs requirements.txt). Serving doesnt need torch, pandas, scikit-learn, matplotlib. This isn't just about image size — fewer dependencies means fewer security vulnerabilities to track, faster pip install, smaller attack surface.

The /health endpoint checks if the ONNX session is loaded and returns 503 if not. Kubernetes uses this for liveness and readiness probes - it wont send traffic to a Pod that has not loaded the model yet.

Softmax is computed manually (exp(logits) / sum(exp(logits))) rather than importing torch just for F.softmax. One less dependency.

Kubernetes, Helm

Using k3s - a real Kubernetes distribution (certified by CNCF), not a simulator like minikube. Helm charts, manifests, and kubectl commands all work identically on EKS or GKE.
Everything is in a Helm chart with parametrized values.yaml. Replicas, image tag, resource limits, ingress host — all configurable without editing templates. helm upgrade deploys, helm rollback reverts.
One gotcha: HPA (Horizontal Pod Autoscaler) and Helm both want to control replica count. When HPA scales to 3 replicas and then helm upgrade tries to set replicas: 2, Kubernetes throws an ownership conflict. Fixed by making replicas conditional in the Deployment template - if HPA is enabled, Deployment doesn't set replicas at all.
Liveness and readiness probes both hit /health but serve different purposes. Liveness: "is the process alive?" (if no, kill and restart). Readiness: "can it handle traffic?" (if no, stop routing to it, but dont kill). Readiness has a shorter initial delay (10s vs 30s) because I want traffic to flow as soon as the model loads, but I dont want to kill the Pod for being slow to start.
Memory limits: started at 2 GB, Pods kept dying. kubectl get pod -o jsonpath showed OOMKilled. ONNX Runtime does graph optimization at load time, which temporarily doubles memory usage (~1 GB model + ~1 GB optimization workspace). Bumped to 4 GB.
Traefik is the Ingress controller (built into k3s). In a larger deployment I would probably switch to Nginx Ingress for the bigger community and more documentation, or Istio if I needed service mesh features. For a single service, Traefik is fine.

Monitoring

Two types of metrics, because ML services can fail in ways that normal monitoring doesnt catch.

Infrastructure metrics:

Request latency as a histogram with buckets. Not average - average hides outliers. Histogram lets Prometheus compute p50, p95, p99. I care about p95 more than average because thats what real users experience.

ML-specific metrics:

Prediction count by category. If the distribution shifts suddenly (yesterday 30% sports, today 90% sports), something changed - either the users or the model.
Prediction confidence distribution. If the model is normally 95%+ confident and suddenly starts giving 50-60% predictions, its seeing inputs unlike its training data. This is a cheap proxy for data drift detection - not as rigorous as statistical tests (PSI, KS-test) on feature distributions, but requires zero additional infrastructure.

Prometheus scrapes the /metrics endpoint every 15 seconds. It discovers Pods automatically through the Kubernetes API - I configured service discovery with RBAC (ServiceAccount + ClusterRole with read-only permissions on pods/services/endpoints). When HPA adds a Pod, Prometheus picks it up without config changes.
Grafana connects to Prometheus for visualization. Password stored as a Kubernetes Secret, not plaintext in YAML - small thing, but its what youd do in production.
One limitation: counters live in Pod memory and reset on restart. Prometheus stores scraped values in its own database, so historical data survives, but theres a brief gap after Pod restart where counters show zero. Prometheus handles this with rate() and increase() functions that account for counter resets.

Frontend
Minimal React + TypeScript dashboard. Three sections: inference playground (type text, get classification), prediction stats (counts from API), model info (static metadata).
Frontend talks to the same FastAPI service through two additional endpoints (/api/stats, /api/model-info) that return JSON. The /metrics endpoint exists for Prometheus (text format), not for the UI.
CORS middleware added because browser blocks cross-origin requests by default. Frontend on localhost:3000 calling API on az-classifier.local would fail without the Access-Control-Allow-Origin header. In production, I would restrict the allowed origin to the dashboard's domain instead of wildcard *.
TypeScript over JavaScript because type safety catches bugs at compile time. For a small dashboard it doesn't matter much, but it's what you'd use in any serious project.

Things I would Do Differently / Next Steps

CI/CD with GitHub Actions - right now I build and push Docker images manually. Should be automated on merge to main.
Alerting - Grafana dashboards exist but nobody watches them 24/7. Need Prometheus AlertManager to send Slack notifications when confidence drops or latency spikes.
Automated retraining - Airflow DAG that periodically scrapes new articles, retrains, compares metrics with current model, deploys if better.
Canary deployments - Argo Rollouts to send 10% traffic to new model version, compare metrics, auto-rollback if worse.
Proper drift detection - statistical tests (PSI, KS-test) on input feature distributions, not just confidence monitoring.
Multi-label classification - some articles genuinely belong to two categories ("dünya bazarında neft qiymətləri" is both dunya and iqtisadiyyat). Current model forces a single label.