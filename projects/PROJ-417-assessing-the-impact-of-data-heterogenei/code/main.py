"""
Main entry point for the meta-analysis heterogeneity impact pipeline.

Orchestrates:
1. Base data resolution (real Cochrane data if present, otherwise the
   verified synthetic base documented in T001 / Jackson et al., 2010)
2. Simulation generation with controlled heterogeneity (tau^2)
3. Estimation (Fixed Effects, DerSimonian-Laird, REML)
4. Metric calculation (bias, 95% CI coverage, Q, I^2)
5. Output of data/results/estimation_results.csv (T005 schema) and
   data/results/reml_failures.json

Usage:
    python code/main.py --mode full --seed 42
    python code/main.py --mode dry-run --seed 42
    python code/main.py --validate-contracts
"""
import argparse
import csv
import importlib.util
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Make sibling packages importable both as a script and as a module.
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
for p in (str(SCRIPT_DIR), str(PROJECT_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from simulation.generator import (
    SimulationConfig,
    generate_synthetic_meta_analysis,
    validate_simulation_output,
)
from simulation.estimators import apply_estimator
from analysis.metrics import calculate_bias, calculate_coverage

logger = logging.getLogger("main")

# Constants
DEFAULT_LEVELS = [0.0, 0.1, 0.5, 1.0, 2.0]
DEFAULT_REPLICATES = 500
DEFAULT_SEED = 42
DRY_RUN_LEVELS = [0.0, 0.1]
DRY_RUN_REPLICATES = 10
OUTPUT_DIR = "data/results"
RAW_DATA_DIR = "data/raw"
SIMULATION_OUTPUT = "simulation_raw.json"
ESTIMATION_OUTPUT = "estimation_results.csv"
REML_FAILURE_LOG = "reml_failures.json"
RUN_SUMMARY_OUTPUT = "run_summary.json"

# Estimator identifiers: (argument name for apply_estimator, schema name)
ESTIMATORS = [
    ("fixed_effects", "FixedEffects"),
    ("dersimonian_laird", "DerSimonianLaird"),
    ("reml", "REML"),
]

# T005 / data-model.md EstimationResult schema
FIELDNAMES = [
    "replicate_id",
    "tau_squared",
    "sweep_type",
    "estimator_type",
    "n_studies",
    "pooled_effect",
    "ci_lower",
    "ci_upper",
    "tau_squared_est",
    "i_squared",
    "q_statistic",
    "bias",
    "coverage_flag",
    "convergence_warning",
    "reliability_flag",
    "injected_true_effect",
]

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Orchestrate the meta-analysis heterogeneity impact pipeline."
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="full",
        choices=["full", "dry-run"],
        help="'full' = 5 levels x 500 replicates; 'dry-run' = 2 levels x 10 replicates (T005 trial)",
    )
    parser.add_argument(
        "--seed", type=int, default=DEFAULT_SEED,
        help=f"Random seed for reproducibility (default: {DEFAULT_SEED})",
    )
    parser.add_argument(
        "--levels", type=float, nargs="+", default=None,
        help=f"Heterogeneity levels (tau^2) to simulate (default: {DEFAULT_LEVELS})",
    )
    parser.add_argument(
        "--replicates", type=int, default=None,
        help=f"Number of replicates per level (default: {DEFAULT_REPLICATES})",
    )
    parser.add_argument(
        "--base-data", type=str, default=None,
        help="Base dataset filename in data/raw/ (default: auto-resolved)",
    )
    parser.add_argument(
        "--skip-generation", action="store_true",
        help="Skip simulation generation if output exists",
    )
    parser.add_argument(
        "--validate-contracts", action="store_true",
        help="Validate data/results/estimation_results.csv against the T005 schema and exit",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    return parser.parse_args()

def setup_logging(verbose: bool = False) -> None:
    """Configure logging; use the project utility when available."""
    level = logging.DEBUG if verbose else logging.INFO
    try:
        from utils.logging import setup_logging as _setup
        _setup(level=level, log_file=Path(OUTPUT_DIR) / "pipeline.log")
    except Exception:
        # Fall back to standard logging if the utility signature differs.
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(Path(OUTPUT_DIR) / "pipeline.log"),
            ],
        )

def ensure_directories() -> None:
    """Ensure output directories exist."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(RAW_DATA_DIR, exist_ok=True)

def ensure_base_data() -> str:
    """
    Resolve the base dataset filename inside data/raw/.

    Priority:
    1. data/raw/cochrane_base.csv (real fetched Cochrane data)
    2. data/raw/cochrane_base_synthetic.csv (the verified synthetic base
       documented in T001: mu=0.0, sigma=1.0, N=20, Jackson et al. 2010)
    3. If neither exists, generate the verified synthetic base via
       code/scripts/generate_synthetic_base.py (the documented T001
       fallback path) so a fresh environment is reproducible.

    Returns:
        Filename (not full path) of the base dataset.
    """
    raw = Path(RAW_DATA_DIR)
    real = raw / "cochrane_base.csv"
    synth = raw / "cochrane_base_synthetic.csv"

    if real.exists():
        logger.info("Using real Cochrane base data: %s", real)
        return real.name
    if synth.exists():
        logger.info(
            "Real Cochrane data absent; using verified synthetic base "
            "(Jackson et al., 2010; mu=0.0, sigma=1.0, N=20): %s",
            synth,
        )
        return synth.name

    # Generate the documented verified synthetic base (T001 fallback).
    gen_path = SCRIPT_DIR / "scripts" / "generate_synthetic_base.py"
    if not gen_path.exists():
        raise FileNotFoundError(
            "REAL_DATA_FETCH_FAILED: no base data in data/raw/ and "
            f"generator script missing at {gen_path}. "
            "Run code/scripts/fetch_cochrane.py (real fetch) or "
            "code/scripts/generate_synthetic_base.py (verified fallback)."
        )
    logger.info("Generating verified synthetic base data (T001 fallback)...")
    spec = importlib.util.spec_from_file_location("gen_synth_base", gen_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    data = module.generate_synthetic_base_data()
    module.save_to_csv(data, synth)
    logger.info("Verified synthetic base written to %s", synth)
    return synth.name

def run_simulation(args: argparse.Namespace) -> Path:
    """Run the simulation generation phase and save simulation_raw.json."""
    levels = args.levels
    replicates = args.replicates
    if levels is None:
        levels = DRY_RUN_LEVELS if args.mode == "dry-run" else DEFAULT_LEVELS
    if replicates is None:
        replicates = DRY_RUN_REPLICATES if args.mode == "dry-run" else DEFAULT_REPLICATES

    logger.info(
        "Starting simulation: mode=%s seed=%s levels=%s replicates=%s",
        args.mode, args.seed, levels, replicates,
    )

    output_path = Path(OUTPUT_DIR) / SIMULATION_OUTPUT
    if args.skip_generation and output_path.exists():
        logger.info("Skipping generation. Output exists at %s", output_path)
        return output_path

    base_file = args.base_data or ensure_base_data()

    config = SimulationConfig(
        seed=args.seed,
        tau2_levels=levels,
        replicates_per_level=replicates,
        base_data_file=base_file,
        base_data_dir=RAW_DATA_DIR,
    )

    simulation_result = generate_synthetic_meta_analysis(config)

    if not validate_simulation_output(simulation_result):
        raise RuntimeError("Simulation output validation failed.")

    with open(output_path, "w") as f:
        json.dump(simulation_result.to_dict(), f, indent=2)

    logger.info("Simulation complete. Output saved to %s", output_path)
    return output_path

def _first_attr(obj: Any, *names: str, default: Any = None) -> Any:
    """Return the first non-None attribute among the given candidate names."""
    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)
            if value is not None:
                return value
    return default

def _extract_studies(replicate: Dict[str, Any]) -> Tuple[List[float], List[float]]:
    """
    Extract (effect_sizes, variances) from a simulation replicate record.

    Supports both the dict-of-studies layout ("studies": [{effect_size,
    variance}, ...]) and the parallel-lists layout ("study_effects" /
    "study_se").
    """
    studies = replicate.get("studies")
    if studies:
        effects = [float(s["effect_size"]) for s in studies]
        variances = [float(s["variance"]) for s in studies]
        return effects, variances

    effects = replicate.get("study_effects")
    ses = replicate.get("study_se")
    if effects and ses:
        return [float(e) for e in effects], [float(se) ** 2 for se in ses]

    raise KeyError(
        "Replicate record has no study-level data (expected 'studies' "
        "or 'study_effects'/'study_se')."
    )

def compute_q_and_i_squared(
    effects: List[float], variances: List[float]
) -> Tuple[float, float]:
    """
    Compute Cochran's Q and I^2 from study-level effects and variances.

    Q = sum(w_i * (y_i - mu)^2) with w_i = 1/v_i and mu the
    fixed-effect pooled estimate; I^2 = max(0, (Q - df)/Q) * 100.
    """
    weights = [1.0 / v for v in variances]
    sum_w = sum(weights)
    mu = sum(w * y for w, y in zip(weights, effects)) / sum_w
    q = sum(w * (y - mu) ** 2 for w, y in zip(weights, effects))
    df = len(effects) - 1
    i2 = max(0.0, (q - df) / q) * 100.0 if q > 0 else 0.0
    return q, i2

def run_estimation(simulation_data: Dict[str, Any], sweep_type: str = "primary") -> List[Dict[str, Any]]:
    """Run estimation phase on simulated data; returns T005-schema rows."""
    logger.info("Starting estimation phase...")
    results: List[Dict[str, Any]] = []
    replicates = simulation_data.get("replicates", [])
    if not replicates:
        raise ValueError("Simulation output contains no replicates.")

    for i, replicate in enumerate(replicates):
        if i % 100 == 0:
            logger.info("Processing replicate %d/%d", i, len(replicates))

        effects, variances = _extract_studies(replicate)
        n_studies = len(effects)
        if n_studies == 0:
            logger.warning("Replicate %d has no studies, skipping.", i)
            continue

        # Ground truth (FR-003): read strictly from injected_true_effect.
        if "injected_true_effect" not in replicate:
            raise KeyError(
                "Replicate record is missing the mandatory "
                "'injected_true_effect' column (FR-003)."
            )
        true_effect = float(replicate["injected_true_effect"])
        injected_tau2 = replicate.get("injected_tau2")
        if injected_tau2 is None:
            injected_tau2 = replicate.get("tau_squared")
        if injected_tau2 is None:
            raise KeyError(
                "Replicate record is missing 'injected_tau2'/'tau_squared'."
            )
        injected_tau2 = float(injected_tau2)

        # Heterogeneity statistics (Constitution Principle VII): always
        # computed so Q and I^2 are non-null for every replicate.
        q_stat, i_squared = compute_q_and_i_squared(effects, variances)

        reliability_flag = "unreliable" if n_studies < 5 else "reliable"
        replicate_id = replicate.get("id", i)

        for est_arg, est_type in ESTIMATORS:
            try:
                est = apply_estimator(effects, variances, estimator=est_arg)
            except Exception as exc:
                logger.error(
                    "Estimation failed for replicate %s, estimator %s: %s",
                    replicate_id, est_type, exc,
                )
                continue

            pooled = _first_attr(est, "pooled_estimate", "pooled_effect", "estimate")
            lower = _first_attr(est, "lower_ci", "ci_lower")
            upper = _first_attr(est, "upper_ci", "ci_upper")
            if pooled is None or lower is None or upper is None:
                raise AttributeError(
                    f"EstimationResult for {est_type} is missing pooled "
                    "effect or CI bound attributes."
                )

            tau2_est = _first_attr(est, "tau2_estimate", "tau_squared_estimate", "tau_squared", default=0.0)

            # convergence_warning: True if REML failed to converge.
            warning = _first_attr(est, "convergence_warning")
            success = _first_attr(est, "convergence_success")
            if warning is None and success is not None:
                warning = not bool(success)
            elif warning is None:
                warning = False

            bias = calculate_bias(float(pooled), true_effect)
            coverage = calculate_coverage(float(lower), float(upper), true_effect)

            results.append({
                "replicate_id": replicate_id,
                "tau_squared": injected_tau2,
                "sweep_type": sweep_type,
                "estimator_type": est_type,
                "n_studies": n_studies,
                "pooled_effect": float(pooled),
                "ci_lower": float(lower),
                "ci_upper": float(upper),
                "tau_squared_est": float(tau2_est),
                "i_squared": float(i_squared),
                "q_statistic": float(q_stat),
                "bias": float(bias),
                "coverage_flag": bool(coverage),
                "convergence_warning": bool(warning),
                "reliability_flag": reliability_flag,
                "injected_true_effect": true_effect,
            })

    logger.info("Estimation phase complete: %d result rows.", len(results))
    return results

def save_estimation_results(rows: List[Dict[str, Any]]) -> Path:
    """Write estimation results to the T005-schema CSV."""
    csv_path = Path(OUTPUT_DIR) / ESTIMATION_OUTPUT
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    logger.info("Estimation results saved to %s", csv_path)
    return csv_path

def ensure_reml_failure_log() -> Path:
    """
    Ensure data/results/reml_failures.json exists (FR-006 deliverable).

    simulation.estimators logs REML convergence failures to this file
    during estimation. If no failure occurred (or the estimator module
    did not create the file), an explicit zero-failure record is written
    so the declared artifact always exists.
    """
    path = Path(OUTPUT_DIR) / REML_FAILURE_LOG
    if not path.exists():
        record = {
            "failure_count": 0,
            "events": [],
            "note": "No REML convergence failures recorded during this run.",
        }
        with open(path, "w") as f:
            json.dump(record, f, indent=2)
        logger.info("Initialized REML failure log at %s (0 failures).", path)
    else:
        logger.info("REML failure log present at %s.", path)
    return path

def run_analysis(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Lightweight aggregation of the estimation rows (mean bias and
    coverage rate per tau^2 x estimator). The full statistical testing
    (binomial, Shapiro-Wilk, Kruskal-Wallis, Bonferroni) is T007.
    """
    groups: Dict[Tuple[float, str], List[Dict[str, Any]]] = {}
    for r in rows:
        groups.setdefault((r["tau_squared"], r["estimator_type"]), []).append(r)

    summary = []
    for (tau2, est_type), group in sorted(groups.items()):
        n = len(group)
        mean_bias = sum(g["bias"] for g in group) / n
        coverage_rate = sum(1 for g in group if g["coverage_flag"]) / n
        n_warnings = sum(1 for g in group if g["convergence_warning"])
        summary.append({
            "tau_squared": tau2,
            "estimator_type": est_type,
            "n_replicates": n,
            "mean_bias": mean_bias,
            "coverage_rate": coverage_rate,
            "reml_convergence_warnings": n_warnings,
        })
        logger.info(
            "tau^2=%s %s: n=%d mean_bias=%.4f coverage=%.3f warnings=%d",
            tau2, est_type, n, mean_bias, coverage_rate, n_warnings,
        )

    out = {"groups": summary, "total_rows": len(rows)}
    with open(Path(OUTPUT_DIR) / RUN_SUMMARY_OUTPUT, "w") as f:
        json.dump(out, f, indent=2)
    return out

def validate_contracts() -> int:
    """
    Validate data/results/estimation_results.csv against the T005 schema:
    required columns present and pooled_effect, i_squared, q_statistic
    non-null for every replicate.
    """
    csv_path = Path(OUTPUT_DIR) / ESTIMATION_OUTPUT
    if not csv_path.exists():
        print(f"FAIL: {csv_path} does not exist. Run the pipeline first.")
        return 1

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    required = [
        "pooled_effect", "ci_lower", "ci_upper", "estimator_type",
        "sweep_type", "convergence_warning", "i_squared", "q_statistic",
    ]
    missing_cols = [c for c in required if c not in fieldnames]
    if missing_cols:
        print(f"FAIL: missing required columns: {missing_cols}")
        return 1
    if not rows:
        print("FAIL: estimation_results.csv contains no data rows.")
        return 1

    bad = []
    for i, row in enumerate(rows):
        for col in ("pooled_effect", "i_squared", "q_statistic"):
            val = row.get(col)
            if val is None or str(val).strip() == "":
                bad.append((i, col))
    if bad:
        print(f"FAIL: null values found in required columns: {bad[:10]}")
        return 1

    print(
        f"PASS: {csv_path} validated: {len(rows)} rows, all required "
        "columns present, pooled_effect / i_squared / q_statistic non-null."
    )
    return 0

def main() -> int:
    """Main orchestration function."""
    args = parse_args()

    if args.validate_contracts:
        return validate_contracts()

    ensure_directories()
    setup_logging(verbose=args.verbose)

    logger.info("Starting meta-analysis heterogeneity pipeline (mode=%s)...", args.mode)

    try:
        # 1. Simulation generation
        sim_path = run_simulation(args)

        # 2. Load simulation data
        with open(sim_path, "r") as f:
            simulation_data = json.load(f)

        # 3. Estimation (T005: dry-run = 2 levels x 10 replicates)
        sweep_type = "primary"
        estimation_rows = run_estimation(simulation_data, sweep_type=sweep_type)
        if not estimation_rows:
            raise RuntimeError("Estimation produced no results.")

        # 4. Save T005-schema CSV
        save_estimation_results(estimation_rows)

        # 5. Ensure the REML failure log artifact exists (FR-006)
        ensure_reml_failure_log()

        # 6. Lightweight aggregation summary
        run_analysis(estimation_rows)

        logger.info("Pipeline completed successfully.")
        return 0

    except Exception as e:
        logger.error("Pipeline failed with error: %s", e, exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
