"""
Training script for the Consciousness Bootstrapping project.
Implements training for both recursive and baseline TinyLlama models.
"""

import os
import sys
import json
import hashlib
import traceback
import gc
import random
import argparse
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from transformers import LlamaConfig, LlamaForCausalLM, LlamaTokenizer
from transformers.modeling_outputs import CausalLMOutputWithPast

# Project imports
from utils.logging import get_logger, log_training_start, log_training_end, log_metric, ModelTrainingError
from utils.config import get_config, validate_config
from models.base_llama import BaseLlamaWrapper
from models.recursive_llama import RecursiveLlamaWrapper, create_recursive_model
from evaluation.loss_functions import compute_joint_loss, compute_self_consistency_proxy
from models.checkpoint import ModelCheckpoint

# Setup logging
logger = get_logger(__name__)

@dataclass
class TrainingState:
    """Tracks the state of the training process."""
    epoch: int = 0
    global_step: int = 0
    best_loss: float = float('inf')
    loss_history: List[float] = field(default_factory=list)
    recursion_depth: int = 2
    seed: int = 42
    start_time: datetime = field(default_factory=datetime.now)

class PileDataset(Dataset):
    """
    Dataset wrapper for the truncated Pile dataset.
    Reads from data/processed/pile_arxiv_truncated.jsonl.
    """
    def __init__(self, data_path: str, tokenizer: LlamaTokenizer, max_length: int = 512):
        super().__init__()
        self.data_path = data_path
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.data = []
        self._load_data()

    def _load_data(self):
        """Load data from JSONL file."""
        logger.info(f"Loading dataset from {self.data_path}")
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Dataset file not found: {self.data_path}")
        
        count = 0
        with open(self.data_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                    text = item.get('text', '')
                    if text:
                        self.data.append(text)
                        count += 1
                except json.JSONDecodeError:
                    continue
        logger.info(f"Loaded {count} samples from {self.data_path}")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        text = self.data[idx]
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
            'labels': encoding['input_ids'].squeeze(0).clone()
        }

def set_seed(seed: int):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def validate_recursion_depth(depth: int, max_allowed: int = 2):
    """
    Validate that recursion depth does not exceed the configured limit.
    Implements hard-fail as per Spec Edge Cases.
    """
    if depth > max_allowed:
        error_msg = f"Recursion depth {depth} exceeds maximum allowed {max_allowed}. Hard-failing as per spec."
        logger.error(error_msg)
        raise ValueError(error_msg)

def check_memory_usage(threshold_gb: float = 6.5):
    """
    Check current memory usage and raise if threshold exceeded.
    Implements hard-fail on OOM as per Spec Edge Cases.
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_mb = process.memory_info().rss / (1024 * 1024)
        mem_gb = mem_mb / 1024.0
        
        if mem_gb > threshold_gb:
            error_msg = f"Memory usage {mem_gb:.2f}GB exceeds threshold {threshold_gb}GB. Hard-failing."
            logger.error(error_msg)
            raise MemoryError(error_msg)
    except ImportError:
        # Fallback: try torch memory if available
        if torch.cuda.is_available():
            mem_mb = torch.cuda.memory_allocated() / (1024 * 1024)
            mem_gb = mem_mb / 1024.0
            if mem_gb > threshold_gb:
                error_msg = f"GPU Memory usage {mem_gb:.2f}GB exceeds threshold {threshold_gb}GB."
                logger.error(error_msg)
                raise MemoryError(error_msg)
        logger.warning("psutil not available, skipping memory check")

def train_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    config: Dict[str, Any],
    state: TrainingState
) -> float:
    """
    Train one epoch of the model.
    Uses the joint loss (cross-entropy + self-consistency proxy) as per T012-IMPL.
    """
    model.train()
    total_loss = 0.0
    num_batches = 0
    
    # Config parameters
    recursion_depth = state.recursion_depth
    temperature = config.get('temperature', 0.7)
    top_p = config.get('top_p', 0.9)
    max_tokens = config.get('max_tokens', 256)
    n_samples = config.get('n_samples', 3)  # N=3 for training proxy

    for batch_idx, batch in enumerate(dataloader):
        # Check memory before processing batch
        check_memory_usage()

        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        labels = batch['labels'].to(device)

        # Forward pass
        if isinstance(model, RecursiveLlamaWrapper):
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                recursion_depth=recursion_depth
            )
        else:
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask
            )

        # Compute joint loss
        # The loss function computes cross-entropy + confidence prediction loss
        # using the internal self-consistency proxy (no ground truth labels used for proxy)
        loss_value, proxy_signal, confidence_pred = compute_joint_loss(
            model=model,
            batch={
                'input_ids': input_ids,
                'attention_mask': attention_mask,
                'labels': labels
            },
            generate_paths_callback=lambda b, n, temp: _mock_generate_paths(b, n, temp, model, device),
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            n_samples=n_samples
        )

        # Backward pass
        optimizer.zero_grad()
        loss_value.backward()
        optimizer.step()

        total_loss += loss_value.item()
        num_batches += 1
        state.global_step += 1

        if batch_idx % 10 == 0:
            log_metric('train_loss', loss_value.item(), step=state.global_step)
            logger.info(f"Epoch {state.epoch+1}, Batch {batch_idx}, Loss: {loss_value.item():.4f}")

        # Clear cache to prevent OOM
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()

    avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
    return avg_loss

def _mock_generate_paths(batch: Dict, n_samples: int, temperature: float, model: nn.Module, device: torch.device) -> List[List[str]]:
    """
    Mock generator for training proxy to break circular dependency on T019a-GEN.
    Returns deterministic identical paths for any input to ensure loss function can be tested.
    This satisfies the T012-MOCK requirement.
    """
    # For training, we use a deterministic mock to avoid circular dependency
    # In real training, this would be replaced by actual generation
    # Returns 3 identical paths as per T012-MOCK logic
    paths = []
    for _ in range(n_samples):
        # Generate a deterministic "path" based on input
        # In reality, this would call model.generate() with frozen weights
        input_text = batch['input_ids'][0].cpu().numpy()
        # Mock: return a simple deterministic string
        path = ["Mock reasoning path for training proxy."]
        paths.append(path)
    return paths

def save_checkpoint(
    model: nn.Module,
    state: TrainingState,
    output_path: str,
    is_recursive: bool
):
    """Save model checkpoint."""
    checkpoint = ModelCheckpoint(
        model_type='recursive' if is_recursive else 'baseline',
        recursion_depth=state.recursion_depth if is_recursive else 0,
        epoch=state.epoch,
        global_step=state.global_step,
        best_loss=state.best_loss,
        loss_history=state.loss_history,
        seed=state.seed,
        timestamp=datetime.now().isoformat(),
        model_state_dict=model.state_dict()
    )
    checkpoint.save(output_path)
    logger.info(f"Saved checkpoint to {output_path}")

def run_training(
    model: nn.Module,
    dataloader: DataLoader,
    config: Dict[str, Any],
    state: TrainingState,
    is_recursive: bool
):
    """Run the full training loop."""
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = model.to(device)
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=config.get('learning_rate', 1e-4))
    num_epochs = config.get('num_epochs', 1)
    token_limit = config.get('token_limit', 100000)

    log_training_start(
        model_type='recursive' if is_recursive else 'baseline',
        recursion_depth=state.recursion_depth if is_recursive else 0,
        num_epochs=num_epochs,
        dataset_size=len(dataloader.dataset)
    )

    for epoch in range(num_epochs):
        state.epoch = epoch
        logger.info(f"Starting epoch {epoch + 1}/{num_epochs}")

        # Validate token limit before training
        dataset_size = len(dataloader.dataset)
        if dataset_size > token_limit:
            error_msg = f"Dataset size {dataset_size} exceeds token_limit {token_limit}. Hard-failing."
            logger.error(error_msg)
            raise ValueError(error_msg)

        epoch_loss = train_epoch(model, dataloader, optimizer, device, config, state)
        state.loss_history.append(epoch_loss)

        if epoch_loss < state.best_loss:
            state.best_loss = epoch_loss
            logger.info(f"New best loss: {state.best_loss:.4f}")

        log_metric('epoch_loss', epoch_loss, step=state.epoch)
        logger.info(f"Epoch {epoch + 1} completed. Loss: {epoch_loss:.4f}")

        # Save intermediate checkpoint
        checkpoint_path = f"{config.get('output_dir', 'artifacts/checkpoints')}/epoch_{epoch+1}_{'recursive' if is_recursive else 'baseline'}.pt"
        save_checkpoint(model, state, checkpoint_path, is_recursive)

    log_training_end(
        model_type='recursive' if is_recursive else 'baseline',
        final_loss=state.loss_history[-1] if state.loss_history else None,
        best_loss=state.best_loss
    )

def main():
    """Main entry point for training script."""
    parser = argparse.ArgumentParser(description='Train Recursive Llama Model')
    parser.add_argument('--recursive', action='store_true', help='Train recursive model')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--config', type=str, default='code/utils/config.py', help='Config file path')
    args = parser.parse_args()

    # Load config
    config = get_config()
    validate_config(config)

    # Set seed
    set_seed(args.seed)

    # Initialize tokenizer
    tokenizer = LlamaTokenizer.from_pretrained('TinyLlama/TinyLlama-1.1B-intermediate-step-1431k-3T')
    
    # Load dataset
    data_path = config.get('data_path', 'projects/PROJ-558-consciousness-bootstrapping-self-aware-a/data/processed/pile_arxiv_truncated.jsonl')
    dataset = PileDataset(data_path, tokenizer, max_length=config.get('max_length', 512))
    dataloader = DataLoader(dataset, batch_size=config.get('batch_size', 1), shuffle=True)

    # Create model
    if args.recursive:
        logger.info("Initializing recursive model...")
        validate_recursion_depth(config.get('recursion_depth', 2))
        model = create_recursive_model(
            config=config,
            tokenizer=tokenizer,
            max_recursion_depth=config.get('recursion_depth', 2)
        )
        state = TrainingState(seed=args.seed, recursion_depth=config.get('recursion_depth', 2))
    else:
        logger.info("Initializing baseline model...")
        model = BaseLlamaWrapper(config=config, tokenizer=tokenizer)
        state = TrainingState(seed=args.seed, recursion_depth=0)

    # Run training
    try:
        run_training(model, dataloader, config, state, is_recursive=args.recursive)
    except (ValueError, MemoryError) as e:
        logger.error(f"Training failed: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during training: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main()