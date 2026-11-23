import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    try:
        import resource
        # Get memory usage of current process
        usage = resource.getrusage(resource.RUSAGE_SELF)
        return usage.ru_maxrss / 1024  # Convert KB to MB on Linux
    except ImportError:
        # Fallback for non-Unix systems (approximate)
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)

def check_memory_and_log(current_step: int, memory_limit_mb: int, logger: Any) -> bool:
    """
    Check if memory usage exceeds limit.
    Returns True if limit exceeded (should terminate), False otherwise.
    """
    current_mem = get_memory_usage_mb()
    if current_mem > memory_limit_mb:
        if logger:
            logger.log_step(current_step, {"memory_usage_mb": current_mem, "reason": "Memory Limit Exceeded"})
        return True
    return False

def handle_termination(reason: str, partial_data: Optional[list], output_path: str):
    """
    Handle graceful termination.
    Saves partial state if available and logs the specific reason.
    """
    status = {
        "termination_reason": reason,
        "timestamp": datetime.now().isoformat(),
        "steps_saved": len(partial_data) if partial_data else 0
    }
    
    # Log to file
    log_path = output_path.replace('.parquet', '_termination.json')
    with open(log_path, 'w') as f:
        json.dump(status, f, indent=2)
    
    print(f"Terminated: {reason}. Partial state saved to {log_path}")
    sys.exit(0)
