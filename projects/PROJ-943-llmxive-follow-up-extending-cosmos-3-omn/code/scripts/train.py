import json
import os
import sys
import time
import logging
import tracemalloc
import psutil
from pathlib import Path
from typing import Dict, Any, List, Optional
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification, get_linear_schedule_with_warmup
from datasets import load_dataset
import numpy as np
import random

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_config, set_seed, get_path, get_device
from utils.logger import get_logger, log_script_start, log_script_end, get_memory_usage_mb

# --- Configuration ---
CONFIG = get_config()
MODEL_NAME = "distilbert-base-uncased"
MAX_LENGTH = 128
BATCH_SIZE = 16
NUM_EPOCHS = 3
LEARNING_RATE = 5e-5
WARMUP_STEPS = 500

# --- Custom Dataset ---
class UnifiedDataset(Dataset):
    def __init__(self, data_path: str, tokenizer, max_length: int = MAX_LENGTH):
        self.data_path = Path(data_path)
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.samples = []
        self._load_data()

    def _load_data(self):
        """Load JSONL data into memory (assuming processed dataset fits in RAM)."""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {self.data_path}")
        
        with open(self.data_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    self.samples.append(json.loads(line))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample = self.samples[idx]
        # Assuming 'text_description' is the input text and 'label' is the target
        # Adjust keys based on actual schema from T010
        text = sample.get('text_description', "")
        label = sample.get('label', 0) # 0 or 1 based on T010 logic

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
            'labels': torch.tensor(label, dtype=torch.long)
        }

# --- Memory Monitoring ---
def monitor_memory(log_file: Path):
    """Log current memory usage to the specified file."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    mem_mb = mem_info.rss / (1024 * 1024)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Current Memory Usage: {mem_mb:.2f} MB")
    
    with open(log_file, 'a') as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}, {mem_mb:.2f} MB\n")

    if mem_mb > 7000: # 7GB threshold
        raise MemoryError(f"Memory usage exceeded 7GB limit: {mem_mb:.2f} MB")

# --- Training Logic ---
def check_data_integrity(data_path: Path) -> bool:
    """Verify the dataset file exists and is not empty."""
    if not data_path.exists():
        return False
    if data_path.stat().st_size == 0:
        return False
    return True

def train_model(
    train_data_path: Path,
    model_output_dir: Path,
    log_dir: Path,
    num_epochs: int = NUM_EPOCHS,
    batch_size: int = BATCH_SIZE,
    lr: float = LEARNING_RATE
):
    """
    Train a DistilBERT proxy model on the unified dataset.
    Logs training progress, loss convergence, and resource usage.
    """
    # Setup paths
    model_output_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    memory_log_path = log_dir / "memory_profile.log"
    training_log_path = log_dir / "training_progress.log"

    # Initialize logging
    logger = get_logger("train_script", log_file=str(training_log_path))
    log_script_start(logger, "T013", "Training Proxy Model")

    # Check data
    if not check_data_integrity(train_data_path):
        raise FileNotFoundError(f"Training data not found or empty at {train_data_path}")

    # Load Tokenizer and Model
    logger.info(f"Loading tokenizer: {MODEL_NAME}")
    tokenizer = DistilBertTokenizer.from_pretrained(MODEL_NAME)
    
    logger.info(f"Loading model: {MODEL_NAME}")
    model = DistilBertForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2)
    
    device = get_device()
    model.to(device)
    logger.info(f"Training on device: {device}")

    # Setup Data Loaders
    logger.info("Preparing datasets...")
    train_dataset = UnifiedDataset(str(train_data_path), tokenizer)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

    # Optimizer and Scheduler
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
    total_steps = len(train_loader) * num_epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=WARMUP_STEPS, num_training_steps=total_steps
    )

    # Training Loop
    logger.info(f"Starting training for {num_epochs} epochs...")
    logger.info(f"Total steps: {total_steps}")
    
    start_time = time.time()
    
    for epoch in range(num_epochs):
        model.train()
        epoch_loss = 0.0
        epoch_start = time.time()
        
        # Log epoch start
        logger.info(f"--- Epoch {epoch + 1}/{num_epochs} ---")
        monitor_memory(memory_log_path) # Check memory at start of epoch

        for step, batch in enumerate(train_loader):
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
            optimizer.step()
            scheduler.step()

            epoch_loss += loss.item()

            # Log progress every 100 steps
            if (step + 1) % 100 == 0:
                avg_loss = epoch_loss / (step + 1)
                elapsed = time.time() - epoch_start
                logger.info(
                    f"Step {step + 1}/{len(train_loader)}, "
                    f"Loss: {avg_loss:.4f}, "
                    f"Time: {elapsed:.1f}s"
                )
                monitor_memory(memory_log_path) # Check memory periodically

        # End of epoch
        epoch_loss /= len(train_loader)
        epoch_time = time.time() - epoch_start
        
        logger.info(f"Epoch {epoch + 1} Summary:")
        logger.info(f"  Average Loss: {epoch_loss:.4f}")
        logger.info(f"  Epoch Time: {epoch_time:.1f}s")
        
        # Save checkpoint per epoch
        checkpoint_path = model_output_dir / f"checkpoint_epoch_{epoch + 1}.pt"
        torch.save({
            'epoch': epoch + 1,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'loss': epoch_loss
        }, checkpoint_path)
        logger.info(f"Checkpoint saved: {checkpoint_path}")

    # Final Save
    total_time = time.time() - start_time
    final_model_path = model_output_dir / "model.pt"
    torch.save(model.state_dict(), final_model_path)
    logger.info(f"Final model saved to: {final_model_path}")
    logger.info(f"Total Training Time: {total_time:.1f}s")

    log_script_end(logger, "T013", "Training completed successfully")
    return final_model_path

def main():
    """Main entry point for the training script."""
    # Set seed for reproducibility
    set_seed(42)
    
    # Define paths based on config and task requirements
    data_path = get_path("data/processed/unified_dataset.jsonl")
    model_dir = get_path("models/proxy_hard")
    log_dir = get_path("logs")
    
    try:
        train_model(
            train_data_path=data_path,
            model_output_dir=model_dir,
            log_dir=log_dir,
            num_epochs=NUM_EPOCHS,
            batch_size=BATCH_SIZE,
            lr=LEARNING_RATE
        )
        print("Training completed successfully.")
    except Exception as e:
        logging.error(f"Training failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()