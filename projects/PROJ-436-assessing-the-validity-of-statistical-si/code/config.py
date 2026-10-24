"""
Configuration module for simulation runs.

This module defines enums for missingness mechanisms, outcome types,
and analysis methods, as well as the ``SimulationConfig`` dataclass
that holds all parameters for a single simulation condition.  It also
provides helper functions for loading, saving, and creating default
configurations, and utilities for validation against the JSON schema
contract.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Enum definitions – these are used throughout the code base and in tests
# ----------------------------------------------------------------------
class MissingMechanism(str, Enum):
    """Missing data mechanisms."""
    MCAR = "MCAR"
    MAR = "MAR"
    MNAR = "MNAR"

    @classmethod
    def from_str(cls, value: str) -> "MissingMechanism":
        """Case‑insensitive conversion from string."""
        try:
            return cls[value.upper()]
        except KeyError as exc:
            raise ValueError(f"Invalid missing mechanism: {value}") from exc


class OutcomeType(str, Enum):
    """Supported outcome variable types."""
    CONTINUOUS = "continuous"
    BINARY = "binary"

    @classmethod
    def from_str(cls, value: str) -> "OutcomeType":
        try:
            return cls[value.lower()]
        except KeyError as exc:
            raise ValueError(f"Invalid outcome type: {value}") from exc


class AnalysisMethod(str, Enum):
    """Analysis methods for handling missing data."""
    COMPLETE_CASE = "CC"
    MULTIPLE_IMPUTATION = "MI"
    INVERSE_PROBABILITY_WEIGHTING = "IPW"

    @classmethod
    def from_str(cls, value: str) -> "AnalysisMethod":
        mapping = {
            "cc": cls.COMPLETE_CASE,
            "complete_case": cls.COMPLETE_CASE,
            "completecase": cls.COMPLETE_CASE,
            "mi": cls.MULTIPLE_IMPUTATION,
            "multiple_imputation": cls.MULTIPLE_IMPUTATION,
            "ipw": cls.INVERSE_PROBABILITY_WEIGHTING,
            "inverse_probability_weighting": cls.INVERSE_PROBABILITY_WEIGHTING,
        }
        try:
            return mapping[value.lower()]
        except KeyError as exc:
            raise ValueError(f"Invalid analysis method: {value}") from exc


# ----------------------------------------------------------------------
# Dataclass for a single simulation configuration
# ----------------------------------------------------------------------
@dataclass
class SimulationConfig:
    """
    Configuration for a single simulation condition.

    Attributes correspond to the fields required by the JSON‑Schema
    contract ``contracts/simulation_config.schema.yaml``.
    """
    dataset_id: int
    mechanism: MissingMechanism
    missing_rate: float
    outcome_type: OutcomeType
    seed: int = 42
    n_iterations: int = 1000
    alpha: float = 0.05
    analysis_methods: List[AnalysisMethod] = field(
        default_factory=lambda: list(AnalysisMethod)
    )
    alternative_hypothesis: bool = False
    covariate_for_mar: Optional[str] = None

    # ------------------------------------------------------------------
    # Validation performed automatically after dataclass init
    # ------------------------------------------------------------------
    def __post_init__(self):
        # dataset_id must be a positive integer
        if not isinstance(self.dataset_id, int) or self.dataset_id <= 0:
            raise ValueError("dataset_id must be a positive integer")

        # missing_rate must be within [0.0, 1.0]
        if not (0.0 <= self.missing_rate <= 1.0):
            raise ValueError(
                f"missing_rate must be between 0.0 and 1.0, got {self.missing_rate}"
            )

        # n_iterations must be at least 1
        if self.n_iterations < 1:
            raise ValueError(
                f"n_iterations must be at least 1, got {self.n_iterations}"
            )

        # alpha must be in (0, 1)
        if not (0.0 < self.alpha < 1.0):
            raise ValueError(
                f"alpha must be between 0.0 and 1.0, got {self.alpha}"
            )

        # analysis_methods must be non‑empty and contain valid members
        if not self.analysis_methods:
            raise ValueError("analysis_methods list cannot be empty")
        for method in self.analysis_methods:
            if not isinstance(method, AnalysisMethod):
                raise ValueError(
                    f"Invalid analysis method in list: {method}"
                )

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the dataclass to a plain dictionary suitable for JSON
        serialization. Enum members are represented by their values.
        """
        d = asdict(self)
        # Convert Enums to their raw values for JSON compatibility
        d["mechanism"] = self.mechanism.value
        d["outcome_type"] = self.outcome_type.value
        d["analysis_methods"] = [m.value for m in self.analysis_methods]
        return d

    def to_json_file(self, output_path: str) -> None:
        """
        Write the configuration to ``output_path`` as a pretty‑printed JSON
        file.  The parent directory is created automatically.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Configuration saved to {output_path}")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimulationConfig":
        """
        Build a ``SimulationConfig`` from a plain dictionary.  Strings for
        enums are accepted in any case (e.g. ``"mcar"``, ``"MCAR"``).
        """
        # Required fields
        required = ["dataset_id", "mechanism", "missing_rate", "outcome_type"]
        for field_name in required:
            if field_name not in data:
                raise ValueError(f"Missing required field: {field_name}")

        # Parse enums
        mechanism = (
            data["mechanism"]
            if isinstance(data["mechanism"], MissingMechanism)
            else MissingMechanism.from_str(str(data["mechanism"]))
        )
        outcome_type = (
            data["outcome_type"]
            if isinstance(data["outcome_type"], OutcomeType)
            else OutcomeType.from_str(str(data["outcome_type"]))
        )

        # analysis_methods: optional; if present accept list of strings or Enums
        analysis_methods_raw = data.get("analysis_methods")
        if analysis_methods_raw is None:
            analysis_methods = list(AnalysisMethod)
        else:
            analysis_methods = []
            for item in analysis_methods_raw:
                if isinstance(item, AnalysisMethod):
                    analysis_methods.append(item)
                else:
                    analysis_methods.append(AnalysisMethod.from_str(str(item)))

        return cls(
            dataset_id=int(data["dataset_id"]),
            mechanism=mechanism,
            missing_rate=float(data["missing_rate"]),
            outcome_type=outcome_type,
            seed=int(data.get("seed", 42)),
            n_iterations=int(data.get("n_iterations", 1000)),
            alpha=float(data.get("alpha", 0.05)),
            analysis_methods=analysis_methods,
            alternative_hypothesis=bool(data.get("alternative_hypothesis", False)),
            covariate_for_mar=data.get("covariate_for_mar"),
        )

    @classmethod
    def from_json_file(cls, path: str) -> "SimulationConfig":
        """
        Load a configuration from a JSON file on disk.
        """
        with open(path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)


# ----------------------------------------------------------------------
# Helper functions used by the rest of the code base
# ----------------------------------------------------------------------
def load_config(config_path: str) -> SimulationConfig:
    """
    Load a ``SimulationConfig`` from ``config_path``.  This is a thin
    wrapper around ``SimulationConfig.from_json_file`` that raises a
    ``FileNotFoundError`` if the path does not exist.
    """
    path = Path(config_path)
    if not path.is_file():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    return SimulationConfig.from_json_file(config_path)


def save_config(config: SimulationConfig, output_path: str) -> None:
    """
    Persist a ``SimulationConfig`` to ``output_path`` as JSON.
    """
    config.to_json_file(output_path)


def validate_config(config: SimulationConfig) -> bool:
    """
    Perform additional runtime validation on a ``SimulationConfig``.
    The dataclass itself already validates its fields in ``__post_init__``.
    This function exists for backward compatibility with the original
    API and can be extended with extra checks if needed.
    """
    # Example extra check – warn if 100 % missingness is paired with CC
    if config.missing_rate == 1.0 and AnalysisMethod.COMPLETE_CASE in config.analysis_methods:
        logger.warning(
            "100% missingness with Complete‑Case analysis will yield an empty dataset."
        )
    return True


def create_default_config(
    dataset_id: int,
    mechanism: Any,
    missing_rate: float,
    outcome_type: Any,
    *,
    n_iterations: int = 1000,
    seed: int = 42,
    alpha: float = 0.05,
    analysis_methods: Optional[List[Any]] = None,
    alternative_hypothesis: bool = False,
    covariate_for_mar: Optional[str] = None,
) -> SimulationConfig:
    """
    Convenience factory that builds a ``SimulationConfig`` with sensible
    defaults.  ``mechanism`` and ``outcome_type`` may be either the Enum
    members or case‑insensitive strings.
    """
    mech = (
        mechanism
        if isinstance(mechanism, MissingMechanism)
        else MissingMechanism.from_str(str(mechanism))
    )
    out_type = (
        outcome_type
        if isinstance(outcome_type, OutcomeType)
        else OutcomeType.from_str(str(outcome_type))
    )
    if analysis_methods is None:
        analysis_methods_enum = list(AnalysisMethod)
    else:
        analysis_methods_enum = []
        for item in analysis_methods:
            if isinstance(item, AnalysisMethod):
                analysis_methods_enum.append(item)
            else:
                analysis_methods_enum.append(AnalysisMethod.from_str(str(item)))

    return SimulationConfig(
        dataset_id=dataset_id,
        mechanism=mech,
        missing_rate=missing_rate,
        outcome_type=out_type,
        seed=seed,
        n_iterations=n_iterations,
        alpha=alpha,
        analysis_methods=analysis_methods_enum,
        alternative_hypothesis=alternative_hypothesis,
        covariate_for_mar=covariate_for_mar,
    )


# ----------------------------------------------------------------------
# Backwards‑compatible aliases for legacy code that expects the old names
# ----------------------------------------------------------------------
# The original module exposed ``MissingMechanism``, ``OutcomeType`` and
# ``AnalysisMethod`` as ``Literal`` types.  Keeping the Enum names ensures
# existing imports continue to work while providing richer functionality.
__all__ = [
    "MissingMechanism",
    "OutcomeType",
    "AnalysisMethod",
    "SimulationConfig",
    "load_config",
    "save_config",
    "validate_config",
    "create_default_config",
]