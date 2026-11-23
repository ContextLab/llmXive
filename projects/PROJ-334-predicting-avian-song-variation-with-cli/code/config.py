"""
Configuration loader for the avian song variation project.

This module defines a ``Config`` dataclass that reads configuration values
from (in order of priority):

1. Environment variables (e.g., ``JOIN_RADIUS_KM``)
2. A YAML configuration file (``config.yaml`` or ``config.yml`` in the
   project root)
3. Hard‑coded defaults.

The primary purpose of the loader is to expose the ``join_radius_km``
parameter with a default value of ``10`` km, as required by the
specification.  Additional configuration fields are provided for
completeness and future extension.
"""

import os
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any, Dict

@dataclass
class Config:
    """
    Dataclass representing the project configuration.

    Attributes
    ----------
    data_dir : Path
        Directory where raw/processed data live.
    code_dir : Path
        Directory containing source code.
    tests_dir : Path
        Directory containing test modules.
    state_dir : Path
        Directory for project state files.
    join_radius_km : float
        Spatial join radius in kilometres (default 10 km).
    max_records : Optional[int]
        Optional cap on the number of records to process.
    log_level : str
        Logging verbosity (default ``INFO``).
    """
    # Core directories – defaults are relative to the project root.
    data_dir: Path = field(default_factory=lambda: Path("data"))
    code_dir: Path = field(default_factory=lambda: Path("code"))
    tests_dir: Path = field(default_factory=lambda: Path("tests"))
    state_dir: Path = field(default_factory=lambda: Path("state/projects"))

    # Primary configurable parameter.
    join_radius_km: float = 10.0

    # Optional extras.
    max_records: Optional[int] = None
    log_level: str = "INFO"

    # Internal storage for raw config dict (useful for debugging).
    _raw_config: Dict[str, Any] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        """
        Resolve configuration sources and apply overrides.
        """
        # 1. Load from a YAML file if present.
        yaml_path = self._detect_yaml_path()
        if yaml_path:
            self._load_from_yaml(yaml_path)

        # 2. Override with environment variables.
        self._load_from_env()

        # 3. Apply any explicit overrides that may have been passed via
        #    the ``load_config`` convenience function.
        #    (Handled in ``load_config`` – no extra work here.)

        # 4. Ensure defaults for any missing values.
        self._apply_defaults()

        # 5. Resolve any relative paths to absolute paths.
        self._resolve_paths()

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    @staticmethod
    def _detect_yaml_path() -> Optional[Path]:
        """Return the first existing config.yaml / config.yml file."""
        possible = [
            Path("config.yaml"),
            Path("config.yml"),
            Path("./config.yaml"),
            Path("./config.yml"),
        ]
        for p in possible:
            if p.is_file():
                return p
        return None

    def _load_from_yaml(self, yaml_path: Path) -> None:
        """Load configuration values from a YAML file into ``_raw_config``."""
        try:
            with yaml_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                if isinstance(data, dict):
                    self._raw_config.update(data)
        except Exception as e:
            # We deliberately do not raise – missing or malformed YAML should
            # not crash the loader; we fall back to env vars / defaults.
            print(f"Warning: could not read config file {yaml_path}: {e}")

    def _load_from_env(self) -> None:
        """Populate configuration from environment variables."""
        env_map = {
            "DATA_DIR": "data_dir",
            "CODE_DIR": "code_dir",
            "TESTS_DIR": "tests_dir",
            "STATE_DIR": "state_dir",
            "JOIN_RADIUS_KM": "join_radius_km",
            "MAX_RECORDS": "max_records",
            "LOG_LEVEL": "log_level",
        }
        for env_var, attr in env_map.items():
            val = os.getenv(env_var)
            if val is None:
                continue
            if attr in {"join_radius_km"}:
                try:
                    setattr(self, attr, float(val))
                except ValueError:
                    pass  # keep previous value if conversion fails
            elif attr in {"max_records"}:
                try:
                    setattr(self, attr, int(val))
                except ValueError:
                    pass
            else:
                # For path‑like values we keep the raw string; later
                # ``_resolve_paths`` will turn them into ``Path`` objects.
                setattr(self, attr, Path(val) if "dir" in attr else val)

    def _apply_defaults(self) -> None:
        """Fill in any missing attributes from the YAML config or defaults."""
        # Mapping of attribute names to their default values.
        defaults = {
            "data_dir": self.data_dir,
            "code_dir": self.code_dir,
            "tests_dir": self.tests_dir,
            "state_dir": self.state_dir,
            "join_radius_km": self.join_radius_km,
            "max_records": self.max_records,
            "log_level": self.log_level,
        }

        for key, default_val in defaults.items():
            # Prefer values already set on the instance; otherwise fall back
            # to YAML values; finally use the hard‑coded default.
            if getattr(self, key, None) is not None:
                continue
            yaml_val = self._raw_config.get(key)
            if yaml_val is not None:
                setattr(self, key, yaml_val)
            else:
                setattr(self, key, default_val)

    def _resolve_paths(self) -> None:
        """Convert directory attributes to absolute ``Path`` objects."""
        project_root = Path.cwd()
        for attr in ("data_dir", "code_dir", "tests_dir", "state_dir"):
            current = getattr(self, attr)
            if isinstance(current, (str, Path)):
                p = Path(current)
                if not p.is_absolute():
                    p = project_root / p
                setattr(self, attr, p.resolve())

    # ------------------------------------------------------------------
    # Convenience accessors
    # ------------------------------------------------------------------
    @property
    def join_radius(self) -> float:
        """Alias for ``join_radius_km`` – kept for backward compatibility."""
        return self.join_radius_km

    def as_dict(self) -> Dict[str, Any]:
        """Return a plain dictionary representation of the configuration."""
        return {
            "data_dir": str(self.data_dir),
            "code_dir": str(self.code_dir),
            "tests_dir": str(self.tests_dir),
            "state_dir": str(self.state_dir),
            "join_radius_km": self.join_radius_km,
            "max_records": self.max_records,
            "log_level": self.log_level,
        }

    def __repr__(self) -> str:
        return (
            f"Config(join_radius_km={self.join_radius_km}, "
            f"data_dir={self.data_dir}, code_dir={self.code_dir}, "
            f"tests_dir={self.tests_dir}, state_dir={self.state_dir})"
        )

def load_config(config_path: Optional[Path] = None, **overrides) -> Config:
    """
    Convenience wrapper to instantiate ``Config`` with an optional explicit
    YAML path and any keyword overrides.

    Parameters
    ----------
    config_path : Optional[Path]
        Path to a YAML configuration file.  If omitted, the loader will
        search for ``config.yaml`` / ``config.yml`` in the project root.
    **overrides :
        Direct keyword arguments that take precedence over all other
        sources (environment variables and YAML file).

    Returns
    -------
    Config
        Fully populated configuration instance.
    """
    # If a custom path is supplied, we temporarily set the environment
    # variable ``CONFIG_PATH`` so that ``Config`` can discover it during its
    # initialization routine.
    if config_path is not None:
        os.environ["CONFIG_PATH"] = str(config_path)

    config = Config()
    # Apply explicit overrides after the object has been constructed.
    for key, value in overrides.items():
        if hasattr(config, key):
            setattr(config, key, value)

    # Clean up the temporary env var to avoid side effects.
    if "CONFIG_PATH" in os.environ:
        del os.environ["CONFIG_PATH"]

    return config