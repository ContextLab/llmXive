import os
import sys
import json
import logging
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import yaml

# Import existing logging utilities
from src.utils.logging_config import get_logger, setup_logging

# Import existing config utility if needed, though we'll handle paths directly
from src.utils.config import Config

# Constants
SEEDS_FILE = "data/seeds.json"
MANIFEST_FILE = "data/manifest.yaml"
NUM_SEEDS = 5

def ensure_data_directory():
    """Ensure the data directory exists."""
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

def generate_seeds() -> List[int]:
    """
    Generate a deterministic list of 5 random seeds.
    In a real scenario, this might be seeded by a master seed or environment variable.
    For reproducibility, we use a fixed base seed derived from a standard source.
    """
    import random
    # Use a fixed base seed to ensure determinism across runs for this specific task
    # unless an environment variable overrides it.
    base_seed = int(os.getenv("MASTER_SEED", "42"))
    random.seed(base_seed)
    seeds = [random.randint(0, 2**32 - 1) for _ in range(NUM_SEEDS)]
    return seeds

def save_seeds(seeds: List[int], output_path: Optional[str] = None) -> str:
    """
    Save the list of seeds to a JSON file.
    Returns the path to the saved file.
    """
    if output_path is None:
        output_path = SEEDS_FILE
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        "seeds": seeds,
        "count": len(seeds),
        "generated_at": datetime.utcnow().isoformat(),
        "base_seed": int(os.getenv("MASTER_SEED", "42"))
    }
    
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    
    logging.info(f"Saved {len(seeds)} seeds to {path}")
    return str(path)

def load_seeds(input_path: Optional[str] = None) -> List[int]:
    """Load seeds from the JSON file."""
    if input_path is None:
        input_path = SEEDS_FILE
    
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Seeds file not found: {path}")
    
    with open(path, "r") as f:
        data = json.load(f)
    
    return data.get("seeds", [])

def get_git_commit_hash() -> Optional[str]:
    """Get the current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return None

def get_python_version() -> str:
    """Get the current Python version."""
    import sys
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

def get_package_versions() -> Dict[str, str]:
    """Get versions of key packages."""
    versions = {}
    packages = ["torch", "transformers", "datasets", "scipy", "psutil", "pandas", "numpy"]
    
    for pkg in packages:
        try:
            module = __import__(pkg)
            if hasattr(module, "__version__"):
                versions[pkg] = str(module.__version__)
            else:
                versions[pkg] = "unknown"
        except ImportError:
            versions[pkg] = "not installed"
    
    return versions

def collect_hyperparameters(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Collect hyperparameters from config or defaults."""
    defaults = {
        "batch_size": 32,
        "learning_rate": 1e-4,
        "num_epochs": 10,
        "wall_time_limit_seconds": 21600,
        "ram_limit_gb": 7.0,
        "num_workers": 2,
        "model_name": "Qwen2-VL-2B",
        "embodiment_platforms": ["franka", "ur5", "kuka"]
    }
    
    if config:
        defaults.update(config)
    
    return defaults

def log_reproducibility_manifest(
    seeds: List[int],
    hyperparams: Dict[str, Any],
    output_path: Optional[str] = None,
    additional_info: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create and write the reproducibility manifest.
    This includes seeds, hyperparameters, versions, and git hash.
    """
    if output_path is None:
        output_path = MANIFEST_FILE
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    manifest = {
        "experiment_id": f"exp_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        "created_at": datetime.utcnow().isoformat(),
        "git_commit": get_git_commit_hash(),
        "python_version": get_python_version(),
        "packages": get_package_versions(),
        "seeds": {
            "count": len(seeds),
            "values": seeds,
            "source": os.getenv("MASTER_SEED", "default")
        },
        "hyperparameters": hyperparams,
        "environment": {
            "os": os.name,
            "cwd": os.getcwd()
        }
    }
    
    if additional_info:
        manifest["additional_info"] = additional_info
    
    with open(path, "w") as f:
        yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)
    
    logging.info(f"Wrote reproducibility manifest to {path}")
    return str(path)

def run_reproducibility_pipeline(config: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """
    Main entry point to run the reproducibility pipeline.
    1. Generate and save seeds.
    2. Collect hyperparameters.
    3. Write the manifest.
    Returns paths to generated files.
    """
    setup_logging(level=logging.INFO)
    logger = get_logger("reproducibility")
    
    logger.info("Starting reproducibility pipeline...")
    
    # 1. Generate and save seeds
    seeds = generate_seeds()
    seeds_path = save_seeds(seeds)
    
    # 2. Collect hyperparameters
    hyperparams = collect_hyperparameters(config)
    
    # 3. Write manifest
    manifest_path = log_reproducibility_manifest(
        seeds=seeds,
        hyperparams=hyperparams,
        additional_info={"task_id": "T018"}
    )
    
    logger.info("Reproducibility pipeline completed.")
    return {
        "seeds_file": seeds_path,
        "manifest_file": manifest_path
    }

def main():
    """CLI entry point for reproducibility tasks."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Reproducibility utilities for llmXive")
    parser.add_argument("--generate-seeds", action="store_true", help="Generate and save seeds only")
    parser.add_argument("--generate-manifest", action="store_true", help="Generate manifest (requires seeds to exist)")
    parser.add_argument("--full-pipeline", action="store_true", help="Run full pipeline: generate seeds and manifest")
    parser.add_argument("--config", type=str, help="Path to JSON config file for hyperparameters")
    parser.add_argument("--output-seeds", type=str, default=SEEDS_FILE, help="Output path for seeds.json")
    parser.add_argument("--output-manifest", type=str, default=MANIFEST_FILE, help="Output path for manifest.yaml")
    
    args = parser.parse_args()
    
    config = None
    if args.config:
        with open(args.config, "r") as f:
            config = json.load(f)
    
    if args.generate_seeds or args.full_pipeline:
        seeds = generate_seeds()
        save_seeds(seeds, args.output_seeds)
    
    if args.generate_manifest or args.full_pipeline:
        # Load seeds if generating manifest
        seeds = load_seeds(args.output_seeds)
        hyperparams = collect_hyperparameters(config)
        log_reproducibility_manifest(
            seeds=seeds,
            hyperparams=hyperparams,
            output_path=args.output_manifest
        )
    
    if not (args.generate_seeds or args.generate_manifest or args.full_pipeline):
        parser.print_help()

if __name__ == "__main__":
    main()
