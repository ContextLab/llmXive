import os
import json
import logging
import time
import torch
import psutil

from src.llmxive.config import StalenessConfig, TrainingConfig
from src.llmxive.model_factory import load_model, get_model_size_info
from src.llmxive.data_loader import GSM8KDataLoader
from src.llmxive.staleness_queue import StalenessQueue
from src.llmxive.baseline_loader import load_baseline_manifest, get_baseline_thresholds, verify_seed_stability
from src.llmxive.metrics import MetricsCollector
from src.llmxive.exceptions import DATA_INTEGRITY_ERROR, ERR_CPU_LOAD_FAIL, STALENESS_OVERFLOW

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/processed/trainer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AsyncRLTrainer:
    """
    Asynchronous RL Trainer with memory monitoring and staleness support.
    
    Features:
    - CPU-only execution with 8-bit quantization
    - Configurable staleness via StalenessQueue
    - Memory monitoring with abort threshold (6.5 GB)
    - Baseline-based divergence detection
    """
    
    def __init__(self, config: TrainingConfig, staleness_config: StalenessConfig):
        self.config = config
        self.staleness_config = staleness_config
        self.device = "cpu"
        self.model = None
        self.tokenizer = None
        self.data_loader = None
        self.staleness_queue = None
        self.metrics = None
        self.max_memory_gb = 6.5
        self.current_seed = None
        
        logger.info(f"Initializing AsyncRLTrainer with max_memory={self.max_memory_gb}GB")
    
    def _check_memory_usage(self) -> float:
        """
        Check current RAM usage in GB.
        
        Returns:
            float: Current RAM usage in GB
        """
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        return mem_info.rss / (1024 ** 3)  # Convert bytes to GB
    
    def _enforce_memory_limit(self):
        """
        Check if memory usage exceeds limit and abort if so.
        
        Raises:
            ERR_CPU_LOAD_FAIL: If memory usage exceeds 6.5 GB
        """
        current_ram = self._check_memory_usage()
        if current_ram > self.max_memory_gb:
            logger.error(f"Memory limit exceeded: {current_ram:.2f}GB > {self.max_memory_gb}GB")
            raise ERR_CPU_LOAD_FAIL(f"Memory usage {current_ram:.2f}GB exceeds limit of {self.max_memory_gb}GB")
        logger.debug(f"Memory usage OK: {current_ram:.2f}GB")
    
    def _log_peak_memory(self, step: int):
        """
        Log peak memory usage at a given step.
        
        Args:
            step: Current training step
        """
        current_ram = self._check_memory_usage()
        if self.metrics:
            self.metrics.log_metric('peak_ram_gb', current_ram, step)
        logger.info(f"Step {step}: Peak RAM usage = {current_ram:.2f}GB")
    
    def setup(self, seed: int):
        """
        Initialize model, data loader, and training components.
        
        Args:
            seed: Random seed for reproducibility
        """
        self.current_seed = seed
        logger.info(f"Setting up trainer with seed {seed}")
        
        # Verify baseline stability before proceeding
        try:
            threshold_info = get_baseline_thresholds(self.config.model_id, seed)
            if not threshold_info:
                raise DATA_INTEGRITY_ERROR(f"No valid baseline found for model {self.config.model_id} and seed {seed}")
            logger.info(f"Baseline thresholds verified: {threshold_info}")
        except Exception as e:
            logger.error(f"Baseline verification failed: {str(e)}")
            raise
        
        # Load model
        logger.info(f"Loading model {self.config.model_id} on {self.device}")
        try:
            self.model, self.tokenizer = load_model(
                model_id=self.config.model_id,
                device=self.device,
                quantization=True
            )
        except ERR_CPU_LOAD_FAIL:
            logger.error("Failed to load model due to CPU memory constraints")
            raise
        
        # Initialize data loader
        self.data_loader = GSM8KDataLoader(
            split="train",
            max_samples=self.config.max_samples
        )
        
        # Initialize staleness queue
        self.staleness_queue = StalenessQueue(
            buffer_size=self.staleness_config.buffer_size,
            staleness_level=self.staleness_config.staleness_level
        )
        
        # Initialize metrics collector
        self.metrics = MetricsCollector(
            output_dir="data/processed",
            model_id=self.config.model_id,
            seed=seed
        )
        
        # Initial memory check
        self._enforce_memory_limit()
        logger.info("Setup complete")
    
    def train_step(self, batch: dict, step: int) -> dict:
        """
        Execute a single training step with staleness handling.
        
        Args:
            batch: Input batch from data loader
            step: Current training step
            
        Returns:
            dict: Training results including loss and metrics
        """
        # Check memory before step
        self._enforce_memory_limit()
        
        # Get current staleness level
        current_staleness = self.staleness_queue.get_current_staleness()
        
        # Forward pass (simplified for CPU demonstration)
        with torch.no_grad():
            outputs = self.model(**batch)
            loss = outputs.loss
        
        # Backward pass
        loss.backward()
        
        # Get gradient norms
        grad_norm = 0.0
        for param in self.model.parameters():
            if param.grad is not None:
                grad_norm += param.grad.norm().item() ** 2
        grad_norm = grad_norm ** 0.5
        
        # Log metrics
        self.metrics.log_metric('loss', loss.item(), step)
        self.metrics.log_metric('grad_norm', grad_norm, step)
        self.metrics.log_metric('staleness_level', current_staleness, step)
        
        # Log peak memory
        self._log_peak_memory(step)
        
        # Add gradient to staleness queue
        self.staleness_queue.add_gradient(grad_norm)
        
        # Apply delayed update if staleness condition met
        if self.staleness_queue.should_update():
            update_grad = self.staleness_queue.get_oldest_gradient()
            # In a real implementation, apply update_grad here
            self.staleness_queue.clear_oldest()
        
        return {
            'loss': loss.item(),
            'grad_norm': grad_norm,
            'staleness': current_staleness,
            'ram_usage': self._check_memory_usage()
        }
    
    def run(self, max_steps: int = 1000):
        """
        Execute the full training loop.
        
        Args:
            max_steps: Maximum number of training steps
        """
        logger.info(f"Starting training for {max_steps} steps")
        start_time = time.time()
        
        try:
            for step in range(max_steps):
                # Get next batch
                batch = next(self.data_loader)
                
                # Execute training step
                result = self.train_step(batch, step)
                
                # Log progress
                if step % 100 == 0:
                    logger.info(f"Step {step}/{max_steps} - Loss: {result['loss']:.4f}, "
                              f"Grad Norm: {result['grad_norm']:.4f}, "
                              f"Staleness: {result['staleness']}, "
                              f"RAM: {result['ram_usage']:.2f}GB")
                
                # Periodic memory check
                if step % 500 == 0:
                    self._enforce_memory_limit()
        
        except ERR_CPU_LOAD_FAIL as e:
            logger.error(f"Training aborted due to memory limit: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Training failed with error: {str(e)}")
            raise
        finally:
            # Save final metrics
            if self.metrics:
                self.metrics.save()
            
            elapsed_time = time.time() - start_time
            logger.info(f"Training completed in {elapsed_time:.2f} seconds")
            self.metrics.log_metric('total_time_seconds', elapsed_time, max_steps)
            self.metrics.save()

def main():
    """
    Main entry point for the trainer.
    """
    from src.llmxive.config import load_config
    
    # Load configuration
    config = load_config()
    staleness_config = StalenessConfig(
        staleness_level=config.staleness_level,
        buffer_size=config.buffer_size
    )
    
    # Initialize trainer
    trainer = AsyncRLTrainer(config.training_config, staleness_config)
    
    # Run with specified seed
    seed = config.seed
    trainer.setup(seed)
    trainer.train(max_steps=config.max_steps)

if __name__ == "__main__":
    main()
