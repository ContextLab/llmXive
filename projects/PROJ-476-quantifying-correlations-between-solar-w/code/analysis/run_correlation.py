"""
Simple entry‑point script to execute the full lagged correlation analysis
for the entire 1998‑2020 period.

It loads the synchronized dataset (``data/processed/synced.csv``),
runs the analysis with the canonical parameter lists and the required
lag set {0,1,2,3,6} hours, and writes the results to ``results/correlations.csv``.

The script is deliberately lightweight so it can be invoked directly
from the quick‑start command or via the CI test suite.
"""
import os

from code.analysis.correlation import (
    load_synced_data,
    run_correlation_analysis,
)
from code.config import LAGS_HOURS, SIGNIFICANCE_LEVEL

# Canonical column names after the synchronization step
COMPOSITION_PARAMS = ["proton_density", "temperature", "helium_abundance"]
GEOMAGNETIC_INDICES = ["Kp", "Dst"]

def main() -> None:
    # Load the full synchronized dataset
    df = load_synced_data()

    # Define output location (exact path required by the specification)
    output_path = os.path.join("results", "correlations.csv")

    # Run the analysis
    run_correlation_analysis(
        df=df,
        composition_params=COMPOSITION_PARAMS,
        geomagnetic_indices=GEOMAGNETIC_INDICES,
        lags=LAGS_HOURS,
        output_path=output_path,
    )

    print(f"Correlation analysis completed – results written to {output_path}")


if __name__ == "__main__":
    main()
