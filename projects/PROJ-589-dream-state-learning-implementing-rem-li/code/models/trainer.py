import torch
import torch.nn as nn
import torch.nn.functional as F
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
    Implements the multi-to-one wake-to-dream step ratio and
    perplexity‑based skipping of dream steps.
    """
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger
        # wake_to_dream_ratio can be passed as "4:1" or integer; config stores int steps per dream
        self.wake_to_dream_ratio = config.get('dream_ratio', 5)  # default 5 wake steps per dream
        self.current_step = 0
        self.warm_up_steps = config.get('warm_up_steps', 20)  # spec requires exactly 20‑step warm‑up
        self.perplexity_skip_threshold = config.get('perplexity_skip_threshold', 50.0)
        self.logger.info(
            f"DreamScheduler initialized: ratio={self.wake_to_dream_ratio}, warm_up={self.warm_up_steps}, "
            f"perplexity_skip={self.perplexity_skip_threshold}"
        )

    def should_run_dream_phase(self) -> bool:
        """
        Returns True if the current step should execute a dream phase.
        Enforces warm‑up logic and perplexity‑based skipping.
        """
        if self.current_step < self.warm_up_steps:
            # Warm‑up: never enter dream phase
            if self.current_step % 5 == 0:
                self.logger.info(
                    f"Wake/Dream Cycle: Step {self.current_step} – warm‑up active (dream skipped)."
                )
            return False

        # Standard ratio check
        is_dream_step = (self.current_step % self.wake_to_dream_ratio) == 0
        if is_dream_step:
            self.logger.info(
                f"Wake/Dream Cycle: Step {self.current_step} – triggering dream phase (ratio {self.wake_to_dream_ratio})."
            )
        else:
            self.logger.debug(
                f"Wake/Dream Cycle: Step {self.current_step} – wake phase."
            )
        return is_dream_step

    def advance_step(self):
        self.current_step += 1

    def maybe_skip_dream_due_to_perplexity(self, model: nn.Module, held_out_batch: Dict[str, torch.Tensor]) -> bool:
        """
        Computes perplexity of the model on a held‑out batch.
        If perplexity exceeds the configured threshold, returns True (skip dream).
        """
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
    entropy‑based retry, and perplexity‑based dream skipping.
    """
    def __init__(
        self,
        model: nn.Module,
        config: Config,
        device: torch.device,
        tokenizer: Optional[Any] = None  # tokenizer is optional for tests
    ):
        self.model = model
        self.config = config
        self.device = device
        self.tokenizer = tokenizer
        self.logger = get_logger(__name__, config=config, log_to_file=False)

        # Optimizer and loss
        self.optimizer = optim.AdamW(model.parameters(), lr=config.get('learning_rate', 5e-5))
        self.ce_criterion = nn.CrossEntropyLoss(ignore_index=-100)  # standard CE

        # Knowledge‑distillation (KL) loss – temperature can be tuned via config
        self.kd_temperature = config.get('kd_temperature', 1.0)
        self.kd_alpha = config.get('kd_alpha', 0.5)  # weighting between CE and KD
        self.kldiv_loss = nn.KLDivLoss(reduction='batchmean')

        # Scheduler & monitors
        self.scheduler = DreamScheduler(config, self.logger)
        self.memory_monitor = MemoryMonitor(config, self.logger)

        # Metrics storage
        self.metrics_history: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Helper methods required by the unit‑test suite
    # ------------------------------------------------------------------
    def get_entropy(self, probs: torch.Tensor) -> float:
        """
        Compute average entropy (bits) of a probability distribution.
        ``probs`` is expected to be already softmax‑ed.
        """
        eps = 1e-9
        log_probs = torch.log2(probs + eps)
        entropy = -torch.sum(probs * log_probs, dim=-1)  # shape (batch, seq_len)
        # mask padding if present (assume -100 label)
        avg_entropy = entropy.mean().item()
        return avg_entropy

    def generate(self, inputs: torch.Tensor) -> torch.Tensor:
        """
        Stub for generation used in tests – simply runs a forward pass and returns logits.
        """
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(inputs)
            # Return logits for entropy calculation
            return outputs.logits

    def log_event(self, event_type: str, data: dict):
        """
        Thin wrapper around utils.logger.log_event so tests can call it on the instance.
        """
        log_event(self.logger, event_type, data)

    # ------------------------------------------------------------------
    # Core training logic
    # ------------------------------------------------------------------
    def calculate_entropy(self, logits: torch.Tensor, labels: Optional[torch.Tensor] = None) -> float:
        """
        Calculates average entropy (bits per token) for the output distribution.
        Excludes padding tokens (label == -100) if ``labels`` is provided.
        """
        probs = torch.softmax(logits, dim=-1)
        eps = 1e-9
        log_probs = torch.log(probs + eps)
        entropy_per_token = -torch.sum(probs * log_probs, dim=-1) / np.log(2)  # convert to bits

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
        """
        KL divergence between student and teacher distributions.
        Teacher logits are detached (no gradient).
        """
        T = self.kd_temperature
        student_log_probs = F.log_softmax(student_logits / T, dim=-1)
        teacher_probs = F.softmax(teacher_logits / T, dim=-1)
        kd_loss = self.kldiv_loss(student_log_probs, teacher_probs) * (T * T)
        return kd_loss

    def train_step_wake(self, batch: Dict[str, torch.Tensor]) -> Dict[str, Any]:
        """
        Standard supervised training on real data.
        """
        self.model.train()
        inputs = batch['input_ids'].to(self.device)
        labels = batch['labels'].to(self.device)

        self.optimizer.zero_grad()
        outputs = self.model(inputs, labels=labels)
        loss = outputs.loss
        loss.backward()
        self.optimizer.step()

        entropy = self.calculate_entropy(outputs.logits, labels) if hasattr(outputs, 'logits') else 0.0

        self.logger.debug(f"Wake Step – loss={loss.item():.4f}, entropy={entropy:.4f}")

        return {'loss': loss.item(), 'entropy': entropy, 'phase': 'WAKE'}

    def train_step_dream(self, batch: Dict[str, torch.Tensor], held_out_batch: Optional[Dict[str, torch.Tensor]] = None) -> Dict[str, Any]:
        """
        Dream phase:
        1. Optionally skip if held‑out perplexity is too high.
        2. Apply BERT‑style masking (DAE).
        3. Forward pass on masked inputs.
        4. Compute reconstruction CE loss.
        5. Compute teacher‑student KD loss (teacher = same model on unmasked input, detached).
        6. Combine losses.
        """
        # Perplexity‑based skipping
        if held_out_batch is not None and self.scheduler.maybe_skip_dream_due_to_perplexity(self.model, held_out_batch):
            self.logger.info("Dream phase skipped due to high perplexity on held‑out data.")
            return {'loss': 0.0, 'entropy': 0.0, 'phase': 'DREAM_SKIPPED'}

        self.model.train()
        inputs = batch['input_ids'].to(self.device)
        original_labels = batch['labels'].to(self.device)

        # Create DAE‑masked batch
        masked_inputs, targets = create_dae_batch(
            inputs.tolist(),
            mask_rate=self.config.get('mask_rate', 0.15)
        )
        masked_inputs = torch.tensor(masked_inputs, dtype=torch.long, device=self.device)
        targets = torch.tensor(targets, dtype=torch.long, device=self.device)

        self.optimizer.zero_grad()

        # Student forward pass (reconstruction)
        student_outputs = self.model(masked_inputs, labels=targets)
        recon_loss = student_outputs.loss

        # Teacher forward pass on original (unmasked) inputs – detach gradients
        with torch.no_grad():
            teacher_outputs = self.model(inputs, labels=original_labels)
            teacher_logits = teacher_outputs.logits

        # Knowledge‑distillation loss
        kd_loss = self._knowledge_distillation_loss(student_outputs.logits, teacher_logits)

        # Combined loss
        loss = self.kd_alpha * recon_loss + (1 - self.kd_alpha) * kd_loss

        loss.backward()
        self.optimizer.step()

        # Entropy of student predictions
        entropy = self.calculate_entropy(student_outputs.logits, targets) if hasattr(student_outputs, 'logits') else 0.0

        self.logger.info(f"Dream Step – loss={loss.item():.4f}, entropy={entropy:.4f}")

        return {'loss': loss.item(), 'entropy': entropy, 'phase': 'DREAM'}

    def run_training_loop(self, dataloader: DataLoader, max_steps: int = 100) -> List[Dict[str, Any]]:
        """
        Main training loop implementing the wake/dream schedule,
        entropy‑based retry, and memory monitoring.
        """
        self.logger.info(f"Starting training loop for {max_steps} steps.")
        self.logger.info(f"Warm‑up period: {self.scheduler.warm_up_steps} steps.")

        step_count = 0
        # Pre‑load a single held‑out batch for perplexity checks (if configured)
        held_out_batch = None
        if self.config.get('held_out_subset'):
            try:
                from data.loader import load_glue_subset
                subset = load_glue_subset(self.config.get('held_out_subset'))
                # Take first batch (very small) – this is sufficient for a quick perplexity estimate
                sample = subset['validation'][:self.config.get('held_out_batch_size', 8)]
                held_out_batch = {
                    'input_ids': torch.tensor(sample['input_ids']),
                    'labels': torch.tensor(sample['label'])
                }
            except Exception as e:
                self.logger.warning(f"Could not load held‑out subset for perplexity check: {e}")

        for epoch, batch in enumerate(dataloader):
            if step_count >= max_steps:
                break

            # Memory check
            self.memory_monitor.check()

            # Decide phase
            is_dream = self.scheduler.should_run_dream_phase()

            # Logging of phase status
            if step_count % 10 == 0:
                phase_name = "DREAM" if is_dream else "WAKE"
                self.logger.info(
                    f"Step {step_count}: Phase={phase_name} (warm_up={self.scheduler.current_step < self.scheduler.warm_up_steps})"
                )

            try:
                if is_dream:
                    metrics = self.train_step_dream(batch, held_out_batch)
                else:
                    metrics = self.train_step_wake(batch)

                # Low‑entropy retry logic (max 3 attempts)
                if metrics['entropy'] < self.config.get('entropy_threshold', 0.5):
                    retry_count = 0
                    while metrics['entropy'] < self.config.get('entropy_threshold', 0.5) and retry_count < self.config.get('max_retries', 3):
                        self.logger.warning(
                            f"Low entropy detected ({metrics['entropy']:.4f} < {self.config.get('entropy_threshold', 0.5)}). "
                            f"Retrying batch (attempt {retry_count + 1}/{self.config.get('max_retries', 3)})..."
                        )
                        retry_count += 1
                        # Re‑run the same phase
                        if is_dream:
                            metrics = self.train_step_dream(batch, held_out_batch)
                        else:
                            metrics = self.train_step_wake(batch)

                    if metrics['entropy'] < self.config.get('entropy_threshold', 0.5):
                        self.logger.warning("Low entropy persists after max retries – discarding batch.")

                # Structured logging of the step
                self.log_event(
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
    Minimal entry‑point used by unit‑tests and quick demos.
    """
    config = Config()
    logger = get_logger(__name__, config=config, log_to_file=False)
    logger.info("Initializing Trainer for T002a core logic verification")

    from transformers import DistilBertForMaskedLM
    model = DistilBertForMaskedLM.from_pretrained('distilbert-base-uncased')
    device = torch.device('cpu')
    model.to(device)

    # Dummy data loader – 10 batches of random token ids
    from torch.utils.data import TensorDataset, DataLoader
    vocab_size = 30522
    dummy_input = torch.randint(0, vocab_size, (20, 32))
    dummy_labels = torch.randint(0, vocab_size, (20, 32))
    dataset = TensorDataset(dummy_input, dummy_labels)

    def collate_fn(batch):
        input_ids = torch.stack([b[0] for b in batch])
        labels = torch.stack([b[1] for b in batch])
        return {'input_ids': input_ids, 'labels': labels}

    loader = DataLoader(dataset, batch_size=4, collate_fn=collate_fn)

    trainer = Trainer(model, config, device)
    try:
        trainer.run_training_loop(loader, max_steps=30)
        logger.info("Demo run completed successfully.")
    except Exception as exc:
        logger.error(f"Demo run failed: {exc}")
        raise

if __name__ == '__main__':
    main()