"""
run_power_analysis.py
---------------------

This script performs a simulation‑based power analysis for the linear mixed‑effects
model (LMM) used in the project.  It generates synthetic datasets for a range of
sample sizes (number of participants), fits a mixed‑effects model to each dataset,
and estimates the statistical power to detect the interaction between cue intensity
and relationship context.

The resulting JSON file, written to ``data/processed/power_analysis_results.json``,
contains three keys required by the verification step:

* ``estimated_power`` – the estimated power at the *target* sample size.
* ``target_N`` – the smallest number of participants that achieves at least
  80 % power (the conventional threshold).
* ``method`` – a short description of the approach used.

The script can be executed directly::

    $ python code/run_power_analysis.py

It relies only on the project's public API (``config``) and on standard scientific
Python libraries that are already declared in ``code/requirements.txt``.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

# Project utilities
from config import get_processed_data_dir

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# Desired power threshold and significance level
POWER_TARGET = 0.80
ALPHA = 0.05

# Simulation parameters
MIN_PARTICIPANTS = 40          # inclusive lower bound
MAX_PARTICIPANTS = 120         # inclusive upper bound
STEP_PARTICIPANTS = 10
REPS_PER_N = 300               # number of simulated datasets per N
RANDOM_SEED = 42

# Fixed effect coefficients (chosen to reflect a medium effect size)
BETA_INTERCEPT = 3.0
BETA_CUE = 0.5                 # main effect of cue intensity
BETA_CONTEXT = 0.3             # main effect of relationship context (binary)
BETA_INTERACTION = 0.4         # interaction we aim to detect

# Number of observations per participant (stimuli)
TRIALS_PER_PARTICIPANT = 20

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def simulate_dataset(num_participants: int, rng: np.random.Generator) -> pd.DataFrame:
    """
    Simulate a single dataset for ``num_participants`` participants.

    Returns a ``pandas.DataFrame`` with columns:
        - participant_id : int
        - cue_intensity   : float (continuous, centred)
        - context         : int   (0 = friend, 1 = acquaintance)
        - rating          : float (dependent variable)
    """
    rows: List[Dict] = []

    # Random intercept for each participant
    participant_intercepts = rng.normal(loc=0.0, scale=0.5, size=num_participants)

    for pid in range(num_participants):
        intercept = participant_intercepts[pid]

        # Generate cue intensity values (standardised)
        cue = rng.normal(loc=0.0, scale=1.0, size=TRIALS_PER_PARTICIPANT)

        # Randomly assign context (binary)
        context = rng.integers(low=0, high=2, size=TRIALS_PER_PARTICIPANT)

        # Linear predictor
        mu = (
            BETA_INTERCEPT
            + intercept
            + BETA_CUE * cue
            + BETA_CONTEXT * context
            + BETA_INTERACTION * cue * context
        )

        # Add residual noise
        rating = mu + rng.normal(loc=0.0, scale=1.0, size=TRIALS_PER_PARTICIPANT)

        for c, ctx, r in zip(cue, context, rating):
            rows.append(
                {
                    "participant_id": pid,
                    "cue_intensity": c,
                    "context": ctx,
                    "rating": r,
                }
            )
    return pd.DataFrame(rows)


def fit_lmm(df: pd.DataFrame) -> float:
    """
    Fit a mixed‑effects model with a random intercept for participant
    and return the two‑sided p‑value for the interaction term
    (cue_intensity:context).

    The model formula is:

        rating ~ cue_intensity * context + (1 | participant_id)

    Returns:
        p_value (float) – p‑value for the interaction term.
    """
    # Convert context to categorical for proper interaction handling
    df = df.copy()
    df["context"] = df["context"].astype("category")

    # Using statsmodels' mixed linear model via formula API
    model = smf.mixedlm(
        "rating ~ cue_intensity * context",
        df,
        groups=df["participant_id"],
    )
    result = model.fit(reml=False)  # use ML for Wald tests

    # The interaction term appears as 'cue_intensity:context[T.1]' in the params
    term_name = "cue_intensity:context[T.1]"
    if term_name not in result.pvalues:
        raise KeyError(f"Interaction term '{term_name}' not found in model results.")

    return float(result.pvalues[term_name])


def estimate_power_for_n(num_participants: int, rng: np.random.Generator) -> float:
    """
    Estimate statistical power for a given number of participants by
    simulating ``REPS_PER_N`` datasets and fitting the model to each.

    Power is defined as the proportion of simulations where the interaction
    p‑value is below ``ALPHA``.
    """
    significant = 0
    for _ in range(REPS_PER_N):
        df = simulate_dataset(num_participants, rng)
        p_val = fit_lmm(df)
        if p_val < ALPHA:
            significant += 1
    power = significant / REPS_PER_N
    logger.debug(
        "N=%d → power=%.3f (based on %d reps)", num_participants, power, REPS_PER_N
    )
    return power


def perform_power_analysis() -> Dict:
    """
    Run the full power analysis across a range of sample sizes and
    return a dictionary ready for JSON serialisation.

    The dictionary contains:
        - estimated_power : power at the discovered target N
        - target_N        : smallest N achieving POWER_TARGET
        - method          : description string
    """
    rng = np.random.default_rng(RANDOM_SEED)

    # Scan sample sizes in ascending order
    target_n = None
    estimated_power_at_target = None

    for n in range(MIN_PARTICIPANTS, MAX_PARTICIPANTS + 1, STEP_PARTICIPANTS):
        power = estimate_power_for_n(n, rng)
        if power >= POWER_TARGET:
            target_n = n
            estimated_power_at_target = power
            logger.info(
                "Achieved target power (%.2f) at N=%d with estimated power %.3f",
                POWER_TARGET,
                n,
                power,
            )
            break
        else:
            logger.info(
                "N=%d → power=%.3f (below target %.2f)", n, power, POWER_TARGET
            )

    # Fallback: if never reached the target, report the highest N examined
    if target_n is None:
        target_n = MAX_PARTICIPANTS
        estimated_power_at_target = estimate_power_for_n(target_n, rng)
        logger.warning(
            "Target power %.2f not reached; using max N=%d with power %.3f",
            POWER_TARGET,
            target_n,
            estimated_power_at_target,
        )

    results = {
        "estimated_power": round(estimated_power_at_target, 3),
        "target_N": target_n,
        "method": "simulation (mixed effects model, Wald test)",
    }
    return results


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the power analysis and write the JSON results to the processed
    data directory.
    """
    processed_dir: Path = get_processed_data_dir()
    processed_dir.mkdir(parents=True, exist_ok=True)

    output_path = processed_dir / "power_analysis_results.json"

    logger.info("Starting simulation‑based power analysis...")
    results = perform_power_analysis()

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    logger.info("Power analysis completed. Results written to %s", output_path)


if __name__ == "__main__":
    main()