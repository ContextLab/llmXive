import torch
import torch.nn as nn
import torch.optim as optim
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
from config import Config
from utils.logger import get_logger, log_event
from utils.memory_monitor import MemoryMonitor, MemoryLimitExceeded
from utils.exceptions import DataIntegrityError
from data.augment import apply_dae_mask, create_dae_batch
from data.loader import load_glue_subset
import time

logger = get_logger(__name__)


class DreamScheduler:
  """Manages the Wake/Dream phase schedule."""

  def __init__(self, wake_dream_ratio: int = 4, warmup_steps: int = 10):
      """
      Initialize the DreamScheduler.

      Args:
          wake_dream_ratio: Ratio of wake steps to dream steps (default 4:1)
          warmup_steps: Number of initial steps before dream phase begins
      """
      self.wake_dream_ratio = wake_dream_ratio
      self.warmup_steps = warmup_steps
      self.current_step = 0

  def is_wake_phase(self) -> bool:
      """Determine if current step should be a Wake phase."""
      if self.current_step < self.warmup_steps:
          return True
      # After warmup, use modulo to alternate phases
      cycle_position = self.current_step % (self.wake_dream_ratio + 1)
      return cycle_position < self.wake_dream_ratio

  def step(self) -> str:
      """
      Advance the scheduler and return the current phase.

      Returns:
          "wake" or "dream"
      """
      self.current_step += 1
      phase = "wake" if self.is_wake_phase() else "dream"
      return phase

  def get_phase(self) -> str:
      """Get current phase without advancing."""
      return "wake" if self.is_wake_phase() else "dream"


class Trainer:
  """Core trainer implementing the Wake/Dream training loop."""

  def __init__(
      self,
      model: nn.Module,
      config: Config,
      device: torch.device,
      optimizer: Optional[optim.Optimizer] = None
  ):
      """
      Initialize the Trainer.

      Args:
          model: PyTorch model to train
          config: Configuration object
          device: Device to run training on
          optimizer: Optimizer instance (creates default if None)
      """
      self.model = model
      self.config = config
      self.device = device
      self.scheduler = DreamScheduler(
          wake_dream_ratio=config.WAKE_DREAM_RATIO,
          warmup_steps=config.WARMUP_STEPS
      )
      self.memory_monitor = MemoryMonitor()

      if optimizer is None:
          self.optimizer = optim.AdamW(
              model.parameters(),
              lr=config.LEARNING_RATE,
              weight_decay=config.WEIGHT_DECAY
          )
      else:
          self.optimizer = optimizer

      self.criterion = nn.CrossEntropyLoss()
      self.global_step = 0
      self.logger = get_logger(__name__)

  def _calculate_entropy(self, logits: torch.Tensor) -> float:
      """
      Calculate entropy of output distribution.

      Args:
          logits: Model output logits [batch_size, vocab_size]

      Returns:
          Average entropy in bits
      """
      probs = torch.softmax(logits, dim=-1)
      # Avoid log(0)
      probs = torch.clamp(probs, min=1e-10)
      log_probs = torch.log2(probs)
      entropy = -torch.sum(probs * log_probs, dim=-1)
      return entropy.mean().item()

  def _wake_phase(self, batch: Dict[str, torch.Tensor]) -> Tuple[float, float]:
      """
      Execute a Wake phase training step.

      Args:
          batch: Dictionary containing input_ids, attention_mask, labels

      Returns:
          Tuple of (loss, accuracy)
      """
      self.model.train()
      input_ids = batch["input_ids"].to(self.device)
      attention_mask = batch["attention_mask"].to(self.device)
      labels = batch["labels"].to(self.device)

      self.optimizer.zero_grad()
      outputs = self.model(
          input_ids=input_ids,
          attention_mask=attention_mask,
          labels=labels
      )
      loss = outputs.loss
      loss.backward()
      self.optimizer.step()

      # Calculate accuracy
      predictions = torch.argmax(outputs.logits, dim=-1)
      accuracy = (predictions == labels).float().mean().item()

      return loss.item(), accuracy

  def _dream_phase(self, batch: Dict[str, torch.Tensor]) -> Tuple[float, float]:
      """
      Execute a Dream phase training step (DAE reconstruction).

      Args:
          batch: Dictionary containing input_ids, attention_mask

      Returns:
          Tuple of (loss, reconstruction_accuracy)
      """
      self.model.train()
      input_ids = batch["input_ids"].to(self.device)
      attention_mask = batch["attention_mask"].to(self.device)

      # Apply DAE masking
      masked_input_ids, labels = apply_dae_mask(
          input_ids,
          mask_rate=self.config.MASK_RATE,
          tokenizer=None  # We work with token IDs directly
      )

      self.optimizer.zero_grad()
      outputs = self.model(
          input_ids=masked_input_ids.to(self.device),
          attention_mask=attention_mask.to(self.device),
          labels=labels.to(self.device)
      )
      loss = outputs.loss
      loss.backward()
      self.optimizer.step()

      # Calculate reconstruction accuracy
      predictions = torch.argmax(outputs.logits, dim=-1)
      # Only consider masked positions
      mask = (labels != -100)
      correct = (predictions[mask] == labels[mask]).float().sum().item()
      total = mask.sum().item()
      accuracy = correct / total if total > 0 else 0.0

      return loss.item(), accuracy

  def _check_entropy_and_retry(
      self,
      batch: Dict[str, torch.Tensor],
      max_retries: int = 3
  ) -> Optional[Dict[str, torch.Tensor]]:
      """
      Check output entropy and retry if too low.

      Args:
          batch: Input batch
          max_retries: Maximum retry attempts

      Returns:
          Batch if valid, None if all retries failed
      """
      for retry in range(max_retries):
          # Forward pass to check entropy
          with torch.no_grad():
              outputs = self.model(
                  input_ids=batch["input_ids"].to(self.device),
                  attention_mask=batch["attention_mask"].to(self.device)
              )
              entropy = self._calculate_entropy(outputs.logits)

          if entropy >= self.config.ENTROPY_THRESHOLD:
              return batch
          else:
              self.logger.warning(
                  f"Low entropy detected: {entropy:.3f} bits (threshold: {self.config.ENTROPY_THRESHOLD})"
              )
              if retry < max_retries - 1:
                  self.logger.info(f"Retrying batch (attempt {retry + 2}/{max_retries})")

      self.logger.warning("Batch discarded due to consistently low entropy")
      return None

  def train_step(
      self,
      batch: Dict[str, torch.Tensor]
  ) -> Dict[str, Any]:
      """
      Execute a single training step (Wake or Dream).

      Args:
          batch: Input batch

      Returns:
          Dictionary with step metrics
      """
      # Check memory before step
      self.memory_monitor.check_memory()

      # Determine phase
      phase = self.scheduler.step()
      self.global_step += 1

      # Check entropy and retry if needed
      valid_batch = self._check_entropy_and_retry(batch)
      if valid_batch is None:
          return {"skipped": True, "phase": phase}

      # Execute appropriate phase
      if phase == "wake":
          loss, accuracy = self._wake_phase(valid_batch)
          log_event(
              self.logger,
              "WAKE_STEP",
              f"Wake phase completed. Loss: {loss:.4f}, Accuracy: {accuracy:.4f}",
              {"loss": loss, "accuracy": accuracy, "step": self.global_step}
          )
      else:
          loss, accuracy = self._dream_phase(valid_batch)
          log_event(
              self.logger,
              "DREAM_STEP",
              f"Dream phase completed. Loss: {loss:.4f}, Reconstruction Accuracy: {accuracy:.4f}",
              {"loss": loss, "accuracy": accuracy, "step": self.global_step}
          )

      # Log phase transition
      if self.global_step > 1:
          prev_phase = "dream" if phase == "wake" else "wake"
          log_event(
              self.logger,
              "PHASE_TRANSITION",
              f"Phase transition: {prev_phase} -> {phase}",
              {"from_phase": prev_phase, "to_phase": phase, "step": self.global_step}
          )

      return {
          "phase": phase,
          "loss": loss,
          "accuracy": accuracy,
          "step": self.global_step
      }

  def train(
      self,
      dataset,
      num_steps: int,
      checkpoint_dir: Optional[str] = None
  ) -> List[Dict[str, Any]]:
      """
      Run the full training loop.

      Args:
          dataset: Training dataset
          num_steps: Number of training steps
          checkpoint_dir: Directory to save checkpoints

      Returns:
          List of step metrics
      """
      history = []
      start_time = time.time()

      log_event(
          self.logger,
          "TRAINING_START",
          f"Starting training for {num_steps} steps",
          {"num_steps": num_steps, "warmup_steps": self.config.WARMUP_STEPS}
      )

      for step in range(num_steps):
          try:
              # Get batch (simplified - in real implementation, use DataLoader)
              batch_idx = step % len(dataset)
              batch = dataset[batch_idx]

              # Convert to tensors
              batch = {
                  k: torch.tensor(v).unsqueeze(0) if isinstance(v, list) else torch.tensor(v)
                  for k, v in batch.items()
              }

              # Train step
              metrics = self.train_step(batch)
              history.append(metrics)

              # Log progress
              if step % 10 == 0:
                  elapsed = time.time() - start_time
                  log_event(
                      self.logger,
                      "PROGRESS",
                      f"Step {step}/{num_steps} completed. Elapsed: {elapsed:.1f}s",
                      {"step": step, "total_steps": num_steps, "elapsed_seconds": elapsed}
                  )

              # Checkpoint if requested
              if checkpoint_dir and step % 50 == 0:
                  checkpoint_path = f"{checkpoint_dir}/checkpoint_step_{step}.pt"
                  torch.save({
                      "step": step,
                      "model_state_dict": self.model.state_dict(),
                      "optimizer_state_dict": self.optimizer.state_dict(),
                  }, checkpoint_path)
                  log_event(
                      self.logger,
                      "CHECKPOINT_SAVED",
                      f"Checkpoint saved to {checkpoint_path}",
                      {"path": checkpoint_path, "step": step}
                  )

          except MemoryLimitExceeded as e:
              log_event(
                  self.logger,
                  "OOM_ABORT",
                  f"Out of memory at step {step}: {str(e)}",
                  {"step": step, "error": str(e)}
              )
              # Save final checkpoint before aborting
              if checkpoint_dir:
                  checkpoint_path = f"{checkpoint_dir}/checkpoint_oom_final.pt"
                  torch.save({
                      "step": step,
                      "model_state_dict": self.model.state_dict(),
                  }, checkpoint_path)
              raise

      total_time = time.time() - start_time
      log_event(
          self.logger,
          "TRAINING_COMPLETE",
          f"Training completed. Total time: {total_time:.1f}s",
          {"total_steps": num_steps, "total_time_seconds": total_time}
      )

      return history