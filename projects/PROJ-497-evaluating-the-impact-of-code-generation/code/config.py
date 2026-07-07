import os
import random
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

# Global configuration
_config: Optional[Dict[str, Any]] = None
_paths: Optional[Dict[str, Path]] = None

def get_config() -> Dict[str, Any]:
    """Get the global configuration dictionary."""
    global _config
    if _config is None:
        # Load from config.yaml if it exists, otherwise use defaults
        config_path = Path("config.yaml")
        if config_path.exists():
            with open(config_path, 'r') as f:
                _config = yaml.safe_load(f)
        else:
            _config = {
                "seed": 42,
                "max_attempts": 200,
                "min_valid_samples": 64,
                "models": ["starcoder", "codegen"],
                "benchmarks": ["humaneval", "mbpp"],
            }
    return _config

def set_seed(seed: Optional[int] = None) -> None:
    """Set random seed for reproducibility."""
    if seed is None:
        seed = get_config().get("seed", 42)
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    # Note: For torch/numpy, we'd set those seeds too if they were imported

def get_paths() -> Dict[str, Path]:
    """Get project paths dictionary."""
    global _paths
    if _paths is None:
        root = Path(__file__).parent.parent
        _paths = {
            "root": root,
            "code": root / "code",
            "data": root / "data",
            "results": root / "results",
            "state": root / "state",
            "tests": root / "tests",
            "specs": root / "specs",
            "human_eval": root / "data" / "human_eval",
            "mbpp": root / "data" / "mbpp",
            "generated": root / "data" / "generated",
            "processed": root / "data" / "processed",
        }
    return _paths

def ensure_directories(dirs: list) -> None:
    """Ensure that the given directories exist."""
    for dir_path in dirs:
        if isinstance(dir_path, str):
            dir_path = Path(dir_path)
        dir_path.mkdir(parents=True, exist_ok=True)

def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to config.yaml."""
    config_path = Path("config.yaml")
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from a YAML file."""
    if config_path is None:
        config_path = Path("config.yaml")
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {}