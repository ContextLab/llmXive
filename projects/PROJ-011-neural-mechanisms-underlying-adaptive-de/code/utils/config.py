import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np

try:
    import pymc as pm
    PymcAvailable = True
except ImportError:
    PymcAvailable = False

try:
    import yaml
    YamlAvailable = True
except ImportError:
    YamlAvailable = False

_global_config: Optional["Config"] = None
_seed: Optional[int] = None


class Config:
    def __init__(
        self,
        project_root: Optional[Union[str, Path]] = None,
        data_root: Optional[Union[str, Path]] = None,
        results_root: Optional[Union[str, Path]] = None,
        random_seed: Optional[int] = None,
        backend: str = "cpu",
        n_chains: int = 2,
        n_draws: int = 1000,
        n_tune: int = 1000,
    ):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.data_root = Path(data_root) if data_root else self.project_root / "data"
        self.results_root = Path(results_root) if results_root else self.project_root / "results"

        self.random_seed = random_seed if random_seed is not None else 42
        self.backend = backend
        self.n_chains = n_chains
        self.n_draws = n_draws
        self.n_tune = n_tune

        self._ensure_paths_defined()

    def _ensure_paths_defined(self) -> None:
        if not self.project_root.exists():
            raise ValueError(f"Project root does not exist: {self.project_root}")
        # Ensure standard subdirectories exist as per T007 requirements
        (self.data_root / "raw").mkdir(parents=True, exist_ok=True)
        (self.data_root / "processed").mkdir(parents=True, exist_ok=True)
        (self.data_root / "models").mkdir(parents=True, exist_ok=True)
        (self.results_root).mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_root": str(self.project_root),
            "data_root": str(self.data_root),
            "results_root": str(self.results_root),
            "random_seed": self.random_seed,
            "backend": self.backend,
            "n_chains": self.n_chains,
            "n_draws": self.n_draws,
            "n_tune": self.n_tune,
        }


def load_config_from_yaml(path: Union[str, Path]) -> Config:
    if not YamlAvailable:
        raise ImportError("PyYAML is not installed. Install it to load YAML configs.")
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r") as f:
        data = yaml.safe_load(f)

    return Config(
        project_root=data.get("project_root"),
        data_root=data.get("data_root"),
        results_root=data.get("results_root"),
        random_seed=data.get("random_seed"),
        backend=data.get("backend", "cpu"),
        n_chains=data.get("n_chains", 2),
        n_draws=data.get("n_draws", 1000),
        n_tune=data.get("n_tune", 1000),
    )


def load_config_from_env() -> Config:
    project_root = os.getenv("PROJ_ROOT")
    data_root = os.getenv("DATA_ROOT")
    results_root = os.getenv("RESULTS_ROOT")
    seed_str = os.getenv("RANDOM_SEED")
    backend = os.getenv("BACKEND", "cpu")
    n_chains = int(os.getenv("N_CHAINS", 2))
    n_draws = int(os.getenv("N_DRAWS", 1000))
    n_tune = int(os.getenv("N_TUNE", 1000))

    random_seed = int(seed_str) if seed_str else None

    return Config(
        project_root=project_root,
        data_root=data_root,
        results_root=results_root,
        random_seed=random_seed,
        backend=backend,
        n_chains=n_chains,
        n_draws=n_draws,
        n_tune=n_tune,
    )


def get_config() -> Config:
    global _global_config
    if _global_config is None:
        _global_config = load_config_from_env()
    return _global_config


def set_config(config: Optional[Config] = None) -> Config:
    global _global_config
    if config is None:
        config = load_config_from_env()
    _global_config = config
    return config


def reset_config() -> None:
    global _global_config
    _global_config = None


def set_seed(seed: Optional[int] = None) -> None:
    """
    Sets the random seed for Python's random module, NumPy, and PyMC.
    If seed is None, it retrieves the seed from the global config.
    """
    global _seed
    if seed is None:
        cfg = get_config()
        seed = cfg.random_seed
    _seed = seed

    # Seed Python's built-in random
    random.seed(seed)

    # Seed NumPy
    np.random.seed(seed)

    # Seed PyMC if available
    if PymcAvailable:
        # PyMC 5.x uses pm.set_seed which sets the global rng
        pm.set_seed(seed)
        # Also ensure the underlying numpy random state is consistent if needed
        # pm uses numpyro which relies on numpy.random, so the np.seed call above is primary.
        # Explicitly setting pm seed ensures any internal rng initialization uses this.

def get_seed() -> Optional[int]:
    global _seed
    return _seed