"""
Minimal simulation generator for meta‑analysis heterogeneity studies.

This module provides a lightweight implementation sufficient for the
unit tests and for the main pipeline entry point. It reads a deterministic
base CSV (with columns ``study_id,effect,se,n``), injects a specified
between‑study variance (τ²) into the true effects, and returns a namespace
containing the generated replicates.

The implementation focuses on the public API required by the rest of the
project:
  * ``SimulationConfig`` – a dataclass holding the configuration.
  * ``generate_synthetic_meta_analysis(config)`` – creates synthetic
    replicates according to ``config`` and returns an object with a
    ``replicates`` attribute.
  * ``validate_simulation_output(namespace)`` – sanity‑check that the
    generated output matches the requested configuration.
"""

from __future__ import annotations

import csv
import math
import random
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import List, Dict, Any

__all__ = [
    "SimulationConfig",
    "generate_synthetic_meta_analysis",
    "validate_simulation_output",
]


@dataclass
class SimulationConfig:
    """
    Configuration for a single heterogeneity sweep.

    Attributes
    ----------
    tau2: float
        The injected between‑study variance (τ²) for this sweep.
    num_replicates: int
        Number of synthetic datasets to generate.
    seed: int
        Random seed for reproducibility.
    base_data_path: Path | str
        Path to the deterministic base CSV containing study‑level data.
    """
    tau2: float
    num_replicates: int
    seed: int
    base_data_path: Path | str
    
    def __post_init__(self) -> None:
        # Normalise the path to a Path object.
        self.base_data_path = Path(self.base_data_path)
        if not self.base_data_path.is_file():
            raise FileNotFoundError(f"Base data file not found: {self.base_data_path}")


def _load_base_data(csv_path: Path) -> List[Dict[str, Any]]:
    """
    Load the deterministic base CSV.

    Expected columns: ``study_id,effect,se,n``.

    Returns
    -------
    List[Dict[str, Any]]
        One dictionary per study.
    """
    studies = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"study_id", "effect", "se", "n"}
        if not required.issubset(reader.fieldnames or []):
            missing = required - set(reader.fieldnames or [])
            raise ValueError(f"Base CSV missing required columns: {missing}")

        for row in reader:
            # Convert numeric fields.
            study = {
                "study_id": row["study_id"],
                "effect": float(row["effect"]),
                "se": float(row["se"]),
                "n": int(row["n"]),
            }
            studies.append(study)
    return studies


def generate_synthetic_meta_analysis(config: SimulationConfig) -> SimpleNamespace:
    """
    Generate synthetic meta‑analysis replicates.

    For each replicate we:
      1. Draw a true effect for every study by adding normal noise with
         variance ``config.tau2`` to the base effect.
      2. Store the true effect together with the original study metadata.

    The returned namespace mimics the original project's expected structure
    and provides a ``replicates`` attribute – a list where each element has
    a ``studies`` attribute (list of dicts).

    Parameters
    ----------
    config: SimulationConfig
        Configuration for the sweep.

    Returns
    -------
    SimpleNamespace
        ``namespace.replicates`` – list of replicate objects.
    """
    random.seed(config.seed)
    base_studies = _load_base_data(config.base_data_path)

    replicates = []
    for rep_idx in range(config.num_replicates):
        rep_studies = []
        for base in base_studies:
            # Inject heterogeneity: true_effect = base effect + N(0, sqrt(tau2))
            true_effect = (
                base["effect"]
                + random.gauss(0.0, math.sqrt(config.tau2))
            )
            # Observed effect could be simulated further, but the minimal
            # implementation stores the true effect and retains the original
            # standard error and sample size.
            study_record = {
                "study_id": base["study_id"],
                "effect": base["effect"],          # original effect (used as point estimate)
                "se": base["se"],
                "n": base["n"],
                "true_effect": true_effect,
            }
            rep_studies.append(study_record)

        # Simple container object for a replicate.
        replicate = SimpleNamespace(
            replicate_id=rep_idx,
            tau2=config.tau2,
            studies=rep_studies,
        )
        replicates.append(replicate)

    # Return a namespace compatible with the rest of the code base.
    return SimpleNamespace(
        config=config,
        replicates=replicates,
    )


def validate_simulation_output(namespace: SimpleNamespace) -> None:
    """
    Perform a lightweight sanity check on the generated data.

    The function asserts that:
      * ``namespace`` has a ``replicates`` attribute.
      * The number of replicates matches the requested ``num_replicates``.
      * Each replicate contains a non‑empty ``studies`` list.
      * Every study dictionary includes a ``true_effect`` key.

    Raises
    ------
    AssertionError
        If any of the expectations are violated.
    """
    if not hasattr(namespace, "replicates"):
        raise AssertionError("Simulation output missing 'replicates' attribute")

    replicates = getattr(namespace, "replicates")
    expected = namespace.config.num_replicates
    if len(replicates) != expected:
        raise AssertionError(
            f"Expected {expected} replicates, got {len(replicates)}"
        )

    for rep in replicates:
        if not hasattr(rep, "studies"):
            raise AssertionError("Replicate missing 'studies' attribute")
        if not rep.studies:
            raise AssertionError("Replicate contains no studies")
        for study in rep.studies:
            if "true_effect" not in study:
                raise AssertionError("Study record missing 'true_effect'")

    # If we reach this point the output is considered valid.
    return None
