"""
Memory monitoring utility for training loop.

Tracks RSS memory usage and implements adaptive strategies:
1. Reduce batch size from 8 to 4 if RSS > 5GB.
2. Cap training dataset to 50% of original size if RSS > 6GB after batch size reduction.
"""
import os
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    import warnings
    warnings.warn("psutil not installed. Memory monitoring will be limited.")


class MemoryMonitor:
    """
    Monitors system memory (RSS) and manages training hyperparameters dynamically.
    """

    def __init__(
        self,
        log_path: Optional[Path] = None,
        initial_batch_size: int = 8,
        reduced_batch_size: int = 4,
        rss_warning_threshold_gb: float = 5.0,
        rss_critical_threshold_gb: float = 6.0,
        dataset_reduction_factor: float = 0.5
    ):
        """
        Initialize the memory monitor.

        Args:
            log_path: Path to write the hyperparameter log JSON.
            initial_batch_size: Starting batch size.
            reduced_batch_size: Batch size to switch to if memory warning is triggered.
            rss_warning_threshold_gb: RSS threshold (GB) to trigger batch size reduction.
            rss_critical_threshold_gb: RSS threshold (GB) to trigger dataset capping.
            dataset_reduction_factor: Factor to multiply dataset size by if critical memory.
        """
        self.log_path = log_path
        self.initial_batch_size = initial_batch_size
        self.reduced_batch_size = reduced_batch_size
        self.rss_warning_threshold_gb = rss_warning_threshold_gb
        self.rss_critical_threshold_gb = rss_critical_threshold_gb
        self.dataset_reduction_factor = dataset_reduction_factor

        # State
        self.current_batch_size = initial_batch_size
        self.dataset_capped = False
        self.capped_dataset_size = None
        self.original_dataset_size = None
        self.log_history: list[Dict[str, Any]] = []

        if log_path:
            log_path.parent.mkdir(parents=True, exist_ok=True)

    def get_current_rss_gb(self) -> float:
        """
        Get current Resident Set Size (RSS) in Gigabytes.

        Returns:
            Current RSS in GB. Returns 0.0 if psutil is unavailable.
        """
        if not PSUTIL_AVAILABLE:
            return 0.0

        process = psutil.Process(os.getpid())
        # memory_info returns bytes
        rss_bytes = process.memory_info().rss
        return rss_bytes / (1024 ** 3)

    def check_and_adapt(self, current_dataset_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Check current memory usage and adapt hyperparameters if necessary.

        This function implements the logic:
        1. If RSS > 5GB and batch size is still 8, reduce to 4.
        2. If RSS > 6GB and batch size is already 4, cap dataset to 50%.

        Args:
            current_dataset_size: The original size of the dataset being used.

        Returns:
            A dictionary containing the current state and decisions made.
        """
        rss_gb = self.get_current_rss_gb()
        timestamp = time.time()

        decision = {
            "timestamp": timestamp,
            "rss_gb": rss_gb,
            "current_batch_size": self.current_batch_size,
            "dataset_capped": self.dataset_capped,
            "action_taken": None,
            "final_batch_size": self.current_batch_size,
            "final_dataset_size": current_dataset_size
        }

        # Logic 1: Reduce Batch Size
        if not self.dataset_capped:
            if rss_gb > self.rss_warning_threshold_gb:
                if self.current_batch_size == self.initial_batch_size:
                    self.current_batch_size = self.reduced_batch_size
                    decision["action_taken"] = "reduce_batch_size"
                    decision["final_batch_size"] = self.reduced_batch_size
                # If we already reduced batch size, we proceed to check critical threshold
                # Logic 2: Cap Dataset (only if we are at reduced batch size and still high)
                if rss_gb > self.rss_critical_threshold_gb and self.current_batch_size == self.reduced_batch_size:
                    if current_dataset_size is not None:
                        self.original_dataset_size = current_dataset_size
                        new_size = int(current_dataset_size * self.dataset_reduction_factor)
                        self.capped_dataset_size = new_size
                        self.dataset_capped = True
                        decision["action_taken"] = "cap_dataset"
                        decision["final_dataset_size"] = new_size
                        decision["dataset_reduction_factor"] = self.dataset_reduction_factor
                    else:
                        decision["action_taken"] = "warning_dataset_cap_needed"
                        decision["message"] = "Dataset size not provided, cannot cap."

        self.log_history.append(decision)

        # Persist log if path is set
        if self.log_path:
            self._write_log()

        return decision

    def _write_log(self) -> None:
        """Write the current log history to the JSON file."""
        if not self.log_path:
            return

        output_data = {
            "monitor_config": {
                "initial_batch_size": self.initial_batch_size,
                "reduced_batch_size": self.reduced_batch_size,
                "rss_warning_threshold_gb": self.rss_warning_threshold_gb,
                "rss_critical_threshold_gb": self.rss_critical_threshold_gb,
                "dataset_reduction_factor": self.dataset_reduction_factor
            },
            "final_state": {
                "effective_batch_size": self.current_batch_size,
                "dataset_capped": self.dataset_capped,
                "original_dataset_size": self.original_dataset_size,
                "effective_dataset_size": self.capped_dataset_size if self.dataset_capped else self.original_dataset_size
            },
            "history": self.log_history
        }

        with open(self.log_path, 'w') as f:
            json.dump(output_data, f, indent=2)

    def get_final_hyperparameters(self) -> Dict[str, Any]:
        """
        Retrieve the final effective hyperparameters after monitoring.

        Returns:
            Dictionary with effective_batch_size and effective_dataset_size.
        """
        return {
            "effective_batch_size": self.current_batch_size,
            "dataset_capped": self.dataset_capped,
            "original_dataset_size": self.original_dataset_size,
            "effective_dataset_size": self.capped_dataset_size if self.dataset_capped else self.original_dataset_size
        }


def main():
    """
    Standalone execution for testing the memory monitor logic.
    Simulates a training loop check.
    """
    log_path = Path("artifacts/results/hyperparams_log.json")
    monitor = MemoryMonitor(
        log_path=log_path,
        initial_batch_size=8,
        reduced_batch_size=4,
        rss_warning_threshold_gb=5.0,
        rss_critical_threshold_gb=6.0,
        dataset_reduction_factor=0.5
    )

    print("Starting Memory Monitor Test...")
    print(f"Initial Batch Size: {monitor.initial_batch_size}")

    # Simulate checks
    # Check 1: Normal memory
    decision = monitor.check_and_adapt(current_dataset_size=10000)
    print(f"Check 1 (Normal): RSS={decision['rss_gb']:.2f}GB, Batch={decision['current_batch_size']}, Action={decision['action_taken']}")

    # In a real scenario, we would inject memory or wait for training to consume it.
    # Here we just demonstrate the logic flow by calling it again.
    # If psutil is not available, RSS will be 0.0, and no action will be taken.
    
    if PSUTIL_AVAILABLE:
        # Simulate a high memory scenario by forcing the logic path manually for demonstration
        # In real usage, this happens automatically based on system state.
        print("\nSimulating high memory scenario (logic path only)...")
        
        # Force a state where we are above warning threshold
        # We can't easily force the OS to report high RSS without actual load,
        # but we can verify the logic by checking the thresholds.
        print(f"Warning Threshold: {monitor.rss_warning_threshold_gb}GB")
        print(f"Critical Threshold: {monitor.rss_critical_threshold_gb}GB")
        
        # If we were to run this inside a training loop that actually consumes memory,
        # the monitor would automatically reduce batch size or cap the dataset.
    
    print("\nFinal Hyperparameters:")
    final_params = monitor.get_final_hyperparameters()
    for k, v in final_params.items():
        print(f"  {k}: {v}")

    print(f"\nLog written to: {log_path}")


if __name__ == "__main__":
    main()