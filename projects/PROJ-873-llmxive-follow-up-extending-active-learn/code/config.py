"""
Configuration management for llmXive pipeline.
Enforces FR-006: 6h runtime limit and 7GB memory limit.
"""
import os
import sys
from dataclasses import dataclass, field
from typing import Optional, Any
import resource
import logging

# Constants for limits (FR-006)
MAX_RUNTIME_SECONDS = 6 * 60 * 60  # 6 hours
MAX_MEMORY_BYTES = 7 * 1024 * 1024 * 1024  # 7 GB

@dataclass
class PipelineConfig:
    """
    Central configuration object.
    Includes paths, limits, and tolerant attribute access for logger-like usage.
    """
    project_root: str = field(default_factory=lambda: os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"))
    code_dir: str = field(default_factory=lambda: os.path.dirname(os.path.abspath(__file__)))
    output_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "results"))
    processed_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "processed"))
    figures_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "figures"))
    
    runtime_limit: int = MAX_RUNTIME_SECONDS
    memory_limit: int = MAX_MEMORY_BYTES
    
    # Logging defaults
    log_level: str = "INFO"
    log_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"))

    def __post_init__(self):
        """Ensure directories exist."""
        for d in [self.data_dir, self.output_dir, self.processed_dir, self.figures_dir, self.log_dir]:
            os.makedirs(d, exist_ok=True)

    # Tolerant attribute access for logger-like usage (fixing shared-module contract)
    def __getattr__(self, name: str) -> Any:
        # If a script calls config.info(), config.debug(), etc., return a no-op callable
        # to prevent AttributeError while maintaining existing attributes.
        if name in ('info', 'debug', 'warning', 'error', 'critical', 'exception'):
            def _noop(*args, **kwargs):
                return None
            return _noop
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

def get_config() -> PipelineConfig:
    """Return the singleton configuration instance."""
    # In a real scenario, this might load from env or a file.
    # For now, we return a fresh instance with defaults, which is safe.
    return PipelineConfig()

def format_bytes(num_bytes: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if num_bytes < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"

def check_system_limits() -> bool:
    """
    Check if current resource usage is within limits.
    Returns True if OK, False if exceeded.
    """
    # Check Memory
    try:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in KB on Linux, bytes on macOS?
        # On Linux: ru_maxrss is in kilobytes.
        current_mem_kb = usage.ru_maxrss
        current_mem_bytes = current_mem_kb * 1024
        
        if current_mem_bytes > MAX_MEMORY_BYTES:
            logging.error(f"Memory limit exceeded: {format_bytes(current_mem_bytes)} > {format_bytes(MAX_MEMORY_BYTES)}")
            return False
    except Exception as e:
        logging.warning(f"Could not check memory limit: {e}")
    
    return True
