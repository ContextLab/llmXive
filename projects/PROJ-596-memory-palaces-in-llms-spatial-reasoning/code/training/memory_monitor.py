import os
import json
import time
import gc
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# Try to import psutil for accurate RSS measurement, fall back to /proc if unavailable
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Constants for memory thresholds (in GB)
RSS_THRESHOLD_GB = 6.0
INITIAL_BATCH_SIZE = 8
REDUCED_BATCH_SIZE = 4
DATASET_CAP_FRACTION = 0.5  # Cap to 50% of original size if memory still exceeded

def get_current_memory_usage_gb() -> float:
    """
    Get the current Resident Set Size (RSS) memory usage of the current process in GB.
    
    Returns:
        float: Memory usage in GB.
    """
    if HAS_PSUTIL:
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        return mem_info.rss / (1024 ** 3)
    else:
        # Fallback for Linux: read /proc/self/status
        if os.name == 'posix':
            try:
                with open('/proc/self/status', 'r') as f:
                    for line in f:
                        if line.startswith('VmRSS:'):
                            # VmRSS is in kB
                            rss_kb = int(line.split()[1])
                            return rss_kb / (1024 * 1024)  # Convert to GB
            except (IOError, ValueError):
                pass
        # If we can't determine, return 0 or raise an error
        # Returning 0 allows the code to continue but might be inaccurate
        return 0.0

class MemoryMonitor:
    """
    Monitors memory usage during training and triggers adaptive batch size reduction
    and dataset capping if memory thresholds are exceeded.
    """

    def __init__(self, 
                 initial_batch_size: int = INITIAL_BATCH_SIZE,
                 reduced_batch_size: int = REDUCED_BATCH_SIZE,
                 rss_threshold_gb: float = RSS_THRESHOLD_GB,
                 dataset_cap_fraction: float = DATASET_CAP_FRACTION,
                 log_path: Optional[Path] = None):
        """
        Initialize the MemoryMonitor.

        Args:
            initial_batch_size: Starting batch size (default: 8).
            reduced_batch_size: Batch size to reduce to if RSS > 6GB (default: 4).
            rss_threshold_gb: Memory threshold in GB to trigger reduction (default: 6.0).
            dataset_cap_fraction: Fraction of dataset to keep if memory still exceeded (default: 0.5).
            log_path: Path to save the memory log file. If None, defaults to artifacts/results/memory_log.json.
        """
        self.initial_batch_size = initial_batch_size
        self.reduced_batch_size = reduced_batch_size
        self.rss_threshold_gb = rss_threshold_gb
        self.dataset_cap_fraction = dataset_cap_fraction
        
        self.current_batch_size = initial_batch_size
        self.dataset_capped = False
        self.original_dataset_size = None
        self.capped_dataset_size = None
        self.log_entries = []
        self.start_time = time.time()

        # Set log path
        if log_path is None:
            log_dir = Path("artifacts/results")
            log_dir.mkdir(parents=True, exist_ok=True)
            self.log_path = log_dir / "memory_log.json"
        else:
            self.log_path = Path(log_path)
            self.log_path.parent.mkdir(parents=True, exist_ok=True)

        self._log_event("monitor_initialized", {
            "initial_batch_size": self.initial_batch_size,
            "rss_threshold_gb": self.rss_threshold_gb,
            "dataset_cap_fraction": self.dataset_cap_fraction
        })

    def _log_event(self, event_type: str, details: Dict[str, Any]):
        """
        Log a memory-related event.
        
        Args:
            event_type: Type of event (e.g., 'memory_check', 'batch_size_reduced', 'dataset_capped').
        details: Dictionary of details about the event.
        """
        entry = {
            "timestamp": time.time(),
            "elapsed_seconds": time.time() - self.start_time,
            "event_type": event_type,
            "current_memory_gb": get_current_memory_usage_gb(),
            "current_batch_size": self.current_batch_size,
            "dataset_capped": self.dataset_capped,
            "details": details
        }
        self.log_entries.append(entry)

    def check_and_adapt(self, current_dataset_size: Optional[int] = None) -> Tuple[int, bool, Optional[int]]:
        """
        Check current memory usage and adapt batch size and dataset size if necessary.
        
        This method implements the following logic:
        1. Check current RSS memory.
        2. If RSS > 6GB and batch_size is still at initial (8), reduce to 4.
        3. If RSS > 6GB and batch_size is already 4, cap dataset to 50% of original size.
        
        Args:
            current_dataset_size: The current size of the dataset being used. If None, 
                                  assumes no capping has occurred yet.
        
        Returns:
            Tuple containing:
                - int: The new effective batch size.
                - bool: Whether the dataset was capped in this call.
                - int or None: The new dataset size if capped, None otherwise.
        """
        current_rss_gb = get_current_memory_usage_gb()
        self._log_event("memory_check", {"current_rss_gb": current_rss_gb})

        dataset_capped_this_call = False
        new_dataset_size = None

        if current_rss_gb > self.rss_threshold_gb:
            if self.current_batch_size == self.initial_batch_size:
                # First level of adaptation: reduce batch size
                self.current_batch_size = self.reduced_batch_size
                self._log_event("batch_size_reduced", {
                    "old_batch_size": self.initial_batch_size,
                    "new_batch_size": self.reduced_batch_size,
                    "reason": f"RSS ({current_rss_gb:.2f} GB) exceeded threshold ({self.rss_threshold_gb} GB)"
                })
            elif self.current_batch_size == self.reduced_batch_size:
                # Second level of adaptation: cap dataset size
                if current_dataset_size is not None:
                    # If we haven't capped yet, calculate new size
                    if not self.dataset_capped:
                        self.original_dataset_size = current_dataset_size
                        self.capped_dataset_size = int(current_dataset_size * self.dataset_cap_fraction)
                        self.dataset_capped = True
                        dataset_capped_this_call = True
                        new_dataset_size = self.capped_dataset_size
                        
                        self._log_event("dataset_capped", {
                            "original_size": self.original_dataset_size,
                            "capped_size": self.capped_dataset_size,
                            "fraction": self.dataset_cap_fraction,
                            "reason": f"RSS ({current_rss_gb:.2f} GB) still exceeded threshold ({self.rss_threshold_gb} GB) after batch size reduction"
                        })
                    else:
                        # Already capped, no further action on dataset size
                        self._log_event("dataset_already_capped", {
                            "current_capped_size": self.capped_dataset_size,
                            "current_rss_gb": current_rss_gb
                        })
                else:
                    # Dataset size not provided, cannot cap
                    self._log_event("dataset_capping_skipped", {
                        "reason": "current_dataset_size not provided",
                        "current_rss_gb": current_rss_gb
                    })
        else:
            self._log_event("memory_within_threshold", {"current_rss_gb": current_rss_gb})

        return self.current_batch_size, dataset_capped_this_call, new_dataset_size

    def get_final_hyperparameters(self) -> Dict[str, Any]:
        """
        Get the final hyperparameters after all adaptations.
        
        Returns:
            Dictionary containing final batch size, dataset capping status, and sizes.
        """
        return {
            "final_batch_size": self.current_batch_size,
            "dataset_capped": self.dataset_capped,
            "original_dataset_size": self.original_dataset_size,
            "capped_dataset_size": self.capped_dataset_size,
            "rss_threshold_gb": self.rss_threshold_gb,
            "dataset_cap_fraction": self.dataset_cap_fraction,
            "final_memory_gb": get_current_memory_usage_gb()
        }

    def save_log(self):
        """
        Save the memory log to the specified file path.
        """
        log_data = {
            "monitor_config": {
                "initial_batch_size": self.initial_batch_size,
                "reduced_batch_size": self.reduced_batch_size,
                "rss_threshold_gb": self.rss_threshold_gb,
                "dataset_cap_fraction": self.dataset_cap_fraction
            },
            "final_hyperparameters": self.get_final_hyperparameters(),
            "log_entries": self.log_entries
        }
        
        with open(self.log_path, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        print(f"Memory monitor log saved to {self.log_path}")

    def clear_cache(self):
        """
        Clear PyTorch cache and run garbage collection.
        """
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()


def main():
    """
    Main function to demonstrate the MemoryMonitor usage.
    This is a simple test script that simulates memory pressure and shows the adaptation logic.
    """
    import torch
    import numpy as np

    print("Starting MemoryMonitor demonstration...")
    
    monitor = MemoryMonitor(
        initial_batch_size=8,
        reduced_batch_size=4,
        rss_threshold_gb=6.0,
        dataset_cap_fraction=0.5,
        log_path=Path("artifacts/results/memory_monitor_test.json")
    )

    # Simulate initial dataset size
    initial_dataset_size = 10000
    print(f"Initial dataset size: {initial_dataset_size}")

    # Simulate memory check with low memory
    print("\n--- Simulating low memory scenario ---")
    # We can't easily simulate low memory without actual pressure, 
    # so we'll just call check_and_adapt
    batch_size, capped, new_size = monitor.check_and_adapt(initial_dataset_size)
    print(f"After check (low memory): batch_size={batch_size}, capped={capped}, new_size={new_size}")

    # Simulate high memory scenario by pretending RSS is high
    # In a real scenario, this would happen naturally
    print("\n--- Simulating high memory scenario (mocked) ---")
    
    # We need to override get_current_memory_usage_gb for demonstration
    # But since we can't easily do that in a clean way, we'll just show the logic
    # by directly manipulating the monitor's internal state for the sake of the demo
    
    # Reset monitor for a clean test
    monitor2 = MemoryMonitor(
        initial_batch_size=8,
        reduced_batch_size=4,
        rss_threshold_gb=6.0,
        dataset_cap_fraction=0.5,
        log_path=Path("artifacts/results/memory_monitor_test2.json")
    )
    
    # Mock the memory check to simulate high memory
    original_get_memory = get_current_memory_usage_gb
    
    def mock_high_memory():
        return 7.5  # Simulate 7.5 GB usage
    
    # Temporarily replace the function
    import training.memory_monitor as mm_module
    mm_module.get_current_memory_usage_gb = mock_high_memory
    
    try:
        # First check: should reduce batch size
        batch_size, capped, new_size = monitor2.check_and_adapt(initial_dataset_size)
        print(f"First check (high memory): batch_size={batch_size}, capped={capped}, new_size={new_size}")
        
        # Second check: should cap dataset
        batch_size, capped, new_size = monitor2.check_and_adapt(initial_dataset_size)
        print(f"Second check (still high memory): batch_size={batch_size}, capped={capped}, new_size={new_size}")
        
        # Third check: dataset already capped
        batch_size, capped, new_size = monitor2.check_and_adapt(initial_dataset_size)
        print(f"Third check (dataset already capped): batch_size={batch_size}, capped={capped}, new_size={new_size}")
        
    finally:
        # Restore original function
        mm_module.get_current_memory_usage_gb = original_get_memory

    # Save logs
    monitor.save_log()
    monitor2.save_log()
    
    print("\nFinal hyperparameters from monitor2:")
    print(json.dumps(monitor2.get_final_hyperparameters(), indent=2))
    
    print("\nDemonstration complete.")


if __name__ == "__main__":
    main()