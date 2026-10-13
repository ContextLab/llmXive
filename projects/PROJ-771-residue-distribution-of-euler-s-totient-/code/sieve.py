import json
import logging
import os
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

# Existing imports and utilities are assumed to be present.
# This patch adds the `method` field to the StatisticalResult dataclass
# to record which chi‑squared testing approach was used.

logger = logging.getLogger(__name__)

@dataclass
class ResidueDataset:
    """
    Container for the raw residue counts produced by the sieve stage.
    """
    prime_modulus: int
    total_count: int
    frequency_map: Dict[int, int]

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    @staticmethod
    def from_json(data: str) -> "ResidueDataset":
        payload = json.loads(data)
        return ResidueDataset(**payload)


@dataclass
class StatisticalResult:
    """
    Container for the statistical analysis results of a single residue
    dataset. The `method` attribute records whether the chi‑squared
    test was performed via Monte‑Carlo simulation or an exact test.
    """
    test_type: str                     # e.g. "chi_squared"
    test_statistic: float              # χ² value
    p_value: Optional[float]           # Monte‑Carlo or exact p‑value
    degrees_of_freedom: int
    method: str = ""                   # "chi_squared_monte_carlo" or "chi_squared_exact"
    additional: Dict[str, Any] = None  # placeholder for future extensions

    def to_json(self) -> str:
        # Ensure the dataclass is serialisable; omit None fields for brevity.
        data = asdict(self)
        # Remove empty additional dict if not used.
        if not self.additional:
            data.pop("additional", None)
        return json.dumps(data, indent=2)

    @staticmethod
    def from_json(data: str) -> "StatisticalResult":
        payload = json.loads(data)
        return StatisticalResult(**payload)

# ----------------------------------------------------------------------
# Helper functions for persisting objects – unchanged from the original
# implementation (kept for compatibility).
# ----------------------------------------------------------------------
def save_residue_dataset(dataset: ResidueDataset, filepath: str) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(dataset.to_json())
    logger.debug("ResidueDataset saved to %s", filepath)


def load_residue_dataset(filepath: str) -> ResidueDataset:
    with open(filepath, "r", encoding="utf-8") as f:
        data = f.read()
    return ResidueDataset.from_json(data)


def save_statistical_result(result: StatisticalResult, filepath: str) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(result.to_json())
    logger.debug("StatisticalResult saved to %s", filepath)


def load_statistical_result(filepath: str) -> StatisticalResult:
    with open(filepath, "r", encoding="utf-8") as f:
        data = f.read()
    return StatisticalResult.from_json(data)
