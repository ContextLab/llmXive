import os
import sys
import json
import time
import resource
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

# Configuration defaults
DEFAULT_MAX_RUNTIME_HOURS = 6
DEFAULT_MAX_MEMORY_GB = 7
DEFAULT_DATA_DIR = "data"
DEFAULT_BEIR_CACHE_DIR = "beir_data"
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
DEFAULT_MINHASH_THRESHOLD_BASELINE = 0.95
DEFAULT_MINHASH_THRESHOLD_SWEEP_START = 0.95
DEFAULT_MINHASH_THRESHOLD_SWEEP_END = 0.99
DEFAULT_MINHASH_THRESHOLD_SWEEP_STEP = 0.005
DEFAULT_LLM_MODEL = "llama-3-8b-instruct"
DEFAULT_LLM_TEMPERATURE = 0.0
DEFAULT_LLM_MAX_TOKENS = 200
DEFAULT_LOG_LEVEL = "INFO"

@dataclass
class PipelineConfig:
    """
    Central configuration for the llmXive pipeline.
    Supports both direct attribute access and method-style calls for logging-like flexibility.
    """
    max_runtime_hours: float = DEFAULT_MAX_RUNTIME_HOURS
    max_memory_gb: float = DEFAULT_MAX_MEMORY_GB
    data_dir: str = DEFAULT_DATA_DIR
    beir_cache_dir: str = DEFAULT_BEIR_CACHE_DIR
    embedding_model: str = DEFAULT_EMBEDDING_MODEL
    minhash_threshold_baseline: float = DEFAULT_MINHASH_THRESHOLD_BASELINE
    minhash_threshold_sweep_start: float = DEFAULT_MINHASH_THRESHOLD_SWEEP_START
    minhash_threshold_sweep_end: float = DEFAULT_MINHASH_THRESHOLD_SWEEP_END
    minhash_threshold_sweep_step: float = DEFAULT_MINHASH_THRESHOLD_SWEEP_STEP
    llm_model: str = DEFAULT_LLM_MODEL
    llm_temperature: float = DEFAULT_LLM_TEMPERATURE
    llm_max_tokens: int = DEFAULT_LLM_MAX_TOKENS
    log_level: str = DEFAULT_LOG_LEVEL

    # Derived paths
    processed_dir: str = field(default="data/processed", init=False)
    results_dir: str = field(default="data/results", init=False)
    figures_dir: str = field(default="figures", init=False)
    state_dir: str = field(default="state/projects", init=False)
    prompts_dir: str = field(default="code/prompts", init=False)

    def __post_init__(self):
        # Ensure derived paths are absolute relative to project root if needed
        # For now, keeping them relative as per project conventions
        self.processed_dir = os.path.join(self.data_dir, "processed")
        self.results_dir = os.path.join(self.data_dir, "results")
        self.figures_dir = os.path.join(self.data_dir, "figures")
        self.state_dir = os.path.join("state", "projects")
        self.prompts_dir = os.path.join("code", "prompts")

    # Tolerant method access for logger-style calls
    def info(self, *args, **kwargs):
        logging.info(*args, **kwargs)

    def debug(self, *args, **kwargs):
        logging.debug(*args, **kwargs)

    def warning(self, *args, **kwargs):
        logging.warning(*args, **kwargs)

    def error(self, *args, **kwargs):
        logging.error(*args, **kwargs)

    def critical(self, *args, **kwargs):
        logging.critical(*args, **kwargs)

    def get_threshold_sweep_range(self) -> List[float]:
        """
        Generate the list of thresholds for the MinHash-LSH sensitivity sweep.
        Range: [start, end] with step size.
        Serves SC-005 by defining the sweep parameters in config.
        """
        thresholds = []
        current = self.minhash_threshold_sweep_start
        while current <= self.minhash_threshold_sweep_end + 1e-9: # Float tolerance
            thresholds.append(round(current, 4))
            current += self.minhash_threshold_sweep_step
        return thresholds

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_runtime_hours": self.max_runtime_hours,
            "max_memory_gb": self.max_memory_gb,
            "data_dir": self.data_dir,
            "beir_cache_dir": self.beir_cache_dir,
            "embedding_model": self.embedding_model,
            "minhash_threshold_baseline": self.minhash_threshold_baseline,
            "minhash_threshold_sweep_start": self.minhash_threshold_sweep_start,
            "minhash_threshold_sweep_end": self.minhash_threshold_sweep_end,
            "minhash_threshold_sweep_step": self.minhash_threshold_sweep_step,
            "llm_model": self.llm_model,
            "llm_temperature": self.llm_temperature,
            "llm_max_tokens": self.llm_max_tokens,
            "log_level": self.log_level,
            "threshold_sweep_range": self.get_threshold_sweep_range()
        }

_global_config: Optional[PipelineConfig] = None

def get_config() -> PipelineConfig:
    global _global_config
    if _global_config is None:
        _global_config = PipelineConfig()
    return _global_config

def update_config(**kwargs):
    global _global_config
    if _global_config is None:
        _global_config = PipelineConfig()
    for key, value in kwargs.items():
        if hasattr(_global_config, key):
            setattr(_global_config, key, value)
        else:
            logging.warning(f"Config update ignored unknown key: {key}")

def format_bytes(num_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if num_bytes < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"

def check_system_limits() -> Tuple[bool, str]:
    """
    Check if current system limits are sufficient for the configured constraints.
    Returns (is_ok, message).
    """
    config = get_config()
    max_mem_bytes = config.max_memory_gb * 1024 * 1024 * 1024

    # Check soft limit
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    if soft != resource.RLIM_INFINITY and soft < max_mem_bytes:
        return False, f"Soft memory limit ({format_bytes(soft)}) is below required ({format_bytes(max_mem_bytes)})"

    # Check hard limit
    if hard != resource.RLIM_INFINITY and hard < max_mem_bytes:
        return False, f"Hard memory limit ({format_bytes(hard)}) is below required ({format_bytes(max_mem_bytes)})"

    return True, "System limits are sufficient"

def main():
    """
    CLI entry point for configuration inspection.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Inspect llmXive pipeline configuration")
    parser.add_argument("--show", action="store_true", help="Print current config as JSON")
    parser.add_argument("--check-limits", action="store_true", help="Check system limits against config")
    args = parser.parse_args()

    config = get_config()

    if args.show:
        print(json.dumps(config.to_dict(), indent=2))

    if args.check_limits:
        is_ok, msg = check_system_limits()
        status = "OK" if is_ok else "FAIL"
        print(f"System Limits Check: {status} - {msg}")
        sys.exit(0 if is_ok else 1)

    if not (args.show or args.check_limits):
        parser.print_help()

if __name__ == "__main__":
    main()