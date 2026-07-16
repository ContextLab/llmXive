"""
Optimized training loop for Memory Palaces project.
Implements adaptive batch sizing, memory monitoring, and early stopping to reduce training time.
Addresses John von Neumann concern on overhead by minimizing redundant computations.
"""
import gc
import json
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import torch
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer

# Local imports from project API surface
from training.memory_monitor import get_current_memory_usage_gb, MemoryMonitor
from models.loading import load_model
from models.base import GPT2Baseline
from models.base_fallback import DistilGPT2Fallback
from utils.logger import ExperimentLogger
from utils.hyperparams_logger import log_hyperparameters


class OptimizedTrainingLoop:
    """
    Training loop with optimizations to reduce training time:
    1. Adaptive batch sizing based on memory monitoring
    2. Gradient accumulation for stability with smaller effective batch sizes
    3. Early stopping based on validation loss
    4. Mixed precision training (AMP) when available
    5. Optimized data loading with prefetching
    """

    def __init__(
        self,
        model_name: str,
        dataset: Dataset,
        val_dataset: Optional[Dataset] = None,
        max_epochs: int = 10,
        initial_batch_size: int = 8,
        learning_rate: float = 5e-5,
        memory_threshold_gb: float = 6.0,
        early_stopping_patience: int = 3,
        use_amp: bool = True,
        gradient_accumulation_steps: int = 1,
        log_dir: Optional[str] = None
    ):
        self.model_name = model_name
        self.dataset = dataset
        self.val_dataset = val_dataset
        self.max_epochs = max_epochs
        self.initial_batch_size = initial_batch_size
        self.learning_rate = learning_rate
        self.memory_threshold_gb = memory_threshold_gb
        self.early_stopping_patience = early_stopping_patience
        self.use_amp = use_amp and torch.cuda.is_available()
        self.gradient_accumulation_steps = gradient_accumulation_steps
        self.log_dir = Path(log_dir) if log_dir else Path("artifacts/results")
        
        # Initialize components
        self.memory_monitor = MemoryMonitor(threshold_gb=self.memory_threshold_gb)
        self.logger = ExperimentLogger(output_dir=str(self.log_dir))
        
        # Training state
        self.current_batch_size = self.initial_batch_size
        self.best_val_loss = float('inf')
        self.patience_counter = 0
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load model with memory monitoring
        self.model, self.tokenizer, self.model_type = self._load_model_with_monitoring()
        self.model.to(self.device)
        
        # Setup optimizer
        self.optimizer = torch.optim.AdamW(self.model.parameters(), lr=self.learning_rate)
        
        # Setup mixed precision scaler
        self.scaler = torch.cuda.amp.GradScaler() if self.use_amp else None
        
        # Log initial hyperparameters
        self._log_initial_hyperparams()

    def _load_model_with_monitoring(self) -> Tuple[Any, Any, str]:
        """Load model with memory monitoring to select appropriate architecture."""
        try:
            # Try loading the primary model (GPT2-medium)
            model, tokenizer = load_model(self.model_name, max_memory_gb=self.memory_threshold_gb)
            return model, tokenizer, "gpt2-medium"
        except Exception as e:
            # Fallback to smaller model if memory is insufficient
            print(f"Primary model load failed: {e}. Falling back to DistilGPT2.")
            model, tokenizer = load_model("distilgpt2", max_memory_gb=self.memory_threshold_gb)
            return model, tokenizer, "distilgpt2"

    def _log_initial_hyperparams(self):
        """Log initial training hyperparameters."""
        hyperparams = {
            "model_name": self.model_name,
            "actual_model": self.model_type,
            "initial_batch_size": self.initial_batch_size,
            "current_batch_size": self.current_batch_size,
            "learning_rate": self.learning_rate,
            "max_epochs": self.max_epochs,
            "memory_threshold_gb": self.memory_threshold_gb,
            "use_amp": self.use_amp,
            "gradient_accumulation_steps": self.gradient_accumulation_steps,
            "device": str(self.device),
            "dataset_size": len(self.dataset),
            "val_dataset_size": len(self.val_dataset) if self.val_dataset else 0
        }
        log_hyperparameters(hyperparams, self.log_dir / "hyperparams_log.json")

    def _create_dataloader(self, dataset: Dataset, batch_size: int, shuffle: bool = True) -> DataLoader:
        """Create optimized DataLoader with prefetching."""
        return DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=shuffle,
            num_workers=2 if self.device.type == "cuda" else 0,
            pin_memory=True if self.device.type == "cuda" else False,
            prefetch_factor=2 if self.device.type == "cuda" else None,
            persistent_workers=True if self.device.type == "cuda" else False
        )

    def _adapt_batch_size(self):
        """Adapt batch size based on current memory usage."""
        current_memory = get_current_memory_usage_gb()
        
        if current_memory > self.memory_threshold_gb:
            if self.current_batch_size > 4:
                self.current_batch_size = 4
                print(f"Memory usage ({current_memory:.2f}GB) exceeds threshold. Reducing batch size to {self.current_batch_size}")
            elif self.current_batch_size == 4:
                # If still over threshold at batch size 4, we need to cap dataset
                print(f"Memory usage ({current_memory:.2f}GB) still exceeds threshold at batch size 4. Dataset capping required.")
                # Note: Dataset capping is handled by the caller or memory_monitor
                raise MemoryError(f"Memory threshold exceeded at minimum batch size {self.current_batch_size}")
        elif current_memory < self.memory_threshold_gb * 0.8 and self.current_batch_size < self.initial_batch_size:
            # Try to increase batch size if memory is well below threshold
            self.current_batch_size = min(self.current_batch_size * 2, self.initial_batch_size)
            print(f"Memory usage ({current_memory:.2f}GB) is low. Increasing batch size to {self.current_batch_size}")

    def _train_epoch(self, epoch: int) -> float:
        """Train for one epoch with optimizations."""
        self.model.train()
        total_loss = 0.0
        num_batches = 0
        
        dataloader = self._create_dataloader(self.dataset, self.current_batch_size, shuffle=True)
        
        for batch_idx, batch in enumerate(dataloader):
            # Move batch to device
            input_ids = batch["input_ids"].to(self.device)
            attention_mask = batch["attention_mask"].to(self.device)
            labels = batch["labels"].to(self.device) if "labels" in batch else input_ids
            
            # Memory check before each batch
            if batch_idx % 10 == 0:  # Check every 10 batches to reduce overhead
                self._adapt_batch_size()
                # Recreate dataloader if batch size changed
                if batch_idx > 0:
                    dataloader = self._create_dataloader(self.dataset, self.current_batch_size, shuffle=True)
                    break  # Break to restart epoch with new batch size
            
            # Forward pass with mixed precision if available
            if self.use_amp and self.scaler:
                with torch.cuda.amp.autocast():
                    outputs = self.model(
                        input_ids=input_ids,
                        attention_mask=attention_mask,
                        labels=labels
                    )
                    loss = outputs.loss / self.gradient_accumulation_steps
                    
                    # Backward pass with gradient scaling
                    self.scaler.scale(loss).backward()
                    
                    # Gradient accumulation
                    if (batch_idx + 1) % self.gradient_accumulation_steps == 0:
                        self.scaler.step(self.optimizer)
                        self.scaler.update()
                        self.optimizer.zero_grad()
            else:
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )
                loss = outputs.loss / self.gradient_accumulation_steps
                loss.backward()
                
                # Gradient accumulation
                if (batch_idx + 1) % self.gradient_accumulation_steps == 0:
                    self.optimizer.step()
                    self.optimizer.zero_grad()
            
            total_loss += loss.item() * self.gradient_accumulation_steps
            num_batches += 1
            
            # Clear GPU cache periodically
            if batch_idx % 50 == 0 and self.device.type == "cuda":
                torch.cuda.empty_cache()
                gc.collect()
        
        avg_loss = total_loss / max(num_batches, 1)
        return avg_loss

    def _validate_epoch(self) -> float:
        """Validate on validation dataset."""
        if not self.val_dataset:
            return float('inf')
        
        self.model.eval()
        total_loss = 0.0
        num_batches = 0
        
        dataloader = self._create_dataloader(self.val_dataset, self.current_batch_size, shuffle=False)
        
        with torch.no_grad():
            for batch in dataloader:
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                labels = batch["labels"].to(self.device) if "labels" in batch else input_ids
                
                if self.use_amp and self.scaler:
                    with torch.cuda.amp.autocast():
                        outputs = self.model(
                            input_ids=input_ids,
                            attention_mask=attention_mask,
                            labels=labels
                        )
                        loss = outputs.loss
                else:
                    outputs = self.model(
                        input_ids=input_ids,
                        attention_mask=attention_mask,
                        labels=labels
                    )
                    loss = outputs.loss
                
                total_loss += loss.item()
                num_batches += 1
        
        return total_loss / max(num_batches, 1)

    def train(self) -> Dict[str, Any]:
        """
        Execute the full training loop with optimizations.
        Returns training summary statistics.
        """
        start_time = time.time()
        training_history = {
            "train_losses": [],
            "val_losses": [],
            "batch_sizes": [],
            "memory_usage_gb": []
        }
        
        print(f"Starting training with model: {self.model_type}")
        print(f"Initial batch size: {self.current_batch_size}, Device: {self.device}")
        
        for epoch in range(self.max_epochs):
            epoch_start = time.time()
            
            # Train one epoch
            train_loss = self._train_epoch(epoch)
            training_history["train_losses"].append(train_loss)
            
            # Validate
            val_loss = self._validate_epoch()
            training_history["val_losses"].append(val_loss)
            
            # Log memory usage
            current_memory = get_current_memory_usage_gb()
            training_history["memory_usage_gb"].append(current_memory)
            training_history["batch_sizes"].append(self.current_batch_size)
            
            # Log epoch results
            epoch_time = time.time() - epoch_start
            print(f"Epoch {epoch+1}/{self.max_epochs} - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}, Time: {epoch_time:.2f}s, Memory: {current_memory:.2f}GB")
            
            self.logger.log_epoch(
                epoch=epoch + 1,
                train_loss=train_loss,
                val_loss=val_loss,
                batch_size=self.current_batch_size,
                memory_usage_gb=current_memory,
                elapsed_time=epoch_time
            )
            
            # Early stopping check
            if val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                self.patience_counter = 0
                # Save best model
                self._save_model_checkpoint(epoch, "best")
            else:
                self.patience_counter += 1
                if self.patience_counter >= self.early_stopping_patience:
                    print(f"Early stopping triggered at epoch {epoch+1}")
                    break
            
            # Save checkpoint every 5 epochs
            if (epoch + 1) % 5 == 0:
                self._save_model_checkpoint(epoch, f"epoch_{epoch+1}")
        
        total_time = time.time() - start_time
        
        # Final summary
        summary = {
            "total_epochs": len(training_history["train_losses"]),
            "total_time_seconds": total_time,
            "final_train_loss": training_history["train_losses"][-1] if training_history["train_losses"] else None,
            "final_val_loss": training_history["val_losses"][-1] if training_history["val_losses"] else None,
            "best_val_loss": self.best_val_loss,
            "final_batch_size": self.current_batch_size,
            "early_stopped": self.patience_counter >= self.early_stopping_patience,
            "history": training_history
        }
        
        # Save training summary
        summary_path = self.log_dir / "training_summary.json"
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)
        
        print(f"Training completed in {total_time:.2f} seconds")
        return summary

    def _save_model_checkpoint(self, epoch: int, checkpoint_name: str):
        """Save model checkpoint."""
        checkpoint_dir = self.log_dir / "checkpoints"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        checkpoint_path = checkpoint_dir / f"{checkpoint_name}.pt"
        
        torch.save({
            "epoch": epoch,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "batch_size": self.current_batch_size,
            "best_val_loss": self.best_val_loss
        }, checkpoint_path)
        
        print(f"Checkpoint saved: {checkpoint_path}")


def main():
    """
    Main entry point for the optimized training loop.
    Demonstrates the training process with realistic parameters.
    """
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Optimized Training Loop for Memory Palaces")
    parser.add_argument("--model_name", type=str, default="gpt2-medium", help="Model name to use")
    parser.add_argument("--dataset_path", type=str, required=True, help="Path to dataset directory")
    parser.add_argument("--val_dataset_path", type=str, default=None, help="Path to validation dataset")
    parser.add_argument("--max_epochs", type=int, default=10, help="Maximum number of epochs")
    parser.add_argument("--batch_size", type=int, default=8, help="Initial batch size")
    parser.add_argument("--learning_rate", type=float, default=5e-5, help="Learning rate")
    parser.add_argument("--log_dir", type=str, default="artifacts/results", help="Directory for logs and artifacts")
    
    args = parser.parse_args()
    
    # Mock dataset for demonstration - in real usage, load actual dataset
    # This would be replaced with actual dataset loading from data/download.py
    class MockDataset(Dataset):
        def __init__(self, size=1000):
            self.size = size
            self.tokenizer = AutoTokenizer.from_pretrained("gpt2")
            
        def __len__(self):
            return self.size
        
        def __getitem__(self, idx):
            # Create a simple mock sequence
            text = f"This is sample text number {idx} for training purposes."
            encoding = self.tokenizer(text, return_tensors="pt", truncation=True, padding="max_length", max_length=128)
            return {
                "input_ids": encoding["input_ids"].squeeze(0),
                "attention_mask": encoding["attention_mask"].squeeze(0),
                "labels": encoding["input_ids"].squeeze(0)
            }
    
    print("Loading datasets...")
    train_dataset = MockDataset(size=1000)
    val_dataset = MockDataset(size=200) if args.val_dataset_path else None
    
    print("Initializing optimized training loop...")
    trainer = OptimizedTrainingLoop(
        model_name=args.model_name,
        dataset=train_dataset,
        val_dataset=val_dataset,
        max_epochs=args.max_epochs,
        initial_batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        log_dir=args.log_dir
    )
    
    print("Starting training...")
    summary = trainer.train()
    
    print("\nTraining Summary:")
    print(json.dumps(summary, indent=2))
    
    return summary


if __name__ == "__main__":
    main()