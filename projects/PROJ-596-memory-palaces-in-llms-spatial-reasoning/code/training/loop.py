import gc
import json
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import torch
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer

# Import from project API surface
from models.loading import load_model, check_memory_budget
from models.spatial import soft_addressed_retrieve, weighted_chunk_aggregation, spatial_attention_loss
from models.memory_slot import MemoryGrid
from models.episodic_chunk import EpisodicChunk
from training.memory_monitor import MemoryMonitor, get_current_memory_usage_gb
from data.capper import cap_dataset_by_memory
from utils.logger import ExperimentLogger, get_logger_for_run

# Enforce single-core execution as per project constraints
os.environ["OMP_NUM_THREADS"] = "1"
torch.set_num_threads(1)

class OptimizedTrainingLoop:
    """
    Training loop skeleton for the Memory Palace experiment.
    Implements basic forward/backward pass with integration points for
    memory monitoring (T005a), dataset capping (T005b), and spatial logic (T013/T036).
    """

    def __init__(
        self,
        model_variant: str,
        dataset_name: str,
        seed: int,
        max_epochs: int = 3,
        initial_batch_size: int = 4,
        memory_threshold_gb: float = 6.0,
        log_dir: Optional[Path] = None
    ):
        self.model_variant = model_variant
        self.dataset_name = dataset_name
        self.seed = seed
        self.max_epochs = max_epochs
        self.batch_size = initial_batch_size
        self.memory_threshold_gb = memory_threshold_gb
        self.log_dir = log_dir or Path("artifacts/results")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.logger = get_logger_for_run(self.log_dir, f"{dataset_name}_{model_variant}_seed{seed}")
        self.memory_monitor = MemoryMonitor(log_path=self.log_dir / "memory_log.json")
        
        # Set device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.logger.log_info(f"Running on device: {self.device}")

        # Load model
        self.model, self.tokenizer = self._load_model()
        
        # Prepare dataset (with capping logic)
        self.train_dataset = self._prepare_dataset()
        self.train_loader = DataLoader(
            self.train_dataset, 
            batch_size=self.batch_size, 
            shuffle=True,
            num_workers=0  # Single core constraint
        )

        self.optimizer = torch.optim.AdamW(self.model.parameters(), lr=1e-5)
        self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(self.optimizer, T_max=self.max_epochs)

    def _load_model(self) -> Tuple[Any, Any]:
        """Load model using the project's loading utility."""
        try:
            model, tokenizer = load_model(self.model_variant, self.device)
            self.logger.log_info(f"Successfully loaded model: {self.model_variant}")
            return model, tokenizer
        except Exception as e:
            self.logger.log_error(f"Failed to load model: {e}")
            raise

    def _prepare_dataset(self) -> Dataset:
        """
        Prepare dataset with memory-based capping.
        This integrates T005b (capper) logic.
        """
        # Placeholder for actual dataset loading logic
        # In a real implementation, this would call code/data/download.py logic
        # and then apply cap_dataset_by_memory
        from datasets import load_dataset
        
        try:
            # Load real dataset
            if self.dataset_name == "babi_task3":
                raw_ds = load_dataset("babi", "task3_10k", split="train")
            else:
                raise ValueError(f"Unsupported dataset: {self.dataset_name}")
            
            # Apply memory capping if RSS > threshold at initial batch size
            capped_ds = cap_dataset_by_memory(
                raw_ds, 
                batch_size=self.batch_size,
                memory_threshold_gb=self.memory_threshold_gb,
                logger=self.logger
            )
            
            self.logger.log_info(f"Dataset capped to {len(capped_ds)} samples")
            return capped_ds
            
        except Exception as e:
            self.logger.log_error(f"Dataset preparation failed: {e}")
            raise

    def _create_episodic_chunk(self, batch: Dict[str, torch.Tensor]) -> EpisodicChunk:
        """Convert a batch into an EpisodicChunk for spatial processing."""
        # Simplified chunk creation for the loop skeleton
        # In full implementation, this would extract semantic features
        return EpisodicChunk(
            content=batch["input_ids"],
            attention_mask=batch["attention_mask"],
            metadata={"batch_size": batch["input_ids"].size(0)}
        )

    def train_epoch(self, epoch: int) -> Dict[str, float]:
        """Train for one epoch with memory monitoring and spatial logic."""
        self.model.train()
        total_loss = 0.0
        batch_count = 0
        
        for step, batch in enumerate(self.train_loader):
            batch = {k: v.to(self.device) for k, v in batch.items()}
            
            # Memory check before forward pass
            current_rss = get_current_memory_usage_gb()
            if current_rss > self.memory_threshold_gb:
                self.logger.log_warning(f"RSS {current_rss:.2f}GB > threshold. Reducing batch size.")
                self._reduce_batch_size()
                # Re-create loader with new batch size
                self.train_loader = DataLoader(
                    self.train_dataset,
                    batch_size=self.batch_size,
                    shuffle=True,
                    num_workers=0
                )
                # Restart epoch with new loader
                return self.train_epoch(epoch)
            
            self.optimizer.zero_grad()
            
            # Create episodic chunk for spatial processing
            chunk = self._create_episodic_chunk(batch)
            
            # Forward pass with spatial memory integration
            # This is where T013/T036 logic is invoked
            try:
                outputs = self.model(
                    input_ids=batch["input_ids"],
                    attention_mask=batch["attention_mask"],
                    labels=batch.get("labels")  # bAbI task labels
                )
                loss = outputs.loss
                
                # Apply spatial attention loss if available
                if hasattr(self.model, 'memory_grid') and self.model.memory_grid is not None:
                    spatial_loss = spatial_attention_loss(
                        self.model.memory_grid,
                        chunk,
                        self.tokenizer
                    )
                    loss = loss + 0.1 * spatial_loss  # Weighted combination
                    
            except Exception as e:
                self.logger.log_error(f"Forward pass failed: {e}")
                raise
            
            # Backward pass
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item()
            batch_count += 1
            
            # Log batch metrics
            if step % 10 == 0:
                self.logger.log_info(f"Epoch {epoch}, Batch {step}, Loss: {loss.item():.4f}")
                
                # Memory monitoring
                self.memory_monitor.record_batch(batch_count, get_current_memory_usage_gb())
                
            # Garbage collection
            if step % 50 == 0:
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
        
        avg_loss = total_loss / batch_count if batch_count > 0 else 0.0
        return {"epoch_loss": avg_loss, "batch_count": batch_count}

    def _reduce_batch_size(self):
        """Reduce batch size when memory threshold is exceeded."""
        if self.batch_size > 1:
            self.batch_size = max(1, self.batch_size // 2)
            self.logger.log_info(f"Reduced batch size to {self.batch_size}")
        else:
            raise RuntimeError("Batch size already at minimum (1) but memory threshold exceeded.")

    def run(self) -> Dict[str, Any]:
        """Run the full training loop."""
        self.logger.log_info(f"Starting training for {self.max_epochs} epochs")
        start_time = time.time()
        
        epoch_results = []
        for epoch in range(self.max_epochs):
            self.logger.log_info(f"Starting epoch {epoch + 1}/{self.max_epochs}")
            result = self.train_epoch(epoch + 1)
            epoch_results.append(result)
            self.scheduler.step()
            
            # Save checkpoint
            checkpoint_path = self.log_dir / f"checkpoint_epoch_{epoch+1}.pt"
            torch.save({
                "epoch": epoch,
                "model_state_dict": self.model.state_dict(),
                "optimizer_state_dict": self.optimizer.state_dict(),
                "batch_size": self.batch_size,
            }, checkpoint_path)
            self.logger.log_info(f"Saved checkpoint to {checkpoint_path}")
        
        total_time = time.time() - start_time
        
        # Final summary
        summary = {
            "model_variant": self.model_variant,
            "dataset": self.dataset_name,
            "seed": self.seed,
            "epochs_completed": len(epoch_results),
            "final_batch_size": self.batch_size,
            "total_time_seconds": total_time,
            "epoch_losses": [r["epoch_loss"] for r in epoch_results],
            "memory_log_path": str(self.memory_monitor.log_path)
        }
        
        # Save summary
        summary_path = self.log_dir / "training_summary.json"
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)
        
        self.logger.log_info(f"Training complete. Summary saved to {summary_path}")
        return summary

def main():
    """Entry point for training loop execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Train Memory Palace model")
    parser.add_argument("--model_variant", type=str, default="spatial", help="Model variant to train")
    parser.add_argument("--dataset", type=str, default="babi_task3", help="Dataset to use")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--epochs", type=int, default=3, help="Number of epochs")
    parser.add_argument("--batch_size", type=int, default=4, help="Initial batch size")
    parser.add_argument("--log_dir", type=str, default="artifacts/results", help="Logging directory")
    
    args = parser.parse_args()
    
    loop = OptimizedTrainingLoop(
        model_variant=args.model_variant,
        dataset_name=args.dataset,
        seed=args.seed,
        max_epochs=args.epochs,
        initial_batch_size=args.batch_size,
        log_dir=Path(args.log_dir)
    )
    
    summary = loop.run()
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()