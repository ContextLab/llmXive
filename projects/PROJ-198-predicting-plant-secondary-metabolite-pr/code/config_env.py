"""
Environment‑variable handling utilities.

Provides:
* ``load_environment`` – reads a ``.env`` file (if present) and returns a
  ``BaseSettings`` subclass containing the values.
* ``get_env_manager`` – singleton that offers a ``.get(key)`` method used
  by ``code.config.get``.
* ``ensure_directories`` – creates the standard data / logs / figures
  directories based on the configuration.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Set

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_env_manager_instance = None  # type: ignore


class EnvConfig(BaseSettings):
    """
    Simple settings container for environment variables.

    ``BaseSettings`` automatically reads from the operating system
    environment and, if a ``.env`` file exists in the project root, from
    that file as well.
    """
    # Core variables used across the pipeline
    NCBI_API_KEY: Optional[str] = None
    PMDB_TOKEN: Optional[str] = None

    # Paths – these are *derived* from the project layout and are kept here
    # for convenience when other modules need to construct absolute paths.
    data_root: Path = Path("data")
    logs_root: Path = Path("logs")
    figures_root: Path = Path("figures")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @classmethod
    def _load_dotenv(cls) -> None:
        """
        Load a ``.env`` file manually if ``pydantic`` does not find it
        (e.g. when the file resides outside the default search path).
        """
        env_path = Path(".env")
        if env_path.is_file():
            with env_path.open() as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())

    @classmethod
    def load(cls) -> "EnvConfig":
        """Load the environment configuration, respecting a ``.env`` file."""
        cls._load_dotenv()
        return cls()


def load_environment() -> EnvConfig:
    """
    Public helper that returns a fully‑initialised ``EnvConfig`` instance.
    """
    return EnvConfig.load()


def ensure_directories(config: EnvConfig) -> None:
    """
    Create the standard directory hierarchy (data, logs, figures) if it does
    not already exist. The function is tolerant of a ``Path`` or a string.
    """
    for attr in ("data_root", "logs_root", "figures_root"):
        base = getattr(config, attr)
        if isinstance(base, (str, Path)):
            Path(base).mkdir(parents=True, exist_ok=True)
        else:
            logging.warning(f"Unexpected type for {attr}: {type(base)}")


def get_api_key(service: str, config: EnvConfig) -> Optional[str]:
    """
    Retrieve an API key for a given service name.

    Parameters
    ----------
    service : str
        Name of the service – e.g. ``'NCBI'`` or ``'PMDB'``.
    config : EnvConfig
        The loaded environment configuration.

    Returns
    -------
    str | None
        The API key if present, otherwise ``None``.
    """
    mapping = {
        "NCBI": config.NCBI_API_KEY,
        "PMDB": config.PMDB_TOKEN,
    }
    return mapping.get(service.upper())


def get_data_path(config: EnvConfig, sub_path: Optional[str] = None) -> Path:
    """
    Return a path inside the data directory.

    Parameters
    ----------
    config : EnvConfig
        The environment configuration.
    sub_path : str | None
        Optional sub‑directory or filename to append.

    Returns
    -------
    pathlib.Path
    """
    base = Path(config.data_root)
    if sub_path:
        return base / sub_path
    return base


def get_logs_path(config: EnvConfig, filename: Optional[str] = None) -> Path:
    """
    Return a path for a log file (or the log directory if ``filename`` is ``None``).
    """
    base = Path(config.logs_root)
    if filename:
        return base / filename
    return base


def get_figures_path(config: EnvConfig, filename: Optional[str] = None) -> Path:
    """
    Return a path for a figure file (or the figures directory if ``filename`` is ``None``).
    """
    base = Path(config.figures_root)
    if filename:
        return base / filename
    return base


def validate_required_env_vars(config: EnvConfig, required_services: Set[str]) -> bool:
    """
    Ensure that all required services have an associated API key.

    Returns ``True`` if every service in ``required_services`` has a non‑empty
    key, otherwise logs a warning and returns ``False``.
    """
    missing = [svc for svc in required_services if not get_api_key(svc, config)]
    if missing:
        logging.warning(f"Missing API keys for services: {missing}")
        return False
    return True


def create_env_file_template() -> str:
    """
    Generate a minimal ``.env`` template that users can copy.
    """
    lines = [
        "# Example environment configuration",
        "NCBI_API_KEY=your_ncbi_api_key_here",
        "PMDB_TOKEN=your_pmdb_token_here",
    ]
    return "\n".join(lines) + "\n"


class EnvManager:
    """
    Lightweight wrapper exposing a ``.get(key)`` method.

    The CLI and ``code.config.get`` expect an object with a ``get`` method
    that returns the value of an environment variable (or ``None``).
    """

    def __init__(self) -> None:
        self._config = load_environment()

    def get(self, key: str) -> Optional[str]:
        """
        Retrieve the environment variable ``key``.  ``os.getenv`` is checked
        first so that values set at runtime override the ``.env`` file.
        """
        return os.getenv(key) or getattr(self._config, key, None)


def get_env_manager() -> EnvManager:
    """
    Return a singleton ``EnvManager`` instance.

    The function is deliberately simple – it creates the manager on first
    call and re‑uses it thereafter.
    """
    global _env_manager_instance
    if _env_manager_instance is None:
        _env_manager_instance = EnvManager()
    return _env_manager_instance


def get_env_config() -> EnvConfig:
    """
    Backwards‑compatible accessor used by older code.
    """
    return load_environment()
