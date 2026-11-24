import json
import logging
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

class MissingMechanism(str, Enum):
    MCAR = "MCAR"
    MAR = "MAR"
    MNAR = "MNAR"

class OutcomeType(str, Enum):
    CONTINUOUS = "continuous"
    BINARY = "binary"

class AnalysisMethod(str, Enum):
    CC = "CC"
    MI = "MI"
    IPW = "IPW"

@dataclass
class SimulationConfig:
    dataset_source: int
    missing_mechanisms: List[MissingMechanism] = field(default_factory=lambda: [MissingMechanism.MCAR])
    missing_rates: List[float] = field(default_factory=lambda: [0.05])
    analysis_methods: List[AnalysisMethod] = field(default_factory=lambda: [AnalysisMethod.CC])
    outcome_type: OutcomeType = OutcomeType.CONTINUOUS
    n_iterations: int = 15000
    seed: int = 42
    alpha: float = 0.05
    covariate_for_mar: Optional[str] = None
    alternative_hypothesis: bool = False

    @classmethod
    def from_json_file(cls, path: str) -> "SimulationConfig":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Convert strings to Enums where appropriate
        data["missing_mechanisms"] = [MissingMechanism(m) for m in data.get("missing_mechanisms", [])]
        data["analysis_methods"] = [AnalysisMethod(m) for m in data.get("analysis_methods", [])]
        if "outcome_type" in data:
            data["outcome_type"] = OutcomeType(data["outcome_type"])
        return cls(**data)

    def to_json(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2)

def load_config(config_path: str) -> SimulationConfig:
    """
    Load a ``SimulationConfig`` from ``config_path``. This is a thin
    wrapper around ``SimulationConfig.from_json_file`` that raises a
    ``FileNotFoundError`` if the path does not exist.
    """
    if not Path(config_path).exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    return SimulationConfig.from_json_file(config_path)

def save_config(config: SimulationConfig, output_path: str) -> None:
    """Persist a ``SimulationConfig`` to ``output_path`` as JSON."""
    config.to_json(output_path)

def validate_config(config: SimulationConfig) -> bool:
    """
    Perform additional runtime validation on a ``SimulationConfig``.
    The dataclass itself already validates its fields in ``__post_init__``.
    This function exists for backward compatibility with the original
    API and can be extended with extra checks if needed.
    """
    # Example additional check: ensure at least one analysis method is selected
    if not config.analysis_methods:
        raise ValueError("At least one analysis method must be specified.")
    return True

def create_default_config(
    dataset_id: int,
    mechanism: Any,
    missing_rate: float,
    outcome_type: Any,
    *,
    n_iterations: int = 15000,
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
    if isinstance(mechanism, str):
        mechanism = MissingMechanism(mechanism.upper())
    if isinstance(outcome_type, str):
        outcome_type = OutcomeType(outcome_type.lower())

    if analysis_methods is None:
        analysis_methods = [AnalysisMethod.CC, AnalysisMethod.MI, AnalysisMethod.IPW]

    return SimulationConfig(
        dataset_source=dataset_id,
        missing_mechanisms=[mechanism],
        missing_rates=[missing_rate],
        analysis_methods=analysis_methods,
        outcome_type=outcome_type,
        n_iterations=n_iterations,
        seed=seed,
        alpha=alpha,
        covariate_for_mar=covariate_for_mar,
        alternative_hypothesis=alternative_hypothesis,
    )

# ----------------------------------------------------------------------
# Helper to convert a SimulationConfig to a plain dict (used by main.py)
# ----------------------------------------------------------------------
def config_to_dict(config: SimulationConfig) -> Dict[str, Any]:
    """
    Return a dictionary representation of ``SimulationConfig`` suitable for
    JSON serialisation or downstream consumption.  This mirrors the
    original helper that was missing and caused import errors in ``main.py``.
    """
    # Use asdict to capture all fields, then convert Enums to their values
    raw_dict = asdict(config)
    # Convert Enum instances to their raw string values
    for key, value in raw_dict.items():
        if isinstance(value, Enum):
            raw_dict[key] = value.value
        elif isinstance(value, list):
            raw_dict[key] = [v.value if isinstance(v, Enum) else v for v in value]
    return raw_dict
