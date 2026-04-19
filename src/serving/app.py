from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import onnxruntime as ort
import numpy as np
from transformers import AutoTokenizer
import json
import time
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

app = FastAPI(title="Azerbaijan News Classifier")

# loading the ONNX model and tokenizer at startup for efficient inference

tokenizer =  AutoTokenizer.from_pretrained("models/final_model")
session = ort.InferenceSession("models/final_model/model.onnx")
with open("models/final_model/label_mapping.json") as f:
    label_mapping = json.load(f)
    
    
# Define request and response models
class PredictionRequest(BaseModel):
    text: str

class PredictionResponse(BaseModel):
    category: str
    confidence: float
    probabilities: dict
    latency_ms: float
    
@app.get("/health")
def health_check():
    if session is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"status": "healthy", "model": "loaded"}

# Prometheus metrics
PREDICTIONS_TOTAL = Counter(
    'predictions_total', 
    'Total predictions by category', 
    ['category']
)
PREDICTION_LATENCY = Histogram(
    'prediction_latency_seconds', 
    'Prediction latency in seconds',
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5] 
)
PREDICTION_CONFIDENCE = Histogram(
    'prediction_confidence', 
    'Prediction confidence scores',
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]
)

@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Endpoint for making predictions
@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")
    
    
    start_time = time.time()
    
    # Tokenize input text
    
    inputs = tokenizer(request.text, return_tensors="np", padding=True, truncation=True, max_length=256)
    
    # Run inference
    outputs = session.run(None, {
        "input_ids": inputs["input_ids"],
        "attention_mask": inputs["attention_mask"]
    })
    
    # Process output
    logits = outputs[0][0] 
    # Converting logits to probabilities and find predicted class(softmax)
    probabilities = np.exp(logits) / np.sum(np.exp(logits))
    pred_class = np.argmax(probabilities) # output with the highest probability
    confidence = probabilities[pred_class]
    
    latency_ms = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    PREDICTIONS_TOTAL.labels(category=label_mapping[str(pred_class)]).inc() # Increment the counter for the predicted category
    PREDICTION_LATENCY.observe(latency_ms / 1000)  # convert ms to seconds
    PREDICTION_CONFIDENCE.observe(float(probabilities[pred_class])) # Observe the confidence score for the predicted class
    
    return PredictionResponse(
        category=label_mapping[str(pred_class)],
        confidence=float(confidence),
        probabilities={label_mapping[str(i)]: float(j) for i, j in enumerate(probabilities)},
        latency_ms=round(latency_ms, 2)
    )
    
    