import os
import sys
import json
import time
import resource
import logging
from dataclasses import dataclass, field
from typing import Optional, Any, Dict, List

logger = logging.getLogger(__name__)

@dataclass
class PipelineConfig:
    data_dir: str = field(default_factory=lambda: os.path.join(os.getcwd(), "data"))
    results_dir: str = field(default_factory=lambda: os.path.join(os.getcwd(), "data", "results"))
    logs_dir: str = field(default_factory=lambda: os.path.join(os.getcwd(), "data", "logs"))
    processed_dir: str = field(default_factory=lambda: os.path.join(os.getcwd(), "data", "processed"))
    max_runtime_hours: float = 6.0
    max_memory_gb: float = 7.0
    embedding_model: str = "all-MiniLM-L6-v2"
    llm_model: str = "llama-3-8b-instruct"
    llm_temperature: float = 0.0
    llm_max_tokens: int = 200
    redundancy_threshold: float = 0.95
    minhash_threshold: float = 0.95
    budget_baseline: int = 100
    budget_clustering: int = 50
    seeds: list = field(default_factory=lambda: [42])
    
    # T025: MinHash-LSH threshold sweep range configuration
    # Defines the range of Jaccard similarity thresholds to sweep for sensitivity analysis (SC-005)
    minhash_threshold_start: float = 0.95
    minhash_threshold_end: float = 0.99
    minhash_threshold_step: float = 0.01
    
    def __post_init__(self):
        # Ensure directories exist
        for dir_path in [self.data_dir, self.results_dir, self.logs_dir, self.processed_dir]:
            os.makedirs(dir_path, exist_ok=True)

_config_instance: Optional[PipelineConfig] = None

def get_config() -> PipelineConfig:
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = PipelineConfig()
    return _config_instance

def update_config(**kwargs) -> None:
    """Update the global configuration."""
    global _config_instance
    if _config_instance is None:
        _config_instance = PipelineConfig()
    for key, value in kwargs.items():
        if hasattr(_config_instance, key):
            setattr(_config_instance, key, value)
        else:
            logger.warning(f"Unknown config key: {key}")

def format_bytes(num_bytes: int) -> str:
    """Format bytes into human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if num_bytes < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"

def check_system_limits() -> Dict[str, Any]:
    """Check current system resource usage against limits."""
    config = get_config()
    
    usage = {}
    try:
        rusage = resource.getrusage(resource.RUSAGE_SELF)
        usage['max_memory_mb'] = rusage.ru_maxrss # In KB on Linux, MB on macOS
        # Adjust for platform differences if necessary
        if sys.platform == 'linux':
            usage['max_memory_mb'] /= 1024.0
    except Exception as e:
        logger.error(f"Failed to get resource usage: {e}")
        usage['max_memory_mb'] = 0.0
    
    usage['current_time'] = time.time()
    
    return usage

def main():
    """Main entry point for config script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Configuration management")
    parser.add_argument("--show", action="store_true", help="Show current config")
    parser.add_argument("--update", nargs="+", help="Update config (key=value)")
    
    args = parser.parse_args()
    
    if args.show:
        config = get_config()
        print(json.dumps({
            "data_dir": config.data_dir,
            "results_dir": config.results_dir,
            "logs_dir": config.logs_dir,
            "processed_dir": config.processed_dir,
            "max_runtime_hours": config.max_runtime_hours,
            "max_memory_gb": config.max_memory_gb,
            "embedding_model": config.embedding_model,
            "llm_model": config.llm_model,
            "llm_temperature": config.llm_temperature,
            "llm_max_tokens": config.llm_max_tokens,
            "redundancy_threshold": config.redundancy_threshold,
            "minhash_threshold": config.minhash_threshold,
            "minhash_threshold_start": config.minhash_threshold_start,
            "minhash_threshold_end": config.minhash_threshold_end,
            "minhash_threshold_step": config.minhash_threshold_step,
            "budget_baseline": config.budget_baseline,
            "budget_clustering": config.budget_clustering,
            "seeds": config.seeds
        }, indent=2))
    elif args.update:
        for item in args.update:
            key, value = item.split("=")
            # Simple type conversion
            if value.isdigit():
                value = int(value)
            elif value.replace('.', '', 1).isdigit():
                value = float(value)
            update_config(**{key: value})
        logger.info("Config updated.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()