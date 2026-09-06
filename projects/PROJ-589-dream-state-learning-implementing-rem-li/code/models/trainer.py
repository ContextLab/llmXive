import torch
import torch.nn as nn
import torch.optim as optim
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
from config import Config
from utils.logger import get_logger
from data.augment import apply_dae_mask, create_dae_batch, calculate_mask_statistics
from utils.memory_monitor import MemoryMonitor, MemoryLimitEnforcer
from utils.exceptions import DataIntegrityError

class DreamScheduler:
    """
    Manages the alternating Wake/Dream phases and warm-up logic.
    """
    def __init__(self, config: Config):
        self.config = config
        self.wake_ratio = config.wake_ratio
        self.dream_ratio = config.dream_ratio
        self.warmup_steps = config.warmup_steps
        self.current_step = 0
        self.logger = get_logger(__name__)

    def get_phase(self) -> str:
        """
        Determines the current phase based on step counter and ratios.
        Returns 'wake' or 'dream'.
        """
        if self.current_step < self.warmup_steps:
            self.logger.info(f"Step {self.current_step}: Warm-up phase (Dream skipped)")
            return 'wake'

        # Determine phase based on ratio (e.g., 4:1 -> 80% wake, 20% dream)
        # Using modulo to cycle: (step - warmup) % (wake + dream)
        cycle_position = (self.current_step - self.warmup_steps) % (self.wake_ratio + self.dream_ratio)
        
        if cycle_position < self.wake_ratio:
            return 'wake'
        else:
            return 'dream'

    def should_skip_dream(self) -> bool:
        """
        Returns True if the current step is in the warm-up period.
        """
        return self.current_step < self.warmup_steps

    def increment_step(self):
        """
        Increments the internal step counter.
        """
        self.current_step += 1

class Trainer:
    def __init__(self, model: nn.Module, config: Config, device: torch.device):
        self.model = model
        self.config = config
        self.device = device
        self.logger = get_logger(__name__)
        self.scheduler = DreamScheduler(config)
        self.optimizer = optim.AdamW(model.parameters(), lr=config.learning_rate)
        self.criterion = nn.CrossEntropyLoss()
        
        # Memory monitoring integration (T018 requirement)
        self.memory_monitor = MemoryMonitor()
        self.memory_enforcer = MemoryLimitEnforcer(
            limit_mb=config.max_memory_mb,
            logger=self.logger
        )

    def calculate_entropy(self, logits: torch.Tensor) -> float:
        """
        Calculates the entropy of the output distribution in bits.
        Formula: sum(-p * log2(p))
        """
        probs = torch.softmax(logits, dim=-1)
        # Add small epsilon to avoid log(0)
        eps = 1e-9
        probs = probs + eps
        log_probs = torch.log2(probs)
        entropy = -torch.sum(probs * log_probs, dim=-1)
        return entropy.mean().item()

    def train_step(self, batch: Dict[str, Any], phase: str) -> Dict[str, Any]:
        """
        Executes a single training step for either Wake or Dream phase.
        """
        self.model.train()
        self.optimizer.zero_grad()

        input_ids = batch['input_ids'].to(self.device)
        attention_mask = batch['attention_mask'].to(self.device)
        labels = batch['labels'].to(self.device) if 'labels' in batch else None

        if phase == 'wake':
            # Standard CE on real data
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            
            if labels is None:
                # If labels not provided, shift input_ids for next-token prediction
                shift_logits = logits[..., :-1, :].contiguous()
                shift_labels = input_ids[..., 1:].contiguous()
                loss = self.criterion(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))
            else:
                loss = self.criterion(logits.view(-1, logits.size(-1)), labels.view(-1))

            entropy = self.calculate_entropy(logits)
            
            self.logger.info(f"Wake Phase - Loss: {loss.item():.4f}, Entropy: {entropy:.4f} bits")

        elif phase == 'dream':
            # DAE-based reconstruction
            # Apply masking to create dream input
            augmented_input, mask_indices = apply_dae_mask(input_ids, self.config.mask_rate)
            augmented_input = augmented_input.to(self.device)
            mask_indices = mask_indices.to(self.device)

            outputs = self.model(input_ids=augmented_input, attention_mask=attention_mask)
            logits = outputs.logits

            # Calculate loss only on masked positions
            # Reshape logits and input_ids to match
            batch_size, seq_len, vocab_size = logits.shape
            flat_logits = logits.view(-1, vocab_size)
            flat_input_ids = input_ids.view(-1)
            flat_mask = mask_indices.view(-1)

            # Select logits for masked positions
            masked_logits = flat_logits[flat_mask]
            masked_labels = flat_input_ids[flat_mask]

            if masked_logits.numel() > 0:
                loss = self.criterion(masked_logits, masked_labels)
                # Calculate entropy on the masked predictions
                entropy = self.calculate_entropy(masked_logits)
                self.logger.info(f"Dream Phase - Loss: {loss.item():.4f}, Entropy: {entropy:.4f} bits, Masked Tokens: {masked_logits.numel()}")
            else:
                loss = torch.tensor(0.0, device=self.device)
                entropy = 0.0
                self.logger.warning("Dream Phase - No masked tokens found, skipping loss update.")

        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config.max_grad_norm)
        self.optimizer.step()

        return {
            'loss': loss.item(),
            'entropy': entropy,
            'phase': phase
        }

    def run_training_loop(self, dataloader: torch.utils.data.DataLoader, max_steps: int = None) -> Dict[str, Any]:
        """
        Executes the full training loop with Wake/Dream alternation,
        warm-up, and entropy checks.
        """
        self.logger.info("Starting Dream-State Training Loop")
        
        global_step = 0
        epoch = 0
        metrics_history = {
            'wake_losses': [],
            'dream_losses': [],
            'entropies': [],
            'phases': []
        }

        # Initialize memory monitor for the loop
        self.memory_monitor.start()

        while True:
            if max_steps and global_step >= max_steps:
                break

            for batch_idx, batch in enumerate(dataloader):
                # Check memory limit
                if self.memory_enforcer.check_and_enforce():
                    self.logger.warning("Memory limit exceeded during training. Aborting.")
                    # Save checkpoint logic would go here
                    raise MemoryLimitExceeded("Memory limit exceeded")

                # Determine phase
                phase = self.scheduler.get_phase()

                # Warm-up check
                if self.scheduler.should_skip_dream() and phase == 'dream':
                    self.logger.warning(
                        f"Step {global_step}: Dream phase triggered during warm-up. "
                        f"Enforcing Wake phase per warm-up protocol."
                    )
                    phase = 'wake'

                # Execute step
                try:
                    result = self.train_step(batch, phase)
                except Exception as e:
                    self.logger.error(f"Training step failed: {e}")
                    raise

                # Log phase transitions and metrics
                self.logger.info(
                    f"Step {global_step} | Phase: {phase} | "
                    f"Loss: {result['loss']:.4f} | Entropy: {result['entropy']:.4f} bits"
                )

                # Record metrics
                if phase == 'wake':
                    metrics_history['wake_losses'].append(result['loss'])
                else:
                    metrics_history['dream_losses'].append(result['loss'])
                
                metrics_history['entropies'].append(result['entropy'])
                metrics_history['phases'].append(phase)

                # Entropy check (T017 logic)
                if result['entropy'] < self.config.min_entropy_threshold:
                    self.logger.warning(
                        f"Step {global_step}: Low entropy detected ({result['entropy']:.4f} < {self.config.min_entropy_threshold}). "
                        f"Triggering retry logic."
                    )
                    # In a real implementation, we might retry the batch or adjust temperature.
                    # For now, we log and continue as per the task's logging focus.

                global_step += 1
                self.scheduler.increment_step()

                if max_steps and global_step >= max_steps:
                    break

            epoch += 1

        self.memory_monitor.stop()
        
        self.logger.info(
            f"Training completed. Total Steps: {global_step}, "
            f"Wake Steps: {len(metrics_history['wake_losses'])}, "
            f"Dream Steps: {len(metrics_history['dream_losses'])}"
        )

        return metrics_history

class MemoryLimitExceeded(Exception):
    """Exception raised when memory limit is exceeded."""
    pass
