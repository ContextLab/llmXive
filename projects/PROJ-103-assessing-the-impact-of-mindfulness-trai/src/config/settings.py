"""
Base configuration management for mindfulness-DMN connectivity study.

This module defines the configuration structure with type hints and
JSON-serializable format as required by the project specification.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Tuple


@dataclass
class DatasetPaths:
    """Dataset path configuration with raw, processed, and result directories."""

    raw: str = "data/raw"
    processed: str = "data/processed"
    result: str = "data/results"

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> DatasetPaths:
        """Create instance from dictionary."""
        return cls(**data)

    def validate(self) -> None:
        """Validate dataset paths are non-empty strings."""
        if not isinstance(self.raw, str) or not self.raw:
            raise ValueError("dataset_paths.raw must be a non-empty string")
        if not isinstance(self.processed, str) or not self.processed:
            raise ValueError("dataset_paths.processed must be a non-empty string")
        if not isinstance(self.result, str) or not self.result:
            raise ValueError("dataset_paths.result must be a non-empty string")


@dataclass
class PreprocessingParams:
    """Preprocessing parameters for fMRIPrep pipeline."""

    motion_correction: bool = True
    slice_timing: bool = True
    normalization: bool = True
    smoothing_mm: int = 6
    bandpass_range: Tuple[float, float] = (0.01, 0.1)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PreprocessingParams:
        """Create instance from dictionary."""
        return cls(**data)

    def validate(self) -> None:
        """Validate preprocessing parameters."""
        if not isinstance(self.motion_correction, bool):
            raise ValueError("preprocessing_params.motion_correction must be bool")
        if not isinstance(self.slice_timing, bool):
            raise ValueError("preprocessing_params.slice_timing must be bool")
        if not isinstance(self.normalization, bool):
            raise ValueError("preprocessing_params.normalization must be bool")
        if not isinstance(self.smoothing_mm, int) or self.smoothing_mm < 0:
            raise ValueError("preprocessing_params.smoothing_mm must be non-negative int")
        if not isinstance(self.bandpass_range, tuple) or len(self.bandpass_range) != 2:
            raise ValueError("preprocessing_params.bandpass_range must be tuple of 2 floats")
        low, high = self.bandpass_range
        if not (isinstance(low, (int, float)) and isinstance(high, (int, float))):
            raise ValueError("bandpass_range values must be numeric")
        if low <= 0 or high <= 0 or low >= high:
            raise ValueError("bandpass_range must be (low, high) with 0 < low < high")


@dataclass
class MotionThresholds:
    """Motion exclusion thresholds for participant filtering."""

    translation_mm: float = 3.0
    rotation_deg: float = 3.0

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> MotionThresholds:
        """Create instance from dictionary."""
        return cls(**data)

    def validate(self) -> None:
        """Validate motion thresholds are positive floats."""
        if not isinstance(self.translation_mm, (int, float)) or self.translation_mm <= 0:
            raise ValueError("motion_thresholds.translation_mm must be positive float")
        if not isinstance(self.rotation_deg, (int, float)) or self.rotation_deg <= 0:
            raise ValueError("motion_thresholds.rotation_deg must be positive float")


@dataclass
class StatisticalThresholds:
    """Statistical thresholds for hypothesis testing and NBS correction."""

    nbs_t: float = 3.1
    nbs_alpha: float = 0.05
    power_target: float = 0.80

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> StatisticalThresholds:
        """Create instance from dictionary."""
        return cls(**data)

    def validate(self) -> None:
        """Validate statistical thresholds."""
        if not isinstance(self.nbs_t, (int, float)) or self.nbs_t <= 0:
            raise ValueError("statistical_thresholds.nbs_t must be positive float")
        if not isinstance(self.nbs_alpha, (int, float)) or not (0 < self.nbs_alpha < 1):
            raise ValueError("statistical_thresholds.nbs_alpha must be in (0, 1)")
        if not isinstance(self.power_target, (int, float)) or not (0 < self.power_target <= 1):
            raise ValueError("statistical_thresholds.power_target must be in (0, 1]")


@dataclass
class Config:
    """
    Main configuration container for the mindfulness-DMN connectivity study.

    Per Constitution Principle VI, atlas_choice is set to 'AAL'.
    """

    dataset_paths: DatasetPaths = field(default_factory=DatasetPaths)
    preprocessing_params: PreprocessingParams = field(default_factory=PreprocessingParams)
    atlas_choice: str = "AAL"
    motion_thresholds: MotionThresholds = field(default_factory=MotionThresholds)
    statistical_thresholds: StatisticalThresholds = field(default_factory=StatisticalThresholds)

    def to_dict(self) -> Dict[str, Any]:
        """Convert entire config to JSON-serializable dictionary."""
        return {
            "dataset_paths": self.dataset_paths.to_dict(),
            "preprocessing_params": self.preprocessing_params.to_dict(),
            "atlas_choice": self.atlas_choice,
            "motion_thresholds": self.motion_thresholds.to_dict(),
            "statistical_thresholds": self.statistical_thresholds.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Config:
        """Create Config instance from dictionary."""
        return cls(
            dataset_paths=DatasetPaths.from_dict(data.get("dataset_paths", {})),
            preprocessing_params=PreprocessingParams.from_dict(data.get("preprocessing_params", {})),
            atlas_choice=data.get("atlas_choice", "AAL"),
            motion_thresholds=MotionThresholds.from_dict(data.get("motion_thresholds", {})),
            statistical_thresholds=StatisticalThresholds.from_dict(data.get("statistical_thresholds", {})),
        )

    def validate(self) -> None:
        """Validate all configuration components."""
        self.dataset_paths.validate()
        self.preprocessing_params.validate()
        self.motion_thresholds.validate()
        self.statistical_thresholds.validate()
        if not isinstance(self.atlas_choice, str):
            raise ValueError("atlas_choice must be a string")
        if self.atlas_choice not in ("AAL", "HarvardOxford", "Yeo"):
            raise ValueError(f"atlas_choice must be one of 'AAL', 'HarvardOxford', 'Yeo', got '{self.atlas_choice}'")

    def save(self, path: str | Path) -> None:
        """Save configuration to JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str | Path) -> Config:
        """Load configuration from JSON file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)


def get_default_config() -> Config:
    """Return a new Config instance with default values."""
    return Config()


def load_config(path: str | Path) -> Config:
    """Load configuration from a JSON file."""
    return Config.load(path)


def save_config(config: Config, path: str | Path) -> None:
    """Save configuration to a JSON file."""
    config.save(path)


def validate_config(config: Config) -> None:
    """Validate a Config instance, raising ValueError on any issues."""
    config.validate()


if __name__ == "__main__":
    # Demo: create default config and save it
    config = get_default_config()
    config.validate()

    # Save to a test location
    output_path = Path("data/results/default_config.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_config(config, output_path)
    print(f"Default configuration saved to: {output_path}")
    print(f"Configuration:\n{json.dumps(config.to_dict(), indent=2)}")
