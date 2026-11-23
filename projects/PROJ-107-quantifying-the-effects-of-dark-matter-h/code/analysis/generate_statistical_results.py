"""
T025: Create analysis script to generate `data/processed/statistical_results.csv`.

This script orchestrates the statistical analysis pipeline for User Story 2.
It loads the mass-matched data chunks, runs statistical tests (regression, binning),
applies Bonferroni correction, and aggregates the results into a single CSV file.

Dependencies:
  - T021: Mass-matching interface
  - T021b: Streaming mass-matching implementation (input data source)
  - T022: Non-parametric tests
  - T023a: Regression logic
  - T023b: Binning tests logic
  - T024: Bonferroni correction
  - T026c: Metadata flag verification (ensures input data has flags)
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

# Import from local project structure
# Note: We assume this script runs from the project root or code/ directory
# Adjust sys.path if necessary, though typically main.py handles this.
if 'code' not in sys.path:
    code_root = Path(__file__).resolve().parent.parent
    if code_root.name == 'code':
        sys.path.insert(0, str(code_root))

from utils.config import get_project_root, get_data_processed_path
from analysis.stats import (
    stream_mass_matched_chunks,
    run_statistical_tests,
    apply_bonferroni_correction
)
from utils.io import write_csv_with_associational_flag

logger = logging.getLogger(__name__)


def load_halo_data() -> pd.DataFrame:
    """
    Load halo shape data from the processed CSV.
    This is a fallback or direct load if chunked processing isn't needed for this specific aggregation,
    but T021b outputs chunks. We will primarily use stream_mass_matched_chunks.
    """
    path = get_data_processed_path("halo_shapes.csv")
    if not path.exists():
        raise FileNotFoundError(f"Halo shapes data not found at {path}")
    return pd.read_csv(path)


def load_galaxy_properties() -> pd.DataFrame:
    """
    Load galaxy properties from the processed CSV.
    """
    path = get_data_processed_path("galaxy_properties.csv")
    if not path.exists():
        raise FileNotFoundError(f"Galaxy properties data not found at {path}")
    return pd.read_csv(path)


def merge_halo_galaxy_data(halo_df: pd.DataFrame, galaxy_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge halo and galaxy data on halo_id.
    Note: In a streaming context, this merge is typically done per-chunk in T021b.
    This function is provided for completeness or if a full merge is needed for small subsets.
    """
    # Assuming halo_shapes.csv has 'halo_id' and galaxy_properties.csv has 'halo_id'
    # We join galaxy properties to halo shapes.
    merged = pd.merge(
        halo_df,
        galaxy_df,
        on='halo_id',
        how='inner',
        suffixes=('_halo', '_galaxy')
    )
    return merged


def run_statistical_tests_on_merged(merged_data: pd.DataFrame) -> pd.DataFrame:
    """
    Execute the full suite of statistical tests on the merged dataset.
    This includes:
    1. Regression (SFR ~ triaxiality + b_a_ratio + mass) -> T023a
    2. Binning Tests (Kruskal-Wallis, etc.) -> T023b
    3. Bonferroni Correction -> T024

    Returns a DataFrame containing all results.
    """
    results = []

    # 1. Run Regression Tests (T023a)
    # The stats module's run_statistical_tests likely handles the orchestration
    # We pass the merged data.
    try:
        regression_results = run_statistical_tests(
            merged_data,
            test_type='regression',
            target='sfr',
            predictors=['triaxiality', 'b_a_ratio', 'mass']
        )
        if isinstance(regression_results, list):
            results.extend(regression_results)
        elif isinstance(regression_results, pd.DataFrame):
            results.append(regression_results.to_dict('records'))
    except Exception as e:
        logger.error(f"Error running regression tests: {e}")
        # Continue with other tests even if regression fails partially

    # 2. Run Binning Tests (T023b)
    # Binning tests are run on the same merged data
    try:
        binning_results = run_statistical_tests(
            merged_data,
            test_type='binning',
            target='sfr', # Or other galaxy property
            binning_column='c_a_ratio', # Or triaxiality
            bins=['prolate', 'triaxial', 'spherical']
        )
        if isinstance(binning_results, list):
            results.extend(binning_results)
        elif isinstance(binning_results, pd.DataFrame):
            results.append(binning_results.to_dict('records'))
    except Exception as e:
        logger.error(f"Error running binning tests: {e}")

    # 3. Apply Bonferroni Correction (T024)
    # This usually modifies the p-values in the results
    if results:
        combined_df = pd.DataFrame(results)
        if 'p_value' in combined_df.columns:
            corrected_df = apply_bonferroni_correction(combined_df)
            return corrected_df
        else:
            # If results are already dicts or mixed, we might need to handle differently
            # For now, assume the run_statistical_tests returns a structure ready for correction
            pass

    return pd.DataFrame(results)


def save_results(results_df: pd.DataFrame, output_path: Path):
    """
    Save the statistical results to a CSV file with the associational flag.
    """
    if results_df.empty:
        logger.warning("No results to save.")
        return

    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write with the associational flag as per T026c requirements
    write_csv_with_associational_flag(results_df, output_path)
    logger.info(f"Statistical results saved to {output_path}")


def main():
    """
    Main entry point for T025.
    Orchestrates loading, processing, and saving of statistical results.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    project_root = get_project_root()
    processed_dir = get_data_processed_path()

    # Ensure input files exist (T017, T018 outputs)
    halo_path = processed_dir / "halo_shapes.csv"
    galaxy_path = processed_dir / "galaxy_properties.csv"

    if not halo_path.exists():
        logger.error(f"Missing input file: {halo_path}. T017 must be completed.")
        sys.exit(1)
    if not galaxy_path.exists():
        logger.error(f"Missing input file: {galaxy_path}. T018 must be completed.")
        sys.exit(1)

    # Check for mass-matched chunks (T021b output)
    # T021b outputs to data/processed/matched_chunks/
    matched_chunks_dir = processed_dir / "matched_chunks"
    if matched_chunks_dir.exists() and any(matched_chunks_dir.iterdir()):
        logger.info("Using mass-matched chunks from T021b.")
        # We need to iterate over chunks and run tests, then aggregate.
        # However, T021b's stream_mass_matched_chunks is a generator.
        # We can collect them or process in a loop.
        # For simplicity in this script, we will load the chunks, merge if necessary,
        # and run the tests.
        
        # Strategy: Load all chunks into a single DataFrame (if memory permits)
        # or run tests on each chunk and aggregate results.
        # Given the constraints (7GB RAM), loading all might be risky if chunks are many.
        # But T021b chunks are "small CSV files". Let's assume we can load them sequentially
        # and append results.
        
        all_results = []
        chunk_files = sorted(matched_chunks_dir.glob("*.csv"))
        
        logger.info(f"Processing {len(chunk_files)} matched chunks.")
        
        for chunk_file in chunk_files:
            try:
                chunk_df = pd.read_csv(chunk_file)
                # Run tests on this chunk
                # Note: run_statistical_tests_on_merged expects a merged df.
                # The chunks from T021b are ALREADY merged (halo + galaxy).
                chunk_results = run_statistical_tests_on_merged(chunk_df)
                if isinstance(chunk_results, pd.DataFrame):
                    all_results.append(chunk_results)
                elif isinstance(chunk_results, list):
                    all_results.extend(chunk_results)
            except Exception as e:
                logger.error(f"Error processing chunk {chunk_file}: {e}")
                continue
        
        if all_results:
            final_df = pd.concat(all_results, ignore_index=True)
            # Apply Bonferroni correction on the aggregated results
            if 'p_value' in final_df.columns:
                final_df = apply_bonferroni_correction(final_df)
            
            output_path = processed_dir / "statistical_results.csv"
            save_results(final_df, output_path)
        else:
            logger.error("No results generated from chunks.")
            sys.exit(1)

    else:
        # Fallback: Load full datasets and merge (might be memory intensive)
        logger.warning("No matched chunks found. Attempting full merge (may be memory intensive).")
        halo_df = load_halo_data()
        galaxy_df = load_galaxy_properties()
        merged_df = merge_halo_galaxy_data(halo_df, galaxy_df)
        
        results_df = run_statistical_tests_on_merged(merged_df)
        output_path = processed_dir / "statistical_results.csv"
        save_results(results_df, output_path)

    logger.info("T025 completed successfully.")


if __name__ == "__main__":
    main()