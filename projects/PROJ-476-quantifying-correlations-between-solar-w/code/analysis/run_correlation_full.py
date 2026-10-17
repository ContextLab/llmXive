"""
Run the full lagged correlation analysis on the synchronized dataset.

This script is intended to be invoked as part of the ``analyze`` stage
(e.g. ``python -m code.main --stage analyze``) or directly via
``python -m code.analysis.run_correlation_full``.  It loads the
synchronized CSV produced by the ``sync`` stage, computes Pearson and
Spearman correlations for each composition parameter against each
geomagnetic index at the prescribed lags (0, 1, 2, 3, 6 h), applies the
effective‑sample‑size adjustment and Bonferroni correction, and writes
the results to ``results/correlations.csv`` which conforms to
``contracts/analysis_schema.schema.yaml``.
"""

import pandas as pd
from llmxive_toolkit import paths, get_logger

# Import the core analysis routine
from code.analysis.correlation import run_correlation_analysis

log = get_logger(__name__)

def main() -> None:
    """
    Entry point for the correlation analysis.

    Steps:
    1. Load the synchronized dataset (``data/processed/synced.csv``).
    2. Define the composition parameters, geomagnetic indices and lags
       required by the specification (3 params × 2 indices × 5 lags = 30 tests).
    3. Execute ``run_correlation_analysis`` which performs all calculations
       and writes the CSV to ``results/correlations.csv``.
    """
    # Path to the synchronized CSV produced by the ``sync`` stage
    synced_path = paths.data("processed", "synced.csv")
    log.info(f"Loading synchronized data from {synced_path}")

    df = pd.read_csv(synced_path, parse_dates=["timestamp"])

    # Parameters defined by the specification
    composition_params = ["proton_density", "temperature", "helium_abundance"]
    geomagnetic_indices = ["Kp", "Dst"]
    lags = [0, 1, 2, 3, 6]  # hours

    # Output location for the correlation results
    output_path = paths.results("correlations.csv")
    log.info(f"Writing correlation results to {output_path}")

    # Run the analysis – the function creates the output directory if needed
    run_correlation_analysis(
        df=df,
        composition_params=composition_params,
        geomagnetic_indices=geomagnetic_indices,
        lags=lags,
        output_path=str(output_path),
    )

    log.info("Correlation analysis completed successfully.")

if __name__ == "__main__":
    main()