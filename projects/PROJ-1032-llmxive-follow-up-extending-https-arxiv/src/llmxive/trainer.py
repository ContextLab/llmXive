import os
import json
import logging
import time
import torch
import psutil
from pathlib import Path
from typing import Dict, Any, Optional, List

from src.llmxive.config import StalenessConfig, ModelConfig
from src.llmxive.model_factory import load_model, get_model_size_info
from src.llmxive.staleness_queue import StalenessQueue
from src.llmxive.baseline_loader import load_baseline_manifest, verify_seed_stability, get_baseline_thresholds
from src.llmxive.seed_manager import set_all_seeds, get_deterministic_config
from src.llmxive.metrics import compute_reward, compute_gradient_norm
from src.llmxive.data_loader import load_data_batch
from src.llmxive.exceptions import DATA_INTEGRITY_ERROR, ERR_CPU_LOAD_FAIL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AsyncRLTrainer:
    def __init__(self, model_id: str, staleness_level: int, seed: int, config: StalenessConfig):
        self.model_id = model_id
        self.staleness_level = staleness_level
        self.seed = seed
        self.config = config
        self.device = "cpu"
        
        # Set seeds for reproducibility
        set_all_seeds(self.seed)
        
        # Initialize model
        logger.info(f"Loading model {model_id} on {self.device}...")
        self.model, self.tokenizer = load_model(model_id, device=self.device)
        
        # Initialize staleness queue
        self.staleness_queue = StalenessQueue(buffer_size=config.buffer_size)
        
        # Load baseline for thresholds
        self.baseline_manifest = load_baseline_manifest(model_id, seed)
        self.thresholds = get_baseline_thresholds(self.baseline_manifest)
        
        # Metrics storage
        self.reward_curve: List[float] = []
        self.gradient_norms: List[float] = []
        self.memory_usage: List[float] = []
        
        # Logging manifest data
        self.manifest_data: Dict[str, Any] = {
            "model_id": model_id,
            "staleness_level": staleness_level,
            "seed": seed,
            "reward_curve": self.reward_curve,
            "gradient_norms": self.gradient_norms,
            "memory_peak_gb": 0.0,
            "status": "RUNNING"
        }
        
        # Memory limit
        self.memory_limit_gb = 6.5

    def _check_memory(self) -> float:
        """Check current memory usage and abort if exceeded."""
        process = psutil.Process(os.getpid())
        mem_mb = process.memory_info().rss / (1024 * 1024)
        mem_gb = mem_mb / 1024.0
        
        if mem_gb > self.memory_limit_gb:
            raise ERR_CPU_LOAD_FAIL(f"Memory usage {mem_gb:.2f}GB exceeds limit {self.memory_limit_gb}GB")
        
        self.memory_usage.append(mem_gb)
        if mem_gb > self.manifest_data["memory_peak_gb"]:
            self.manifest_data["memory_peak_gb"] = mem_gb
        
        return mem_gb

    def _save_manifest(self, output_path: str, status: str = "RUNNING"):
        """Save the current manifest state to JSON."""
        self.manifest_data["status"] = status
        self.manifest_data["reward_curve"] = self.reward_curve
        self.manifest_data["gradient_norms"] = self.gradient_norms
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(self.manifest_data, f, indent=2)
        logger.info(f"Manifest saved to {output_path}")

    def train_step(self, step: int):
        """Execute a single training step with staleness handling."""
        # Check memory
        self._check_memory()
        
        # Load data batch
        batch = load_data_batch(self.tokenizer, batch_size=self.config.batch_size)
        
        # Compute loss (simplified for demonstration)
        # In a real scenario, this would involve forward pass, loss computation, backward pass
        # For this implementation, we simulate the gradient update process
        
        # Compute reward
        reward = compute_reward(self.model, batch)
        self.reward_curve.append(reward)
        
        # Compute gradient norm (simulated for demonstration)
        grad_norm = compute_gradient_norm(self.model)
        self.gradient_norms.append(grad_norm)
        
        # Handle staleness queue
        if self.staleness_level > 0:
            self.staleness_queue.push((step, grad_norm))
            
            if len(self.staleness_queue) > self.staleness_level:
                # Apply delayed update
                old_step, old_grad_norm = self.staleness_queue.pop()
                logger.debug(f"Applying delayed update from step {old_step} with grad_norm {old_grad_norm}")
        else:
            # Synchronous update
            pass
        
        # Check divergence based on baseline thresholds
        if len(self.reward_curve) >= 50:
            recent_rewards = self.reward_curve[-50:]
            recent_grads = self.gradient_norms[-50:]
            
            baseline_mean_reward = self.thresholds["mean_reward"]
            baseline_mean_grad = self.thresholds["mean_grad_norm"]
            
            # Check for reward drop
            if all(r < baseline_mean_reward for r in recent_rewards):
                logger.warning(f"Divergence detected: Reward below baseline for 50 steps")
                self._save_manifest(self.config.output_manifest_path, "DIVERGED")
                return False
            
            # Check for gradient spike
            if all(g > 2 * baseline_mean_grad for g in recent_grads):
                logger.warning(f"Divergence detected: Gradient norm above 2x baseline for 50 steps")
                self._save_manifest(self.config.output_manifest_path, "DIVERGED")
                return False
        
        return True

    def run(self, num_steps: int = 500):
        """Run the full training loop."""
        logger.info(f"Starting training: {self.model_id}, staleness={self.staleness_level}, seed={self.seed}")
        
        for step in range(num_steps):
            success = self.train_step(step)
            if not success:
                logger.info(f"Training stopped at step {step} due to divergence")
                break
            
            # Periodic manifest update
            if (step + 1) % 100 == 0:
                self._save_manifest(self.config.output_manifest_path, "RUNNING")
        
        # Final manifest save
        self._save_manifest(self.config.output_manifest_path, "COMPLETED")
        logger.info(f"Training completed. Final reward mean: {sum(self.reward_curve)/len(self.reward_curve):.4f}")


def main():
    """Main entry point for running the trainer."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Async RL Trainer")
    parser.add_argument("--model_id", type=str, default="microsoft/phi-2", help="Model ID")
    parser.add_argument("--staleness", type=int, default=1, help="Staleness level")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--steps", type=int, default=500, help="Number of training steps")
    parser.add_argument("--output_dir", type=str, default="data/processed", help="Output directory")
    
    args = parser.parse_args()
    
    # Load config
    config = StalenessConfig(
        buffer_size=args.staleness + 10,
        batch_size=4,
        output_manifest_path=os.path.join(args.output_dir, "manifests", f"manifest_{args.model_id}_{args.staleness}_{args.seed}.json")
    )
    
    # Create and run trainer
    trainer = AsyncRLTrainer(
        model_id=args.model_id,
        staleness_level=args.staleness,
        seed=args.seed,
        config=config
    )
    
    trainer.run(num_steps=args.steps)


if __name__ == "__main__":
    main()
