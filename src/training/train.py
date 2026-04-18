from config import TrainingConfig
from data_prep import prepare_data
from transformers import AutoModelForSequenceClassification, Trainer, TrainingArguments
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import json

# To compute evaluation metrics by epoch during training
def compute_metrics(pred):
    logits, labels = pred
    predictions = np.argmax(logits, axis=-1) # Get the index of the highest logit for each prediction
    acc = accuracy_score(labels, predictions)
    # Using weighted average to penalize more imbalanced classes
    precision = precision_score(labels, predictions, average='weighted')
    recall = recall_score(labels, predictions, average='weighted')
    f1 = f1_score(labels, predictions, average='weighted')
    return {
        'accuracy': acc,
        'precision': precision,
        'recall': recall,
        'f1': f1
    }
    
def main():
    config = TrainingConfig()
    
    train_dataset, val_dataset, label_names = prepare_data(config)
    
    model = AutoModelForSequenceClassification.from_pretrained(config.model_name, num_labels=len(label_names))
    
    training_args = TrainingArguments(
        output_dir=config.output_dir,
        num_train_epochs=config.num_epochs,
        per_device_train_batch_size=config.batch_size,
        per_device_eval_batch_size=config.batch_size,
        eval_strategy="epoch",
        save_strategy="epoch",
        # F1 score to determine the best model
        # instead of last epoch to avoid overfitting
        learning_rate=config.learning_rate,
        # To prevent overfitting by adding L2 regularization
        weight_decay=config.weight_decay,
        fp16=True, # Use mixed precision for faster training on GPU
        load_best_model_at_end=True,
        # F1 score to determine the best model instead of last epoch to avoid overfitting
        metric_for_best_model="f1",
        logging_steps=100,
        report_to="none"
        
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics
    )
    
    print("Starting training...")
    trainer.train()
    trainer.save_model(f"{config.output_dir}/final_best_model")
    
    # Save label mapping for inference
    label_mapping = {i: label for i, label in enumerate(label_names)}
    with open(f"{config.output_dir}/final_best_model/label_mapping.json", "w") as f:
        json.dump(label_mapping, f)
    
    print(f"Label mapping: {label_mapping}")
    print("Training completed!")

if __name__ == "__main__":
    main()