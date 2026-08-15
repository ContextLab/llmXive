import json
import os
import sys
import time
import logging
import tracemalloc
from pathlib import Path
from typing import Dict, Any, Optional, List

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification, get_linear_schedule_with_warmup
from datasets import load_dataset

from config import get_config, set_seed, get_path, get_device
from utils.logger import (
    get_logger,
    log_script_start,
    log_script_end,
    get_memory_usage_mb,
    log_memory_usage,
    track_execution_time
)

# --- Configuration & Constants ---
MAX_MEMORY_GB = 7.0
MAX_TRAINING_HOURS = 6.0
MODEL_OUTPUT_PATH = "models/proxy_hard/model.pt"
LOG_OUTPUT_PATH = "logs/memory_profile.log"
TRAINING_PROGRESS_LOG = "logs/training_progress.log"

# --- Dataset Class ---
class UnifiedDataset(Dataset):
    def __init__(self, data_path: str, tokenizer, max_length: int = 128):
        self.data = []
        self.tokenizer = tokenizer
        self.max_length = max_length
        logger = get_logger(__name__)
        logger.info(f"Loading dataset from {data_path}...")

        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                self.data.append(json.loads(line))

        logger.info(f"Loaded {len(self.data)} samples.")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        text = item.get('text_description', '')
        label = 1 if item.get('label') == 'constraint_violated' else 0

        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )

        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }

# --- Data Integrity Check ---
def check_data_integrity(data_path: str) -> bool:
    logger = get_logger(__name__)
    if not os.path.exists(data_path):
        logger.error(f"Data file not found: {data_path}")
        return False

    try:
        with open(data_path, 'r') as f:
            first_line = f.readline()
            if not first_line:
                logger.error("Data file is empty.")
                return False
            json.loads(first_line)
        return True
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in data file: {e}")
        return False

# --- Memory Monitor ---
def monitor_memory(threshold_gb: float = MAX_MEMORY_GB):
    current_mb = get_memory_usage_mb()
    current_gb = current_mb / 1024.0
    logger = get_logger(__name__)
    
    if current_gb > threshold_gb:
        logger.critical(f"Memory usage {current_gb:.2f} GB exceeds threshold {threshold_gb} GB. Aborting.")
        raise MemoryError(f"Memory limit exceeded: {current_gb:.2f} GB > {threshold_gb} GB")
    
    return current_gb

# --- Training Logic with Enhanced Logging ---
def train_model(
    train_loader: DataLoader,
    model: nn.Module,
    device: torch.device,
    epochs: int = 3,
    learning_rate: float = 5e-5,
    weight_decay: float = 0.01
):
    logger = get_logger(__name__)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
    num_training_steps = len(train_loader) * epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=0,
        num_training_steps=num_training_steps
    )

    model.train()
    total_loss = 0.0
    start_time = time.time()
    tracemalloc.start()

    logger.info(f"Starting training on {device} for {epochs} epochs...")
    logger.info(f"Total training steps: {num_training_steps}")

    # Initialize progress logging
    progress_log_path = get_path(TRAINING_PROGRESS_LOG)
    os.makedirs(os.path.dirname(progress_log_path), exist_ok=True)
    progress_file = open(progress_log_path, 'w')
    progress_file.write("Epoch,Batch,Step,Current_Loss,Running_Avg_Loss,Memory_MB,Time_Elapsed\n")
    progress_file.flush()

    for epoch in range(1, epochs + 1):
        epoch_loss = 0.0
        step_count = 0

        for batch_idx, batch in enumerate(train_loader):
            # Check memory periodically
            if batch_idx % 10 == 0:
                current_mem = monitor_memory(MAX_MEMORY_GB)
                log_memory_usage(f"Epoch {epoch}, Batch {batch_idx}: {current_mem:.2f} GB")

            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)

            model.zero_grad()

            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )
            loss = outputs.loss

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            scheduler.step()

            current_loss = loss.item()
            epoch_loss += current_loss
            step_count += 1
            total_loss += current_loss

            # Log progress every 10 steps
            if step_count % 10 == 0:
                elapsed = time.time() - start_time
                current_mem = get_memory_usage_mb()
                running_avg = epoch_loss / step_count
                
                log_msg = (
                    f"Epoch {epoch}/{epochs}, Step {step_count}/{len(train_loader)}, "
                    f"Loss: {current_loss:.4f}, Avg Loss: {running_avg:.4f}, "
                    f"Memory: {current_mem/1024:.2f} GB, Time: {elapsed:.1f}s"
                )
                logger.info(log_msg)
                
                # Write to progress file
                progress_file.write(f"{epoch},{batch_idx},{step_count},{current_loss:.4f},{running_avg:.4f},{current_mem},{elapsed:.1f}\n")
                progress_file.flush()

            # Safety check for time limit
            if elapsed > (MAX_TRAINING_HOURS * 3600):
                logger.warning(f"Training time limit ({MAX_TRAINING_HOURS}h) reached. Stopping early.")
                break

        avg_epoch_loss = epoch_loss / len(train_loader)
        logger.info(f"Epoch {epoch} completed. Average Loss: {avg_epoch_loss:.4f}")

    # Final memory check
    current_mem = get_memory_usage_mb()
    log_memory_usage(f"Training finished. Final Memory: {current_mem/1024:.2f} GB")
    
    # Log convergence info
    final_avg_loss = total_loss / num_training_steps
    logger.info(f"Training converged. Final Average Loss: {final_avg_loss:.4f}")
    
    progress_file.write(f"FINAL,Avg_Loss:{final_avg_loss:.4f},Final_Mem:{current_mem}\n")
    progress_file.close()

    tracemalloc.stop()
    return model

# --- Main Entry Point ---
def main():
    config = get_config()
    set_seed(config.seed)
    device = get_device()
    logger = log_script_start("train.py")

    try:
        # Paths
        data_path = get_path("data/processed/unified_dataset.jsonl")
        model_output_dir = get_path("models/proxy_hard")
        os.makedirs(model_output_dir, exist_ok=True)

        # 1. Data Integrity Check
        if not check_data_integrity(data_path):
            raise FileNotFoundError(f"Data integrity check failed for {data_path}")

        # 2. Initialize Tokenizer and Model
        logger.info("Initializing DistilBERT model...")
        tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')
        model = DistilBertForSequenceClassification.from_pretrained(
            'distilbert-base-uncased',
            num_labels=2
        )
        model.to(device)

        # 3. Prepare Dataset and Loader
        logger.info("Creating data loaders...")
        train_dataset = UnifiedDataset(data_path, tokenizer)
        train_loader = DataLoader(
            train_dataset,
            batch_size=config.batch_size,
            shuffle=True,
            num_workers=0  # Set to 0 to avoid multiprocessing issues in some environments
        )

        # 4. Train Model
        logger.info("Starting training loop...")
        train_model(
            train_loader,
            model,
            device,
            epochs=config.epochs,
            learning_rate=config.learning_rate
        )

        # 5. Save Model
        model_path = os.path.join(model_output_dir, "model.pt")
        logger.info(f"Saving model to {model_path}...")
        torch.save({
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': None, # Not saving optimizer state for inference
            'epoch': config.epochs,
            'loss': 0.0 # Placeholder, actual final loss is in logs
        }, model_path)
        logger.info("Model saved successfully.")

        log_script_end("train.py", status="SUCCESS")

    except Exception as e:
        logger.error(f"Training failed with error: {e}", exc_info=True)
        log_script_end("train.py", status="FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()