"""
Global timeout enforcement utility.
Ensures the research pipeline does not exceed the allocated compute budget.
"""
import time
import sys
from pathlib import Path
from typing import Optional

class TimeoutState:
    def __init__(self):
        self.start_time: Optional[float] = None
        self.duration: Optional[float] = None
        self.exceeded: bool = False

# Singleton state
_state = TimeoutState()

def set_global_timeout(seconds: float):
    """Initialize the global timeout timer."""
    _state.start_time = time.time()
    _state.duration = seconds

def check_timeout() -> bool:
    """
    Check if the current elapsed time exceeds the duration.
    Returns True if timed out, False otherwise.
    """
    if _state.start_time is None or _state.duration is None:
        return False
    
    elapsed = time.time() - _state.start_time
    if elapsed > _state.duration:
        _state.exceeded = True
        return True
    return False

def get_remaining_time_seconds() -> float:
    """Calculate remaining time in the budget."""
    if _state.start_time is None or _state.duration is None:
        return 0.0
    elapsed = time.time() - _state.start_time
    return max(0.0, _state.duration - elapsed)

def log_timeout_warning():
    """Write a timeout warning to the dedicated log file."""
    log_path = Path("logs/timeout.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{time.ctime()}: Global timeout of {_state.duration}s exceeded.\n")

def get_timeout_context() -> TimeoutState:
    """Return the current timeout state object."""
    return _state
