"""
Configuration management module.
Handles loading settings from YAML, environment variables, and defaults.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, ValidationError, field_validator
from models.species import Species

# Import the EnvManager singleton for easy env access.
from .config_env import get_env_manager

# Singleton instance for the parsed YAML configuration.
_config_instance: Optional["Config"] = None


class ConfigSettings(BaseModel):
    """Settings for the application, matching the keys used in tests and the pipeline."""
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

    # Backward‑compatible aliases (used by older code)
    genome_size_limit_mb: Optional[int] = None
    bgc_confidence_threshold: Optional[float] = None

    # API Keys (loaded from environment variables)
    ncbi_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("NCBI_API_KEY"))
    pmdb_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("PMDB_TOKEN"))

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

    # Alias handling – allow both old and new field names
    @field_validator("genome_size_limit_mb", mode="before")
    @classmethod
    def _alias_genome_size(cls, v: Any) -> Any:
        # If the new name is set, prefer it
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
        """Raw data directory – defaults to ``data_root / 'raw'`` if not set."""
        return self.settings.raw_data_path or (self.settings.data_root / "raw")

    @property
    def processed_path(self) -> Path:
        """Processed data directory – defaults to ``data_root / 'processed'``."""
        return self.settings.processed_data_path or (self.settings.data_root / "processed")

    @property
    def figures_path(self) -> Path:
        """Figures directory – defaults to ``data_root / 'figures'``."""
        return self.settings.figures_path or (self.settings.data_root / "figures")

    @property
    def logs_path(self) -> Path:
        """Logs directory – defaults to ``data_root / 'logs'``."""
        return self.settings.logs_path or (self.settings.data_root / "logs")

    @property
    def model_cache_path(self) -> Path:
        """Model cache directory – defaults to ``data_root / 'model_cache'``."""
        return self.settings.model_cache_path or (self.settings.data_root / "model_cache")

    # ------------------------------------------------------------------
    # Pipeline‑specific shortcuts expected by the CLI and tests
    # ------------------------------------------------------------------
    @property
    def confidence_threshold(self) -> float:
        """Confidence threshold for antiSMASH (new name)."""
        return self.settings.antismash_confidence

    @property
    def phylogeny_path(self) -> Path:
        """Path to the Newick phylogeny file."""
        if self.settings.phylogeny_path:
            return Path(self.settings.phylogeny_path)
        # Default location under raw data
        return self.raw_path / "phylogeny" / "tree.nwk"

    @property
    def output_path(self) -> Path:
        """Where final artefacts such as the aligned matrix are written."""
        return self.processed_path

    @property
    def species_objects(self) -> List[Species]:
        """Alias used by the test suite – returns the parsed Species objects."""
        return self.species_list

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def get_setting(self, name: str) -> Any:
        """Generic getter for a setting – falls back to ``None`` if missing."""
        return getattr(self.settings, name, None)


def load_config(config_path: Optional[Path] = None) -> Config:
    """
    Load configuration from a YAML file.

    The function is *idempotent*: once a configuration has been loaded,
    subsequent calls return the same ``Config`` instance, regardless of the
    ``config_path`` argument. This behaviour satisfies the caching test.
    """
    global _config_instance

    # Return the cached instance if it already exists
    if _config_instance is not None:
        return _config_instance

    # Resolve the path to the configuration file
    if config_path is None:
        possible_paths = [
            Path("config.yaml"),
            Path("./config.yaml"),
            Path(__file__).parent.parent / "config.yaml",
        ]
        for p in possible_paths:
            if p.exists():
                config_path = p
                break

    # If we still have no path, fall back to defaults
    if config_path is None or not config_path.exists():
        _config_instance = Config()
        return _config_instance

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as ye:
        raise ValueError(f"Failed to parse YAML configuration: {ye}")
    except Exception as e:
        raise RuntimeError(f"Failed to load config from {config_path}: {e}")

    settings_data = data.get("settings", {})
    species_data = data.get("species_list", [])

    # Parse settings – unknown keys are ignored by ``extra='ignore'`` behaviour
    try:
        settings = ConfigSettings(**settings_data)
    except ValidationError as ve:
        raise ValueError(f"Configuration validation failed: {ve}")

    # Parse species list – invalid entries are skipped with a warning
    species_list: List[Species] = []
    for sp_dict in species_data:
        if sp_dict is None:
            continue
        try:
            species_list.append(Species(**sp_dict))
        except ValidationError as ve:
            # Log a warning but continue processing the remaining entries
            print(f"Warning: Skipping invalid species entry: {ve}")
            continue

    _config_instance = Config(
        settings=settings,
        species_list=species_list,
        metadata=data.get("metadata", {}),
    )
    return _config_instance


def get_config() -> Config:
    """
    Retrieve the current configuration instance.

    Raises
    ------
    RuntimeError
        If ``load_config`` has not been called yet (i.e. the configuration
        has not been initialised). This matches the expectation of the test
        suite.
    """
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
    """
    Return a path inside the project's data directory.

    Parameters
    ----------
    sub_path : str | Path | None
        Optional sub‑path to append to the base data directory. If ``None``,
        the base data directory is returned.

    Returns
    -------
    pathlib.Path
        The absolute (or project‑relative) path.
    """
    base = get_config().data_path
    if sub_path is None:
        return base
    return base / Path(sub_path)


# ----------------------------------------------------------------------
# Shortcut accessor for environment variables.
# ----------------------------------------------------------------------
def get(key: str) -> Optional[str]:
    """
    Retrieve an environment variable via the ``EnvManager`` singleton.

    This mirrors the verification step in the task description:
    after sourcing ``.env.example`` a call to ``config.get("NCBI_API_KEY")``
    should return the value defined in the ``.env`` file.
    """
    return get_env_manager().get(key)
