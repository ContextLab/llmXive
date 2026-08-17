"""
Runtime monitoring for dataset generation.
Ensures the generation process stays within time bounds.
"""
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

class RuntimeMonitor:
    """Monitors runtime and provides early stop recommendations."""
    
    def __init__(self, max_runtime_hours: float = 5.5):
        """
        Initialize the runtime monitor.
        
        Args:
            max_runtime_hours: Maximum allowed runtime in hours.
        """
        self.max_runtime_seconds = max_runtime_hours * 3600
        self.start_time = time.time()
        logger.info(f"Runtime monitor initialized with max runtime: {max_runtime_hours} hours")
    
    def get_elapsed_seconds(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self.start_time
    
    def get_remaining_seconds(self) -> float:
        """Get remaining time in seconds."""
        elapsed = self.get_elapsed_seconds()
        return max(0, self.max_runtime_seconds - elapsed)
    
    def should_stop(self, current_sample_count: int, min_sample_floor: int) -> bool:
        """
        Determine if the process should stop early.
        
        Args:
            current_sample_count: Current number of samples processed.
            min_sample_floor: Minimum number of samples required.
            
        Returns:
            True if should stop, False otherwise.
        """
        elapsed = self.get_elapsed_seconds()
        remaining = self.get_remaining_seconds()
        
        # If we're below the minimum floor, don't stop
        if current_sample_count <= min_sample_floor:
            if remaining < 60:  # Less than 1 minute left
                logger.warning(f"Reached minimum sample floor ({min_sample_floor}) with only {remaining:.0f}s remaining. Stopping gracefully.")
                return True
            return False
        
        # If we're above the minimum floor and time is running low
        # Reserve some time for validation (e.g., 30 minutes)
        reserve_time = 30 * 60  # 30 minutes
        if remaining <= reserve_time:
            logger.info(f"Approaching time limit. Remaining: {remaining:.0f}s, Reserve: {reserve_time}s. Suggesting early stop.")
            return True
        
        return False
    
    def log_status(self, sample_count: int) -> None:
        """Log current runtime status."""
        elapsed = self.get_elapsed_seconds()
        remaining = self.get_remaining_seconds()
        elapsed_hours = elapsed / 3600
        remaining_hours = remaining / 3600
        
        logger.info(f"Runtime status: {sample_count} samples, elapsed: {elapsed_hours:.2f}h, remaining: {remaining_hours:.2f}h")

def main():
    """Main entry point for testing the monitor."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test runtime monitor")
    parser.add_argument("--max-hours", type=float, default=5.5,
                      help="Maximum runtime in hours")
    parser.add_argument("--min-floor", type=int, default=300,
                      help="Minimum sample floor")
    
    args = parser.parse_args()
    
    monitor = RuntimeMonitor(max_runtime_hours=args.max_hours)
    
    print(f"Testing runtime monitor with max {args.max_hours} hours")
    print(f"Minimum sample floor: {args.min_floor}")
    
    # Simulate some samples
    for i in range(10):
        time.sleep(1)
        monitor.log_status(i * 100)
        if monitor.should_stop(i * 100, args.min_floor):
            print("Monitor suggests stopping!")
            break
    
    print("Monitor test complete")
