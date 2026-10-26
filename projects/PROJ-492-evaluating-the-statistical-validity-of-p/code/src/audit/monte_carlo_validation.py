"""
Monte‑Carlo validation module for statistical test correctness (FR‑026).

This module validates the statistical reconstruction logic by running Monte‑Carlo
simulations for:
  * two‑proportion Z‑test,
  * Fisher’s exact test,
  * Welch’s t‑test,
  * binomial test.

For each test it compares an empirical p‑value (estimated from 10 000 simulated
replicates) to the theoretical p‑value obtained from SciPy.  The absolute
difference must be ≤ 0.005 (SC‑003, SC‑026).  Results are written to
``output/monte_carlo_validation_report.json``.  If any test fails the script
logs an ``ERR‑801`` error and exits with a non‑zero status, aborting the pipeline.
"""

import sys
import time
from pathlib import Path
from typing import Any, Dict

import numpy as np
from scipy import stats

from code.src.config import SEED, set_rng_seed
from code.src.audit.monte_carlo_core import (
    set_seeds,
    simulate_z_test_statistic,
    simulate_fisher_exact_table,
    simulate_welch_t_statistic,
    simulate_binomial_statistic,
    compute_empirical_p_value,
    run_monte_carlo_validation_core,
)
from code.src.utils.logger import get_default_logger

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
NUM_REPLICATES = 10_000
TOLERANCE = 0.005
ALPHA = 0.05

log = get_default_logger(__name__)

# ----------------------------------------------------------------------
# Helper validation functions
# ----------------------------------------------------------------------
def _compare_and_log(
    test_name: str,
    empirical: float,
    theoretical: float,
) -> Dict[str, Any]:
    """Compare empirical vs. theoretical p‑value and return a result dict."""
    diff = abs(empirical - theoretical)
    passed = diff <= TOLERANCE
    if passed:
        log.info(
            f"{test_name} validation PASSED: diff={diff:.6f} ≤ {TOLERANCE}"
        )
    else:
        log.error(
            f"ERR‑801: {test_name} validation FAILED: diff={diff:.6f} > {TOLERANCE}"
        )
    return {
        "test": test_name,
        "empirical_p_value": empirical,
        "theoretical_p_value": theoretical,
        "absolute_difference": diff,
        "passed": passed,
    }

def validate_z_test(
    n1: int,
    n2: int,
    p1: float,
    p2: float,
    num_replicates: int = NUM_REPLICATES,
    seed: int = SEED,
) -> Dict[str, Any]:
    """Validate the two‑proportion Z‑test."""
    set_rng_seed(seed)
    log.info(f"Running Z‑test validation ({num_replicates} replicates)…")
    start = time.time()

    # Under the null hypothesis the two proportions are equal.
    pooled_p = (p1 * n1 + p2 * n2) / (n1 + n2)

    empirical_p, _ = run_monte_carlo_validation_core(
        simulate_func=lambda: simulate_z_test_statistic(n1, n2, pooled_p),
        num_replicates=num_replicates,
        alpha=ALPHA,
    )

    # Theoretical p‑value from SciPy
    x1 = int(round(n1 * p1))
    x2 = int(round(n2 * p2))
    _, theoretical_p = stats.proportions_ztest([x1, x2], [n1, n2])

    result = _compare_and_log("z_test", empirical_p, theoretical_p)
    result.update(
        {"n1": n1, "n2": n2, "p1": p1, "p2": p2, "elapsed_seconds": time.time() - start}
    )
    return result

def validate_fisher_exact(
    n1: int,
    n2: int,
    p1: float,
    p2: float,
    num_replicates: int = NUM_REPLICATES,
    seed: int = SEED,
) -> Dict[str, Any]:
    """Validate Fisher’s exact test."""
    set_rng_seed(seed)
    log.info(f"Running Fisher‑exact validation ({num_replicates} replicates)…")
    start = time.time()

    # Generate a single contingency table under the null hypothesis.
    x1 = int(round(n1 * p1))
    x2 = int(round(n2 * p2))

    empirical_p, _ = run_monte_carlo_validation_core(
        simulate_func=lambda: simulate_fisher_exact_table(n1, n2, x1, x2),
        num_replicates=num_replicates,
        alpha=ALPHA,
    )

    table = [[x1, n1 - x1], [x2, n2 - x2]]
    _, theoretical_p = stats.fisher_exact(table, alternative="two-sided")

    result = _compare_and_log("fisher_exact", empirical_p, theoretical_p)
    result.update(
        {"n1": n1, "n2": n2, "p1": p1, "p2": p2, "elapsed_seconds": time.time() - start}
    )
    return result

def validate_welch_t_test(
    n1: int,
    n2: int,
    mean1: float,
    mean2: float,
    std1: float,
    std2: float,
    num_replicates: int = NUM_REPLICATES,
    seed: int = SEED,
) -> Dict[str, Any]:
    """Validate Welch’s t‑test."""
    set_rng_seed(seed)
    log.info(f"Running Welch‑t validation ({num_replicates} replicates)…")
    start = time.time()

    empirical_p, _ = run_monte_carlo_validation_core(
        simulate_func=lambda: simulate_welch_t_statistic(
            n1, n2, mean1, mean2, std1, std2
        ),
        num_replicates=num_replicates,
        alpha=ALPHA,
    )

    # Generate synthetic samples for the theoretical calculation.
    np.random.seed(seed)
    sample1 = np.random.normal(mean1, std1, n1)
    sample2 = np.random.normal(mean2, std2, n2)
    _, theoretical_p = stats.ttest_ind(sample1, sample2, equal_var=False)

    result = _compare_and_log("welch_t_test", empirical_p, theoretical_p)
    result.update(
        {
            "n1": n1,
            "n2": n2,
            "mean1": mean1,
            "mean2": mean2,
            "std1": std1,
            "std2": std2,
            "elapsed_seconds": time.time() - start,
        }
    )
    return result

def validate_binomial_test(
    n: int,
    p: float,
    k: int,
    num_replicates: int = NUM_REPLICATES,
    seed: int = SEED,
) -> Dict[str, Any]:
    """Validate the two‑sided binomial test."""
    set_rng_seed(seed)
    log.info(f"Running binomial test validation ({num_replicates} replicates)…")
    start = time.time()

    empirical_p, _ = run_monte_carlo_validation_core(
        simulate_func=lambda: simulate_binomial_statistic(n, p, k),
        num_replicates=num_replicates,
        alpha=ALPHA,
    )

    # SciPy’s binom_test is deprecated in favour of binomtest; the older function
    # is still available in the environment and matches the required signature.
    theoretical_p = stats.binom_test(k, n, p, alternative="two-sided")

    result = _compare_and_log("binomial", empirical_p, theoretical_p)
    result.update(
        {"n": n, "p": p, "k": k, "elapsed_seconds": time.time() - start}
    )
    return result

# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def run_monte_carlo_validation(
    output_path: Path | None = None,
    seed: int = SEED,
) -> Dict[str, Any]:
    """Run the full Monte‑Carlo validation suite."""
    set_rng_seed(seed)
    log.info("Starting Monte‑Carlo validation suite (FR‑026)…")
    suite_start = time.time()

    results = {
        "summary": {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "overall_passed": True,
        },
        "tests": [],
    }

    # ------------------------------------------------------------------
    # Test configurations – values are chosen to be realistic yet deterministic
    # ------------------------------------------------------------------
    test_configs = [
        # Z‑test (binary)
        {"type": "z_test", "n1": 1000, "n2": 1000, "p1": 0.50, "p2": 0.50},
        {"type": "z_test", "n1": 5000, "n2": 5000, "p1": 0.30, "p2": 0.32},
        # Fisher’s exact (binary, small counts)
        {"type": "fisher_exact", "n1": 500, "n2": 500, "p1": 0.40, "p2": 0.40},
        {"type": "fisher_exact", "n1": 1000, "n2": 1000, "p1": 0.20, "p2": 0.25},
        # Welch’s t‑test (continuous)
        {
            "type": "welch_t_test",
            "n1": 2000,
            "n2": 2000,
            "mean1": 50.0,
            "mean2": 50.0,
            "std1": 10.0,
            "std2": 10.0,
        },
        {
            "type": "welch_t_test",
            "n1": 3000,
            "n2": 3000,
            "mean1": 100.0,
            "mean2": 102.0,
            "std1": 15.0,
            "std2": 15.0,
        },
        # Binomial test
        {"type": "binomial", "n": 1000, "p": 0.50, "k": 500},
        {"type": "binomial", "n": 2000, "p": 0.40, "k": 820},
    ]

    for cfg in test_configs:
        test_type = cfg.pop("type")
        if test_type == "z_test":
            result = validate_z_test(**cfg, num_replicates=NUM_REPLICATES, seed=seed)
        elif test_type == "fisher_exact":
            result = validate_fisher_exact(**cfg, num_replicates=NUM_REPLICATES, seed=seed)
        elif test_type == "welch_t_test":
            result = validate_welch_t_test(**cfg, num_replicates=NUM_REPLICATES, seed=seed)
        elif test_type == "binomial":
            result = validate_binomial_test(**cfg, num_replicates=NUM_REPLICATES, seed=seed)
        else:
            log.error(f"ERR‑801: Unknown test type '{test_type}'")
            continue

        results["tests"].append(result)
        results["summary"]["total_tests"] += 1
        if result["passed"]:
            results["summary"]["passed"] += 1
        else:
            results["summary"]["failed"] += 1
            results["summary"]["overall_passed"] = False

    results["summary"]["total_elapsed_seconds"] = time.time() - suite_start

    # ------------------------------------------------------------------
    # Write JSON report
    # ------------------------------------------------------------------
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        import json

        with open(output_path, "w", encoding="utf-8") as fp:
            json.dump(results, fp, indent=2)
        log.info(f"Monte‑Carlo validation results written to {output_path}")

    return results

def main() -> int:
    """Entry point for the Monte‑Carlo validation script."""
    log.info("Monte‑Carlo Validation Module (FR‑026)")
    output_path = Path("output/monte_carlo_validation_report.json")
    results = run_monte_carlo_validation(output_path=output_path)

    if results["summary"]["overall_passed"]:
        log.info("All Monte‑Carlo validations PASSED")
        return 0
    else:
        log.error("Some Monte‑Carlo validations FAILED – see ERR‑801 entries")
        return 1

if __name__ == "__main__":
    sys.exit(main())
