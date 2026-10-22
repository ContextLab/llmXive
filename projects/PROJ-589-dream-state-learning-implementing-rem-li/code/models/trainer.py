import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import logging
from pathlib import Path

# Local imports based on API surface
from utils.logger import get_logger, log_event
from data.augment import create_dae_batch
from config import Config
from utils.memory_monitor import MemoryMonitor, MemoryLimitExceeded

class DummyOptimizer:
    """
    A minimal optimizer that satisfies the optimizer interface used in the
    training loop but performs no parameter updates. This is primarily
    intended for unit‑test scenarios where a mock model has no learnable
    parameters.
    """
    def __init__(self):
        pass

    def zero_grad(self):
        # No parameters to zero‑out
        pass

    def step(self):
        # No parameters to update
        pass

class DreamScheduler:
    """
    Manages the wake/dream cycle ratio and warm‑up logic.
    Implements the multi‑to‑one wake‑to‑dream step ratio and
    perplexity‑based skipping of dream steps.
    """
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.wake_to_dream_ratio = config.get('dream_ratio', 5)
        self.current_step = 0
        self.warm_up_steps = config.get('warm_up_steps', 20)
        self.perplexity_skip_threshold = config.get('perplexity_skip_threshold', 50.0)
        self.logger.info(
            f"DreamScheduler initialized: ratio={self.wake_to_dream_ratio}, warm_up={self.warm_up_steps}, "
            f"perplexity_skip={self.perplexity_skip_threshold}"
        )

    def should_run_dream_phase(self) -> bool:
        if self.current_step < self.warm_up_steps:
            return False
        # Dream step occurs when the step index is a multiple of the total cycle length
        return (self.current_step % self.wake_to_dream_ratio) == 0

    def advance_step(self):
        self.current_step += 1

    def maybe_skip_dream_due_to_perplexity(self, model: nn.Module, held_out_batch: Dict[str, torch.Tensor]) -> bool:
        model.eval()
        with torch.no_grad():
            inputs = held_out_batch['input_ids'].to(self.config.device)
            labels = held_out_batch['labels'].to(self.config.device)
            outputs = model(inputs, labels=labels)
            loss = outputs.loss.item()
            perplexity = np.exp(loss)
            self.logger.info(
                f"Perplexity check on held‑out batch: {perplexity:.2f} (threshold {self.perplexity_skip_threshold})"
            )
            return perplexity > self.perplexity_skip_threshold

class Trainer:
    """
    Core training engine implementing wake/dream cycles,
    BERT‑style masking, DAE reconstruction, knowledge‑distillation,
    entropy‑based retry (only for dream phases), and perplexity‑based dream skipping.
    """
    def __init__(
        self,
        model: nn.Module,
        config: Config,
        device: torch.device,
        tokenizer: Optional[Any] = None
    ):
        self.model = model
        self.config = config
        self.device = device
        self.tokenizer = tokenizer
        self.logger = get_logger(__name__, config=config, log_to_file=False)

        # Initialise optimizer – handle models with no parameters (e.g., mocks)
        try:
            self.optimizer = optim.AdamW(model.parameters(), lr=config.get('learning_rate', 5e-5))
        except ValueError:
            # Model has no parameters; fall back to a no‑op optimizer
            self.logger.warning("Model has no parameters; using DummyOptimizer.")
            self.optimizer = DummyOptimizer()

        self.ce_criterion = nn.CrossEntropyLoss(ignore_index=-100)

        self.kd_temperature = config.get('kd_temperature', 1.0)
        self.kd_alpha = config.get('kd_alpha', 0.5)
        self.kldiv_loss = nn.KLDivLoss(reduction='batchmean')

        self.scheduler = DreamScheduler(config, self.logger)

        # Initialise the memory monitor with the configured limit
        limit_kb = config.memory_limit_bytes // 1024
        checkpoint_dir = config.get('checkpoint_dir', 'data/checkpoints')
        self.memory_monitor = MemoryMonitor(limit_kb, checkpoint_dir)

        self.metrics_history: List[Dict[str, Any]] = []

    def calculate_entropy(self, logits: torch.Tensor, labels: Optional[torch.Tensor] = None) -> float:
        probs = torch.softmax(logits, dim=-1)
        eps = 1e-9
        log_probs = torch.log(probs + eps)
        entropy_per_token = -torch.sum(probs * log_probs, dim=-1) / np.log(2)

        if labels is not None:
            mask = (labels != -100).float()
            valid_tokens = mask.sum()
            if valid_tokens == 0:
                return 0.0
            avg_entropy = (entropy_per_token * mask).sum() / valid_tokens
        else:
            avg_entropy = entropy_per_token.mean()
        return avg_entropy.item()

    def _knowledge_distillation_loss(self, student_logits: torch.Tensor, teacher_logits: torch.Tensor) -> torch.Tensor:
        T = self.kd_temperature
        student_log_probs = F.log_softmax(student_logits / T, dim=-1)
        teacher_probs = F.softmax(teacher_logits / T, dim=-1)
        kd_loss = self.kldiv_loss(student_log_probs, teacher_probs) * (T * T)
        return kd_loss

    def train_step_wake(self, batch: Dict[str, torch.Tensor]) -> Dict[str, Any]:
        self.model.train()
        inputs = batch['input_ids'].to(self.device)
        labels = batch['labels'].to(self.device)

        self.optimizer.zero_grad()
        outputs = self.model(inputs, labels=labels)
        loss = outputs.loss
        loss.backward()
        self.optimizer.step()

        entropy = self.calculate_entropy(outputs.logits, labels) if hasattr(outputs, 'logits') else 0.0
        return {'loss': loss.item(), 'entropy': entropy, 'phase': 'WAKE'}

    def train_step_dream(self, batch: Dict[str, torch.Tensor], held_out_batch: Optional[Dict[str, torch.Tensor]] = None) -> Dict[str, Any]:
        # Perplexity‑based skipping (only evaluated for dream phases)
        if held_out_batch is not None and self.scheduler.maybe_skip_dream_due_to_perplexity(self.model, held_out_batch):
            return {'loss': 0.0, 'entropy': 0.0, 'phase': 'DREAM_SKIPPED'}

        self.model.train()
        inputs = batch['input_ids'].to(self.device)
        original_labels = batch['labels'].to(self.device)

        # Create DAE‑style masked inputs and targets
        masked_inputs_list, _, targets_list = create_dae_batch(
            inputs.tolist(),
            mask_rate=self.config.get('mask_rate', 0.15)
        )
        masked_inputs = torch.tensor(masked_inputs_list, dtype=torch.long, device=self.device)
        targets = torch.tensor(targets_list, dtype=torch.long, device=self.device)

        self.optimizer.zero_grad()

        student_outputs = self.model(masked_inputs, labels=targets)
        recon_loss = student_outputs.loss

        with torch.no_grad():
            teacher_outputs = self.model(inputs, labels=original_labels)
            teacher_logits = teacher_outputs.logits

        kd_loss = self._knowledge_distillation_loss(student_outputs.logits, teacher_logits)
        loss = self.kd_alpha * recon_loss + (1 - self.kd_alpha) * kd_loss

        loss.backward()
        self.optimizer.step()

        entropy = self.calculate_entropy(student_outputs.logits, targets) if hasattr(student_outputs, 'logits') else 0.0
        return {'loss': loss.item(), 'entropy': entropy, 'phase': 'DREAM'}

    def run_training_loop(self, dataloader: DataLoader, max_steps: int = 100) -> List[Dict[str, Any]]:
        self.logger.info(f"Starting training loop for {max_steps} steps.")

        step_count = 0
        held_out_batch = None
        if self.config.get('held_out_subset'):
            try:
                from data.loader import load_glue_subset
                subset = load_glue_subset(self.config.get('held_out_subset'))
                sample = subset['validation'][:self.config.get('held_out_batch_size', 8)]
                held_out_batch = {
                    'input_ids': torch.tensor(sample['input_ids']),
                    'labels': torch.tensor(sample['label'])
                }
            except Exception as e:
                self.logger.warning(f"Could not load held‑out subset for perplexity check: {e}")

        for batch in dataloader:
            if step_count >= max_steps:
                break

            # Enforce memory cap before each step
            self.memory_monitor.enforce()
            is_dream = self.scheduler.should_run_dream_phase()

            try:
                if is_dream:
                    metrics = self.train_step_dream(batch, held_out_batch)
                else:
                    metrics = self.train_step_wake(batch)

                # Entropy‑based retry only for dream phases
                if is_dream and metrics['entropy'] < self.config.get('entropy_threshold', 0.5):
                    retry_count = 0
                    while metrics['entropy'] < self.config.get('entropy_threshold', 0.5) and retry_count < self.config.get('max_retries', 3):
                        self.logger.warning(f"Low entropy ({metrics['entropy']:.4f} < {self.config.get('entropy_threshold')}) during DREAM – retry {retry_count+1}")
                        retry_count += 1
                        metrics = self.train_step_dream(batch, held_out_batch)

                # Log structured event
                log_event(self.logger, "training_step", {
                    "step": self.scheduler.current_step,
                    "phase": metrics['phase'],
                    "loss": metrics['loss'],
                    "entropy": metrics['entropy']
                })

                self.metrics_history.append(metrics)
                step_count += 1
                self.scheduler.advance_step()

            except MemoryLimitExceeded as e:
                self.logger.critical(f"OOM detected at step {step_count}. Aborting.")
                raise e
            except Exception as e:
                self.logger.error(f"Error in training step: {e}")
                raise

        return self.metrics_history
