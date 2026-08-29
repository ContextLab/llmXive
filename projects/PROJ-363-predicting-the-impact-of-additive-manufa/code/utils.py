import hashlib
import json
import logging
import os
import random
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Callable, Type, Union

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None  # type: ignore

# Custom Exception Types for better error handling
class PipelineError(Exception):
    """Base exception for pipeline-specific errors."""
    pass

class ConfigurationError(PipelineError):
    """Raised when configuration loading or validation fails."""
    pass

class StateError(PipelineError):
    """Raised when state management operations fail (e.g., missing state file)."""
    pass

class DataError(PipelineError):
    """Raised when data processing or validation fails."""
    pass

class HashError(PipelineError):
    """Raised when hash computation or validation fails."""
    pass

def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    name: str = "llmXive_pipeline"
) -> logging.Logger:
    """
    Configure and return the project logger.
    Reads LOG_LEVEL and LOG_FILE from environment if not provided.
    Ensures idempotent configuration (does not re-add handlers if already configured).
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    level_str = log_level or os.getenv("LOG_LEVEL", "INFO")
    try:
        level = getattr(logging, level_str.upper(), logging.INFO)
    except AttributeError:
        raise ConfigurationError(f"Invalid log level: {level_str}. Must be one of DEBUG, INFO, WARNING, ERROR, CRITICAL.")

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    ch.setLevel(level)
    logger.addHandler(ch)

    # File handler (optional)
    file_path = log_file or os.getenv("LOG_FILE")
    if file_path:
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(file_path)
            fh.setFormatter(formatter)
            fh.setLevel(level)
            logger.addHandler(fh)
        except OSError as e:
            raise ConfigurationError(f"Failed to create log file at {file_path}: {e}")

    logger.setLevel(level)
    logger.propagate = False
    return logger


def load_env_config() -> Dict[str, str]:
    """
    Load environment variables from a .env file if present.
    Returns a dictionary of loaded variables.
    Raises ConfigurationError if python-dotenv is missing when a .env file exists.
    """
    dotenv_path = Path.cwd() / ".env"
    if dotenv_path.exists():
        if load_dotenv is None:
            raise ConfigurationError(
                "python-dotenv is required to load .env files but is not installed. "
                "Install with: pip install python-dotenv"
            )
        load_dotenv(dotenv_path)
        logging.getLogger("llmXive_pipeline").debug(f"Loaded environment from {dotenv_path}")
    else:
        example_path = Path.cwd() / ".env.example"
        if example_path.exists():
            logging.getLogger("llmXive_pipeline").debug(f"Found .env.example at {example_path}. Please copy to .env to configure.")

    return dict(os.environ)


def set_seed(seed: Optional[int] = None) -> int:
    """
    Set the random seed for reproducibility across libraries.
    Reads RANDOM_SEED from environment if not provided.
    Returns the seed actually used.
    """
    if seed is None:
        seed_str = os.getenv("RANDOM_SEED", "42")
        try:
            seed = int(seed_str)
        except ValueError:
            logging.getLogger("llmXive_pipeline").warning(f"Invalid RANDOM_SEED '{seed_str}', defaulting to 42")
            seed = 42

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
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass

    return seed


def compute_file_hash(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Compute the hash of a file.
    Raises HashError if file not found or hash algorithm unsupported.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    try:
        hash_func = hashlib.new(algorithm)
    except ValueError:
        raise HashError(f"Unsupported hash algorithm: {algorithm}")

    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
    except OSError as e:
        raise HashError(f"Failed to read file {path} for hashing: {e}")

    return hash_func.hexdigest()


def compute_string_hash(text: str, algorithm: str = "sha256") -> str:
    """
    Compute the hash of a string.
    Raises HashError if hash algorithm unsupported.
    """
    try:
        hash_func = hashlib.new(algorithm)
    except ValueError:
        raise HashError(f"Unsupported hash algorithm: {algorithm}")

    hash_func.update(text.encode("utf-8"))
    return hash_func.hexdigest()


def load_state(state_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Load the state.yaml file.
    Returns a default state structure if the file does not exist.
    Raises StateError if PyYAML is missing when the file exists.
    """
    if state_path is None:
        state_path = Path.cwd() / "state.yaml"
    else:
        state_path = Path(state_path)

    if not state_path.exists():
        return {"artifacts": {}, "version": 1, "last_updated": None}

    try:
        import yaml
    except ImportError:
        raise StateError(
            "PyYAML is required to load state.yaml but is not installed. "
            "Install with: pip install pyyaml"
        )

    try:
        with open(state_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data is None:
                return {"artifacts": {}, "version": 1, "last_updated": None}
            return data
    except yaml.YAMLError as e:
        raise StateError(f"Failed to parse state.yaml: {e}")
    except OSError as e:
        raise StateError(f"Failed to read state.yaml: {e}")


def update_state(state: Dict[str, Any], artifact_name: str, file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Update the state dictionary with a new artifact hash.
    Raises StateError if the file cannot be hashed or state is malformed.
    """
    if "artifacts" not in state or not isinstance(state["artifacts"], dict):
        state["artifacts"] = {}

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Cannot update state: artifact file not found at {path}")

    try:
        file_hash = compute_file_hash(path)
    except HashError as e:
        raise StateError(f"Failed to compute hash for {path}: {e}")

    state["artifacts"][artifact_name] = {
        "path": str(path),
        "hash": file_hash,
        "updated": True
    }
    return state


def get_state_hash(state: Dict[str, Any]) -> str:
    """
    Compute a hash of the entire state dictionary to detect changes.
    """
    state_str = json.dumps(state, sort_keys=True, default=str)
    return compute_string_hash(state_str)


def validate_hash(state: Dict[str, Any], artifact_name: str) -> bool:
    """
    Validate that the stored hash matches the current file hash.
    Returns False if artifact missing, file missing, or hash mismatch.
    """
    if artifact_name not in state.get("artifacts", {}):
        return False

    artifact_info = state["artifacts"][artifact_name]
    stored_hash = artifact_info.get("hash")
    file_path = Path(artifact_info.get("path"))

    if not file_path.exists():
        return False

    try:
        current_hash = compute_file_hash(file_path)
    except (FileNotFoundError, HashError):
        return False

    return stored_hash == current_hash
