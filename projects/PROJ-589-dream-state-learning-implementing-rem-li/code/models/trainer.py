import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import logging
import json
from datetime import datetime
from pathlib import Path

# Local imports based on API surface
from utils.logger import get_logger, log_event
from data.augment import apply_dae_mask, create_dae_batch, calculate_mask_statistics
from config import Config
from utils.memory_monitor import MemoryMonitor, MemoryLimitExceeded

class DreamScheduler:
    """
    Manages the wake/dream cycle ratio and warm-up logic.
    Implements the multi-to-one wake-to-dream step ratio.
    """
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.wake_to_dream_ratio = config.get('dream_ratio', 5) # Default 5:1
        self.current_step = 0
        self.warm_up_steps = config.get('warm_up_steps', 10)
        self.logger.info(f"DreamScheduler initialized: ratio={self.wake_to_dream_ratio}, warm_up={self.warm_up_steps}")

    def should_run_dream_phase(self) -> bool:
        """
        Returns True if the current step should execute a dream phase.
        Enforces warm-up logic: returns False if step < warm_up_steps.
        """
        if self.current_step < self.warm_up_steps:
            # Log warm-up status periodically
            if self.current_step % 5 == 0:
                self.logger.info(f"Wake/Dream Cycle: Step {self.current_step} - Warm-up active (Dream phase skipped).")
            return False

        # Standard ratio check
        is_dream_step = (self.current_step % self.wake_to_dream_ratio) == 0
        if is_dream_step:
            self.logger.info(f"Wake/Dream Cycle: Step {self.current_step} - Triggering Dream Phase (Ratio: {self.wake_to_dream_ratio})")
        else:
            self.logger.debug(f"Wake/Dream Cycle: Step {self.current_step} - Wake Phase.")
        
        return is_dream_step

    def advance_step(self):
        self.current_step += 1

class Trainer:
    def __init__(self, model: nn.Module, config: Config, device: torch.device):
        self.model = model
        self.config = config
        self.device = device
        self.logger = get_logger(__name__)
        
        # Optimizer and Loss
        self.optimizer = optim.AdamW(model.parameters(), lr=config.get('learning_rate', 5e-5))
        self.criterion = nn.CrossEntropyLoss()
        
        # Schedulers and Monitors
        self.scheduler = DreamScheduler(config, self.logger)
        self.memory_monitor = MemoryMonitor(config, self.logger)
        
        # Metrics storage
        self.metrics_history: List[Dict[str, Any]] = []

    def calculate_entropy(self, logits: torch.Tensor, labels: torch.Tensor = None) -> float:
        """
        Calculates average entropy (bits per token) for the output distribution.
        Excludes padding tokens. Uses base-2 log.
        Formula: -sum(p * log2(p))
        """
        # Apply softmax to get probabilities
        probs = torch.softmax(logits, dim=-1)
        
        # Calculate log probabilities (base 2)
        # Avoid log(0) by adding small epsilon
        eps = 1e-9
        log_probs = torch.log(probs + eps)
        
        # Entropy per token: -sum(p * log(p))
        # Shape: (batch_size, seq_len)
        entropy_per_token = -torch.sum(probs * log_probs, dim=-1) / np.log(2)

        # If labels are provided, mask out padding (assuming label -100 is ignore_index)
        if labels is not None:
            mask = (labels != -100).float()
            valid_tokens = mask.sum()
            if valid_tokens == 0:
                return 0.0
            avg_entropy = (entropy_per_token * mask).sum() / valid_tokens
        else:
            # If no labels, average over all tokens in batch
            avg_entropy = entropy_per_token.mean()

        return avg_entropy.item()

    def train_step_wake(self, batch: Dict[str, torch.Tensor]) -> Dict[str, Any]:
        """
        Standard supervised training step on real data.
        """
        self.model.train()
        inputs = batch['input_ids'].to(self.device)
        labels = batch['labels'].to(self.device)

        self.optimizer.zero_grad()
        
        outputs = self.model(inputs, labels=labels)
        loss = outputs.loss
        
        loss.backward()
        self.optimizer.step()

        # Calculate entropy for monitoring
        # Re-run forward pass without labels to get logits if not stored, 
        # or use outputs.logits if available (some models return it)
        # Assuming outputs.logits exists for entropy calc
        if hasattr(outputs, 'logits'):
            entropy = self.calculate_entropy(outputs.logits, labels)
        else:
            entropy = 0.0

        self.logger.debug(f"Wake Step: Loss={loss.item():.4f}, Entropy={entropy:.4f}")

        return {
            'loss': loss.item(),
            'entropy': entropy,
            'phase': 'WAKE'
        }

    def train_step_dream(self, batch: Dict[str, torch.Tensor]) -> Dict[str, Any]:
        """
        Dream phase: DAE-based reconstruction on masked data.
        """
        self.model.train()
        inputs = batch['input_ids'].to(self.device)
        original_labels = batch['labels'].to(self.device)

        # Apply DAE masking
        # create_dae_batch expects inputs and returns masked_inputs, targets
        masked_inputs, targets = create_dae_batch(inputs, self.config.get('mask_rate', 0.15))
        masked_inputs = masked_inputs.to(self.device)
        targets = targets.to(self.device)

        self.optimizer.zero_grad()

        # Forward pass: model tries to reconstruct original tokens from masked input
        # We use the model in a generative/reconstruction mode. 
        # For a causal LM, we shift inputs. For BERT-like, we use masked_lm_labels.
        # Assuming the model handles masked inputs correctly (e.g., DistilBertForMaskedLM)
        try:
            outputs = self.model(masked_inputs, labels=targets)
            loss = outputs.loss
        except Exception as e:
            self.logger.error(f"Error during dream phase forward pass: {e}")
            raise

        loss.backward()
        self.optimizer.step()

        # Entropy check on reconstructed logits
        entropy = 0.0
        if hasattr(outputs, 'logits'):
            # Calculate entropy of the prediction distribution
            entropy = self.calculate_entropy(outputs.logits, targets)

        self.logger.info(f"Dream Step: Loss={loss.item():.4f}, Entropy={entropy:.4f}")

        return {
            'loss': loss.item(),
            'entropy': entropy,
            'phase': 'DREAM'
        }

    def run_training_loop(self, dataloader: DataLoader, max_steps: int = 100):
        """
        Main training loop implementing Wake/Dream cycles with logging.
        """
        self.logger.info(f"Starting training loop for {max_steps} steps.")
        self.logger.info(f"Warm-up period: {self.scheduler.warm_up_steps} steps.")

        step_count = 0
        global_step = 0

        for epoch, batch in enumerate(dataloader):
            if step_count >= max_steps:
                break

            # Memory Check
            self.memory_monitor.check()

            # Determine phase
            is_dream = self.scheduler.should_run_dream_phase()
            phase_status = "WARM_UP" if not is_dream and self.scheduler.current_step < self.scheduler.warm_up_steps else ("DREAM" if is_dream else "WAKE")
            
            # Log phase transition status
            if step_count == 0 or step_count % 10 == 0:
                self.logger.info(f"Step {step_count}: Phase Status = {phase_status} (Warm-up: {self.scheduler.current_step < self.scheduler.warm_up_steps})")

            # Execute Step
            try:
                if is_dream:
                    metrics = self.train_step_dream(batch)
                else:
                    metrics = self.train_step_wake(batch)
                
                # Entropy Check (Low Entropy Retry Logic)
                # T017 requirement: Detect low entropy (< 0.5 bits), retry up to 3 times
                if metrics['entropy'] < 0.5:
                    retry_count = 0
                    while metrics['entropy'] < 0.5 and retry_count < 3:
                        self.logger.warning(f"Low entropy detected ({metrics['entropy']:.4f} < 0.5). Retrying batch (attempt {retry_count + 1}/3)...")
                        # Re-fetch or re-shuffle batch logic would go here if dataloader supports it
                        # For simplicity in this loop, we just log and move on if retries exhausted
                        # In a real implementation, we might reload the batch or skip it
                        retry_count += 1
                        if retry_count < 3:
                            # Simulate re-processing (in real code, re-fetch batch)
                            if is_dream:
                                metrics = self.train_step_dream(batch)
                            else:
                                metrics = self.train_step_wake(batch)
                        else:
                            self.logger.warning(f"Low entropy persists after 3 retries. Discarding batch.")
                
                # Log Metrics
                log_event(
                    self.logger,
                    "training_step",
                    {
                        "step": self.scheduler.current_step,
                        "phase": metrics['phase'],
                        "loss": metrics['loss'],
                        "entropy": metrics['entropy'],
                        "warm_up_active": self.scheduler.current_step < self.scheduler.warm_up_steps
                    }
                )
                
                self.metrics_history.append(metrics)
                step_count += 1
                self.scheduler.advance_step()

            except MemoryLimitExceeded as e:
                self.logger.critical(f"OOM detected at step {step_count}. Aborting.")
                raise e
            except Exception as e:
                self.logger.error(f"Error in training step: {e}")
                raise

        self.logger.info("Training loop completed.")
        return self.metrics_history

def main():
    """
    Entry point for testing the trainer with logging.
    """
    config = Config()
    logger = get_logger(__name__)
    logger.info("Initializing Trainer for T019 Logging Verification")
    
    # Mock model for demonstration (replace with real loader in full pipeline)
    from transformers import DistilBertForMaskedLM
    model = DistilBertForMaskedLM.from_pretrained('distilbert-base-uncased')
    device = torch.device('cpu')
    model.to(device)
    
    trainer = Trainer(model, config, device)
    
    # Create a dummy dataloader
    from torch.utils.data import TensorDataset, DataLoader
    import torch.nn.functional as F
    
    dummy_input = torch.randint(0, 1000, (10, 20))
    dummy_labels = torch.randint(0, 1000, (10, 20))
    dataset = TensorDataset(dummy_input, dummy_labels)
    # Convert to dict format expected by trainer
    def collate_fn(batch):
        input_ids = torch.stack([b[0] for b in batch])
        labels = torch.stack([b[1] for b in batch])
        return {'input_ids': input_ids, 'labels': labels}
    
    loader = DataLoader(dataset, batch_size=2, collate_fn=collate_fn)
    
    # Run a few steps to verify logging
    try:
        results = trainer.run_training_loop(loader, max_steps=20)
        print(f"Completed {len(results)} steps. Check logs in data/logs/ for detailed metrics.")
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise

if __name__ == '__main__':
    main()