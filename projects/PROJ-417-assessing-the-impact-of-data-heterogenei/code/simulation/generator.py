"""
Simulation generator for meta‑analysis heterogeneity studies.

This module provides both the original API used by the pipeline
(``SimulationConfig`` with ``tau2``/``num_replicates`` fields) and
the unit‑test API required by ``tests/unit/test_generator.py``.
It also implements a CLI that matches the quick‑start run‑book
(``--tau-squared``, ``--replicates``, ``--sweep-type``, ``--out``).

The generated JSON‑lines conform to ``contracts/simulated_dataset.schema.yaml``.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import List, Dict, Any, Iterable, Optional

import numpy as np

__all__ = [
    "SimulationConfig",
    "SimulationResult",
    "load_base_data_structure",
    "calculate_effect_and_variance",
    "create_replicate",
    "validate_simulation_output",
    "generate_synthetic_meta_analysis",
    "main",
]


# -------------------------------------------------------------------------
# Data classes
# -------------------------------------------------------------------------

@dataclass
class SimulationConfig:
    """
    Unified configuration class used both by the pipeline and the unit tests.

    The class is deliberately permissive – it accepts the union of the
    arguments required by the two call‑sites:

    * Pipeline usage (``code/main.py``):
          tau2, num_replicates, seed, base_data_path
    * Unit‑test usage (``tests/unit/test_generator.py``):
          injected_true_effect, injected_tau2, N_studies,
          base_data_path, seed, sweep_type (optional)

    Unused fields are set to ``None``.  ``__post_init__`` validates the
    path to the base CSV when it is accessed.
    """
    # Pipeline fields
    tau2: Optional[float] = None
    num_replicates: Optional[int] = None
    # Unit‑test fields
    injected_true_effect: Optional[float] = None
    injected_tau2: Optional[float] = None
    N_studies: Optional[int] = None
    # Common fields
    seed: int = 42
    base_data_path: str | Path = ""
    sweep_type: str = "primary"

    def __post_init__(self) -> None:
        # Normalise the path – we only check existence when the path
        # is actually used (the generator will raise if the file is
        # missing).
        self.base_data_path = Path(self.base_data_path)


@dataclass
class SimulationResult:
    """
    Result of a single replicate.

    Attributes match what the unit tests expect and also provide the
    information needed to build a ``SimulatedDataset`` record for the
    JSON‑lines output.
    """
    replicate_id: int
    injected_tau2: float
    true_effect: float                     # overall injected true effect
    studies: List[Dict[str, Any]]          # per‑study dicts
    observed_between_study_variance: float = field(init=False)
    mean_effect: float = field(init=False)

    def __post_init__(self) -> None:
        true_effects = [s["true_effect"] for s in self.studies]
        # Sample variance (ddof=1) – if only one study we fall back to 0.
        if len(true_effects) > 1:
            self.observed_between_study_variance = float(
                np.var(true_effects, ddof=1)
            )
        else:
            self.observed_between_study_variance = 0.0
        self.mean_effect = float(np.mean(true_effects))


# -------------------------------------------------------------------------
# Helper functions used by the unit tests
# -------------------------------------------------------------------------

def load_base_data_structure(csv_path: str | Path) -> tuple[list[float], list[float]]:
    """
    Load a deterministic base CSV used by the unit tests.

    The CSV is expected to contain the columns
    ``study_id, effect_size, standard_error`` (the test creates exactly
    this header).  The function returns two parallel lists:
    * ``effects`` – the base effect for each study
    * ``ses`` – the standard error for each study
    """
    path = Path(csv_path)
    effects: list[float] = []
    ses: list[float] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"study_id", "effect_size", "standard_error"}
        if not required.issubset(reader.fieldnames or []):
            missing = required - set(reader.fieldnames or [])
            raise ValueError(
                f"Base CSV missing required columns: {missing}"
            )
        for row in reader:
            effects.append(float(row["effect_size"]))
            ses.append(float(row["standard_error"]))
    return effects, ses


def calculate_effect_and_variance(
    tau2: float,
    base_se: float,
    true_effect: float,
    _unused: float,
    rng: np.random.Generator,
) -> tuple[float, float]:
    """
    Simulate an observed effect and its variance.

    * ``tau2`` – injected between‑study variance.
    * ``base_se`` – standard error from the base data.
    * ``true_effect`` – the injected overall true effect for the study.
    * ``_unused`` – placeholder kept for backward compatibility with the
      original signature used elsewhere in the repo.
    * ``rng`` – a NumPy random generator.

    The observed variance is ``base_se**2 + tau2`` (so when ``tau2==0``
    the variance equals the base SE squared, matching the unit test).

    The observed effect is the true effect perturbed by normal noise with
    standard deviation ``sqrt(tau2)``.  When ``tau2==0`` the effect equals
    the true effect.
    """
    observed_variance = base_se ** 2 + tau2
    noise = rng.normal(0.0, math.sqrt(tau2)) if tau2 > 0 else 0.0
    observed_effect = true_effect + noise
    return float(observed_effect), float(observed_variance)


def create_replicate(
    config: SimulationConfig,
    base_effects: List[float],
    base_ses: List[float],
    rng: np.random.Generator,
) -> SimulationResult:
    """
    Produce a single replicate according to ``config``.

    The function uses ``config.injected_true_effect`` as the overall
    true effect and ``config.injected_tau2`` as the heterogeneity level.
    ``config.N_studies`` determines how many studies to simulate; if it
    is ``None`` the length of ``base_effects`` is used.

    Returns a ``SimulationResult`` instance.
    """
    tau2 = config.injected_tau2 if config.injected_tau2 is not None else 0.0
    true_overall = (
        config.injected_true_effect
        if config.injected_true_effect is not None
        else 0.0
    )
    n_studies = (
        config.N_studies if config.N_studies is not None else len(base_effects)
    )

    studies: List[Dict[str, Any]] = []
    for i in range(n_studies):
        base_eff = base_effects[i]
        base_se = base_ses[i]
        # Inject heterogeneity per study.
        true_eff = base_eff + rng.normal(0.0, math.sqrt(tau2)) if tau2 > 0 else base_eff
        study_dict = {
            "study_id": f"s{i}",
            "effect_size": base_eff,
            "standard_error": base_se,
            "true_effect": true_eff,
            "n": 1,  # dummy study size – the schema only requires an integer
        }
        studies.append(study_dict)

    # The replicate id will be filled by the caller; we use a placeholder here.
    result = SimulationResult(
        replicate_id=0,
        injected_tau2=tau2,
        true_effect=true_overall,
        studies=studies,
    )
    return result


def validate_simulation_output(results: List[SimulationResult]) -> bool:
    """
    Light‑weight sanity check used by the unit tests.

    Returns ``True`` if every result contains a non‑empty ``studies``
    list and each study has a ``true_effect`` entry.
    """
    if not isinstance(results, list):
        raise AssertionError("Expected a list of SimulationResult objects")
    for res in results:
        if not isinstance(res, SimulationResult):
            raise AssertionError("List element is not a SimulationResult")
        if not res.studies:
            raise AssertionError("Replicate contains no studies")
        for study in res.studies:
            if "true_effect" not in study:
                raise AssertionError("Study record missing 'true_effect'")
    return True


# -------------------------------------------------------------------------
# Pipeline‑oriented generator (used by ``code/main.py``)
# -------------------------------------------------------------------------

def _load_base_data(csv_path: Path) -> List[Dict[str, Any]]:
    """
    Load the deterministic base CSV used by the full pipeline.

    Expected columns: ``study_id,effect,se,n``.
    Returns a list of dictionaries, one per study.
    """
    studies = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"study_id", "effect", "se", "n"}
        if not required.issubset(reader.fieldnames or []):
            missing = required - set(reader.fieldnames or [])
            raise ValueError(
                f"Base CSV missing required columns: {missing}"
            )
        for row in reader:
            studies.append(
                {
                    "study_id": row["study_id"],
                    "effect": float(row["effect"]),
                    "se": float(row["se"]),
                    "n": int(row["n"]),
                }
            )
    return studies


def generate_synthetic_meta_analysis(config: SimulationConfig) -> SimpleNamespace:
    """
    Backwards‑compatible generator used by ``code/main.py``.

    It produces a namespace with a ``replicates`` attribute where each
    replicate is a ``SimpleNamespace`` containing ``replicate_id``,
    ``tau2`` and a list of per‑study dictionaries (including the injected
    ``true_effect``).
    """
    if config.base_data_path is None or not config.base_data_path.is_file():
        raise FileNotFoundError(
            f"Base data file not found: {config.base_data_path}"
        )
    random.seed(config.seed)
    base_studies = _load_base_data(config.base_data_path)

    replicates = []
    for rep_idx in range(config.num_replicates or 0):
        rep_studies = []
        for base in base_studies:
            true_effect = (
                base["effect"]
                + random.gauss(0.0, math.sqrt(config.tau2 or 0.0))
            )
            study_record = {
                "study_id": base["study_id"],
                "effect": base["effect"],          # point estimate (unchanged)
                "se": base["se"],
                "n": base["n"],
                "true_effect": true_effect,
            }
            rep_studies.append(study_record)

        replicate = SimpleNamespace(
            replicate_id=rep_idx,
            tau2=config.tau2,
            studies=rep_studies,
        )
        replicates.append(replicate)

    return SimpleNamespace(
        config=config,
        replicates=replicates,
    )


# -------------------------------------------------------------------------
# CLI entry point – matches the quick‑start run‑book
# -------------------------------------------------------------------------

def _parse_tau_list(arg: str) -> List[float]:
    """Parse a comma‑separated list of floats."""
    return [float(x) for x in arg.split(",") if x.strip()]

def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate synthetic meta‑analysis datasets."
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
        help="Number of replicates per τ² level.",
    )
    parser.add_argument(
        "--sweep-type",
        choices=["primary", "sensitivity"],
        required=True,
        help="Label for the sweep (used in the output schema).",
    )
    parser.add_argument(
        "--out",
        type=str,
        required=True,
        help="Path to the JSON‑lines output file.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    parser.add_argument(
        "--base-csv",
        type=str,
        default=str(
            Path("data") / "processed" / "base_template.csv"
        ),
        help="Path to the deterministic base CSV.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    tau_values = _parse_tau_list(args.tau_squared)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Load base data once.
    base_effects, base_ses = load_base_data_structure(args.base_csv)

    # Global replicate counter to ensure unique IDs across τ² levels.
    global_rep_id = 0

    with out_path.open("w", encoding="utf-8") as out_f:
        for tau in tau_values:
            # Build a config compatible with the unit‑test API.
            cfg = SimulationConfig(
                injected_true_effect=0.5,
                injected_tau2=tau,
                N_studies=len(base_effects),
                base_data_path=args.base_csv,
                seed=args.seed,
                sweep_type=args.sweep_type,
            )
            rng = np.random.default_rng(args.seed)
            for _ in range(args.replicates):
                result = create_replicate(
                    cfg, base_effects, base_ses, rng
                )
                # Assign a unique replicate ID.
                result.replicate_id = global_rep_id
                global_rep_id += 1

                # Build a dict that matches the contract.
                record = {
                    "replicate_id": result.replicate_id,
                    "tau_squared": tau,
                    "true_effect": cfg.injected_true_effect,
                    "study_effects": [
                        s["true_effect"] for s in result.studies
                    ],
                    "study_se": [
                        s["standard_error"] for s in result.studies
                    ],
                    "study_sizes": [s["n"] for s in result.studies],
                    "k": len(result.studies),
                    "sweep_type": cfg.sweep_type,
                }
                out_f.write(json.dumps(record) + "\n")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
