"""
Training loop for Memory Palaces in LLMs project.

Implements adaptive batch size logic and dataset capping based on memory constraints.
"""
import os
import sys
import gc
import json
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
import torch
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer

# Project imports
from models.loading import load_model, check_memory_budget
from models.memory_slot import MemoryGrid
from models.coordinate_assigner import CoordinateAssigner
from utils.logger import setup_experiment_logger, log_to_json
from training.memory_monitor import MemoryMonitor

logger = logging.getLogger(__name__)

# Constants
RAM_THRESHOLD_GB = 6.0
INITIAL_BATCH_SIZE = 8
MIN_BATCH_SIZE = 4
DATASET_CAP_FRACTION = 0.5  # [deferred] fraction as per task description

class TrainingLoop:
    def __init__(
        self,
        model,
        tokenizer: AutoTokenizer,
        train_dataset: Dataset,
        device: str,
        output_dir: Path,
        seed: int = 42
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.train_dataset = train_dataset
        self.device = device
        self.output_dir = output_dir
        self.seed = seed
        
        # Memory monitoring
        self.memory_monitor = MemoryMonitor(output_dir)
        self.logger = setup_experiment_logger(output_dir / "training.log")
        
        # Hyperparameters (adaptive)
        self.batch_size = INITIAL_BATCH_SIZE
        self.effective_batch_size = INITIAL_BATCH_SIZE
        self.dataset_capped = False
        self.original_dataset_size = len(train_dataset)
        self.capped_dataset_size = 0
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _log_memory_state(self, stage: str, batch_size: int, rss_mb: float):
        """Log current memory state."""
        self.logger.info(
            f"[{stage}] RSS: {rss_mb:.2f} MB | Batch Size: {batch_size} | "
            f"Dataset Size: {len(self.train_dataset)}"
        )
        self.memory_monitor.log_state(
            stage=stage,
            rss_mb=rss_mb,
            batch_size=batch_size,
            dataset_size=len(self.train_dataset),
            dataset_capped=self.dataset_capped
        )

    def _adapt_batch_size_and_dataset(self) -> Tuple[int, bool]:
        """
        Adapt batch size and dataset size based on memory constraints.
        
        Returns:
            Tuple of (final_batch_size, dataset_was_capped)
        """
        # Start with initial batch size
        current_batch_size = INITIAL_BATCH_SIZE
        gc.collect()
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        
        # Check RSS before any training
        rss_mb = self.memory_monitor.get_current_rss_mb()
        self._log_memory_state("pre-train-init", current_batch_size, rss_mb)
        
        # If RSS > 6GB at initial batch size, reduce to min batch size
        if rss_mb > RAM_THRESHOLD_GB * 1024:
            self.logger.warning(
                f"Initial RSS ({rss_mb/1024:.2f} GB) exceeds threshold "
                f"({RAM_THRESHOLD_GB} GB). Reducing batch size to {MIN_BATCH_SIZE}."
            )
            current_batch_size = MIN_BATCH_SIZE
            gc.collect()
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            rss_mb = self.memory_monitor.get_current_rss_mb()
            self._log_memory_state("after-batch-reduction", current_batch_size, rss_mb)
            
            # If still above threshold, cap dataset
            if rss_mb > RAM_THRESHOLD_GB * 1024:
                self.logger.warning(
                    f"RSS ({rss_mb/1024:.2f} GB) still exceeds threshold "
                    f"({RAM_THRESHOLD_GB} GB) at batch size {MIN_BATCH_SIZE}. "
                    f"Capping dataset to {DATASET_CAP_FRACTION*100:.0f}%."
                )
                cap_size = int(len(self.train_dataset) * DATASET_CAP_FRACTION)
                self.train_dataset = torch.utils.data.Subset(
                    self.train_dataset, 
                    list(range(cap_size))
                )
                self.dataset_capped = True
                self.capped_dataset_size = cap_size
                self.effective_batch_size = current_batch_size
                self.batch_size = current_batch_size
                return current_batch_size, True
        
        self.effective_batch_size = current_batch_size
        self.batch_size = current_batch_size
        return current_batch_size, False

    def train_epoch(self, epoch: int, dataloader: DataLoader) -> float:
        """Train for one epoch and return average loss."""
        self.model.train()
        total_loss = 0.0
        num_batches = 0
        
        for batch_idx, batch in enumerate(dataloader):
            # Move batch to device
            batch = {k: v.to(self.device) for k, v in batch.items()}
            
            # Forward pass
            outputs = self.model(**batch)
            loss = outputs.loss
            
            # Backward pass
            loss.backward()
            
            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            
            # Optimizer step (assuming optimizer is set up outside)
            # Note: In a full implementation, optimizer would be passed in
            # For this loop, we assume the model has an optimizer attribute
            if hasattr(self.model, 'optimizer'):
                self.model.optimizer.step()
                self.model.optimizer.zero_grad()
            
            total_loss += loss.item()
            num_batches += 1
            
            # Log memory periodically
            if batch_idx % 10 == 0:
                rss_mb = self.memory_monitor.get_current_rss_mb()
                self._log_memory_state(
                    f"epoch-{epoch}-batch-{batch_idx}", 
                    self.batch_size, 
                    rss_mb
                )
        
        avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
        return avg_loss

    def run(
        self,
        epochs: int = 3,
        learning_rate: float = 5e-5,
        log_interval: int = 100
    ) -> Dict[str, Any]:
        """
        Run the full training loop with memory-adaptive logic.
        
        Args:
            epochs: Number of training epochs
            learning_rate: Learning rate for optimizer
            log_interval: Log interval in batches
        
        Returns:
            Dictionary with training results and metadata
        """
        self.logger.info("Starting training loop with adaptive memory management")
        
        # Adapt batch size and dataset if needed
        final_batch_size, was_capped = self._adapt_batch_size_and_dataset()
        self.logger.info(
            f"Final configuration: batch_size={final_batch_size}, "
            f"dataset_capped={was_capped}, "
            f"original_size={self.original_dataset_size}, "
            f"current_size={len(self.train_dataset)}"
        )
        
        # Create dataloader
        dataloader = DataLoader(
            self.train_dataset,
            batch_size=final_batch_size,
            shuffle=True,
            num_workers=0,  # Set to 0 to avoid memory issues with workers
            pin_memory=False
        )
        
        # Setup optimizer (simple example, should be passed in for flexibility)
        if not hasattr(self.model, 'optimizer'):
            self.model.optimizer = torch.optim.AdamW(
                self.model.parameters(),
                lr=learning_rate,
                weight_decay=0.01
            )
        
        # Training history
        history = {
            "epochs": [],
            "losses": [],
            "memory_snapshots": []
        }
        
        start_time = time.time()
        
        for epoch in range(epochs):
            self.logger.info(f"Starting epoch {epoch + 1}/{epochs}")
            epoch_loss = self.train_epoch(epoch + 1, dataloader)
            history["epochs"].append(epoch + 1)
            history["losses"].append(epoch_loss)
            
            self.logger.info(f"Epoch {epoch + 1} completed. Loss: {epoch_loss:.4f}")
            
            # Log memory state at end of epoch
            rss_mb = self.memory_monitor.get_current_rss_mb()
            self._log_memory_state(f"epoch-{epoch+1}-end", final_batch_size, rss_mb)
        
        total_runtime = time.time() - start_time
        
        # Final summary
        summary = {
            "seed": self.seed,
            "effective_batch_size": final_batch_size,
            "dataset_capped": was_capped,
            "original_dataset_size": self.original_dataset_size,
            "capped_dataset_size": self.capped_dataset_size if was_capped else self.original_dataset_size,
            "epochs_completed": epochs,
            "final_loss": history["losses"][-1] if history["losses"] else None,
            "runtime_seconds": total_runtime,
            "ram_threshold_gb": RAM_THRESHOLD_GB,
            "initial_batch_size": INITIAL_BATCH_SIZE,
            "min_batch_size": MIN_BATCH_SIZE,
            "dataset_cap_fraction": DATASET_CAP_FRACTION
        }
        
        # Save training summary
        summary_path = self.output_dir / "training_summary.json"
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)
        
        # Save memory monitor data
        self.memory_monitor.save()
        
        self.logger.info(f"Training completed. Summary saved to {summary_path}")
        return summary

def main():
    """
    Main entry point for training loop.
    
    This function demonstrates the training loop with adaptive batch size
    and dataset capping based on memory constraints.
    """
    import argparse
    from datasets import load_dataset
    
    parser = argparse.ArgumentParser(description="Training loop with adaptive memory management")
    parser.add_argument("--model", type=str, default="gpt2-medium", help="Model name")
    parser.add_argument("--dataset", type=str, default="babi", help="Dataset name (babi, lambada, story_cloze)")
    parser.add_argument("--epochs", type=int, default=3, help="Number of epochs")
    parser.add_argument("--lr", type=float, default=5e-5, help="Learning rate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output-dir", type=str, default="artifacts/results", help="Output directory")
    
    args = parser.parse_args()
    
    # Setup
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load dataset (simplified for demonstration)
    logger.info(f"Loading dataset: {args.dataset}")
    if args.dataset == "babi":
        dataset = load_dataset("babi", "task3_10k")
        train_data = dataset["train"]
    else:
        # Fallback for other datasets
        logger.warning(f"Dataset {args.dataset} not fully implemented in demo. Using babi.")
        dataset = load_dataset("babi", "task3_10k")
        train_data = dataset["train"]
    
    # Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    tokenizer.pad_token = tokenizer.eos_token
    
    # Simple dataset wrapper for training
    class SimpleDataset(Dataset):
        def __init__(self, data, tokenizer, max_length=128):
            self.data = data
            self.tokenizer = tokenizer
            self.max_length = max_length
        
        def __len__(self):
            return len(self.data)
        
        def __getitem__(self, idx):
            item = self.data[idx]
            # For bAbI task 3, we have question and answer
            # Simplified: use the story + question as input, answer as target
            text = item.get("story", "") + " " + item.get("question", "")
            encoding = self.tokenizer(
                text,
                max_length=self.max_length,
                padding="max_length",
                truncation=True,
                return_tensors="pt"
            )
            return {k: v.squeeze(0) for k, v in encoding.items()}
    
    train_dataset = SimpleDataset(train_data, tokenizer)
    
    # Load model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Loading model: {args.model} on {device}")
    
    model, _ = load_model(args.model, device=device)
    model.to(device)
    
    # Create and run training loop
    trainer = TrainingLoop(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        device=device,
        output_dir=output_dir,
        seed=args.seed
    )
    
    summary = trainer.run(
        epochs=args.epochs,
        learning_rate=args.lr
    )
    
    logger.info("Training completed successfully")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()