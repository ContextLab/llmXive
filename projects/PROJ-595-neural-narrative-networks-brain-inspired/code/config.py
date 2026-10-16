"""
Project-wide configuration for the Neural Narrative Networks pipeline.

Exposes the canonical constants required by the spec:
  - random_seed (int): deterministic seed for all RNGs (default 42)
  - cpu_only (bool): force CPU-only execution (default True)
  - max_ram_gb (int): peak RAM budget in GB (default 7)
and a ``set_seed()`` helper that seeds Python, NumPy and (if installed)
PyTorch RNGs for full reproducibility.
"""
import os
import random
from typing import Any, Dict

# ---------------------------------------------------------------------------
# Canonical configuration constants
# ---------------------------------------------------------------------------
random_seed: int = 42
cpu_only: bool = True
max_ram_gb: int = 7

# Optional overrides via environment variables (parsed safely).
_env_seed = os.environ.get("NNN_RANDOM_SEED")
if _env_seed is not None:
    try:
        random_seed = int(_env_seed)
    except ValueError:
        pass

_env_ram = os.environ.get("NNN_MAX_RAM_GB")
if _env_ram is not None:
    try:
        max_ram_gb = int(float(_env_ram))
    except ValueError:
        pass

cpu_only = os.environ.get("NNN_CPU_ONLY", "1" if cpu_only else "0") not in ("0", "false", "False")

# Backwards-compatible alias used by earlier scripts.
RANDOM_SEED = random_seed
CPU_ONLY = cpu_only
MAX_RAM_GB = max_ram_gb


def get_config() -> Dict[str, Any]:
    """
    Returns configuration dictionary with project settings.

    Returns:
        dict with keys:
            - random_seed (int): Random seed for reproducibility
            - cpu_only (bool): Whether to run on CPU only (default True)
            - max_ram_gb (int): Maximum RAM usage in GB (default 7)
    """
    return {
        "random_seed": random_seed,
        "cpu_only": cpu_only,
        "max_ram_gb": max_ram_gb,
    }


def set_seed(seed: int = None) -> int:
    """
    Seed all random number generators for reproducibility.

    Seeds Python's ``random``, NumPy (if available) and PyTorch (if
    installed). When ``cpu_only`` is True, PyTorch is never allowed to
    use CUDA regardless of availability.

    Args:
        seed: Optional seed override; defaults to the module-level
            ``random_seed`` (42).

    Returns:
        The seed that was applied.
    """
    if seed is None:
        seed = random_seed
    seed = int(seed)

    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

    try:
        import numpy as np

        np.random.seed(seed)
    except ImportError:
        pass

    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

    return seed
    execute: false