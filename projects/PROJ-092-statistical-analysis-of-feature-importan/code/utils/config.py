"""Base configuration management for the feature-importance drift project.

Provides a singleton :class:`Config` object that behaves like a mapping
(``config.get(key, default)``) so pipeline code can query settings with
sensible defaults, and can optionally be overridden from a JSON file or
environment variables.
"""
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

@dataclass
class Config:
    """Project-wide configuration with mapping-style access."""

    project_root: Path = field(
        default_factory=lambda: Path(__file__).resolve().parents[2]
    )
    # Derived directories (set in __post_init__)
    data_dir: Path = field(init=False)
    raw_dir: Path = field(init=False)
    processed_dir: Path = field(init=False)
    outputs_dir: Path = field(init=False)
    figures_dir: Path = field(init=False)

    # Analysis settings (defaults per spec/plan)
    base_path: str = "."
    raw_data_file: str = "data/raw/electricity_load.csv"
    target_col: str = "load"
    window_size_days: int = 30
    r2_threshold: float = 0.8
    min_variance_threshold: float = 1e-7
    random_seed: int = 42
    n_estimators: int = 100
    max_depth: int = 10

    # Extra overrides loaded from JSON file or environment
    overrides: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.data_dir = self.project_root / "data"
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.outputs_dir = self.project_root / "outputs"
        self.figures_dir = self.project_root / "figures"

    # ------------------------------------------------------------------
    # Mapping-style access so callers can do config.get("key", default)
    # ------------------------------------------------------------------
    def _all_settings(self) -> Dict[str, Any]:
        settings: Dict[str, Any] = dict(self.overrides)
        for f in self.__dataclass_fields__:
            if f == "overrides":
                continue
            settings[f] = getattr(self, f)
        settings["paths"] = {
            "importance_profiles": str(self.outputs_dir / "importance_profiles.csv"),
            "stability_report": str(self.outputs_dir / "stability_report.json"),
            "drift_metrics": str(self.outputs_dir / "drift_metrics.csv"),
            "null_baseline": str(self.outputs_dir / "null_baseline.json"),
            "global_stats": str(self.outputs_dir / "global_stats.json"),
            "p_values": str(self.outputs_dir / "p_values.json"),
        }
        # Paths as strings for convenience
        for name in (
            "project_root", "data_dir", "raw_dir", "processed_dir",
            "outputs_dir", "figures_dir",
        ):
            settings[name] = str(getattr(self, name))
        return settings

    def get(self, key: str, default: Any = None) -> Any:
        return self._all_settings().get(key, default)

    def __getitem__(self, key: str) -> Any:
        try:
            return self._all_settings()[key]
        except KeyError:
            raise KeyError(f"Unknown config key: {key}")

    def __contains__(self, key: str) -> bool:
        return key in self._all_settings()

    def to_dict(self) -> Dict[str, Any]:
        return self._all_settings()

_config_instance: Optional[Config] = None

def get_config(config_path: Optional[str] = None) -> Config:
    """Return the singleton Config, optionally applying JSON overrides.

    Args:
        config_path: Optional path to a JSON file whose keys override
            the defaults. Missing files are ignored (defaults are used).

    Returns:
        The project configuration object.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    if config_path:
        path = Path(config_path)
        if path.is_file():
            with open(path, "r") as f:
                data = json.load(f)
            if isinstance(data, dict):
                _config_instance.overrides.update(data)
        else:
            # A path was requested but does not exist: keep defaults.
            pass
    return _config_instance

def reset_config() -> None:
    """Reset the singleton so the next get_config() builds fresh."""
    global _config_instance
    _config_instance = None

def load_config_from_env() -> Dict[str, Any]:
    """Load configuration overrides from ``FID_*`` environment variables.

    Returns the dict of overrides that were applied (also merged into
    the current singleton, if one exists).
    """
    overrides: Dict[str, Any] = {}
    prefix = "FID_"
    mapping = {
        "FID_TARGET_COL": ("target_col", str),
        "FID_WINDOW_SIZE_DAYS": ("window_size_days", int),
        "FID_R2_THRESHOLD": ("r2_threshold", float),
        "FID_RANDOM_SEED": ("random_seed", int),
        "FID_RAW_DATA_FILE": ("raw_data_file", str),
    }
    for env_var, (key, cast) in mapping.items():
        raw = os.environ.get(env_var)
        if raw is not None:
            try:
                overrides[key] = cast(raw)
            except (TypeError, ValueError):
                continue
    if _config_instance is not None and overrides:
        _config_instance.overrides.update(overrides)
    return overrides

def main() -> None:
    cfg = get_config()
    print("Configuration module loaded.")
    print(json.dumps(cfg.to_dict(), indent=2, default=str))

if __name__ == "__main__":
    main()
