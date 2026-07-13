"""
Pipeline configuration for time limits and fallback logic.

This module enforces a predefined wall-clock time limit for analysis tasks
and provides mechanisms to trigger fallback logic when the limit is approached
or exceeded.
"""
import os
import time
import logging
from typing import Optional, Callable, Any
from dataclasses import dataclass, field
from pathlib import Path

from src.config import get_config
from src.pipeline.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class TimeBudgetConfig:
    """Configuration for time budgeting and fallback strategies."""
    
    # Maximum wall-clock time in seconds (default: 300s / 5min for testing)
    # Can be overridden by environment variable WALL_CLOCK_BUDGET_SECONDS
    max_seconds: int = field(
        default_factory=lambda: int(os.getenv("WALL_CLOCK_BUDGET_SECONDS", "300"))
    )
    
    # Percentage of budget at which to trigger soft warning
    warning_threshold: float = 0.8
    
    # Percentage of budget at which to trigger fallback logic
    fallback_threshold: float = 0.95
    
    # Fallback strategy: 'subsampling', 'simplified_model', 'abort'
    fallback_strategy: str = "subsampling"
    
    # Minimum time remaining (seconds) to continue complex operations
    min_remaining_seconds: float = 30.0

class TimeBudgetMonitor:
    """
    Monitors wall-clock time for a specific analysis task.
    
    Tracks elapsed time, remaining budget, and triggers fallback logic
    when thresholds are exceeded.
    """
    
    def __init__(self, budget_config: Optional[TimeBudgetConfig] = None):
        self.config = budget_config or TimeBudgetConfig()
        self.start_time: Optional[float] = None
        self.elapsed: float = 0.0
        self.fallback_triggered: bool = False
        self.fallback_reason: Optional[str] = None
        self._logger = get_logger(__name__)
        
        # Load base config for any additional overrides
        base_config = get_config()
        if hasattr(base_config, 'time_limit_seconds'):
            self.config.max_seconds = base_config.time_limit_seconds
        
        self._logger.info(
            "TimeBudgetMonitor initialized",
            extra={
                "max_seconds": self.config.max_seconds,
                "warning_threshold": self.config.warning_threshold,
                "fallback_threshold": self.config.fallback_threshold,
                "fallback_strategy": self.config.fallback_strategy
            }
        )
    
    def start(self):
        """Start the time budget timer."""
        self.start_time = time.time()
        self.elapsed = 0.0
        self.fallback_triggered = False
        self._logger.info("TimeBudgetMonitor started")
    
    def stop(self):
        """Stop the timer and log final elapsed time."""
        if self.start_time:
            self.elapsed = time.time() - self.start_time
            self._logger.info(
                "TimeBudgetMonitor stopped",
                extra={"elapsed_seconds": self.elapsed}
            )
            self.start_time = None
    
    def reset(self):
        """Reset the timer without stopping."""
        self.start_time = time.time()
        self.elapsed = 0.0
        self.fallback_triggered = False
    
    def get_elapsed(self) -> float:
        """Get current elapsed time in seconds."""
        if self.start_time is None:
            return self.elapsed
        return time.time() - self.start_time
    
    def get_remaining(self) -> float:
        """Get remaining time in seconds."""
        elapsed = self.get_elapsed()
        return max(0.0, self.config.max_seconds - elapsed)
    
    def get_progress(self) -> float:
        """Get progress as a fraction of the total budget (0.0 to 1.0+)."""
        elapsed = self.get_elapsed()
        return elapsed / self.config.max_seconds
    
    def check_status(self) -> dict:
        """
        Check current time budget status.
        
        Returns:
            dict with keys:
                - 'elapsed': seconds elapsed
                - 'remaining': seconds remaining
                - 'progress': fraction of budget used
                - 'warning': bool, warning threshold exceeded
                - 'fallback': bool, fallback threshold exceeded
                - 'fallback_triggered': bool, if fallback was already triggered
        """
        elapsed = self.get_elapsed()
        remaining = self.get_remaining()
        progress = self.get_progress()
        
        warning = progress >= self.config.warning_threshold
        fallback = progress >= self.config.fallback_threshold
        
        status = {
            "elapsed": elapsed,
            "remaining": remaining,
            "progress": progress,
            "warning": warning,
            "fallback": fallback,
            "fallback_triggered": self.fallback_triggered
        }
        
        if warning and not self.fallback_triggered:
            self._logger.warning(
                "Time budget warning threshold exceeded",
                extra={
                    "elapsed": elapsed,
                    "remaining": remaining,
                    "progress": progress,
                    "threshold": self.config.warning_threshold
                }
            )
        
        if fallback and not self.fallback_triggered:
            self.fallback_triggered = True
            self.fallback_reason = f"Time budget {self.config.fallback_threshold*100:.0f}% exceeded"
            self._logger.warning(
                "Fallback logic triggered due to time budget",
                extra={
                    "elapsed": elapsed,
                    "remaining": remaining,
                    "progress": progress,
                    "strategy": self.config.fallback_strategy
                }
            )
        
        return status
    
    def should_fallback(self) -> bool:
        """Check if fallback logic should be triggered."""
        status = self.check_status()
        return status["fallback"] or status["fallback_triggered"]
    
    def get_fallback_action(self) -> str:
        """Get the recommended fallback action based on current strategy."""
        if not self.should_fallback():
            return "continue"
        
        return self.config.fallback_strategy
    
    def enforce_time_limit(self):
        """
        Enforce hard time limit.
        
        Raises TimeoutError if the budget is exceeded.
        """
        elapsed = self.get_elapsed()
        if elapsed > self.config.max_seconds:
            raise TimeoutError(
                f"Time budget exceeded: {elapsed:.2f}s > {self.config.max_seconds}s"
            )
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False


def with_time_limit(
    budget_config: Optional[TimeBudgetConfig] = None,
    fallback_callback: Optional[Callable] = None
):
    """
    Decorator to enforce time limits on functions.
    
    Args:
        budget_config: TimeBudgetConfig instance
        fallback_callback: Optional callback to execute when fallback is triggered
        
    Returns:
        Decorated function with time limit enforcement
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            monitor = TimeBudgetMonitor(budget_config)
            monitor.start()
            
            try:
                result = func(*args, **kwargs)
                
                # Check if we exceeded time during execution
                if monitor.should_fallback():
                    action = monitor.get_fallback_action()
                    logger.warning(
                        f"Function {func.__name__} exceeded time threshold",
                        extra={
                            "action": action,
                            "elapsed": monitor.get_elapsed()
                        }
                    )
                    
                    if fallback_callback and callable(fallback_callback):
                        fallback_result = fallback_callback(result, monitor)
                        if fallback_result is not None:
                            result = fallback_result
                
                monitor.stop()
                return result
                
            except TimeoutError:
                monitor.stop()
                logger.error(
                    f"Function {func.__name__} hit hard time limit",
                    extra={"elapsed": monitor.get_elapsed()}
                )
                raise
            except Exception as e:
                monitor.stop()
                logger.error(
                    f"Function {func.__name__} failed",
                    extra={"error": str(e)}
                )
                raise
        
        return wrapper
    return decorator


def create_fallback_subsampler(
    sampling_rate: float = 0.33,
    min_samples: int = 100
) -> Callable:
    """
    Create a fallback callback that subsamples data.
    
    Args:
        sampling_rate: Fraction of data to keep (e.g., 0.33 = 1/3)
        min_samples: Minimum number of samples to retain
        
    Returns:
        Callback function for time-limited fallback
    """
    def subsample_callback(result, monitor: TimeBudgetMonitor):
        """Subsample logic for fallback."""
        logger.info(
            "Executing subsampling fallback strategy",
            extra={
                "sampling_rate": sampling_rate,
                "min_samples": min_samples,
                "elapsed": monitor.get_elapsed()
            }
        )
        
        if hasattr(result, 'sample'):
            # Assume result is a DataFrame or similar
            n = max(min_samples, int(len(result) * sampling_rate))
            return result.sample(n=n, random_state=42)
        
        return result
    
    return subsample_callback


# Global monitor instance for pipeline-wide tracking
_global_monitor: Optional[TimeBudgetMonitor] = None


def get_global_monitor() -> TimeBudgetMonitor:
    """Get or create the global time budget monitor."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = TimeBudgetMonitor()
    return _global_monitor


def reset_global_monitor():
    """Reset the global time budget monitor."""
    global _global_monitor
    _global_monitor = None