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
from typing import List, Dict, Any, Iterable

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

    The class is deliberately permissive – it contains the fields required
    by the unit tests (``injected_true_effect``, ``injected_tau2``,
    ``N_studies``) as well as the fields used by the pipeline
    (``tau2``, ``num_replicates``).  Unused fields may be left at their
    default values.
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

    Attributes
    ----------
    replicate_id : int
        Identifier for the replicate (0‑based).
    injected_true_effect : float
        Ground‑truth overall effect size used to generate the data.
    injected_tau2 : float
        Ground‑truth between‑study variance.
    N_studies : int
        Number of studies in this replicate.
    studies : List[Dict[str, Any]]
        List of per‑study dictionaries.  Each dictionary contains at least
        ``study_id``, ``true_effect``, ``effect_size``,
        ``standard_error`` and ``variance``.
    mean_effect : float
        Mean of the latent true effects across studies.
    observed_between_study_variance : float
        Sample variance of the latent true effects (method‑of‑moments
        estimator of τ²).
    """
    replicate_id: int
    injected_true_effect: float
    injected_tau2: float
    N_studies: int
    studies: List[Dict[str, Any]] = field(default_factory=list)
    mean_effect: float = 0.0
    observed_between_study_variance: float = 0.0


# ----------------------------------------------------------------------
# Helper functions used by the unit tests
# ----------------------------------------------------------------------
def _load_number_of_studies(base_path: Path) -> int:
    """
    Reads the base CSV and returns the number of study rows (excluding the header).

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If the file cannot be parsed or contains no study rows.
    """
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
    """
    Load a base CSV file and return two parallel lists:
    * ``effects`` – the effect size column (if present, otherwise zeros)
    * ``ses`` – the standard error column.

    The function expects a header row containing at least the column
    ``standard_error`` (or ``se``).  If an ``effect``/``effect_size`` column
    is present its values are returned; otherwise a list of zeros is
    returned.

    Parameters
    ----------
    base_path : str or Path
        Path to the CSV file.

    Returns
    -------
    tuple(list[float], list[float])
        (effects, standard_errors)

    Raises
    ------
    FileNotFoundError
        If the file cannot be found.
    ValueError
        If the CSV cannot be parsed.
    """
    path = Path(base_path)
    if not path.is_file():
        raise FileNotFoundError(f"Base data file not found: {path}")

    effects: list[float] = []
    ses: list[float] = []

    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        # Normalise column names to lower case for flexibility.
        fieldnames = {name.lower(): name for name in reader.fieldnames or []}
        effect_key = fieldnames.get("effect") or fieldnames.get("effect_size") or None
        se_key = fieldnames.get("standard_error") or fieldnames.get("se") or None

        if se_key is None:
            raise ValueError("CSV must contain a standard error column")

        for row in reader:
            # Effect may be missing – default to 0.0.
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
    """
    Generate a simulated observed effect size and its variance.

    The observed effect is drawn from a Normal distribution centred on the
    true effect with standard deviation ``sqrt(tau2 + base_se**2)``.
    The returned variance is the sum of the measurement variance
    (``base_se**2``) and the injected between‑study variance ``tau2``.
    This matches the expectations of the unit tests.

    Parameters
    ----------
    tau2 : float
        Injected between‑study variance.
    base_se : float
        Standard error of the study (measurement error).
    true_effect : float
        Latent true effect for this study.
    _unused : float
        Placeholder to keep the signature compatible with the historic
        implementation; ignored.
    rng : np.random.Generator
        Random number generator.

    Returns
    -------
    tuple[float, float]
        (observed_effect, observed_variance)
    """
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
    """
    Build a single replicate according to ``config``.

    The function uses ``config.injected_true_effect`` as the grand mean,
    ``config.injected_tau2`` as the between‑study variance, and
    ``config.N_studies`` as the number of studies.  The ``base_effects``
    and ``base_ses`` arguments provide the measurement‑error structure;
    only the standard errors are required for the test suite.

    Returns
    -------
    SimulationResult
        Dataclass containing all generated information.
    """
    n = config.N_studies
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
        # Use the historic helper to obtain the observed effect and variance.
        obs_effect, obs_variance = calculate_effect_and_variance(
            config.injected_tau2, se, true_effects[i], config.injected_true_effect, rng
        )
        study_dict = {
            "study_id": f"study_{i}",
            "true_effect": float(true_effects[i]),
            "effect_size": float(obs_effect),
            "standard_error": float(se),
            "variance": float(obs_variance),
        }
        studies.append(study_dict)

    mean_effect = float(np.mean(true_effects))
    # Sample variance (ddof=1) provides an unbiased estimator of τ².
    observed_between = (
        float(np.var(true_effects, ddof=1)) if n > 1 else 0.0
    )

    return SimulationResult(
        replicate_id=0,  # will be overwritten by the caller if needed
        injected_true_effect=config.injected_true_effect,
        injected_tau2=config.injected_tau2,
        N_studies=n,
        studies=studies,
        mean_effect=mean_effect,
        observed_between_study_variance=observed_between,
    )


def validate_simulation_output(results: Iterable[SimulationResult]) -> bool:
    """
    Validate that each ``SimulationResult`` in ``results`` conforms to the
    minimal schema required by the unit tests.

    The function raises ``AssertionError`` if any check fails and returns
    ``True`` otherwise.

    Parameters
    ----------
    results : iterable of SimulationResult
        The results to validate.

    Returns
    -------
    bool
        ``True`` if all checks pass.
    """
    for res in results:
        assert isinstance(res, SimulationResult), "Result must be a SimulationResult"
        assert isinstance(res.studies, list), "'studies' must be a list"
        for study in res.studies:
            assert isinstance(study, dict), "Each study must be a dict"
            assert "true_effect" in study, "Missing 'true_effect' in study dict"
            te = study["true_effect"]
            assert isinstance(te, (int, float)), "'true_effect' must be numeric"
            assert math.isfinite(te), "'true_effect' must be finite"
    return True


# ----------------------------------------------------------------------
# High‑level generator used by the pipeline (kept for backward compatibility)
# ----------------------------------------------------------------------
def generate_synthetic_meta_analysis(
    config: SimulationConfig,
) -> SimpleNamespace:
    """
    Generate ``config.num_replicates`` synthetic meta‑analysis datasets.

    This function mirrors the historic API used by ``code/main.py``.  It
    returns a ``SimpleNamespace`` with a ``replicates`` attribute, where
    each element is a ``SimpleNamespace`` exposing a ``studies`` list.
    The inner dictionaries contain the keys required by downstream code.
    """
    # Resolve number of studies from the base CSV if not supplied.
    n_studies = config.effective_n_studies()
    rng = np.random.default_rng(config.seed)

    replicates: List[SimpleNamespace] = []

    sigma = math.sqrt(config.effective_tau2()) if config.effective_tau2() > 0 else 0.0

    for rep_idx in range(config.num_replicates or 0):
        studies: List[Dict[str, Any]] = []
        true_effects = rng.normal(loc=0.0, scale=sigma, size=n_studies)
        for study_idx, te in enumerate(true_effects):
            studies.append(
                {
                    "study_id": f"study_{rep_idx}_{study_idx}",
                    "true_effect": float(te),
                    # Compatibility placeholders for downstream code.
                    "effect": float(te),
                    "se": 0.1,
                    "n": 30,
                }
            )
        replicates.append(SimpleNamespace(studies=studies))

    return SimpleNamespace(replicates=replicates)


# ----------------------------------------------------------------------
# JSON‑Lines writer used by the CLI
# ----------------------------------------------------------------------
def write_simulation_results(
    results: Iterable[SimulationResult],
    output_path: Path | None = None,
) -> Path:
    """
    Write a sequence of ``SimulationResult`` objects to a JSON‑Lines file.

    The output format matches the ``SimulatedDataset`` contract used in the
    rest of the project.  Each line represents a single replicate and
    contains the replicate ID, the injected heterogeneity level, the true
    overall effect, the number of studies, and the list of per‑study
    dictionaries.

    Parameters
    ----------
    results : iterable of SimulationResult
        Replicates to write.
    output_path : Path, optional
        Destination path.  If omitted the default location
        ``data/results/simulation_raw.jsonl`` is used.

    Returns
    -------
    Path
        Path to the written file.
    """
    if output_path is None:
        output_path = paths.results("simulation_raw.jsonl")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        for res in results:
            record: Dict[str, Any] = {
                "replicate_id": res.replicate_id,
                "tau_squared": res.injected_tau2,
                "injected_true_effect": res.injected_true_effect,
                "N_studies": res.N_studies,
                "studies": res.studies,
            }
            json.dump(record, f)
            f.write("\n")
    log.info(f"Written {len(list(results))} simulated replicates to {output_path}")
    return output_path


# ----------------------------------------------------------------------
# Command‑line interface
# ----------------------------------------------------------------------
def _parse_cli_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate synthetic meta‑analysis replicates."
    )
    parser.add_argument(
        "--tau-squared",
        type=float,
        required=True,
        help="Injected between‑study variance (τ²) for all replicates.",
    )
    parser.add_argument(
        "--replicates",
        type=int,
        required=True,
        help="Number of replicates to generate.",
    )
    parser.add_argument(
        "--base-data",
        type=str,
        default=str(paths.data("processed", "base_template.csv")),
        help="Path to a CSV file defining the study count and SE structure.",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=str(paths.results("simulation_raw.jsonl")),
        help="Output JSON‑Lines file.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = _parse_cli_args(argv)

    # Build a minimal configuration for the low‑level API.
    cfg = SimulationConfig(
        injected_true_effect=0.0,   # ground‑truth overall effect (zero for simplicity)
        injected_tau2=args.tau_squared,
        N_studies=_load_number_of_studies(Path(args.base_data)),
        base_data_path=args.base_data,
        seed=args.seed,
    )

    # Load the base SE structure (the actual effect column is not needed).
    _, base_ses = load_base_data_structure(args.base_data)

    rng = np.random.default_rng(args.seed)

    results: List[SimulationResult] = []
    for rep_id in range(args.replicates):
        # Use a fresh RNG for each replicate to guarantee deterministic
        # seeding across replicates (seed + rep_id).
        rep_rng = np.random.default_rng(args.seed + rep_id)
        res = create_replicate(cfg, [], base_ses, rep_rng)
        # Overwrite the automatically set replicate_id (0) with the true ID.
        object.__setattr__(res, "replicate_id", rep_id)
        results.append(res)

    write_simulation_results(results, Path(args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())