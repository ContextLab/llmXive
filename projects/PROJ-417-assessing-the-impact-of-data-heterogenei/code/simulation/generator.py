"""
Synthetic dataset generator for the heterogeneity‑impact study.

This module provides:
* ``SimulationConfig`` – a dataclass describing a simulation configuration.
* ``SimulationResult`` – a dataclass representing a single replicate.
* ``load_base_data_structure`` – reads a CSV base file and returns effect
  sizes and standard errors.
* ``calculate_effect_and_variance`` – given a between‑study variance (τ²),
  a study’s standard error and a true effect, returns a simulated observed
  effect and its variance.
* ``create_replicate`` – builds a ``SimulationResult`` for one replicate.
* ``validate_simulation_output`` – sanity‑check that a list of results has
  the required structure.
* ``generate_synthetic_meta_analysis`` – high‑level helper used by the
  pipeline (returns a ``SimpleNamespace`` for backward compatibility).
* CLI entry point – writes ``SimulatedDataset`` records to
  ``data/results/simulation_raw.jsonl``.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import List, Dict, Any, Iterable, Union

import numpy as np

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

__all__ = [
    "SimulationConfig",
    "SimulationResult",
    "load_base_data_structure",
    "calculate_effect_and_variance",
    "create_replicate",
    "validate_simulation_output",
    "generate_synthetic_meta_analysis",
    "write_simulation_results",
]

# ----------------------------------------------------------------------
# Configuration & result containers
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class SimulationConfig:
    """
    Configuration for a synthetic meta‑analysis simulation.
    """
    # Fields required by the unit‑test API
    injected_true_effect: float = 0.0
    injected_tau2: float = 0.0
    N_studies: int = 0

    # Fields required by the pipeline / CLI
    tau2: float | None = None
    num_replicates: int | None = None
    seed: int = 0
    base_data_path: str | Path = ""

    def effective_tau2(self) -> float:
        """Return the τ² that should be used for the simulation."""
        return self.tau2 if self.tau2 is not None else self.injected_tau2

    def effective_n_studies(self) -> int:
        """Return the number of studies per replicate."""
        return self.N_studies if self.N_studies > 0 else _load_number_of_studies(
            Path(self.base_data_path)
        )

@dataclass
class SimulationResult:
    """
    Result of a single replicate.
    """
    replicate_id: int
    injected_true_effect: float
    injected_tau2: float
    N_studies: int
    studies: List[Dict[str, Any]] = field(default_factory=list)
    mean_effect: float = 0.0
    observed_between_study_variance: float = 0.0

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_number_of_studies(base_path: Path) -> int:
    """Reads the base CSV and returns the number of study rows."""
    if not base_path.is_file():
        raise FileNotFoundError(f"Base data file not found: {base_path}")

    with base_path.open(newline="") as f:
        reader = csv.reader(f)
        try:
            next(reader)  # skip header
        except StopIteration as exc:
            raise ValueError("Base CSV appears to be empty") from exc
        count = sum(1 for _ in reader)

    if count == 0:
        raise ValueError("Base CSV contains no study rows")
    return count

def load_base_data_structure(base_path: str | Path) -> tuple[list[float], list[float]]:
    """Load a base CSV file and return parallel lists of effects and SEs."""
    path = Path(base_path)
    if not path.is_file():
        raise FileNotFoundError(f"Base data file not found: {path}")

    effects: list[float] = []
    ses: list[float] = []

    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = {name.lower(): name for name in reader.fieldnames or []}
        effect_key = fieldnames.get("effect") or fieldnames.get("effect_size") or None
        se_key = fieldnames.get("standard_error") or fieldnames.get("se") or None

        if se_key is None:
            raise ValueError("CSV must contain a standard error column")

        for row in reader:
            if effect_key:
                effects.append(float(row[effect_key]))
            else:
                effects.append(0.0)
            ses.append(float(row[se_key]))

    return effects, ses

def calculate_effect_and_variance(
    tau2: float,
    base_se: float,
    true_effect: float,
    _unused: float,
    rng: np.random.Generator,
) -> tuple[float, float]:
    """Generate a simulated observed effect size and its variance."""
    sigma = math.sqrt(tau2 + base_se ** 2)
    observed_effect = rng.normal(loc=true_effect, scale=sigma)
    observed_variance = base_se ** 2 + tau2
    return float(observed_effect), float(observed_variance)

def create_replicate(
    config: SimulationConfig,
    base_effects: List[float],
    base_ses: List[float],
    rng: np.random.Generator,
) -> SimulationResult:
    """Build a single replicate according to config."""
    n = config.N_studies if config.N_studies > 0 else len(base_ses)
    if n <= 0:
        raise ValueError("Number of studies must be positive")

    true_effects = rng.normal(
        loc=config.injected_true_effect,
        scale=math.sqrt(config.injected_tau2) if config.injected_tau2 > 0 else 0.0,
        size=n,
    )

    studies: List[Dict[str, Any]] = []
    for i in range(n):
        se = base_ses[i] if i < len(base_ses) else 0.1
        obs_effect, obs_variance = calculate_effect_and_variance(
            config.injected_tau2, se, true_effects[i], config.injected_true_effect, rng
        )
        studies.append({
            "study_id": f"study_{i}",
            "true_effect": float(true_effects[i]),
            "effect_size": float(obs_effect),
            "standard_error": float(se),
            "variance": float(obs_variance),
        })

    mean_effect = float(np.mean(true_effects))
    observed_between = float(np.var(true_effects, ddof=1)) if n > 1 else 0.0

    return SimulationResult(
        replicate_id=0,
        injected_true_effect=config.injected_true_effect,
        injected_tau2=config.injected_tau2,
        N_studies=n,
        studies=studies,
        mean_effect=mean_effect,
        observed_between_study_variance=observed_between,
    )

def validate_simulation_output(results: Any) -> bool:
    """
    Validate that the results conform to the required structure.
    Handles both List[SimulationResult] and SimpleNamespace.
    """
    # Fix for TypeError in main.py: handle SimpleNamespace
    if hasattr(results, "replicates"):
        results = results.replicates
    
    if not isinstance(results, (list, tuple, Iterable)):
        raise TypeError(f"Expected iterable or SimpleNamespace, got {type(results)}")

    for res in results:
        # If it's a SimpleNamespace (from generate_synthetic_meta_analysis), 
        # it doesn't have the SimulationResult dataclass type but has 'studies'
        if not hasattr(res, "studies"):
            raise AssertionError("Result must have 'studies' attribute")
        
        studies = res.studies
        assert isinstance(studies, list), "'studies' must be a list"
        for study in studies:
            assert isinstance(study, dict), "Each study must be a dict"
            assert "true_effect" in study, "Missing 'true_effect' in study dict"
            te = study["true_effect"]
            assert isinstance(te, (int, float)), "'true_effect' must be numeric"
            assert math.isfinite(te), "'true_effect' must be finite"
    return True

# ----------------------------------------------------------------------
# High‑level generator for pipeline compatibility
# ----------------------------------------------------------------------
def generate_synthetic_meta_analysis(
    config: SimulationConfig,
) -> SimpleNamespace:
    """
    Generate synthetic meta‑analysis datasets.
    Returns a SimpleNamespace for backward compatibility with main.py.
    """
    n_studies = config.effective_n_studies()
    rng = np.random.default_rng(config.seed)
    replicates: List[SimpleNamespace] = []
    sigma = math.sqrt(config.effective_tau2()) if config.effective_tau2() > 0 else 0.0

    for rep_idx in range(config.num_replicates or 0):
        # To ensure deterministic seeding across replicates
        rep_rng = np.random.default_rng(config.seed + rep_idx)
        true_effects = rep_rng.normal(loc=0.0, scale=sigma, size=n_studies)
        studies: List[Dict[str, Any]] = []
        for study_idx, te in enumerate(true_effects):
            studies.append({
                "study_id": f"study_{rep_idx}_{study_idx}",
                "true_effect": float(te),
                "effect": float(te),
                "se": 0.1,
                "n": 30,
            })
        replicates.append(SimpleNamespace(studies=studies))

    return SimpleNamespace(replicates=replicates)

# ----------------------------------------------------------------------
# JSON‑Lines writer
# ----------------------------------------------------------------------
def write_simulation_results(
    results: Iterable[SimulationResult],
    output_path: Path | None = None,
) -> Path:
    """Write a sequence of SimulationResult objects to a JSON‑Lines file."""
    if output_path is None:
        output_path = paths.results("simulation_raw.jsonl")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to list to avoid consuming generator before logging count
    results_list = list(results)
    with output_path.open("w", encoding="utf-8") as f:
        for res in results_list:
            record: Dict[str, Any] = {
                "replicate_id": res.replicate_id,
                "tau_squared": res.injected_tau2,
                "injected_true_effect": res.injected_true_effect,
                "N_studies": res.N_studies,
                "studies": res.studies,
            }
            json.dump(record, f)
            f.write("\n")
    log.info(f"Written {len(results_list)} simulated replicates to {output_path}")
    return output_path

# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def _parse_cli_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic meta‑analysis replicates.")
    parser.add_argument("--tau-squared", type=float, required=True)
    parser.add_argument("--replicates", type=int, required=True)
    parser.add_argument("--base-data", type=str, default=str(paths.data("processed", "base_template.csv")))
    parser.add_argument("--out", type=str, default=str(paths.results("simulation_raw.jsonl")))
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args(argv)

def main(argv: List[str] | None = None) -> int:
    args = _parse_cli_args(argv)
    cfg = SimulationConfig(
        injected_true_effect=0.0,
        injected_tau2=args.tau_squared,
        N_studies=_load_number_of_studies(Path(args.base_data)),
        base_data_path=args.base_data,
        seed=args.seed,
    )
    _, base_ses = load_base_data_structure(args.base_data)
    results: List[SimulationResult] = []
    for rep_id in range(args.replicates):
        rep_rng = np.random.default_rng(args.seed + rep_id)
        res = create_replicate(cfg, [], base_ses, rep_rng)
        object.__setattr__(res, "replicate_id", rep_id)
        results.append(res)

    write_simulation_results(results, Path(args.out))
    return 0

if __name__ == "__main__":
    sys.exit(main())
