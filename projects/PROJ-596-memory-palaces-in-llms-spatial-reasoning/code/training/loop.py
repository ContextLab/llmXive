"""
Training loop for Memory Palaces in LLMs project.

Implements adaptive batch size logic:
1. Start with batch_size = 8.
2. If RSS > 6GB, reduce to batch_size = 4.
3. If RSS still > 6GB at batch_size = 4, cap dataset to 1/4 of original size.
"""
import gc
import json
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import torch
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer
import numpy as np

# Local imports matching API surface
from models.base import GPT2Baseline
from models.base_fallback import DistilGPT2Fallback
from models.loading import load_model, check_memory_budget
from training.memory_monitor import MemoryMonitor
from utils.logger import ExperimentLogger

# Constants
RSS_THRESHOLD_GB = 6.0
INITIAL_BATCH_SIZE = 8
MIN_BATCH_SIZE = 4
DATASET_CAP_FRACTION = 0.25  # 1/4 of original size

class TrainingLoop:
    def __init__(
        self,
        model_name: str,
        tokenizer: AutoTokenizer,
        dataset: Dataset,
        logger: ExperimentLogger,
        device: Optional[str] = None,
    ):
        self.model_name = model_name
        self.tokenizer = tokenizer
        self.original_dataset = dataset
        self.logger = logger
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        
        self.model = None
        self.batch_size = INITIAL_BATCH_SIZE
        self.dataset = dataset
        self.dataset_capped = False
        self.dataset_capped_fraction = 0.0
        self.memory_monitor = MemoryMonitor()
        
    def _load_model(self) -> Tuple[Any, str]:
        """
        Load model based on memory budget.
        Returns (model, model_type) where model_type is 'gpt2-medium' or 'distilgpt2'.
        """
        # Check memory budget first
        can_load_gpt2, memory_info = check_memory_budget(
            model_name="gpt2-medium", 
            batch_size=self.batch_size,
            rss_threshold_gb=RSS_THRESHOLD_GB
        )
        
        if can_load_gpt2:
            self.logger.log_event("model_loading", {"status": "loading_gpt2_medium"})
            self.model, _ = load_model("gpt2-medium", self.device)
            return self.model, "gpt2-medium"
        else:
            self.logger.log_event("model_loading", {
                "status": "fallback_to_distilgpt2",
                "reason": "insufficient_memory",
                "memory_info": memory_info
            })
            self.model, _ = load_model("distilgpt2", self.device)
            return self.model, "distilgpt2"

    def _adapt_batch_size_and_dataset(self) -> None:
        """
        Adapt batch size and dataset size based on RSS measurements.
        """
        self.logger.log_event("memory_adaptation_start", {
            "initial_batch_size": self.batch_size,
            "dataset_size": len(self.dataset)
        })
        
        # Step 1: Check if we need to reduce batch size from 8 to 4
        if self.batch_size == INITIAL_BATCH_SIZE:
            self.logger.log_event("checking_memory_at_batch_size_8", {})
            # Simulate a small forward pass to check memory
            try:
                dummy_input = torch.randint(0, 1000, (self.batch_size, 10)).to(self.device)
                if self.model is not None:
                    with torch.no_grad():
                        _ = self.model(dummy_input).logits
                
                # Check RSS after dummy pass
                gc.collect()
                if self.device == "cuda":
                    torch.cuda.empty_cache()
                
                current_rss = self.memory_monitor.get_current_rss_gb()
                self.logger.log_event("memory_check_batch_8", {"rss_gb": current_rss})
                
                if current_rss > RSS_THRESHOLD_GB:
                    self.batch_size = MIN_BATCH_SIZE
                    self.logger.log_event("batch_size_reduced", {
                        "from": INITIAL_BATCH_SIZE,
                        "to": MIN_BATCH_SIZE,
                        "reason": "rss_exceeded_threshold",
                        "rss_gb": current_rss
                    })
            except Exception as e:
                self.logger.log_event("memory_check_error", {"error": str(e)})
                self.batch_size = MIN_BATCH_SIZE
        
        # Step 2: If still at high memory usage with batch_size=4, cap dataset
        if self.batch_size == MIN_BATCH_SIZE:
            self.logger.log_event("checking_memory_at_batch_size_4", {})
            try:
                dummy_input = torch.randint(0, 1000, (self.batch_size, 10)).to(self.device)
                if self.model is not None:
                    with torch.no_grad():
                        _ = self.model(dummy_input).logits
                
                gc.collect()
                if self.device == "cuda":
                    torch.cuda.empty_cache()
                
                current_rss = self.memory_monitor.get_current_rss_gb()
                self.logger.log_event("memory_check_batch_4", {"rss_gb": current_rss})
                
                if current_rss > RSS_THRESHOLD_GB:
                    original_size = len(self.original_dataset)
                    new_size = max(1, int(original_size * DATASET_CAP_FRACTION))
                    self.dataset = torch.utils.data.Subset(self.original_dataset, range(new_size))
                    self.dataset_capped = True
                    self.dataset_capped_fraction = DATASET_CAP_FRACTION
                    
                    self.logger.log_event("dataset_capped", {
                        "original_size": original_size,
                        "new_size": new_size,
                        "fraction": DATASET_CAP_FRACTION,
                        "reason": "rss_still_exceeded_at_batch_4",
                        "rss_gb": current_rss
                    })
            except Exception as e:
                self.logger.log_event("memory_check_error_batch4", {"error": str(e)})
                # Fallback: cap dataset anyway
                original_size = len(self.original_dataset)
                new_size = max(1, int(original_size * DATASET_CAP_FRACTION))
                self.dataset = torch.utils.data.Subset(self.original_dataset, range(new_size))
                self.dataset_capped = True
                self.dataset_capped_fraction = DATASET_CAP_FRACTION

    def train(
        self,
        epochs: int = 3,
        learning_rate: float = 5e-5,
        seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Execute the training loop.
        
        Args:
            epochs: Number of training epochs
            learning_rate: Learning rate for optimizer
            seed: Random seed for reproducibility
            
        Returns:
            Dictionary with training metrics and configuration
        """
        if seed is not None:
            torch.manual_seed(seed)
            np.random.seed(seed)
            if self.device == "cuda":
                torch.cuda.manual_seed_all(seed)
        
        # Load model
        model, model_type = self._load_model()
        model.train()
        
        # Adapt batch size and dataset based on memory
        self._adapt_batch_size_and_dataset()
        
        # Create DataLoader
        dataloader = DataLoader(
            self.dataset,
            batch_size=self.batch_size,
            shuffle=True,
            drop_last=True
        )
        
        # Setup optimizer
        optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
        criterion = torch.nn.CrossEntropyLoss()
        
        # Training metrics
        total_steps = 0
        start_time = time.time()
        epoch_losses = []
        memory_log = []
        
        for epoch in range(epochs):
            epoch_loss = 0.0
            epoch_steps = 0
            
            for batch_idx, batch in enumerate(dataloader):
                # Move batch to device
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch.get("attention_mask", None)
                if attention_mask is not None:
                    attention_mask = attention_mask.to(self.device)
                
                # Forward pass
                outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                logits = outputs.logits
                
                # Shift for next token prediction
                shift_logits = logits[..., :-1, :].contiguous()
                shift_labels = input_ids[..., 1:].contiguous()
                
                # Flatten for loss calculation
                shift_logits = shift_logits.view(-1, shift_logits.size(-1))
                shift_labels = shift_labels.view(-1)
                
                # Compute loss
                loss = criterion(shift_logits, shift_labels)
                
                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
                epoch_steps += 1
                total_steps += 1
                
                # Log memory usage periodically
                if batch_idx % 10 == 0:
                    gc.collect()
                    if self.device == "cuda":
                        torch.cuda.empty_cache()
                    
                    rss = self.memory_monitor.get_current_rss_gb()
                    memory_log.append({
                        "epoch": epoch,
                        "batch": batch_idx,
                        "rss_gb": rss,
                        "batch_size": self.batch_size,
                        "dataset_capped": self.dataset_capped
                    })
                
                # Log loss
                if batch_idx % 50 == 0:
                    self.logger.log_event("batch_loss", {
                        "epoch": epoch,
                        "batch": batch_idx,
                        "loss": loss.item(),
                        "cumulative_loss": epoch_loss / (batch_idx + 1)
                    })
            
            avg_epoch_loss = epoch_loss / epoch_steps if epoch_steps > 0 else 0.0
            epoch_losses.append(avg_epoch_loss)
            
            self.logger.log_event("epoch_complete", {
                "epoch": epoch,
                "avg_loss": avg_epoch_loss,
                "total_steps": epoch_steps
            })
        
        end_time = time.time()
        runtime_seconds = end_time - start_time
        
        # Final metrics
        metrics = {
            "model_type": model_type,
            "batch_size": self.batch_size,
            "dataset_capped": self.dataset_capped,
            "dataset_capped_fraction": self.dataset_capped_fraction if self.dataset_capped else None,
            "original_dataset_size": len(self.original_dataset),
            "effective_dataset_size": len(self.dataset),
            "epochs": epochs,
            "total_steps": total_steps,
            "final_loss": epoch_losses[-1] if epoch_losses else None,
            "epoch_losses": epoch_losses,
            "runtime_seconds": runtime_seconds,
            "memory_log": memory_log
        }
        
        # Log final configuration
        self.logger.log_event("training_complete", metrics)
        
        return metrics

def main():
    """
    Main entry point for training loop demonstration.
    This function demonstrates the training loop with a minimal setup.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Training Loop for Memory Palaces")
    parser.add_argument("--model", type=str, default="gpt2-medium", help="Model name")
    parser.add_argument("--epochs", type=int, default=3, help="Number of epochs")
    parser.add_argument("--lr", type=float, default=5e-5, help="Learning rate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output-dir", type=str, default="artifacts/results", help="Output directory")
    
    args = parser.parse_args()
    
    # Setup output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize logger
    logger = ExperimentLogger(output_dir)
    
    # Create a minimal dataset for demonstration
    # In production, this would be loaded from code/data/download.py
    class MinimalDataset(Dataset):
        def __init__(self, size=100, seq_len=10):
            self.size = size
            self.seq_len = seq_len
            
        def __len__(self):
            return self.size
        
        def __getitem__(self, idx):
            # Create random token IDs
            input_ids = torch.randint(0, 1000, (self.seq_len,))
            attention_mask = torch.ones_like(input_ids)
            return {
                "input_ids": input_ids,
                "attention_mask": attention_mask
            }
    
    dataset = MinimalDataset(size=200, seq_len=10)
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Initialize training loop
    trainer = TrainingLoop(
        model_name=args.model,
        tokenizer=tokenizer,
        dataset=dataset,
        logger=logger,
    )
    
    # Run training
    metrics = trainer.train(
        epochs=args.epochs,
        learning_rate=args.lr,
        seed=args.seed,
    )
    
    # Save metrics
    metrics_path = output_dir / "training_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2, default=str)
    
    print(f"Training complete. Metrics saved to {metrics_path}")
    print(f"Model type: {metrics['model_type']}")
    print(f"Effective batch size: {metrics['batch_size']}")
    print(f"Dataset capped: {metrics['dataset_capped']}")
    if metrics['dataset_capped']:
        print(f"Dataset capped fraction: {metrics['dataset_capped_fraction']}")
    print(f"Runtime: {metrics['runtime_seconds']:.2f} seconds")
    
    return metrics

if __name__ == "__main__":
    main()
