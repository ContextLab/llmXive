"""
Configuration management module.
Handles loading settings from YAML (``config.yaml`` / ``spec.yaml``),
environment variables, and defaults.  Also hosts the global random
seed manager (T004): ``load_config`` seeds Python's ``random`` and
NumPy's RNG so runs are reproducible, and ``config.seed`` is stable
across runs.
"""

import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from models.species import Species
from pydantic import BaseModel, Field, ValidationError, field_validator

# Import the EnvManager singleton for easy env access.
from config_env import get_env_manager

# Load .env file using python-dotenv
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError as e:
    raise ImportError(
        "python-dotenv is required for environment-variable management. "
        "Install it via 'pip install python-dotenv' and ensure a .env file exists."
    ) from e

# Singleton instance for the parsed YAML configuration.
_config_instance: Optional["Config"] = None

# Global seed managed by the seed manager.
_global_seed: int = 42


class ConfigSettings(BaseModel):
    """Settings for the application, matching the keys used in tests and the pipeline."""

    # Reproducibility (T004)
    seed: int = Field(default=42)

    # Core data directories
    data_root: Path = Field(default=Path("data"))
    raw_data_path: Optional[Path] = None
    processed_data_path: Optional[Path] = None
    figures_path: Optional[Path] = None
    logs_path: Optional[Path] = None
    model_cache_path: Optional[Path] = None

    # Pipeline parameters (names expected by the test suite)
    phylogeny_path: Optional[str] = None
    mibig_ontology_path: Optional[str] = None
    max_genome_size_mb: int = Field(default=500)
    antismash_confidence: float = Field(default=0.5)
    min_species_count: int = Field(default=5)
    download_timeout: int = Field(default=300)

    # Backward-compatible aliases (used by older code)
    genome_size_limit_mb: Optional[int] = None
    bgc_confidence_threshold: Optional[float] = None

    # API Keys (loaded from environment variables)
    ncbi_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("NCBI_API_KEY")
    )
    pmdb_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("PMDB_API_TOKEN")
    )

    # Convert any string paths to Path objects
    @field_validator(
        "data_root",
        "raw_data_path",
        "processed_data_path",
        "figures_path",
        "logs_path",
        "model_cache_path",
        mode="before",
    )
    @classmethod
    def _to_path(cls, v: Any) -> Any:
        if isinstance(v, str):
            return Path(v)
        return v

    @field_validator("genome_size_limit_mb", mode="before")
    @classmethod
    def _alias_genome_size(cls, v: Any) -> Any:
        return v

    @field_validator("bgc_confidence_threshold", mode="before")
    @classmethod
    def _alias_confidence(cls, v: Any) -> Any:
        return v


class Config(BaseModel):
    """Main configuration container."""

    settings: ConfigSettings = Field(default_factory=ConfigSettings)
    species_list: List[Species] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # ------------------------------------------------------------------
    # Convenience properties for backward compatibility with existing code
    # ------------------------------------------------------------------
    @property
    def data_path(self) -> Path:
        """Alias for ``settings.data_root`` used by legacy code."""
        return self.settings.data_root

    @property
    def raw_path(self) -> Path:
        return self.settings.raw_data_path or (self.settings.data_root / "raw")

    @property
    def processed_path(self) -> Path:
        return self.settings.processed_data_path or (
            self.settings.data_root / "processed"
        )

    @property
    def figures_path(self) -> Path:
        return self.settings.figures_path or (self.settings.data_root / "figures")

    @property
    def logs_path(self) -> Path:
        return self.settings.logs_path or (self.settings.data_root / "logs")

    @property
    def model_cache_path(self) -> Path:
        return self.settings.model_cache_path or (
            self.settings.data_root / "model_cache"
        )

    # ------------------------------------------------------------------
    # Pipeline-specific shortcuts expected by the CLI and tests
    # ------------------------------------------------------------------
    @property
    def confidence_threshold(self) -> float:
        return self.settings.antismash_confidence

    @property
    def seed(self) -> int:
        """Global random seed (T004) – reproducible across runs."""
        return self.settings.seed

    @property
    def phylogeny_path(self) -> Path:
        if self.settings.phylogeny_path:
            return Path(self.settings.phylogeny_path)
        return self.raw_path / "phylogeny" / "tree.nwk"

    @property
    def output_path(self) -> Path:
        return self.processed_path

    @property
    def species_objects(self) -> List[Species]:
        return self.species_list

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def get_setting(self, name: str) -> Any:
        return getattr(self.settings, name, None)


# ----------------------------------------------------------------------
# Seed manager (T004)
# ----------------------------------------------------------------------
def set_global_seed(seed: Optional[int] = None) -> int:
    """
    Set the global random seed for Python's ``random`` module and NumPy.

    Returns the seed actually applied.  When *seed* is ``None`` the
    currently configured seed (default 42) is re-applied, which makes
    consecutive runs reproducible.
    """
    global _global_seed
    if seed is not None:
        _global_seed = int(seed)
    random.seed(_global_seed)
    try:
        import numpy as np

        np.random.seed(_global_seed)
    except ImportError:
        pass
    return _global_seed


def get_seed() -> int:
    """Return the current global seed without re-seeding."""
    return _global_seed


def load_config(config_path: Optional[Path] = None) -> Config:
    """
    Load configuration from a YAML file (``config.yaml`` / ``spec.yaml``).

    The function is *idempotent*: once a configuration has been loaded,
    subsequent calls return the same ``Config`` instance, regardless of the
    ``config_path`` argument.

    As part of T004 the global random seed is applied immediately after the
    configuration is parsed, and an INFO message is written to
    ``logs/run.log``.
    """
    global _config_instance

    # Ensure .env file is loaded
    try:
        from dotenv import load_dotenv

        load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    except Exception:
        pass

    if _config_instance is not None:
        return _config_instance

    if config_path is None:
        project_root = Path(__file__).resolve().parent.parent
        possible_paths = [
            Path("config.yaml"),
            Path("./config.yaml"),
            project_root / "config.yaml",
            project_root / "config" / "spec.yaml",
            project_root / "spec.yaml",
        ]
        for p in possible_paths:
            if p.exists():
                config_path = p
                break

    if config_path is None or not Path(config_path).exists():
        _config_instance = Config()
    else:
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except yaml.YAMLError as ye:
            raise ValueError(f"Failed to parse YAML configuration: {ye}")
        except Exception as e:
            raise RuntimeError(f"Failed to load config from {config_path}: {e}")

        settings_data = data.get("settings", {})
        species_data = data.get("species_list", data.get("species", []))

        try:
            settings = ConfigSettings(**settings_data)
        except ValidationError as ve:
            raise ValueError(f"Configuration validation failed: {ve}")

        species_list: List[Species] = []
        for sp_dict in species_data:
            if sp_dict is None:
                continue
            if isinstance(sp_dict, str):
                sp_dict = {"name": sp_dict}
            try:
                species_list.append(Species(**sp_dict))
            except ValidationError as ve:
                print(f"Warning: Skipping invalid species entry: {ve}")
                continue

        _config_instance = Config(
            settings=settings,
            species_list=species_list,
            metadata=data.get("metadata", {}),
        )

    # T004: apply the seed and log the configuration load.
    set_global_seed(_config_instance.seed)
    try:
        from utils.logging import get_logger

        get_logger(__name__).info(
            "Configuration loaded (seed=%d, species=%d)",
            _config_instance.seed,
            len(_config_instance.species_list),
        )
    except Exception:
        pass

    return _config_instance


def get_config() -> Config:
    """Retrieve the current configuration instance (raises if unloaded)."""
    global _config_instance
    if _config_instance is None:
        raise RuntimeError("Configuration not loaded")
    return _config_instance


def reset_config() -> None:
    """Reset the configuration singleton to force a reload on next call."""
    global _config_instance
    _config_instance = None


def get_species_list() -> List[Species]:
    """Convenience function to retrieve the list of parsed Species objects."""
    return get_config().species_list


def get_data_path(sub_path: Optional[Union[str, Path]] = None) -> Path:
    """Return a path inside the project's data directory."""
    base = get_config().data_path
    if sub_path is None:
        return base
    return base / Path(sub_path)


def get(key: str) -> Optional[str]:
    """Retrieve an environment variable via the ``EnvManager`` singleton."""
    val = get_env_manager().get(key)
    if val is None:
        val = os.getenv(key)
    return val
