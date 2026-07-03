"""
Memory monitoring utility for training loops.

Tracks RSS memory usage and triggers adaptive batch size reduction
and dataset capping if thresholds are exceeded.
"""
import gc
import json
import os
import resource
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MEMORY_THRESHOLD_GB = 6.0
MEMORY_THRESHOLD_BYTES = MEMORY_THRESHOLD_GB * (1024 ** 3)
MIN_BATCH_SIZE = 4
DATASET_CUTOFF_FRACTION = 0.25  # [deferred] interpreted as 25% per spec context

class MemoryMonitor:
    """
    Monitors RSS memory usage during training and triggers adaptive strategies.
    """

    def __init__(self, log_path: Optional[str] = None):
        """
        Initialize the memory monitor.
        
        Args:
            log_path: Path to the JSON log file for hyperparameter decisions.
                      Defaults to artifacts/results/memory_log.json.
        """
        self.log_path = log_path or "artifacts/results/memory_log.json"
        self.log_data: Dict[str, Any] = {
            "decisions": [],
            "final_hyperparameters": {}
        }
        
        # Ensure log directory exists
        Path(self.log_path).parent.mkdir(parents=True, exist_ok=True)

    def get_current_rss_gb(self) -> float:
        """
        Get the current Resident Set Size (RSS) in GB.
        
        Returns:
            Current RSS in gigabytes.
        """
        # Use resource module for Unix-like systems (Linux/macOS)
        # For Windows, resource.getrusage is not fully supported for peak, 
        # but we can try to use psutil if available, otherwise fallback to resource
        try:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            # ru_maxrss is in kilobytes on Linux, megabytes on macOS
            # We normalize to bytes
            if os.name == 'posix':
                # Check platform specific behavior
                import platform
                if platform.system() == 'Darwin':
                    # macOS returns MB
                    rss_bytes = usage.ru_maxrss * (1024 ** 2)
                else:
                    # Linux returns KB
                    rss_bytes = usage.ru_maxrss * 1024
            else:
                # Fallback for Windows (if resource works, though often limited)
                rss_bytes = usage.ru_maxrss * 1024 
            
            return rss_bytes / (1024 ** 3)
        except Exception as e:
            logger.warning(f"Could not read resource usage: {e}. Returning 0.0.")
            return 0.0

    def check_and_adjust(
        self, 
        current_batch_size: int, 
        current_dataset_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Check current memory usage and adjust hyperparameters if necessary.
        
        Logic:
        1. If RSS > 6GB:
           a. If batch_size > 4, reduce batch_size to 4.
           b. If batch_size == 4 and RSS still > 6GB, cap dataset to 25% of original.
        
        Args:
            current_batch_size: The currently intended batch size.
            current_dataset_size: The full size of the dataset (if known).
            
        Returns:
            A dictionary containing the adjusted batch size, dataset size, 
            and the decision log.
        """
        rss_gb = self.get_current_rss_gb()
        decision = {
            "timestamp": None, # Will be set by caller or internal logic if needed
            "initial_batch_size": current_batch_size,
            "initial_dataset_size": current_dataset_size,
            "rss_gb": rss_gb,
            "action_taken": "none",
            "final_batch_size": current_batch_size,
            "final_dataset_size": current_dataset_size
        }

        if rss_gb > MEMORY_THRESHOLD_GB:
            logger.warning(f"Memory usage ({rss_gb:.2f} GB) exceeds threshold ({MEMORY_THRESHOLD_GB} GB).")
            
            if current_batch_size > MIN_BATCH_SIZE:
                logger.info(f"Reducing batch size from {current_batch_size} to {MIN_BATCH_SIZE}.")
                decision["action_taken"] = "reduce_batch_size"
                decision["final_batch_size"] = MIN_BATCH_SIZE
                decision["reason"] = f"RSS {rss_gb:.2f}GB > {MEMORY_THRESHOLD_GB}GB"
            elif current_batch_size == MIN_BATCH_SIZE:
                logger.warning(f"Batch size already at minimum ({MIN_BATCH_SIZE}). Capping dataset.")
                if current_dataset_size is not None:
                    new_size = max(1, int(current_dataset_size * DATASET_CUTOFF_FRACTION))
                    logger.info(f"Capping dataset from {current_dataset_size} to {new_size} samples.")
                    decision["action_taken"] = "cap_dataset"
                    decision["final_batch_size"] = MIN_BATCH_SIZE
                    decision["final_dataset_size"] = new_size
                    decision["reason"] = f"RSS {rss_gb:.2f}GB > {MEMORY_THRESHOLD_GB}GB after batch reduction"
                else:
                    logger.error("Dataset size unknown; cannot cap dataset. Please provide current_dataset_size.")
                    decision["action_taken"] = "error_dataset_size_unknown"
                    decision["reason"] = "Dataset size not provided for capping."
            else:
                logger.error(f"Unexpected batch size state: {current_batch_size}.")
                decision["action_taken"] = "error_unexpected_state"
        else:
            logger.info(f"Memory usage ({rss_gb:.2f} GB) within threshold.")
            decision["action_taken"] = "none"

        self.log_data["decisions"].append(decision)
        self.log_data["final_hyperparameters"] = {
            "batch_size": decision["final_batch_size"],
            "dataset_size": decision["final_dataset_size"],
            "threshold_gb": MEMORY_THRESHOLD_GB,
            "dataset_cutoff_fraction": DATASET_CUTOFF_FRACTION
        }
        
        self._save_log()
        
        return {
            "batch_size": decision["final_batch_size"],
            "dataset_size": decision["final_dataset_size"],
            "decision_log": decision
        }

    def _save_log(self):
        """Save the current log state to disk."""
        try:
            with open(self.log_path, 'w') as f:
                json.dump(self.log_data, f, indent=2)
            logger.debug(f"Memory log saved to {self.log_path}")
        except Exception as e:
            logger.error(f"Failed to save memory log: {e}")

    def force_gc(self):
        """Force garbage collection to free up memory."""
        gc.collect()
        logger.debug("Garbage collection forced.")


def main():
    """
    Standalone execution for testing the memory monitor.
    Simulates a check and logs the result.
    """
    monitor = MemoryMonitor(log_path="artifacts/results/memory_log.json")
    
    # Simulate a check with a hypothetical high memory usage scenario
    # In a real training loop, this would be called periodically.
    # Here we just demonstrate the logic path.
    
    print("Running Memory Monitor Self-Test...")
    current_rss = monitor.get_current_rss_gb()
    print(f"Current RSS: {current_rss:.2f} GB")
    
    # Test with a scenario that might trigger reduction if memory is high
    # We pass a large batch size to test reduction logic
    result = monitor.check_and_adjust(current_batch_size=8, current_dataset_size=10000)
    
    print(f"Adjusted Batch Size: {result['batch_size']}")
    print(f"Adjusted Dataset Size: {result['dataset_size']}")
    print(f"Action Taken: {result['decision_log']['action_taken']}")
    
    if result['decision_log']['action_taken'] != "none":
        print("Memory pressure detected and handled.")
    else:
        print("Memory pressure within limits.")

if __name__ == "__main__":
    main()