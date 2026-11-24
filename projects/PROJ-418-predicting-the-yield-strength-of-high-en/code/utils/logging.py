"""
code/utils/logging.py
---------------------

Utility functions for deterministic logging and seed management
used throughout the project.  The implementation satisfies the unit
tests in ``tests/unit/test_logging_seed.py`` and provides a simple
``get_logger`` API compatible with the existing code base.

Public symbols:
  - DEFAULT_SEED: int
  - LOG_DIR: pathlib.Path
  - set_seeds(seed: int) -> None
  - get_seed() -> int
  - get_logger(name: str, seed: int | None = None, log_to_file: bool = False) -> logging.Logger
"""
import os
import random
import logging
from pathlib import Path
from typing import Optional

# The project root is the current working directory when the
# pipeline is executed.  Logs are stored under ``output/logs``.
LOG_DIR: Path = Path.cwd() / "output" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Default deterministic seed used when the environment variable
# ``HEA_SEED`` is not set.
DEFAULT_SEED: int = 42

def get_seed() -> int:
    """
    Return the random seed to be used for the run.

    The function first checks the ``HEA_SEED`` environment variable.
    If it is not defined, ``DEFAULT_SEED`` is returned.
    """
    env_val = os.getenv("HEA_SEED")
    if env_val is not None:
        try:
            return int(env_val)
        except ValueError:
            # Fall back to default if the variable cannot be parsed.
            pass
    return DEFAULT_SEED

def set_seeds(seed: int) -> None:
    """
    Set deterministic seeds for the standard library ``random`` module,
    NumPy (if available) and PyTorch (if available).  The function also
    stores the seed in the ``HEA_SEED`` environment variable so that
    downstream processes can retrieve it via :func:`get_seed`.
    """
    os.environ["HEA_SEED"] = str(seed)

    random.seed(seed)

    # NumPy – optional dependency, already available in the runner.
    try:
        import numpy as np
        np.random.seed(seed)
    except Exception:
        pass

    # PyTorch – optional; guard against import errors.
    try:
        import torch
        torch.manual_seed(seed)
        # For deterministic CUDA behaviour (if CUDA were used)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    except Exception:
        pass

def get_logger(name: str, seed: Optional[int] = None, log_to_file: bool = False) -> logging.Logger:
    """
    Retrieve a configured ``logging.Logger`` instance.

    Parameters
    ----------
    name : str
        Name of the logger (typically ``__name__``).
    seed : int | None
        If provided, ``set_seeds`` is called with this value.
        If ``None``, the seed is obtained via :func:`get_seed`.
    log_to_file : bool
        When ``True`` a ``FileHandler`` is added that writes to
        ``LOG_DIR/run_seed_<seed>.log``.  The file is opened in
        append mode so that multiple calls to ``get_logger`` do not
        overwrite previous logs.

    Returns
    -------
    logging.Logger
        Configured logger with a stream handler (stdout) and, if
        requested, a file handler.
    """
    if seed is None:
        seed = get_seed()
    else:
        # Ensure the global seed matches the explicit value.
        set_seeds(seed)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid adding duplicate handlers on repeated calls.
    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        if log_to_file:
            log_file = LOG_DIR / f"run_seed_{seed}.log"
            file_handler = logging.FileHandler(log_file, mode="a")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger
