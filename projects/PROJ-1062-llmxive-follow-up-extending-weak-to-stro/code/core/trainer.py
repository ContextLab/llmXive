import os
import gc
import time
import json
import logging
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path

import torch
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer
from peft import PeftModel

from core.reward_computation import compute_implicit_reward
from core.memory_monitor import MemoryMonitor
from core.hard_floor_enforcer import HardFloorEnforcer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DistillationDataset(Dataset):
    """Simple dataset wrapper for AIME processed data."""
    def __init__(self, data_path: str, tokenizer: AutoTokenizer, max_length: int = 512):
        self.data = []
        self.tokenizer = tokenizer
        self.max_length = max_length
        
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Processed data file not found: {data_path}")
        
        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                self.data.append(json.loads(line))

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        # Expecting 'prompt' and 'reasoning' or 'response' fields based on preprocess output
        prompt = item.get('prompt', '')
        response = item.get('response', item.get('reasoning', ''))
        
        full_text = f"{prompt}\n{response}"
        
        encoding = self.tokenizer(
            full_text,
            return_tensors='pt',
            truncation=True,
            max_length=self.max_length,
            padding='max_length'
        )
        
        return {
            'input_ids': encoding['input_ids'].squeeze(0),
            'attention_mask': encoding['attention_mask'].squeeze(0),
            'original_text': full_text
        }

class OnPolicyTrainer:
    """
    Implements the on-policy distillation loop with gradient accumulation
    and memory monitoring.
    
    Supports:
    - Gradient accumulation to simulate larger batch sizes on limited RAM
    - Memory monitoring to trigger OOM handling
    - Hard floor enforcement for batch size
    """
    
    def __init__(
        self,
        student_model,
        teacher_model,
        tokenizer: AutoTokenizer,
        device: str,
        config: Dict[str, Any]
    ):
        self.student_model = student_model
        self.teacher_model = teacher_model
        self.tokenizer = tokenizer
        self.device = device
        self.config = config
        
        # Initialize memory monitoring components
        self.memory_monitor = MemoryMonitor(
            threshold_percent=config.get('ram_threshold_percent', 90),
            hard_limit_gb=config.get('hard_ram_limit_gb', 7.0)
        )
        self.hard_floor = HardFloorEnforcer(
            min_batch_size=config.get('min_batch_size', 1)
        )
        
        self.batch_size = config.get('batch_size', 1)
        self.gradient_accumulation_steps = config.get('gradient_accumulation_steps', 4)
        self.learning_rate = config.get('learning_rate', 1e-5)
        self.epsilon = config.get('epsilon_smoothing', 1e-6)
        self.max_steps = config.get('max_steps', 500)
        
        # Optimizer
        self.optimizer = torch.optim.AdamW(
            self.student_model.parameters(),
            lr=self.learning_rate
        )
        
        self.current_step = 0
        self.total_loss_accumulated = 0.0
        self.loss_count = 0

    def _get_teacher_logits(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        """Get logits from teacher model."""
        with torch.no_grad():
            self.teacher_model.eval()
            outputs = self.teacher_model(
                input_ids=input_ids.to(self.device),
                attention_mask=attention_mask.to(self.device)
            )
            return outputs.logits

    def _get_student_logits(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        """Get logits from student model."""
        self.student_model.train()
        outputs = self.student_model(
            input_ids=input_ids.to(self.device),
            attention_mask=attention_mask.to(self.device)
        )
        return outputs.logits

    def _compute_loss(
        self,
        student_logits: torch.Tensor,
        teacher_logits: torch.Tensor,
        attention_mask: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute distillation loss using implicit reward.
        Uses epsilon-smoothing for numerical stability.
        """
        # Shift logits for next-token prediction
        shift_student = student_logits[:, :-1, :]
        shift_teacher = teacher_logits[:, :-1, :]
        shift_mask = attention_mask[:, 1:]
        
        # Compute implicit reward (log-ratio of probabilities)
        # R = log(P_student / P_teacher) -> loss = -R (minimize negative reward)
        # Using logits directly: log_softmax(logits) - log_softmax(teacher_logits)
        
        log_p_student = torch.log_softmax(shift_student / (1.0 + self.epsilon), dim=-1)
        log_p_teacher = torch.log_softmax(shift_teacher, dim=-1)
        
        # Implicit reward signal
        implicit_reward = log_p_student - log_p_teacher
        
        # Loss is negative reward (we want to maximize reward, so minimize negative)
        # Mask out padding tokens
        loss = - (implicit_reward * shift_mask.unsqueeze(-1)).sum(dim=-1).mean()
        
        return loss

    def train_step(self, batch: Dict[str, torch.Tensor]) -> float:
        """Execute a single training step with gradient accumulation."""
        input_ids = batch['input_ids']
        attention_mask = batch['attention_mask']
        
        # Check memory before forward pass
        if not self.memory_monitor.check_memory_safe():
            # Trigger reduction if needed
            new_bs = self.hard_floor.enforce_floor(self.batch_size)
            if new_bs < self.batch_size:
                logger.warning(f"Memory limit reached. Reducing batch size from {self.batch_size} to {new_bs}")
                self.batch_size = new_bs
                raise MemoryError(f"Batch size reduced to {self.batch_size} due to memory constraints.")
            else:
                logger.error("Batch size already at hard floor, cannot reduce further.")
                raise MemoryError("OOM: Batch size at hard floor limit.")

        # Forward pass: Teacher
        teacher_logits = self._get_teacher_logits(input_ids, attention_mask)
        
        # Forward pass: Student
        student_logits = self._get_student_logits(input_ids, attention_mask)
        
        # Compute loss
        loss = self._compute_loss(student_logits, teacher_logits, attention_mask)
        
        # Normalize loss for gradient accumulation
        loss = loss / self.gradient_accumulation_steps
        
        # Backward pass
        loss.backward()
        
        self.total_loss_accumulated += loss.item() * self.gradient_accumulation_steps
        self.loss_count += 1
        
        return loss.item()

    def _step_optimizer(self):
        """Execute optimizer step and reset gradients."""
        self.optimizer.step()
        self.optimizer.zero_grad()
        self.current_step += 1

    def train(
        self,
        dataloader: DataLoader,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run the full training loop.
        
        Args:
            dataloader: DataLoader for the training data
            output_path: Path to save results JSON
        
        Returns:
            Dictionary containing training metrics
        """
        logger.info(f"Starting training with batch_size={self.batch_size}, "
                    f"accum_steps={self.gradient_accumulation_steps}, "
                    f"max_steps={self.max_steps}")
        
        start_time = time.time()
        losses = []
        steps_per_epoch = len(dataloader)
        
        try:
            for epoch in range(self.max_steps // steps_per_epoch + 1):
                if self.current_step >= self.max_steps:
                    break
                    
                for batch_idx, batch in enumerate(dataloader):
                    if self.current_step >= self.max_steps:
                        break
                        
                    try:
                        step_loss = self.train_step(batch)
                        losses.append(step_loss)
                        
                        # Perform optimizer step every gradient_accumulation_steps
                        if (batch_idx + 1) % self.gradient_accumulation_steps == 0:
                            self._step_optimizer()
                            self.memory_monitor.log_snapshot(self.current_step)
                            
                    except MemoryError as e:
                        logger.warning(f"Step {self.current_step} failed: {e}")
                        # If we hit memory error, we might need to restart with smaller batch
                        # For now, we break to let the caller handle the retry or abort
                        raise e
                        
        except MemoryError as e:
            logger.error(f"Training terminated due to memory error: {e}")
            # Return partial results if any
        
        end_time = time.time()
        execution_time_ms = (end_time - start_time) * 1000
        
        avg_loss = sum(losses) / len(losses) if losses else 0.0
        
        results = {
            'total_steps': self.current_step,
            'final_avg_loss': avg_loss,
            'execution_time_ms': execution_time_ms,
            'batch_size_used': self.batch_size,
            'gradient_accumulation_steps': self.gradient_accumulation_steps,
            'memory_peak_gb': self.memory_monitor.get_peak_usage_gb()
        }
        
        if output_path:
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to {output_path}")
        
        return results

def main():
    """
    Entry point for running the trainer.
    Expects configuration via environment or defaults.
    """
    # Default configuration
    config = {
        'batch_size': 1,
        'gradient_accumulation_steps': 4,
        'learning_rate': 1e-5,
        'epsilon_smoothing': 1e-6,
        'max_steps': 500,
        'ram_threshold_percent': 90,
        'hard_ram_limit_gb': 7.0,
        'data_path': 'data/processed/aime_train.jsonl',
        'model_name': 'mistralai/Mixtral-8x7B-v0.1', # Example for MoE
        'output_path': 'data/results/trainer_run.json'
    }
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(config['model_name'])
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        
    # Placeholder for model loading - in real usage, models are passed in
    # This function is meant to be called by specific MoE/SSM scripts
    logger.info("Trainer module loaded. Use OnPolicyTrainer class for training.")
    return config

if __name__ == '__main__':
    main()