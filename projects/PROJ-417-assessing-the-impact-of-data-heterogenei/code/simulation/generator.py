import json
import math
import os
import csv
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
import argparse

# Project utilities
from utils.logging import get_logger
from config_loader import (
    load_config,
    get_simulation_params,
    get_base_data_path,
    get_random_seed,
)
from llmxive_toolkit import paths

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Data classes
# ----------------------------------------------------------------------
@dataclass
class SimulationConfig:
    """Configuration for a single τ² simulation run."""
    injected_true_effect: float
    injected_tau2: float
    N_studies: int
    base_data_path: str
    seed: int

@dataclass
class StudyResult:
    """Result for a single synthetic study."""
    study_id: int
    effect_size: float
    standard_error: float
    variance: float
    # Flag used for quick homogeneity checks
    is_homogeneous: bool = False

@dataclass
class SimulationResult:
    """Aggregated result for one replicate."""
    replicate_id: int
    injected_true_effect: float
    injected_tau2: float
    N_studies: int
    studies: List[Dict[str, Any]]
    observed_between_study_variance: float = 0.0
    mean_effect: float = 0.0

# ----------------------------------------------------------------------
# Core helper functions
# ----------------------------------------------------------------------
def load_base_data_structure(base_data_path: str) -> Tuple[List[float], List[float]]:
    """
    Load effect sizes and standard errors from a CSV base file.

    Parameters
    ----------
    base_data_path: str
        Path to the CSV containing ``effect_size`` (or ``effect``) and
        ``standard_error`` (or ``se``) columns.

    Returns
    -------
    Tuple[List[float], List[float]]
        Two parallel lists: effects and standard errors.
    """
    effects: List[float] = []
    ses: List[float] = []

    if not os.path.exists(base_data_path):
        logger.error(f"Base data file not found: {base_data_path}")
        raise FileNotFoundError(f"Base data file not found: {base_data_path}")

    with open(base_data_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Accept either the canonical names or the short aliases
            eff_key = "effect_size" if "effect_size" in row else "effect"
            se_key = "standard_error" if "standard_error" in row else "se"

            try:
                effects.append(float(row[eff_key]))
                ses.append(float(row[se_key]))
            except (ValueError, KeyError) as e:
                logger.warning(
                    f"Skipping invalid row in base data: {row}, error: {e}"
                )
                continue

    if len(effects) == 0:
        raise ValueError(
            "Base data file is empty or contains no valid rows."
        )

    logger.info(f"Loaded {len(effects)} studies from base data.")
    return effects, ses

def calculate_effect_and_variance(
    base_effect: float,
    base_se: float,
    true_effect: float,
    tau2: float,
    rng: np.random.Generator,
) -> Tuple[float, float]:
    """
    Generate a synthetic effect size for a single study.

    The model is:
        y_i = μ + u_i + ε_i
    where
        u_i ~ N(0, τ²)        (heterogeneity)
        ε_i ~ N(0, σ_i²)      (sampling error)

    Parameters
    ----------
    base_effect: float
        Ignored – kept for API compatibility.
    base_se: float
        Standard error for the study (σ_i).
    true_effect: float
        The injected overall true effect (μ).
    tau2: float
        Between‑study variance (τ²).
    rng: np.random.Generator
        Random generator for reproducibility.

    Returns
    -------
    Tuple[float, float]
        Simulated effect size and its variance (σ_i²).
    """
    # Heterogeneity component
    if tau2 == 0.0:
        heterogeneity_component = 0.0
    else:
        heterogeneity_component = rng.normal(0.0, math.sqrt(tau2))

    # Sampling error component
    sampling_error = rng.normal(0.0, base_se)

    simulated_effect = true_effect + heterogeneity_component + sampling_error
    simulated_variance = base_se ** 2

    return simulated_effect, simulated_variance

def create_replicate(
    config: SimulationConfig,
    base_effects: List[float],
    base_ses: List[float],
    rng: np.random.Generator,
) -> SimulationResult:
    """
    Produce a single synthetic meta‑analysis replicate.

    Parameters
    ----------
    config: SimulationConfig
        All parameters required for the simulation.
    base_effects: List[float]
        Unused – retained for API compatibility.
    base_ses: List[float]
        Standard errors from the base dataset.
    rng: np.random.Generator
        Random generator seeded per replicate.

    Returns
    -------
    SimulationResult
        Fully populated result for the replicate.
    """
    studies: List[Dict[str, Any]] = []
    N = config.N_studies

    # Choose N standard errors from the base distribution (with wrap‑around)
    if len(base_ses) >= N:
        selected_ses = base_ses[:N]
    else:
        repeats = math.ceil(N / len(base_ses))
        selected_ses = (base_ses * repeats)[:N]

    for i in range(N):
        se = selected_ses[i]
        effect, var = calculate_effect_and_variance(
            0.0,
            se,
            config.injected_true_effect,
            config.injected_tau2,
            rng,
        )
        is_homogeneous = config.injected_tau2 == 0.0

        study = StudyResult(
            study_id=i,
            effect_size=effect,
            standard_error=se,
            variance=var,
            is_homogeneous=is_homogeneous,
        )
        studies.append(asdict(study))

    # Method‑of‑moments estimate of τ²
    if N > 1:
        effects_arr = np.array([s["effect_size"] for s in studies])
        total_var = np.var(effects_arr, ddof=1)
        avg_var = np.mean([s["variance"] for s in studies])
        tau2_obs = max(0.0, total_var - avg_var)
        mean_eff = float(np.mean(effects_arr))
    else:
        tau2_obs = 0.0
        mean_eff = studies[0]["effect_size"] if studies else 0.0

    return SimulationResult(
        replicate_id=0,  # will be overwritten by the caller
        injected_true_effect=config.injected_true_effect,
        injected_tau2=config.injected_tau2,
        N_studies=N,
        studies=studies,
        observed_between_study_variance=tau2_obs,
        mean_effect=mean_eff,
    )

def validate_simulation_output(results: List[SimulationResult]) -> bool:
    """
    Basic schema‑like validation of generated results.

    Returns True if the first result contains all required fields.
    """
    if not results:
        logger.error("Validation failed: No results to validate.")
        return False

    r = results[0]
    required_fields = [
        "injected_true_effect",
        "injected_tau2",
        "N_studies",
        "studies",
    ]
    for field in required_fields:
        if not hasattr(r, field):
            logger.error(f"Validation failed: Missing field {field} in result.")
            return False

    if r.studies:
        study = r.studies[0]
        study_fields = ["study_id", "effect_size", "standard_error", "variance"]
        for field in study_fields:
            if field not in study:
                logger.error(
                    f"Validation failed: Missing field {field} in study."
                )
                return False

    logger.info("Simulation output validation passed.")
    return True

def save_results_to_jsonl(results: List[SimulationResult], output_path: Path) -> None:
    """
    Write each SimulationResult as a single JSON line.

    Parameters
    ----------
    results: List[SimulationResult]
        Replicates to persist.
    output_path: Path
        Destination file (will be created/overwritten).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for r in results:
            record = asdict(r)
            # Ensure JSON serialisable scalars
            record["injected_true_effect"] = float(record["injected_true_effect"])
            record["injected_tau2"] = float(record["injected_tau2"])
            record["N_studies"] = int(record["N_studies"])
            record["replicate_id"] = int(record["replicate_id"])
            record["observed_between_study_variance"] = float(
                record["observed_between_study_variance"]
            )
            record["mean_effect"] = float(record["mean_effect"])
            json.dump(record, f)
            f.write("\n")
    logger.info(f"Saved {len(results)} records to {output_path}")

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def _build_config_from_cli(
    tau_squared: float, replicates: int, seed: int
) -> Tuple[SimulationConfig, int]:
    """
    Construct a SimulationConfig from explicit CLI arguments.

    Returns the config and the number of replicates.
    """
    # Load project‑wide parameters that are not overridden by CLI
    cfg = load_config()
    params = get_simulation_params(cfg)

    # The true effect size is optional in the config; default to 0.5
    true_effect = params.get("injected_true_effect", 0.5)

    base_path = str(get_base_data_path(cfg))
    n_studies = params.get("N_studies", 20)

    sim_cfg = SimulationConfig(
        injected_true_effect=true_effect,
        injected_tau2=tau_squared,
        N_studies=n_studies,
        base_data_path=base_path,
        seed=seed,
    )
    return sim_cfg, replicates

def main() -> int:
    """
    Command‑line interface.

    Supported usage:
        python -m simulation.generator --tau-squared 0.5 --replicates 900
    """
    parser = argparse.ArgumentParser(
        description="Generate synthetic meta‑analysis datasets."
    )
    parser.add_argument(
        "--tau-squared",
        type=float,
        required=False,
        help="Injected between‑study variance (τ²). If omitted, the full config is used.",
    )
    parser.add_argument(
        "--replicates",
        type=int,
        required=False,
        help="Number of replicates to generate. If omitted, the config value is used.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=get_random_seed(),
        help="Base random seed for deterministic per‑replicate seeding.",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Determine execution mode
    # ------------------------------------------------------------------
    if args.tau_squared is not None and args.replicates is not None:
        # CLI‑driven single‑τ² run
        sim_cfg, n_replicates = _build_config_from_cli(
            args.tau_squared, args.replicates, args.seed
        )
        logger.info(
            f"Generating {n_replicates} replicates for τ²={args.tau_squared}"
        )
        base_effects, base_ses = load_base_data_structure(sim_cfg.base_data_path)
        results: List[SimulationResult] = []
        for i in range(n_replicates):
            sub_rng = np.random.default_rng(sim_cfg.seed + i)
            result = create_replicate(sim_cfg, base_effects, base_ses, sub_rng)
            result.replicate_id = i
            results.append(result)

        output_path = paths.data("results", "simulation_raw.jsonl")
        save_results_to_jsonl(results, output_path)

        if not validate_simulation_output(results):
            raise ValueError("Generated simulation output failed validation.")
        return 0

    # ------------------------------------------------------------------
    # Fallback: use the full project configuration (previous behaviour)
    # ------------------------------------------------------------------
    cfg = load_config()
    params = get_simulation_params(cfg)
    tau2_levels = cfg.get("simulation_parameters", {}).get("tau2_levels", [0.0])
    base_path = str(get_base_data_path(cfg))
    seed = get_random_seed(cfg)

    output_dir = Path("data/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "simulation_raw.json"

    all_results: List[SimulationResult] = []

    for tau2 in tau2_levels:
        logger.info(f"Starting simulation for τ²={tau2}")

        sim_cfg = SimulationConfig(
            injected_true_effect=params.get("injected_true_effect", 0.5),
            injected_tau2=tau2,
            N_studies=params.get("N_studies", 20),
            base_data_path=base_path,
            seed=seed,
        )

        base_effects, base_ses = load_base_data_structure(sim_cfg.base_data_path)

        # Use the replicate count defined in the config (primary sweep by default)
        from config_loader import get_replicate_count

        n_replicates = get_replicate_count()
        results = []
        for i in range(n_replicates):
            sub_rng = np.random.default_rng(sim_cfg.seed + i)
            result = create_replicate(sim_cfg, base_effects, base_ses, sub_rng)
            result.replicate_id = i
            results.append(result)
        all_results.extend(results)
        logger.info(
            f"Completed τ²={tau2}: generated {len(results)} replicates."
        )

    if validate_simulation_output(all_results):
        # Preserve historic JSON array output for backward compatibility
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump([asdict(r) for r in all_results], f, indent=2)
        logger.info(f"Simulation pipeline completed successfully → {output_file}")
        return 0
    else:
        logger.error("Simulation pipeline failed validation.")
        raise ValueError("Simulation output validation failed.")

if __name__ == "__main__":
    raise SystemExit(main())