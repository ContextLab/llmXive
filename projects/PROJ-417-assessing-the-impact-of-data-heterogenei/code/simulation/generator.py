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
* ``write_simulation_results`` – writes ``SimulatedDataset`` records to a
  JSON‑Lines file that conforms to ``contracts/simulated_dataset.schema.yaml``.
* CLI entry point – accepts a list of τ² values, number of replicates per
  τ², sweep type, and output path.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
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
    "write_simulation_results",
    "main",
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
    sweep_type: str = "primary"  # “primary” or “sensitivity”

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

    # Draw a true effect for each study from N(0, sqrt(tau2))
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
        studies.append(
            {
                "study_id": f"study_{i}",
                "true_effect": float(true_effects[i]),
                "effect_size": float(obs_effect),
                "standard_error": float(se),
                "variance": float(obs_variance),
                "n": 30,
            }
        )

    mean_effect = float(np.mean(true_effects))
    observed_between = (
        float(np.var(true_effects, ddof=1)) if n > 1 else 0.0
    )

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
# JSON‑Lines writer conforming to the contract
# ----------------------------------------------------------------------
def write_simulation_results(
    results: Iterable[SimulationResult],
    sweep_type: str,
    output_path: Path | None = None,
) -> Path:
    """
    Write a sequence of ``SimulationResult`` objects to a JSON‑Lines file
    that matches ``contracts/simulated_dataset.schema.yaml``.

    The contract expects the following fields per line:
    - replicate_id (int)
    - tau_squared (number)
    - true_effect (number)
    - study_effects (array[number])
    - study_se (array[number])
    - study_sizes (array[int])
    - k (int)
    - sweep_type (string, enum)

    Parameters
    ----------
    results: Iterable[SimulationResult]
        The simulated replicates.
    sweep_type: str
        Either ``\"primary\"`` or ``\"sensitivity\"`` – recorded for each line.
    output_path: Path | None
        Destination path.  If ``None`` the default location
        ``data/results/simulation_raw.jsonl`` (via ``paths.data``) is used.
    """
    if output_path is None:
        # Use the *data* folder as required by the specification.
        output_path = paths.data("results", "simulation_raw.jsonl")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    with output_path.open("w", encoding="utf-8") as f:
        for res in results:
            # Extract per‑study vectors
            study_effects = [s.get("effect_size", s.get("effect", 0.0)) for s in res.studies]
            study_se = [s.get("standard_error", s.get("se", 0.1)) for s in res.studies]
            study_sizes = [int(s.get("n", 0)) for s in res.studies]

            record: Dict[str, Any] = {
                "replicate_id": res.replicate_id,
                "tau_squared": res.injected_tau2,
                "true_effect": res.injected_true_effect,
                "study_effects": study_effects,
                "study_se": study_se,
                "study_sizes": study_sizes,
                "k": len(res.studies),
                "sweep_type": sweep_type,
            }
            json.dump(record, f)
            f.write("\n")
            written += 1

    log.info(f"Written {written} simulated replicates to {output_path}")
    return output_path

# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def _parse_cli_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate synthetic meta‑analysis replicates."
    )
    parser.add_argument(
        "--tau-squared",
        type=str,
        required=True,
        help="Comma‑separated list of τ² values (e.g. \"0,0.1,0.5\").",
    )
    parser.add_argument(
        "--replicates",
        type=int,
        required=True,
        help="Number of replicates to generate per τ² level.",
    )
    parser.add_argument(
        "--sweep-type",
        type=str,
        choices=["primary", "sensitivity"],
        required=True,
        help="Sweep type – either \"primary\" or \"sensitivity\".",
    )
    parser.add_argument(
        "--base-data",
        type=str,
        default=str(paths.data("processed", "base_template.csv")),
        help="Path to the base CSV containing study SEs.",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=str(paths.data("results", "simulation_raw.jsonl")),
        help="Output JSON‑Lines file.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Base random seed for reproducibility.",
    )
    return parser.parse_args(argv)

def main(argv: List[str] | None = None) -> int:
    args = _parse_cli_args(argv)

    # Parse τ² list
    try:
        tau2_values = [float(v) for v in args.tau_squared.split(",") if v.strip() != ""]
    except ValueError as exc:
        log.error("Failed to parse --tau-squared values.")
        raise

    # Load base SEs (effects are not needed for the current generator)
    _, base_ses = load_base_data_structure(args.base_data)

    all_results: List[SimulationResult] = []
    replicate_counter = 0

    for tau2 in tau2_values:
        cfg = SimulationConfig(
            injected_true_effect=0.0,
            injected_tau2=tau2,
            N_studies=_load_number_of_studies(Path(args.base_data)),
            base_data_path=args.base_data,
            seed=args.seed,
            sweep_type=args.sweep_type,
        )
        for rep_idx in range(args.replicates):
            # Derive a deterministic RNG per replicate
            rng = np.random.default_rng(args.seed + replicate_counter)
            res = create_replicate(cfg, [], base_ses, rng)
            # Assign a global replicate_id as required by the schema
            object.__setattr__(res, "replicate_id", replicate_counter)
            all_results.append(res)
            replicate_counter += 1

    write_simulation_results(
        all_results,
        sweep_type=args.sweep_type,
        output_path=Path(args.out),
    )
    return 0

if __name__ == "__main__":
    sys.exit(main())