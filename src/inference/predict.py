import json
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch.nn.functional as F
import os

class NewsPredictor:
    # initialize the predictor by loading the model and tokenizer
    def __init__(self, model_path):
        print(f"Loading model from {model_path}...")
        self.tokenizer = AutoTokenizer.from_pretrained("xlm-roberta-base")
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.model.to("cuda" if torch.cuda.is_available() else "cpu")
        self.model.eval()
        
        # Load label mapping to convert predicted class index back to category name
        with open(f"{model_path}/label_mapping.json") as f:
            self.labels = json.load(f)
        self.labels = {int(k): v for k, v in self.labels.items()}
        

    def predict(self, text):
        inputs = self.tokenizer(
            text, 
            return_tensors="pt", 
            truncation=True, 
            max_length=256, 
            padding="max_length"
        ).to(self.model.device)
        
        # Make predictions without computing gradients
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # Apply softmax to get probabilities to find the predicted class
        probs = F.softmax(outputs.logits, dim=-1)
        confidence, pred_class = torch.max(probs, dim=-1)
        
        return self.labels[pred_class.item()], confidence.item()

if __name__ == "__main__":
    
    MODEL_PATH = "models/checkpoints/checkpoint-1332" 
    
    if not os.path.exists(MODEL_PATH):
        print("Model checkpoint not found. Please run the training script first to generate the model.")
    else:
        predictor = NewsPredictor(MODEL_PATH)
        
        print("Azerbaijan News Classifier")
        user_text = input("Please enter the news text for classification: ")
        
        if user_text:
            category, conf = predictor.predict(user_text)
            print(f"\n[Result]")
            print(f"Category: {category.upper()}")
            print(f"Confidence: {conf:.2%}")