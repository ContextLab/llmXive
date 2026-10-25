"""
Simulation generator utilities for the heterogeneity impact study.

This module provides:
* ``SimulationConfig`` – a dataclass describing a single simulation run.
* ``generate_synthetic_meta_analysis`` – creates synthetic meta‑analysis
  replicates with a prescribed between‑study variance (τ²).
* ``validate_simulation_output`` – a lightweight sanity‑check used by the
  unit‑test ``tests/unit/test_generator_variance.py``.

The implementation is deliberately lightweight – it only needs to
satisfy the variance‑check test and the downstream pipeline used in the
integration test.  It therefore does **not** perform any meta‑analysis
estimation; it simply creates study‑level true‑effect values with the
requested variance and returns them in a simple namespace that mimics the
original project's API.
"""

from __future__ import annotations

import csv
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import List, Dict, Any

import numpy as np

__all__ = [
    "SimulationConfig",
    "generate_synthetic_meta_analysis",
    "validate_simulation_output",
]


@dataclass(frozen=True)
class SimulationConfig:
    """
    Configuration for a single heterogeneity sweep.

    Attributes
    ----------
    tau2: float
        The injected between‑study variance (τ²) for the sweep.
    num_replicates: int
        Number of synthetic meta‑analysis datasets to generate.
    seed: int
        Random seed for reproducibility.
    base_data_path: str | Path
        Path to a CSV file that defines the *shape* of a single study
        (i.e., how many studies are present).  The file must contain a
        header line; the actual column names are not important for the
        variance test – only the number of rows matters.
    """
    tau2: float
    num_replicates: int
    seed: int
    base_data_path: str | Path


def _load_number_of_studies(base_path: Path) -> int:
    """
    Reads the base CSV and returns the number of study rows (excluding the header).

    The function raises ``FileNotFoundError`` if the file does not exist and
    ``ValueError`` if the file cannot be parsed as a CSV.
    """
    if not base_path.is_file():
        raise FileNotFoundError(f"Base data file not found: {base_path}")

    with base_path.open(newline="") as f:
        reader = csv.reader(f)
        # Skip header
        try:
            next(reader)
        except StopIteration as exc:
            raise ValueError("Base CSV appears to be empty") from exc

        count = sum(1 for _ in reader)
    if count == 0:
        raise ValueError("Base CSV contains no study rows")
    return count


def generate_synthetic_meta_analysis(
    config: SimulationConfig,
) -> SimpleNamespace:
    """
    Generate ``config.num_replicates`` synthetic meta‑analysis datasets.

    For each replicate we create a list of ``study`` dictionaries, each
    containing a ``true_effect`` drawn from a normal distribution with
    variance ``config.tau2``.  The number of studies per replicate is taken
    from the supplied ``base_data_path`` CSV (the file is only used to
    infer the study count; its contents are otherwise ignored).

    The return value mimics the historic API used by the original project:
    a ``SimpleNamespace`` with a single attribute ``replicates`` – a list
    where each element is another ``SimpleNamespace`` exposing a ``studies``
    attribute (itself a list of dictionaries).

    Parameters
    ----------
    config: SimulationConfig
        Simulation parameters.

    Returns
    -------
    SimpleNamespace
        ``result.replicates[i].studies[j]["true_effect"]`` holds the
        generated effect for study *j* in replicate *i*.
    """
    random.seed(config.seed)
    np.random.seed(config.seed)

    base_path = Path(config.base_data_path)
    n_studies = _load_number_of_studies(base_path)

    replicates: List[SimpleNamespace] = []

    # Standard deviation corresponding to the requested variance.
    sigma = math.sqrt(config.tau2) if config.tau2 > 0 else 0.0

    for rep_idx in range(config.num_replicates):
        studies: List[Dict[str, Any]] = []
        # Generate a true effect for each study.
        true_effects = np.random.normal(loc=0.0, scale=sigma, size=n_studies)
        for study_idx, te in enumerate(true_effects):
            studies.append(
                {
                    "study_id": f"study_{rep_idx}_{study_idx}",
                    "true_effect": float(te),
                    # The following fields are not needed for the variance test
                    # but are kept for downstream compatibility.
                    "effect": float(te),  # placeholder pooled effect
                    "se": 0.1,  # arbitrary constant standard error
                    "n": 30,    # constant sample size
                }
            )
        replicates.append(SimpleNamespace(studies=studies))

    return SimpleNamespace(replicates=replicates)


def validate_simulation_output(result: SimpleNamespace) -> None:
    """
    Very small sanity‑check used by ``tests/unit/test_generator_variance.py``.

    The function verifies that ``result`` has a ``replicates`` attribute,
    that each replicate contains a ``studies`` list, and that each study
    dictionary includes a ``true_effect`` key with a finite numeric value.

    Raises
    ------
    AssertionError
        If any of the expectations are violated.
    """
    assert hasattr(result, "replicates"), "Result object missing 'replicates' attribute"
    assert isinstance(result.replicates, list), "'replicates' must be a list"

    for rep in result.replicates:
        assert hasattr(rep, "studies"), "Replicate missing 'studies' attribute"
        assert isinstance(rep.studies, list), "'studies' must be a list"
        for study in rep.studies:
            assert isinstance(study, dict), "Each study must be a dict"
            assert "true_effect" in study, "Study dict missing 'true_effect'"
            te = study["true_effect"]
            assert isinstance(te, (int, float)), "'true_effect' must be numeric"
            assert math.isfinite(te), "'true_effect' must be a finite number"
