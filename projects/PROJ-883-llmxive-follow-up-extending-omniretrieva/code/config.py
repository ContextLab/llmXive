"""Project configuration and path management."""
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Global constants
DEFAULT_SEED = 42
DEFAULT_CORES = 2
DEFAULT_MEMORY_GB = 7

# Dataset configurations for real fetching
DATASET_CONFIGS = {
    "ms_marco": {
        "hf_path": "microsoft/ms_marco",
        "config_name": "v1.1",
        "split": "train",
        "max_samples": 1000,
    },
    "spider": {
        "hf_path": "xlangai/spider",
        "config_name": None,
        "split": "train",
        "max_samples": 1000,
    },
    "dbpedia_sample": {
        "url": "https://raw.githubusercontent.com/RDFWebTools/rdf-samples/master/dbpedia-sample.ttl",
        "max_samples": None,
    },
}

def get_config() -> dict:
    """Returns the runtime configuration dictionary."""
    return {
        "seed": DEFAULT_SEED,
        "cpu_cores": DEFAULT_CORES,
        "memory_gb": DEFAULT_MEMORY_GB,
        "paths": {
            "raw": paths.data("raw"),
            "processed": paths.data("processed"),
            "results": paths.results(""),
        }
    }

def get_dataset_config(name: str) -> dict:
    """Returns the configuration for a specific dataset."""
    if name not in DATASET_CONFIGS:
        raise KeyError(f"Dataset '{name}' not found in DATASET_CONFIGS")
    return DATASET_CONFIGS[name]

if __name__ == "__main__":
    log.info("Config module loaded. Seed: %s", DEFAULT_SEED)
