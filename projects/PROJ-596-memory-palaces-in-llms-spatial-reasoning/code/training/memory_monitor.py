import os
import json
import time
import gc
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# Constants
RSS_THRESHOLD_GB = 6.0
INITIAL_BATCH_SIZE = 8
REDUCED_BATCH_SIZE = 4
DATASET_CAP_FRACTION = 0.5  # Cap to 50% of original size if memory still exceeds threshold

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('artifacts/results/memory_monitor.log')
    ]
)
logger = logging.getLogger(__name__)

def get_current_memory_usage_gb() -> float:
    """
    Get the current Resident Set Size (RSS) memory usage in GB.
    Uses /proc/self/status on Linux or psutil if available.
    Falls back to a safe estimate if neither is available.
    """
    try:
        # Try psutil first (more robust)
        import psutil
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        return mem_info.rss / (1024 ** 3)  # Convert bytes to GB
    except ImportError:
        pass

    try:
        # Fallback to /proc/self/status on Linux
        with open('/proc/self/status', 'r') as f:
            for line in f:
                if line.startswith('VmRSS:'):
                    # VmRSS is in kB
                    rss_kb = int(line.split()[1])
                    return rss_kb / (1024 * 1024)  # Convert kB to GB
    except (FileNotFoundError, IndexError, ValueError):
        logger.warning("Could not read memory usage from /proc/self/status.")
    
    # Final fallback: return 0.0 and let the caller handle it
    logger.error("Could not determine memory usage. Returning 0.0.")
    return 0.0

class MemoryMonitor:
    """
    Monitors memory usage during training and adjusts hyperparameters accordingly.
    
    Behavior:
    1. Checks current RSS.
    2. If RSS > 6GB, reduces batch size to 4.
    3. If RSS still > 6GB after reduction, caps the dataset to 50% of its original size.
    4. Logs all decisions and final hyperparameters.
    """

    def __init__(self, output_path: str = "artifacts/results/memory_log.json"):
        self.output_path = Path(output_path)
        self.initial_batch_size = INITIAL_BATCH_SIZE
        self.reduced_batch_size = REDUCED_BATCH_SIZE
        self.dataset_cap_fraction = DATASET_CAP_FRACTION
        self.current_batch_size = self.initial_batch_size
        self.dataset_capped = False
        self.original_dataset_size = 0
        self.final_dataset_size = 0
        self.memory_log: Dict[str, Any] = {
            "decisions": [],
            "final_hyperparameters": {},
            "memory_readings": []
        }
        self._ensure_output_dir()

    def _ensure_output_dir(self):
        """Ensure the output directory exists."""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def log_decision(self, action: str, details: str):
        """Log a decision made by the monitor."""
        entry = {
            "timestamp": time.time(),
            "action": action,
            "details": details,
            "current_rss_gb": get_current_memory_usage_gb()
        }
        self.memory_log["decisions"].append(entry)
        logger.info(f"Decision: {action} - {details}")

    def log_memory_reading(self, reason: str = "Periodic check"):
        """Log a memory reading."""
        rss = get_current_memory_usage_gb()
        self.memory_log["memory_readings"].append({
            "timestamp": time.time(),
            "reason": reason,
            "rss_gb": rss
        })
        logger.info(f"Memory Reading ({reason}): {rss:.2f} GB")
        return rss

    def check_and_adjust(self, current_dataset_size: int) -> Tuple[int, int]:
        """
        Check memory usage and adjust batch size and dataset size if necessary.
        
        Args:
            current_dataset_size: The original size of the dataset.
        
        Returns:
            A tuple of (adjusted_batch_size, adjusted_dataset_size).
        """
        self.original_dataset_size = current_dataset_size
        self.final_dataset_size = current_dataset_size
        self.current_batch_size = self.initial_batch_size

        # Initial check
        rss = self.log_memory_reading("Initial check")

        if rss > RSS_THRESHOLD_GB:
            self.log_decision(
                "Batch Size Reduction",
                f"RSS ({rss:.2f} GB) exceeds threshold ({RSS_THRESHOLD_GB} GB). "
                f"Reducing batch size from {self.initial_batch_size} to {self.reduced_batch_size}."
            )
            self.current_batch_size = self.reduced_batch_size
            
            # Force garbage collection after batch size reduction
            gc.collect()
            
            # Re-check memory
            rss_after = self.log_memory_reading("After batch size reduction")
            
            if rss_after > RSS_THRESHOLD_GB:
                self.log_decision(
                    "Dataset Capping",
                    f"RSS ({rss_after:.2f} GB) still exceeds threshold after batch size reduction. "
                    f"Capping dataset to {self.dataset_cap_fraction * 100}% of original size."
                )
                self.final_dataset_size = int(current_dataset_size * self.dataset_cap_fraction)
                self.dataset_capped = True
                
                # Force garbage collection after dataset capping
                gc.collect()
                
                # Final check
                rss_final = self.log_memory_reading("After dataset capping")
                if rss_final > RSS_THRESHOLD_GB:
                    self.log_decision(
                        "Critical Warning",
                        f"RSS ({rss_final:.2f} GB) still exceeds threshold after all adjustments. "
                        f"Training may fail due to OOM."
                    )
            else:
                self.log_decision(
                    "Memory Stabilized",
                    f"RSS ({rss_after:.2f} GB) is now within threshold after batch size reduction."
                )
        else:
            self.log_decision(
                "Memory Within Limits",
                f"RSS ({rss:.2f} GB) is within threshold. No adjustments needed."
            )

        # Log final hyperparameters
        self.memory_log["final_hyperparameters"] = {
            "initial_batch_size": self.initial_batch_size,
            "reduced_batch_size": self.reduced_batch_size,
            "dataset_cap_fraction": self.dataset_cap_fraction,
            "final_batch_size": self.current_batch_size,
            "original_dataset_size": self.original_dataset_size,
            "final_dataset_size": self.final_dataset_size,
            "dataset_capped": self.dataset_capped,
            "rss_threshold_gb": RSS_THRESHOLD_GB
        }

        self._save_log()
        return self.current_batch_size, self.final_dataset_size

    def _save_log(self):
        """Save the memory log to a JSON file."""
        with open(self.output_path, 'w') as f:
            json.dump(self.memory_log, f, indent=2)
        logger.info(f"Memory log saved to {self.output_path}")

    def get_final_hyperparameters(self) -> Dict[str, Any]:
        """Return the final hyperparameters after adjustments."""
        return self.memory_log["final_hyperparameters"]

def main():
    """
    Main function to demonstrate the memory monitor's functionality.
    This is typically called by the training loop.
    """
    monitor = MemoryMonitor()
    
    # Simulate a dataset size
    simulated_dataset_size = 10000
    print(f"Starting memory check for dataset of size {simulated_dataset_size}...")
    
    batch_size, capped_size = monitor.check_and_adjust(simulated_dataset_size)
    
    print(f"Final Batch Size: {batch_size}")
    print(f"Final Dataset Size: {capped_size}")
    print(f"Dataset Capped: {monitor.dataset_capped}")
    
    # Print final hyperparameters
    final_params = monitor.get_final_hyperparameters()
    print("\nFinal Hyperparameters:")
    for key, value in final_params.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    main()