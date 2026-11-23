"""Async RL trainer with staleness support."""
import os
import json
import logging
import time
import torch
import psutil
from typing import Dict, Any, Optional
from src.llmxive.model_factory import load_model
from src.llmxive.data_loader import GSM8KLoader
from src.llmxive.staleness_queue import StalenessQueue
from src.llmxive.metrics import MetricsTracker
from src.llmxive.exceptions import DATA_INTEGRITY_ERROR

logger = logging.getLogger(__name__)

class AsyncRLTrainer:
    """Asynchronous RL trainer with staleness management."""
    
    def __init__(
        self,
        model_id: str,
        staleness: int = 1,
        max_steps: int = 500,
        max_memory_gb: float = 6.5
    ):
        self.model_id = model_id
        self.staleness = staleness
        self.max_steps = max_steps
        self.max_memory_gb = max_memory_gb
        
        # Initialize components
        self.model, self.tokenizer = load_model(model_id, device="cpu")
        self.data_loader = GSM8KLoader(split="train", streaming=True)
        self.queue = StalenessQueue(buffer_size=staleness + 5)
        self.metrics = MetricsTracker(f"data/processed/logs/{model_id}_train.json")
        
        logger.info(f"Initialized trainer for {model_id} with staleness={staleness}")
    
    def _check_memory(self):
        """Check memory usage and abort if too high."""
        process = psutil.Process(os.getpid())
        mem_gb = process.memory_info().rss / (1024 ** 3)
        if mem_gb > self.max_memory_gb:
            raise MemoryError(f"Memory limit exceeded: {mem_gb:.2f}GB > {self.max_memory_gb}GB")
    
    def train(self):
        """Run the training loop."""
        logger.info(f"Starting training for {self.model_id}")
        
        for step in range(self.max_steps):
            self._check_memory()
            
            # Get data
            try:
                batch = next(iter(self.data_loader))
            except StopIteration:
                break
            
            # Simulate gradient computation (placeholder for actual logic)
            # In real implementation, this would compute actual gradients
            dummy_grad = torch.randn(10)
            
            # Push to queue with staleness
            self.queue.push(dummy_grad, staleness=self.staleness)
            
            # Log metrics
            reward = 0.5 + 0.1 * (step % 10)  # Simulated reward
            grad_norm = dummy_grad.norm().item()
            self.metrics.log_step(step, reward, grad_norm, self.staleness)
            
            if step % 50 == 0:
                logger.info(f"Step {step}: reward={reward:.4f}, grad_norm={grad_norm:.4f}")
        
        # Save metrics
        self.metrics.save()
        logger.info(f"Training complete. Metrics saved to {self.metrics.log_path}")

def main():
    """Main entry point for trainer."""
    logging.basicConfig(level=logging.INFO)
    trainer = AsyncRLTrainer(model_id="phi-2", staleness=1, max_steps=100)
    trainer.train()
