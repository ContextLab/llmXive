"""
Environment-variable management module.

Provides a singleton ``EnvManager`` backed by a pydantic model that
reads optional API keys and mode flags from the process environment
(populated from a ``.env`` file by ``code.config``).

NOTE: this module intentionally uses a plain ``pydantic.BaseModel``
(no ``class Config`` / ``model_config`` mixing) — the previous
pydantic-settings implementation raised
``PydanticUserError: "Config" and "model_config" cannot be used together``
and blocked every pipeline entry point.
"""

import os
from pathlib import Path
from typing import Optional, Set, Union

from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent

_TRUTHY = {"1", "true", "yes", "on"}


class EnvConfig(BaseModel):
    """Snapshot of the relevant environment variables."""

    ncbi_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("NCBI_API_KEY")
    )
    pmdb_api_token: Optional[str] = Field(
        default_factory=lambda: os.getenv("PMDB_API_TOKEN")
    )
    ci_mode: bool = Field(
        default_factory=lambda: os.getenv("CI_MODE", "").strip().lower()
        in _TRUTHY
    )
    data_root: Path = Field(
        default_factory=lambda: Path(
            os.getenv("DATA_ROOT", str(PROJECT_ROOT / "data"))
        )
    )


class EnvManager:
    """Thin wrapper giving attribute-style access to env values."""

    def __init__(self, config: EnvConfig) -> None:
        self.config = config

    def get(self, key: str) -> Optional[str]:
        """Return the environment variable *key*, or ``None``."""
        val = os.getenv(key)
        if val is not None:
            return val
        attr = key.lower()
        if hasattr(self.config, attr):
            val = getattr(self.config, attr)
            return val if isinstance(val, str) else None
        return None


_env_manager: Optional[EnvManager] = None


def get_env_manager() -> EnvManager:
    """Return the singleton ``EnvManager`` instance."""
    global _env_manager
    if _env_manager is None:
        _env_manager = EnvManager(EnvConfig())
    return _env_manager


def load_environment() -> EnvConfig:
    """Load and return the ``EnvConfig`` instance (backward compatible)."""
    return get_env_manager().config


def get_env_config() -> EnvConfig:
    """Backwards-compatible accessor used by older code."""
    return get_env_manager().config


def _resolve_root(config: Union[EnvConfig, Path, str, None]) -> Path:
    if config is None:
        return PROJECT_ROOT
    if isinstance(config, (Path, str)):
        return Path(config)
    return Path(getattr(config, "data_root", PROJECT_ROOT / "data")).parent


def ensure_directories(config: Union[EnvConfig, Path, str, None] = None) -> None:
    """Create the standard project directories if they do not exist.

    Accepts either an ``EnvConfig`` or a plain path (the CLI passes the
    configured data root directly).
    """
    if isinstance(config, (Path, str)):
        data_root = Path(config)
    elif config is None:
        data_root = PROJECT_ROOT / "data"
    else:
        data_root = Path(getattr(config, "data_root", PROJECT_ROOT / "data"))

    for d in [
        data_root,
        data_root / "raw",
        data_root / "interim",
        data_root / "processed",
        data_root.parent / "logs",
        data_root.parent / "figures",
    ]:
        d.mkdir(parents=True, exist_ok=True)


def get_api_key(service: str, config: Optional[EnvConfig] = None) -> Optional[str]:
    """Retrieve an API key for *service* (e.g. ``NCBI`` or ``PMDB``)."""
    if config is None:
        config = get_env_manager().config
    env_var = f"{service.upper()}_API_KEY"
    token = os.getenv(env_var)
    if token:
        return token
    attr = env_var.lower()
    return getattr(config, attr, None)


def get_data_path(config: Optional[EnvConfig] = None, sub_path: Optional[str] = None) -> Path:
    """Return a ``Path`` inside the project's ``data`` directory."""
    root = _resolve_root(config) / "data"
    return root if sub_path is None else root / Path(sub_path)


def get_logs_path(config: Optional[EnvConfig] = None, filename: Optional[str] = None) -> Path:
    """Return the ``logs`` directory (or a specific log file)."""
    root = _resolve_root(config) / "logs"
    return root if filename is None else root / filename


def get_figures_path(config: Optional[EnvConfig] = None, filename: Optional[str] = None) -> Path:
    """Return the ``figures`` directory (or a specific figure file)."""
    root = _resolve_root(config) / "figures"
    return root if filename is None else root / filename


def validate_required_env_vars(
    config: Optional[EnvConfig] = None, required_services: Optional[Set[str]] = None
) -> bool:
    """Ensure every service in *required_services* has a non-empty API key."""
    if config is None:
        config = get_env_manager().config
    required_services = required_services or set()
    return all(bool(get_api_key(s, config)) for s in required_services)


def create_env_file_template() -> str:
    """Generate a minimal ``.env`` file template."""
    return (
        "# Optional API keys\n"
        "NCBI_API_KEY=\n"
        "PMDB_API_TOKEN=\n"
        "# Set to 1 to enable CI mode\n"
        "CI_MODE=0\n"
    )