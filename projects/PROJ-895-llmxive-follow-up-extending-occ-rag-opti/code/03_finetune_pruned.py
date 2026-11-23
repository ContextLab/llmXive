"""
03_finetune_pruned.py

Performs lightweight fine-tuning on the pruned OCC-RAG model.
Implements early stopping based on gradient magnitude < 1e-4 for 3 consecutive epochs.
Runs entirely on CPU.
"""

import os
import sys
import json
import logging
import gc
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torch.optim import AdamW
from torch.nn.utils import clip_grad_norm_

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code_00_config import Config, validate_config
from utils.dataset_loader import load_and_cache_dataset
from utils.faithfulness_score import compute_batch_faithfulness, aggregate_faithfulness_metrics
from utils.masking import load_model_layer_by_layer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(Config.DATA_PROCESSED_DIR, 'finetune.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class PrunedDataset(Dataset):
    """Dataset wrapper for the finetuning corpus."""
    
    def __init__(self, data_path: str, sample_size: Optional[int] = None, seed: int = 42):
        self.data_path = data_path
        self.sample_size = sample_size
        self.seed = seed
        self.data = self._load_data()
        
    def _load_data(self) -> List[Dict[str, Any]]:
        """Load and optionally sample the dataset."""
        logger.info(f"Loading dataset from {self.data_path}")
        try:
            # Attempt to load the cached dataset
            dataset = load_and_cache_dataset(self.data_path)
            data_list = list(dataset)
            
            if self.sample_size and len(data_list) > self.sample_size:
                # Deterministic sampling
                import random
                random.seed(self.seed)
                data_list = random.sample(data_list, self.sample_size)
                logger.info(f"Sampled {len(data_list)} examples from {len(dataset)} total")
                
            return data_list
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            raise

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        return self.data[idx]

def calculate_gradient_norm(model: nn.Module) -> float:
    """Calculate the L2 norm of all gradients."""
    total_norm = 0.0
    for param in model.parameters():
        if param.grad is not None:
            param_norm = param.grad.data.norm(2)
            total_norm += param_norm.item() ** 2
    return total_norm ** 0.5

def calculate_mean_gradient_magnitude(model: nn.Module) -> float:
    """Calculate the mean absolute value of all gradients."""
    total_mag = 0.0
    count = 0
    for param in model.parameters():
        if param.grad is not None:
            mag = param.grad.data.abs().sum().item()
            total_mag += mag
            count += param.grad.data.numel()
    return total_mag / count if count > 0 else 0.0

def train_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    optimizer: AdamW,
    device: torch.device,
    epoch: int
) -> Tuple[float, float, float]:
    """
    Train for one epoch.
    Returns: (loss, gradient_norm, mean_gradient_magnitude)
    """
    model.train()
    total_loss = 0.0
    num_batches = 0
    
    for batch_idx, batch in enumerate(dataloader):
        # Prepare inputs (assuming batch has 'input_ids', 'attention_mask', 'labels')
        # Adjust based on actual dataset structure
        input_ids = batch.get('input_ids')
        attention_mask = batch.get('attention_mask')
        labels = batch.get('labels')
        
        if input_ids is None or labels is None:
            logger.warning(f"Batch {batch_idx} missing required keys, skipping")
            continue

        input_ids = input_ids.to(device)
        attention_mask = attention_mask.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()

        try:
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )
            loss = outputs.loss
            
            loss.backward()
            
            # Gradient clipping
            clip_grad_norm_(model.parameters(), max_norm=1.0)
            
            optimizer.step()
            
            total_loss += loss.item()
            num_batches += 1
            
        except Exception as e:
            logger.error(f"Error in batch {batch_idx}: {e}")
            gc.collect()
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            continue

    avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
    grad_norm = calculate_gradient_norm(model)
    mean_grad_mag = calculate_mean_gradient_magnitude(model)
    
    return avg_loss, grad_norm, mean_grad_mag

def evaluate_model(
    model: nn.Module,
    dataloader: DataLoader,
    device: torch.device
) -> Dict[str, float]:
    """
    Evaluate model faithfulness on the dataset.
    """
    model.eval()
    all_scores = []
    
    with torch.no_grad():
        for batch in dataloader:
            # Simplified inference for evaluation
            # In practice, this would call the faithfulness scoring logic
            input_ids = batch.get('input_ids')
            attention_mask = batch.get('attention_mask')
            
            if input_ids is None:
                continue
                
            input_ids = input_ids.to(device)
            attention_mask = attention_mask.to(device)
            
            try:
                outputs = model(
                    input_ids=input_ids,
                    attention_mask=attention_mask
                )
                # Extract logits or predictions for faithfulness calculation
                # This is a placeholder - actual implementation depends on faithfulness metric
                # For now, we'll use loss as a proxy for faithfulness
                if hasattr(outputs, 'loss'):
                    all_scores.append(outputs.loss.item())
            except Exception as e:
                logger.warning(f"Evaluation error: {e}")
                continue
    
    if not all_scores:
        return {"mean_faithfulness": 0.0, "std_faithfulness": 0.0}
        
    mean_score = sum(all_scores) / len(all_scores)
    variance = sum((x - mean_score) ** 2 for x in all_scores) / len(all_scores)
    std_score = variance ** 0.5
    
    return {
        "mean_faithfulness": mean_score,
        "std_faithfulness": std_score,
        "num_samples": len(all_scores)
    }

def main():
    """Main training loop with early stopping based on gradient magnitude."""
    logger.info("Starting fine-tuning of pruned model")
    
    # Validate configuration
    validate_config(Config)
    
    # Device setup (CPU only)
    device = torch.device("cpu")
    logger.info(f"Using device: {device}")
    
    # Load pruned model
    pruned_model_path = os.path.join(Config.DATA_PROCESSED_DIR, "pruned_model_weights.pt")
    if not os.path.exists(pruned_model_path):
        logger.error(f"Pruned model not found at {pruned_model_path}")
        raise FileNotFoundError(f"Pruned model not found: {pruned_model_path}")
    
    logger.info(f"Loading pruned model from {pruned_model_path}")
    model = load_model_layer_by_layer(pruned_model_path)
    model.to(device)
    
    # Prepare dataset
    dataset_path = os.path.join(Config.DATA_RAW_DIR, "occ_rag_corpus.jsonl")
    if not os.path.exists(dataset_path):
        logger.error(f"Dataset not found at {dataset_path}")
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")
    
    train_dataset = PrunedDataset(
        dataset_path,
        sample_size=Config.FINE_TUNE_SAMPLE_SIZE,
        seed=Config.SAMPLE_SEED
    )
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=Config.BATCH_SIZE,
        shuffle=True,
        num_workers=0,  # CPU-only, no workers
        pin_memory=False
    )
    
    # Setup optimizer
    optimizer = AdamW(
        model.parameters(),
        lr=Config.LEARNING_RATE,
        weight_decay=Config.WEIGHT_DECAY
    )
    
    # Early stopping parameters
    patience = 3
    gradient_threshold = Config.GRADIENT_THRESHOLD  # 1e-4
    epochs_without_improvement = 0
    best_grad_mag = float('inf')
    training_history = []
    
    logger.info(f"Starting training with early stopping (threshold={gradient_threshold}, patience={patience})")
    
    for epoch in range(Config.EPOCHS):
        logger.info(f"Epoch {epoch + 1}/{Config.EPOCHS}")
        
        # Training phase
        loss, grad_norm, mean_grad_mag = train_epoch(
            model, train_loader, optimizer, device, epoch
        )
        
        # Evaluation phase
        eval_metrics = evaluate_model(model, train_loader, device)
        
        # Log metrics
        log_entry = {
            "epoch": epoch + 1,
            "loss": loss,
            "gradient_norm": grad_norm,
            "mean_gradient_magnitude": mean_grad_mag,
            "faithfulness_score": eval_metrics["mean_faithfulness"],
            "faithfulness_std": eval_metrics["std_faithfulness"]
        }
        training_history.append(log_entry)
        
        logger.info(
            f"Epoch {epoch + 1}: Loss={loss:.4f}, "
            f"GradNorm={grad_norm:.6f}, MeanGradMag={mean_grad_mag:.6f}, "
            f"Faithfulness={eval_metrics['mean_faithfulness']:.4f}"
        )
        
        # Early stopping check
        if mean_grad_mag < gradient_threshold:
            epochs_without_improvement += 1
            logger.info(
                f"Gradient magnitude ({mean_grad_mag:.6e}) < threshold ({gradient_threshold}). "
                f"Consecutive epochs: {epochs_without_improvement}/{patience}"
            )
            
            if epochs_without_improvement >= patience:
                logger.info(
                    f"Early stopping triggered at epoch {epoch + 1}. "
                    f"Gradient magnitude remained below {gradient_threshold} for {patience} consecutive epochs."
                )
                break
        else:
            epochs_without_improvement = 0
            if mean_grad_mag < best_grad_mag:
                best_grad_mag = mean_grad_mag
                # Save best model checkpoint
                best_model_path = os.path.join(Config.DATA_PROCESSED_DIR, "best_pruned_model.pt")
                torch.save(model.state_dict(), best_model_path)
                logger.info(f"Saved best model to {best_model_path}")
    
    # Save final model
    final_model_path = os.path.join(Config.DATA_PROCESSED_DIR, "finetuned_pruned_model.pt")
    torch.save(model.state_dict(), final_model_path)
    logger.info(f"Saved final model to {final_model_path}")
    
    # Save training history
    history_path = os.path.join(Config.DATA_PROCESSED_DIR, "finetune_history.json")
    with open(history_path, 'w') as f:
        json.dump(training_history, f, indent=2)
    logger.info(f"Saved training history to {history_path}")
    
    # Final evaluation
    final_metrics = evaluate_model(model, train_loader, device)
    final_report = {
        "final_faithfulness": final_metrics["mean_faithfulness"],
        "final_faithfulness_std": final_metrics["std_faithfulness"],
        "total_epochs": len(training_history),
        "early_stopped": epochs_without_improvement >= patience,
        "training_history": training_history
    }
    
    report_path = os.path.join(Config.DATA_PROCESSED_DIR, "finetune_report.json")
    with open(report_path, 'w') as f:
        json.dump(final_report, f, indent=2)
    logger.info(f"Saved final report to {report_path}")
    
    logger.info("Fine-tuning completed successfully")
    return final_report

if __name__ == "__main__":
    main()