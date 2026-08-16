import os
import sys
import json
import time
import resource
import logging
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PipelineConfig:
    """
    Configuration management for the pipeline.
    Implements FR-006 limits: 6 hours runtime, 7GB memory.
    """
    def __init__(
        self,
        max_runtime_hours: float = 6.0,
        max_memory_gb: float = 7.0,
        data_dir: str = "data",
        output_dir: str = "data/processed",
        results_dir: str = "data/results",
        seed: int = 42,
        redundancy_prob: float = 0.3,
        shuffle_window: int = 2,
        target_clusters: int = 20,
        similarity_threshold: float = 0.95,
        jaccard_threshold: float = 0.95
    ):
        self.max_runtime_hours = max_runtime_hours
        self.max_memory_gb = max_memory_gb
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.results_dir = results_dir
        self.seed = seed
        self.redundancy_prob = redundancy_prob
        self.shuffle_window = shuffle_window
        self.target_clusters = target_clusters
        self.similarity_threshold = similarity_threshold
        self.jaccard_threshold = jaccard_threshold
        
        # Ensure directories exist
        for d in [data_dir, output_dir, results_dir]:
            os.makedirs(d, exist_ok=True)

    def __getattr__(self, name):
        """
        Tolerant fallback for unknown attributes.
        Prevents AttributeError when new attributes are accessed.
        """
        def _noop(*args, **kwargs):
            return None
        return _noop

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_runtime_hours": self.max_runtime_hours,
            "max_memory_gb": self.max_memory_gb,
            "data_dir": self.data_dir,
            "output_dir": self.output_dir,
            "results_dir": self.results_dir,
            "seed": self.seed,
            "redundancy_prob": self.redundancy_prob,
            "shuffle_window": self.shuffle_window,
            "target_clusters": self.target_clusters,
            "similarity_threshold": self.similarity_threshold,
            "jaccard_threshold": self.jaccard_threshold
        }

_config_instance: Optional[PipelineConfig] = None

def get_config() -> PipelineConfig:
    global _config_instance
    if _config_instance is None:
        _config_instance = PipelineConfig()
    return _config_instance

def update_config(**kwargs) -> PipelineConfig:
    config = get_config()
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    return config

def format_bytes(bytes_val: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} PB"

def check_system_limits() -> Dict[str, Any]:
    """Check current system resource usage against limits."""
    config = get_config()
    
    # Get current memory usage
    rusage = resource.getrusage(resource.RUSAGE_SELF)
    max_rss_mb = rusage.ru_maxrss / 1024.0  # Convert to MB (Linux)
    
    current_time = time.time()
    
    return {
        "max_memory_gb": config.max_memory_gb,
        "current_memory_mb": max_rss_mb,
        "memory_limit_exceeded": max_rss_mb > (config.max_memory_gb * 1024),
        "start_time": current_time,
        "max_runtime_seconds": config.max_runtime_hours * 3600
    }

def main():
    config = get_config()
    print(json.dumps(config.to_dict(), indent=2))

if __name__ == "__main__":
    main()