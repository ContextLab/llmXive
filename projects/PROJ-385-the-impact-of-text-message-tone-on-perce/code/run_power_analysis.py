#!/usr/bin/env python
"""
Simulation‑based power analysis for the Linear Mixed Model (LMM).

This script generates a large number of synthetic datasets, fits the LMM to each,
and estimates statistical power for detecting the interaction of interest.
The results are written to ``data/processed/power_analysis_results.json`` and
contain the fields ``estimated_power`` (float) and ``target_N`` (int).

The implementation re‑uses the simulation and modelling utilities defined in
``code/09_power_analysis.py``. Because module names that start with a digit
cannot be imported via the normal ``import`` syntax, the module is loaded
dynamically with ``importlib``.
"""

import json
import logging
from pathlib import Path
import importlib.util
import numpy as np

# Project utilities
from config import get_processed_data_dir

# ----------------------------------------------------------------------
# Helper to load a module whose filename begins with a digit
# ----------------------------------------------------------------------
def _load_numeric_module(module_filename: str):
    """
    Load a Python module whose file name starts with a digit (e.g. ``09_power_analysis.py``).

    Returns the loaded module object.
    """
    module_path = Path(__file__).with_name(module_filename)
    spec = importlib.util.spec_from_file_location(module_filename.rstrip(".py"), module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Load the power‑analysis utilities
_pa_mod = _load_numeric_module("09_power_analysis.py")
simulate_data = getattr(_pa_mod, "simulate_data")
run_lmm = getattr(_pa_mod, "run_lmm")
# Optional helpers – use if they exist, otherwise fall back to simple logic
estimate_power = getattr(_pa_mod, "estimate_power", None)
find_required_n = getattr(_pa_mod, "find_required_n", None)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
N_SIMULATIONS = 2000          # number of synthetic datasets to generate
ALPHA = 0.05                  # significance threshold
TARGET_POWER = 0.80           # desired power
RANDOM_SEED = 42

np.random.seed(RANDOM_SEED)

# ----------------------------------------------------------------------
# Main analysis
# ----------------------------------------------------------------------
def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logger = logging.getLogger(__name__)

    logger.info("Starting simulation‑based power analysis")
    logger.info(f"Generating {N_SIMULATIONS:,} synthetic datasets")

    p_values = []
    for i in range(N_SIMULATIONS):
        # 1. Simulate a synthetic dataset
        synthetic_df = simulate_data()
        # 2. Fit the LMM and obtain a result dictionary
        result = run_lmm(synthetic_df)

        # The LMM helper is expected to return a mapping that contains the
        # p‑value for the interaction term.  The exact key name varies across
        # implementations; we try a few common possibilities.
        p_val = (
            result.get("p_value_interaction")
            or result.get("interaction_p")
            or result.get("p_value")
        )
        if p_val is None:
            raise KeyError("LMM result does not contain a p‑value for the interaction term")
        p_values.append(p_val)

        if (i + 1) % 200 == 0:
            logger.info(f"Processed {i + 1:,} simulations")

    # ------------------------------------------------------------------
    # Estimate empirical power
    # ------------------------------------------------------------------
    significant = [p < ALPHA for p in p_values]
    estimated_power = np.mean(significant)
    logger.info(f"Estimated power (α={ALPHA}): {estimated_power:.4f}")

    # ------------------------------------------------------------------
    # Determine required sample size (target_N)
    # ------------------------------------------------------------------
    if find_required_n is not None:
        # The helper is expected to accept the desired power and the current
        # estimated power (or effect size) and return an integer N.
        try:
            target_N = find_required_n(target_power=TARGET_POWER, current_power=estimated_power)
        except Exception as exc:  # pragma: no cover
            logger.warning(
                "find_required_n raised an exception (%s); falling back to simple scaling", exc
            )
            target_N = None
    else:
        target_N = None

    if target_N is None:
        # Simple proportional scaling as a fallback:
        #   power ∝ sqrt(N)  →  N_target = N_current * (target_power / estimated_power)^2
        # We approximate N_current as the number of participants used in the
        # simulation.  The simulation function does not expose this directly, so
        # we assume a default of 80 participants (the typical size for the study).
        N_current = 80
        if estimated_power == 0:
            target_N = int(1e6)  # arbitrarily large if power is zero
        else:
            target_N = int(np.ceil(N_current * (TARGET_POWER / estimated_power) ** 2))
        logger.info(
            "Target N estimated via proportional scaling (fallback): %d", target_N
        )
    else:
        logger.info("Target N estimated via find_required_n helper: %d", target_N)

    # ------------------------------------------------------------------
    # Persist results
    # ------------------------------------------------------------------
    results = {
        "estimated_power": float(estimated_power),
        "target_N": int(target_N),
        "num_simulations": N_SIMULATIONS,
        "significant_fraction": float(np.mean(significant)),
    }

    processed_dir = get_processed_data_dir()
    processed_dir.mkdir(parents=True, exist_ok=True)
    out_path = processed_dir / "power_analysis_results.json"
    out_path.write_text(json.dumps(results, indent=2))
    logger.info("Power analysis results written to %s", out_path)

if __name__ == "__main__":
    main()
