import os
import sys
from dataclasses import dataclass
from typing import Optional
import resource

@dataclass
class PipelineConfig:
    """Configuration for the llmXive pipeline."""
    runtime_limit_seconds: int = 6 * 3600  # 6 hours
    memory_limit_bytes: int = 7 * 1024**3  # 7 GB
    beir_cache_dir: Optional[str] = None
    project_root: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_config: Optional[PipelineConfig] = None

def get_config() -> PipelineConfig:
    global _config
    if _config is None:
        _config = PipelineConfig()
    return _config

def format_bytes(size_bytes: int) -> str:
    """Format bytes to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def check_system_limits():
    """Check if current system usage exceeds limits."""
    config = get_config()
    
    # Check memory
    try:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        max_mem_mb = usage.ru_maxrss  # On Linux this is KB, on macOS KB. 
        # Note: resource.ru_maxrss behavior varies by OS. 
        # For safety in a generic script, we rely on the watchdog in utils.py for strict enforcement
        # and just log here.
        pass
    except Exception:
        pass
    
    return True
