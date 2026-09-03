import json
import os
import sys
import time
import logging
import tracemalloc
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification, get_linear_schedule_with_warmup
from pathlib import Path
from typing import Dict, Any, List, Optional
import psutil

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_config, set_seed, get_path, get_device
from utils.logger import get_logger, log_script_start, log_script_end, get_memory_usage_mb

# Constants
MAX_MEMORY_MB = 7000  # 7 GB limit
BATCH_SIZE = 16
MAX_EPOCHS = 5
LEARNING_RATE = 5e-5
MAX_SEQ_LENGTH = 128
MODEL_OUTPUT_DIR = "models/proxy_hard"
LOG_OUTPUT_DIR = "logs"

class UnifiedDataset(Dataset):
    """Dataset class for loading the transformed unified dataset."""
    def __init__(self, data_path: str, tokenizer, max_length: int = MAX_SEQ_LENGTH):
        self.data_path = data_path
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.samples = []
        self._load_data()

    def _load_data(self):
        """Load samples from JSONL file."""
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Data file not found: {self.data_path}")
        
        with open(self.data_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    self.samples.append(json.loads(line))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample = self.samples[idx]
        # Construct input text from available fields
        text = sample.get('text_description', '')
        label = sample.get('label')  # "constraint_violated" or "constraint_satisfied"
        
        # Map labels to integers
        label_map = {"constraint_violated": 1, "constraint_satisfied": 0}
        if label not in label_map:
            raise ValueError(f"Invalid label: {label}")
        
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].squeeze(0),
            'attention_mask': encoding['attention_mask'].squeeze(0),
            'labels': torch.tensor(label_map[label], dtype=torch.long)
        }

def check_data_integrity(data_path: str) -> bool:
    """Verify the data file exists and contains valid entries."""
    if not os.path.exists(data_path):
        return False
    
    valid_count = 0
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    if 'text_description' in data and 'label' in data:
                        valid_count += 1
                except json.JSONDecodeError:
                    return False
    
    return valid_count > 0

def monitor_memory(logger: logging.Logger) -> bool:
    """
    Check current memory usage. Returns True if within limits, False if exceeded.
    Logs the current usage.
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    current_mb = mem_info.rss / (1024 * 1024)
    
    logger.info(f"Current memory usage: {current_mb:.2f} MB")
    
    if current_mb > MAX_MEMORY_MB:
        logger.error(f"Memory limit exceeded: {current_mb:.2f} MB > {MAX_MEMORY_MB} MB")
        return False
    
    return True

def train_model(
    train_loader: DataLoader,
    val_loader: DataLoader,
    model: DistilBertForSequenceClassification,
    tokenizer,
    device: torch.device,
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Train the DistilBERT model with memory monitoring.
    Returns training history and final metrics.
    """
    model.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE)
    num_training_steps = len(train_loader) * MAX_EPOCHS
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=0.1 * num_training_steps,
        num_training_steps=num_training_steps
    )

    best_val_acc = 0.0
    training_history = {
        'train_loss': [],
        'val_loss': [],
        'val_acc': []
    }

    logger.info("Starting training loop...")

    for epoch in range(MAX_EPOCHS):
        # --- Training Phase ---
        model.train()
        total_train_loss = 0
        start_time = time.time()

        for batch in train_loader:
            if not monitor_memory(logger):
                raise MemoryError("Memory limit exceeded during training.")

            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)

            optimizer.zero_grad()
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )
            loss = outputs.loss
            loss.backward()

            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()

            total_train_loss += loss.item()

        avg_train_loss = total_train_loss / len(train_loader)
        training_history['train_loss'].append(avg_train_loss)
        epoch_time = time.time() - start_time
        logger.info(f"Epoch {epoch+1}/{MAX_EPOCHS} - Train Loss: {avg_train_loss:.4f} - Time: {epoch_time:.2f}s")

        # --- Validation Phase ---
        model.eval()
        total_val_loss = 0
        correct = 0
        total = 0

        with torch.no_grad():
            for batch in val_loader:
                if not monitor_memory(logger):
                    raise MemoryError("Memory limit exceeded during validation.")

                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                labels = batch['labels'].to(device)

                outputs = model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )
                total_val_loss += outputs.loss.item()

                predictions = outputs.logits.argmax(dim=1)
                total += labels.size(0)
                correct += (predictions == labels).sum().item()

        avg_val_loss = total_val_loss / len(val_loader)
        val_acc = correct / total
        training_history['val_loss'].append(avg_val_loss)
        training_history['val_acc'].append(val_acc)

        logger.info(f"Epoch {epoch+1} - Val Loss: {avg_val_loss:.4f} - Val Acc: {val_acc:.4f}")

        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            logger.info(f"New best model found with accuracy: {best_val_acc:.4f}")
            model.save_pretrained(get_path(MODEL_OUTPUT_DIR))
            tokenizer.save_pretrained(get_path(MODEL_OUTPUT_DIR))

    return {
        'history': training_history,
        'best_val_acc': best_val_acc,
        'final_val_acc': val_acc
    }

def main():
    """Main entry point for the training script."""
    # Setup logging
    log_path = get_path(LOG_OUTPUT_DIR)
    os.makedirs(log_path, exist_ok=True)
    log_file = os.path.join(log_path, "memory_profile.log")
    
    # Start tracing for memory profiling
    tracemalloc.start()
    
    logger = get_logger("train", log_file)
    log_script_start(logger)
    
    # Configuration
    config = get_config()
    set_seed(config['seed'])
    device = get_device()
    logger.info(f"Using device: {device}")
    
    # Paths
    data_path = get_path("data/processed/unified_dataset.jsonl")
    model_dir = get_path(MODEL_OUTPUT_DIR)
    os.makedirs(model_dir, exist_ok=True)
    
    # Check data integrity
    if not check_data_integrity(data_path):
        logger.error("Data integrity check failed. Exiting.")
        log_script_end(logger, success=False)
        sys.exit(1)
    
    logger.info(f"Loading data from {data_path}")
    
    # Initialize Tokenizer
    try:
        tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")
    except Exception as e:
        logger.error(f"Failed to load tokenizer: {e}")
        log_script_end(logger, success=False)
        sys.exit(1)
    
    # Create Datasets
    try:
        full_dataset = UnifiedDataset(data_path, tokenizer)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        log_script_end(logger, success=False)
        sys.exit(1)
    
    # Split into train/val (80/20)
    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(
        full_dataset, [train_size, val_size], generator=torch.Generator().manual_seed(config['seed'])
    )
    
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)
    
    logger.info(f"Train size: {len(train_dataset)}, Val size: {len(val_dataset)}")
    
    # Initialize Model
    try:
        model = DistilBertForSequenceClassification.from_pretrained(
            "distilbert-base-uncased",
            num_labels=2
        )
    except Exception as e:
        logger.error(f"Failed to initialize model: {e}")
        log_script_end(logger, success=False)
        sys.exit(1)
    
    # Train
    try:
        results = train_model(train_loader, val_loader, model, tokenizer, device, logger)
    except MemoryError as e:
        logger.error(f"Training failed due to memory constraints: {e}")
        log_script_end(logger, success=False)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Training failed: {e}")
        log_script_end(logger, success=False)
        sys.exit(1)
    
    # Final Memory Check
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    logger.info(f"Peak memory usage: {peak / 1024 / 1024:.2f} MB")
    
    if peak / 1024 / 1024 > MAX_MEMORY_MB:
        logger.warning(f"Peak memory ({peak / 1024 / 1024:.2f} MB) exceeded limit ({MAX_MEMORY_MB} MB).")
    else:
        logger.info(f"Peak memory usage ({peak / 1024 / 1024:.2f} MB) is within limits.")
    
    # Save final results summary
    results_path = os.path.join(log_path, "training_summary.json")
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Training complete. Best validation accuracy: {results['best_val_acc']:.4f}")
    logger.info(f"Model saved to {model_dir}")
    log_script_end(logger, success=True)

if __name__ == "__main__":
    main()