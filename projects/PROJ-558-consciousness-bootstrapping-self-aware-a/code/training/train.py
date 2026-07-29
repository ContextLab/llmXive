import os
import sys
import json
import hashlib
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, List

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from transformers import LlamaConfig, LlamaForCausalLM, LlamaTokenizer
from datasets import load_dataset
from transformers import LlamaConfig, LlamaForCausalLM, TrainingArguments, Trainer
from transformers.utils import is_torch_available

from config import get_config, validate_config, ConfigurationError
from utils.logging import get_logger, log_training_start, log_training_end, log_metric, ConsciousnessBootstrappingError, RecursionDepthError
from models.recursive_llama import create_recursive_model, RecursiveLlamaWrapper
from models.base_llama import BaseLlamaWrapper
from models.checkpoint import ModelCheckpoint
from evaluation.loss_functions import compute_joint_loss

logger = get_logger(__name__)

# Memory profiling integration
try:
    import resource
    def get_peak_memory_mb():
        usage = resource.getrusage(resource.RUSAGE_SELF)
        return usage.ru_maxrss / 1024.0
except ImportError:
    def get_peak_memory_mb():
        return 0.0

class PileDataset(Dataset):
    def __init__(self, data_path: str, tokenizer: LlamaTokenizer, max_length: int = 512):
        self.data_path = data_path
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.data = []
        
        logger.info(f"Loading dataset from {data_path}")
        # Load the truncated Pile dataset (arXiv subset)
        # Assuming the data was saved as JSON by data_loader.py
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Dataset file not found: {data_path}")
        
        with open(data_path, 'r') as f:
            self.data = json.load(f)
        
        logger.info(f"Loaded {len(self.data)} samples")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        text = item.get('text', '')
        # Tokenize
        encoding = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            padding='max_length',
            return_tensors='pt'
        )
        return {
            'input_ids': encoding['input_ids'].squeeze(0),
            'attention_mask': encoding['attention_mask'].squeeze(0),
            'labels': encoding['input_ids'].squeeze(0) # For next token prediction
        }

def train_epoch(model: nn.Module, dataloader: DataLoader, optimizer: torch.optim.Optimizer, 
                criterion: nn.Module, device: torch.device, epoch: int, config: Dict[str, Any]) -> float:
    model.train()
    total_loss = 0.0
    batch_count = 0

    for batch_idx, batch in enumerate(dataloader):
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        labels = batch['labels'].to(device)

        optimizer.zero_grad()

        try:
            # Forward pass
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )
            
            loss = outputs.loss
            
            # Backward pass
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            batch_count += 1

            if batch_idx % 10 == 0:
                logger.info(f"Epoch {epoch}, Batch {batch_idx}, Loss: {loss.item():.4f}")
                log_metric(f"train_loss_epoch_{epoch}", loss.item())

        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                logger.error(f"OOM detected at batch {batch_idx}")
                raise RecursionDepthError("OOM detected during training. Recursion depth or batch size too high.") from e
            else:
                raise

    avg_loss = total_loss / batch_count if batch_count > 0 else 0.0
    return avg_loss

def save_checkpoint(model: nn.Module, optimizer: torch.optim.Optimizer, epoch: int, 
                    loss: float, config: Dict[str, Any], output_path: str):
    checkpoint = ModelCheckpoint(
        epoch=epoch,
        loss=loss,
        model_state=model.state_dict(),
        optimizer_state=optimizer.state_dict(),
        config=config,
        timestamp=datetime.now().isoformat()
    )
    checkpoint.save(output_path)
    logger.info(f"Checkpoint saved to {output_path}")

def validate_recursion_depth(depth: int, config: Dict[str, Any]):
    """
    Validates that recursion depth does not exceed the configured maximum.
    Hard-fails if violated.
    """
    max_depth = config.get('recursion_depth', 2)
    if depth > max_depth:
        error_msg = f"Recursion depth {depth} exceeds maximum allowed {max_depth}."
        logger.error(error_msg)
        raise RecursionDepthError(error_msg)
    logger.info(f"Recursion depth validated: {depth} <= {max_depth}")

def run_training(config: Dict[str, Any]):
    """
    Main training loop.
    """
    # Validate recursion depth early
    validate_recursion_depth(config.get('recursion_depth', 2), config)

    # Setup device
    device = torch.device("cpu") # Enforce CPU-only as per config
    if torch.cuda.is_available():
        logger.warning("CUDA detected but CPU-only mode enforced.")

    # Load tokenizer and model
    model_name = config.get('model_name', 'tinyllama')
    tokenizer = LlamaTokenizer.from_pretrained(model_name)
    
    # Create model (Recursive or Baseline)
    if config.get('use_recursive', False):
        model = create_recursive_model(config, tokenizer)
        model_type = "recursive"
    else:
        model = BaseLlamaWrapper(config, tokenizer)
        model_type = "baseline"
    
    model.to(device)

def run_training(config: Config):
    """
    Main training loop.
    Implements the hard-fail logic for recursion depth > 2.
    """
    device = torch.device("cpu") # Enforce CPU-only as per config
    if torch.cuda.is_available() and not config.cpu_only:
        logger.warning("CUDA available but CPU-only mode enforced by config.")
    
    logger.info("Initializing training...")
    
    # Load dataset
    data_path = config.get('train_data_path', 'data/raw/pile_arxiv_truncated.json')
    dataset = PileDataset(data_path, tokenizer, max_length=config.get('max_length', 512))
    dataloader = DataLoader(
        dataset, 
        batch_size=config.get('batch_size', 4), 
        shuffle=True
    )

    # Optimizer and Loss
    optimizer = torch.optim.AdamW(model.parameters(), lr=config.get('learning_rate', 1e-4))
    # Loss is handled inside the model or via compute_joint_loss if needed
    # For simplicity, we assume the model outputs a loss directly or we use a standard CE
    criterion = nn.CrossEntropyLoss() 

    # Training Loop
    epochs = config.get('epochs', 1)
    for epoch in range(epochs):
        logger.info(f"Starting Epoch {epoch+1}/{epochs}")
        log_training_start(epoch)

        try:
            avg_loss = train_epoch(model, dataloader, optimizer, criterion, device, epoch, config)
            
            # Log memory usage
            peak_mem = get_peak_memory_mb()
            logger.info(f"Epoch {epoch+1} Avg Loss: {avg_loss:.4f}, Peak Memory: {peak_mem:.2f} MB")
            log_metric(f"peak_memory_epoch_{epoch}", peak_mem)

            # Save checkpoint
            output_dir = config.get('output_dir', 'artifacts/checkpoints')
            os.makedirs(output_dir, exist_ok=True)
            ckpt_path = os.path.join(output_dir, f"checkpoint_{model_type}_epoch_{epoch+1}.pt")
            save_checkpoint(model, optimizer, epoch, avg_loss, config, ckpt_path)

        except RecursionDepthError as e:
            logger.error(f"Training failed due to recursion depth violation: {e}")
            raise
        except Exception as e:
            logger.error(f"Training failed in epoch {epoch}: {e}")
            traceback.print_exc()
            raise

    log_training_end(epochs)
    logger.info("Training completed successfully.")

def main():
    config = get_config()
    validate_config(config)
    
    try:
        config = get_config()
        validate_config(config)
        
        log_training_start(config)
        
        run_training(config)
        
        log_training_end(config)
        
    except RecursionDepthError as e:
        logger.critical(f"CRITICAL FAILURE: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error in training: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()