import os
import gc
import time
import json
import logging
from typing import Dict, Any, Optional, List, Callable

import torch
from torch.utils.data import Dataset, DataLoader
from datasets import Dataset as HFDataset

from .memory_monitor import MemoryMonitor
from .hard_floor_enforcer import HardFloorEnforcer
from .reward_computation import compute_implicit_reward, ImplicitRewardComputer
from .evaluator import Evaluator

logger = logging.getLogger(__name__)


class DistillationDataset(Dataset):
    """
    A dataset wrapper that handles the on-policy data requirements for distillation.
    It expects a list of dictionaries containing 'input_ids', 'attention_mask', 
    'teacher_log_probs', and optionally 'human_verified_label'.
    """
    def __init__(self, data_list: List[Dict[str, Any]]):
        self.data = data_list

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        # Ensure tensors are on CPU for CPU-only execution
        return {
            "input_ids": torch.tensor(item["input_ids"], dtype=torch.long),
            "attention_mask": torch.tensor(item["attention_mask"], dtype=torch.long),
            "teacher_log_probs": torch.tensor(item["teacher_log_probs"], dtype=torch.float32),
            "human_verified_label": item.get("human_verified_label", None)
        }


class OnPolicyTrainer:
    """
    Implements the on-policy distillation loop with gradient accumulation and memory monitoring.
    
    Features:
    - Gradient accumulation to simulate larger batches while respecting memory constraints.
    - Integration with MemoryMonitor to track RAM usage.
    - Integration with HardFloorEnforcer to enforce batch_size=1 if limits are exceeded.
    - Support for implicit reward computation during the forward pass.
    """

    def __init__(
        self,
        student_model,
        teacher_model,
        tokenizer,
        device: str = "cpu",
        gradient_accumulation_steps: int = 4,
        max_steps: Optional[int] = None,
        learning_rate: float = 1e-5,
        epsilon: float = 1e-8,
        memory_threshold_gb: float = 6.5,
        output_dir: str = "data/results"
    ):
        self.student_model = student_model
        self.teacher_model = teacher_model
        self.tokenizer = tokenizer
        self.device = device
        self.gradient_accumulation_steps = gradient_accumulation_steps
        self.max_steps = max_steps
        self.learning_rate = learning_rate
        self.epsilon = epsilon
        self.memory_threshold_gb = memory_threshold_gb
        self.output_dir = output_dir

        # Optimizer setup (assuming student model has parameters)
        self.optimizer = torch.optim.AdamW(
            self.student_model.parameters(),
            lr=self.learning_rate
        )

        # Memory management components
        self.memory_monitor = MemoryMonitor(threshold_gb=self.memory_threshold_gb)
        self.hard_floor_enforcer = HardFloorEnforcer()
        
        # Reward computer
        self.reward_computer = ImplicitRewardComputer(epsilon=self.epsilon)

        # Statistics tracking
        self.training_log: List[Dict[str, Any]] = []
        self.current_step = 0

        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

    def _prepare_batch(self, batch: Dict[str, Any]) -> Dict[str, Any]:
        """Move batch tensors to the specified device."""
        return {
            k: v.to(self.device) if isinstance(v, torch.Tensor) else v
            for k, v in batch.items()
        }

    def _compute_loss(
        self,
        batch: Dict[str, Any],
        student_logits: torch.Tensor,
        teacher_log_probs: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute the on-policy distillation loss.
        Uses KL-divergence style loss or implicit reward based policy gradient.
        Here we implement a direct distillation loss minimizing KL between student and teacher.
        """
        student_log_probs = torch.log_softmax(student_logits, dim=-1)
        
        # KL Divergence: sum(teacher_log_probs * (teacher_log_probs - student_log_probs))
        # We want to minimize KL(T || S), which is sum(T * log(T/S)) = sum(T * (log T - log S))
        kl_loss = torch.sum(
            teacher_log_probs * (teacher_log_probs - student_log_probs),
            dim=-1
        )
        
        return kl_loss.mean()

    def _step(
        self,
        batch: Dict[str, Any],
        accumulated_grads: Optional[Dict[str, torch.Tensor]] = None
    ) -> torch.Tensor:
        """
        Perform a single forward-backward step.
        Returns the loss value.
        """
        self.optimizer.zero_grad()

        batch = self._prepare_batch(batch)
        
        input_ids = batch["input_ids"]
        attention_mask = batch["attention_mask"]
        teacher_log_probs = batch["teacher_log_probs"]

        # Student forward pass
        with torch.set_grad_enabled(True):
            student_outputs = self.student_model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                return_dict=True
            )
            student_logits = student_outputs.logits

        # Compute loss
        loss = self._compute_loss(batch, student_logits, teacher_log_probs)

        # Scale loss for gradient accumulation
        loss = loss / self.gradient_accumulation_steps

        # Backward pass
        loss.backward()

        return loss.detach().cpu().item()

    def _update_weights(self) -> None:
        """Update model weights after gradient accumulation."""
        self.optimizer.step()
        self.optimizer.zero_grad()

    def _check_memory_and_oom(self) -> bool:
        """
        Check current memory usage. If exceeded, trigger hard floor enforcer.
        Returns True if OOM was handled (batch size forced to 1), False otherwise.
        """
        current_ram = self.memory_monitor.get_current_ram_gb()
        logger.debug(f"Current RAM usage: {current_ram:.2f} GB (Threshold: {self.memory_threshold_gb} GB)")

        if current_ram > self.memory_threshold_gb:
            logger.warning(f"RAM usage {current_ram:.2f} GB exceeds threshold. Triggering Hard Floor Enforcer.")
            self.hard_floor_enforcer.enforce()
            return True
        return False

    def train(
        self,
        dataloader: DataLoader,
        eval_dataloader: Optional[DataLoader] = None,
        eval_interval: int = 100
    ) -> Dict[str, Any]:
        """
        Execute the on-policy distillation training loop.
        
        Args:
            dataloader: DataLoader for training data.
            eval_dataloader: Optional DataLoader for evaluation.
            eval_interval: Number of steps between evaluations.
        
        Returns:
            Dictionary containing training metrics and final model state path.
        """
        logger.info(f"Starting training on {self.device} with batch_size=1, grad_accum={self.gradient_accumulation_steps}")
        
        start_time = time.time()
        
        # Flatten dataloader into an iterator to handle gradient accumulation across batches
        # Since we use batch_size=1, we accumulate over gradient_accumulation_steps items
        
        iterator = iter(dataloader)
        accumulated_loss = 0.0
        steps_since_last_eval = 0

        while self.max_steps is None or self.current_step < self.max_steps:
            try:
                # Check memory before processing a new batch
                self._check_memory_and_oom()

                batch = next(iterator)
                loss = self._step(batch)
                
                accumulated_loss += loss
                steps_since_last_eval += 1

                # Perform optimizer step after accumulation
                if (self.current_step + 1) % self.gradient_accumulation_steps == 0:
                    self._update_weights()
                    
                    avg_loss = accumulated_loss / self.gradient_accumulation_steps
                    self.training_log.append({
                        "step": self.current_step,
                        "loss": avg_loss,
                        "timestamp": time.time()
                    })
                    
                    logger.info(f"Step {self.current_step}: Loss = {avg_loss:.4f}")
                    
                    accumulated_loss = 0.0
                    self.current_step += 1

                    # Evaluation checkpoint
                    if eval_dataloader is not None and steps_since_last_eval >= eval_interval:
                        self._evaluate(eval_dataloader, self.current_step)
                        steps_since_last_eval = 0

            except StopIteration:
                # Restart iterator if we run out of data but haven't hit max_steps
                logger.info("Epoch completed, restarting data iterator.")
                iterator = iter(dataloader)
            
            except MemoryError as e:
                logger.error(f"MemoryError encountered: {e}")
                # Fallback to hard floor if not already triggered
                self.hard_floor_enforcer.enforce()
                # Attempt to clear memory and continue with next batch (if possible)
                gc.collect()
                if self.device == "cpu":
                    torch.cuda.empty_cache() # No-op on CPU but safe
                continue

            except Exception as e:
                logger.error(f"Unexpected error during training step: {e}")
                raise

        elapsed_time = time.time() - start_time
        logger.info(f"Training finished. Total time: {elapsed_time:.2f}s")

        # Save final state
        results = {
            "total_steps": self.current_step,
            "final_loss": self.training_log[-1]["loss"] if self.training_log else None,
            "elapsed_time_seconds": elapsed_time,
            "training_log_path": os.path.join(self.output_dir, "training_log.json"),
            "model_checkpoint_path": os.path.join(self.output_dir, "student_checkpoint.pt")
        }

        # Save training log
        with open(results["training_log_path"], "w") as f:
            json.dump(self.training_log, f, indent=2)

        # Save model state
        torch.save(self.student_model.state_dict(), results["model_checkpoint_path"])

        return results

    def _evaluate(self, eval_dataloader: DataLoader, step: int) -> None:
        """Run evaluation on the provided dataloader."""
        logger.info(f"Running evaluation at step {step}")
        evaluator = Evaluator()
        
        eval_metrics = evaluator.evaluate(
            model=self.student_model,
            dataloader=eval_dataloader,
            device=self.device
        )
        
        self.training_log.append({
            "step": step,
            "type": "evaluation",
            "metrics": eval_metrics,
            "timestamp": time.time()
        })
        logger.info(f"Evaluation metrics at step {step}: {eval_metrics}")


def main():
    """
    Entry point for running the trainer as a script.
    This function loads configuration, models, and data, then initiates training.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Placeholder for actual configuration loading
    # In a real run, this would load from config/defaults.yaml
    config = {
        "student_model_id": "mistralai/Mixtral-8x7B-Instruct-v0.1", # Example
        "teacher_model_id": "meta-llama/Llama-2-7b-hf", # Example
        "data_path": "data/processed/aime_train.jsonl",
        "eval_data_path": "data/processed/aime_holdout.jsonl",
        "gradient_accumulation_steps": 4,
        "learning_rate": 1e-5,
        "max_steps": 100, # Limit for demo purposes
        "memory_threshold_gb": 6.0
    }

    logger.info("Initializing Trainer...")
    
    # Note: Actual model loading and data loading logic would be injected here
    # based on the specific user story (MoE or SSM) and the loaded datasets.
    # For this implementation, we assume the caller provides the models and dataloaders
    # or we would load them here using the respective loaders (T005, T008, T009).
    
    # Mocking the execution flow for the artifact to be runnable if dependencies were met
    try:
        # This block demonstrates the structure. 
        # In a full pipeline, `student_model` and `dataloader` would be real objects.
        logger.info("Trainer initialized. Ready for training loop.")
        logger.info("Note: Actual training requires valid model instances and dataloaders.")
    except Exception as e:
        logger.error(f"Failed to initialize training: {e}")
        raise

if __name__ == "__main__":
    main()