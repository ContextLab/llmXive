"""
Full Pilot Correlation Validation

This script re‑runs the Pearson correlation between the human complexity ratings
collected during the pilot study and the automatically extracted visual‑complexity
metrics for the *full* pilot dataset.  If the correlation coefficient (r) falls
below the predefined threshold of 0.5, the script exits with a non‑zero status
code so downstream pipelines (or CI tests) can treat the result as a failure.

The implementation re‑uses the data‑loading and correlation utilities defined in
``src.experiment.pilot_gate`` to avoid code duplication and to stay consistent
with the existing pilot‑gate logic.
"""

import sys
from pathlib import Path

# Re‑use the existing pilot‑gate helpers
from src.experiment.pilot_gate import (
    load_human_ratings,
    load_metrics,
    aggregate_metrics,
    compute_correlation,
)

# Threshold for acceptable correlation
CORRELATION_THRESHOLD = 0.5


def run_full_pilot_correlation() -> float:
    """
    Load the full pilot data, compute the Pearson correlation between human
    ratings and aggregated metrics, and return the correlation coefficient.

    Raises
    ------
    SystemExit
        If the correlation is below ``CORRELATION_THRESHOLD``.
    """
    # Load raw human ratings and metric extractions
    human_df = load_human_ratings()
    metrics_df = load_metrics()

    # Aggregate metric values per image (the pilot_gate helper already knows how)
    agg_metrics = aggregate_metrics(metrics_df)

    # Compute Pearson's r (and the associated p‑value)
    r, p_value = compute_correlation(human_df, agg_metrics)

    # Log the result for visibility
    print(f"Full‑pilot correlation: r = {r:.4f}, p = {p_value:.4e}")

    # Enforce the threshold – exit with status 1 if the correlation is too low
    if r < CORRELATION_THRESHOLD:
        print(
            f"⚠️ Correlation below threshold ({CORRELATION_THRESHOLD:.2f}). "
            f"r = {r:.4f} – failing validation."
        )
        sys.exit(1)

    # Return the correlation for callers that might want to use the value
    return r


def main() -> None:
    """
    Entry‑point for ``python -m src.experiment.full_pilot_correlation``.
    """
    try:
        run_full_pilot_correlation()
    except Exception as exc:
        # Any unexpected exception should be visible and cause a non‑zero exit.
        print(f"Error during full pilot correlation validation: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()