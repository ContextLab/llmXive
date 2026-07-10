"""
Main orchestration script for the Impact of Incidental Music on Autobiographical Memory Retrieval pipeline.

This script coordinates the execution of the full research pipeline:
1. Data Ingestion (US1)
2. Cue Matching and Aggregation (US2)
3. Statistical Modeling and Analysis (US3)
4. Result Generation and Visualization

Usage:
    python code/main.py
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_project_root, ensure_directories, get_config_dict
from utils import setup_logging, get_logger
from state_manager import load_state, save_state, register_file, verify_all
from data_ingestion import (
    download_datasets,
    filter_cohort,
    handle_fallback,
    apply_frequency_threshold,
    calculate_ratio_score,
    calculate_residualized_score
)
from cue_matching import normalize_cues, match_cues, resolve_collisions
from aggregation import (
    join_exposure_data,
    aggregate_to_user_track,
    filter_zero_variance,
    enforce_match_rate
)
from modeling import (
    fit_mixed_model,
    fit_valence_model,
    check_collinearity,
    run_sensitivity_analysis,
    run_permutation_test,
    extract_model_summary,
    save_regression_results
)
from generate_user_track_pairs import main as generate_pairs_main
from generate_regression_summary import main as generate_regression_main
from generate_final_results import main as generate_final_results_main
from generate_diagnostic_plots import main as generate_plots_main

logger = get_logger(__name__)


def run_pipeline():
    """Execute the full research pipeline."""
    logger.info("Starting the Impact of Incidental Music pipeline...")
    project_root = get_project_root()
    ensure_directories()
    config = get_config_dict()

    # Initialize state tracking
    state = load_state(project_root)

    # ------------------------------------------------------------------
    # PHASE 1: Data Ingestion (User Story 1)
    # ------------------------------------------------------------------
    logger.info("--- Phase 1: Data Ingestion ---")
    
    # Download datasets if not present or checksums invalid
    msd_path, amt_path = download_datasets()
    
    # Filter cohort based on birth year
    cohort_df = filter_cohort(msd_path)
    
    # Handle fallback if birth year data is insufficient
    cohort_df = handle_fallback(cohort_df, msd_path)
    
    # Apply frequency threshold
    cohort_df = apply_frequency_threshold(cohort_df, min_listens=config.get('min_listens', 10))
    
    # Calculate exposure scores
    cohort_df = calculate_ratio_score(cohort_df)
    cohort_df = calculate_residualized_score(cohort_df)
    
    # Save ingested cohort
    ingested_path = project_root / "data" / "processed" / "ingested_cohort.parquet"
    cohort_df.to_parquet(ingested_path, index=False)
    register_file(state, str(ingested_path))
    logger.info(f"Ingested cohort saved to {ingested_path}")

    # ------------------------------------------------------------------
    # PHASE 2: Cue Matching and Aggregation (User Story 2)
    # ------------------------------------------------------------------
    logger.info("--- Phase 2: Cue Matching and Aggregation ---")
    
    # Load AMT data and normalize cues
    amt_df = pd.read_csv(amt_path)
    amt_df = normalize_cues(amt_df)
    
    # Build index from ingested cohort tracks
    track_index = {
        row['track_id']: row['track_name'] 
        for _, row in cohort_df.iterrows()
    }
    
    # Match cues to tracks
    matched_df, unmatched_count = match_cues(amt_df, track_index, 
                                             max_distance=config.get('levenshtein_threshold', 4))
    
    # Resolve collisions
    matched_df = resolve_collisions(matched_df)
    
    # Log match rate warning if below threshold
    enforce_match_rate(matched_df, amt_df, min_rate=config.get('min_match_rate', 0.80))
    
    # Join with exposure data
    joined_df = join_exposure_data(matched_df, cohort_df)
    
    # Aggregate to User-Track pairs
    user_track_df = aggregate_to_user_track(joined_df)
    
    # Filter zero variance tracks
    user_track_df = filter_zero_variance(user_track_df)
    
    # Save user-track pairs
    pairs_path = project_root / "data" / "processed" / "user_track_pairs.parquet"
    user_track_df.to_parquet(pairs_path, index=False)
    register_file(state, str(pairs_path))
    logger.info(f"User-Track pairs saved to {pairs_path}")

    # ------------------------------------------------------------------
    # PHASE 3: Statistical Modeling (User Story 3)
    # ------------------------------------------------------------------
    logger.info("--- Phase 3: Statistical Modeling ---")
    
    # Fit mixed models
    vividness_model = fit_mixed_model(user_track_df, 'mean_vividness')
    valence_model = fit_valence_model(user_track_df, 'mean_valence')
    
    # Check collinearity
    vif_results = check_collinearity(user_track_df)
    
    # Extract and save regression results
    regression_results = extract_model_summary(vividness_model, valence_model, vif_results)
    regression_path = project_root / "data" / "final" / "regression_summary.csv"
    save_regression_results(regression_results, regression_path)
    register_file(state, str(regression_path))
    logger.info(f"Regression summary saved to {regression_path}")

    # ------------------------------------------------------------------
    # PHASE 4: Sensitivity Analysis and Permutation Tests
    # ------------------------------------------------------------------
    logger.info("--- Phase 4: Sensitivity Analysis and Permutation Tests ---")
    
    # Run sensitivity analysis
    sensitivity_results = run_sensitivity_analysis(user_track_df, cohort_df, amt_df)
    sensitivity_path = project_root / "data" / "final" / "sensitivity_analysis.csv"
    sensitivity_results.to_csv(sensitivity_path, index=False)
    register_file(state, str(sensitivity_path))
    
    # Run permutation test
    permutation_results = run_permutation_test(user_track_df, n_iterations=1000)
    permutation_path = project_root / "data" / "final" / "permutation_results.csv"
    permutation_results.to_csv(permutation_path, index=False)
    register_file(state, str(permutation_path))
    logger.info("Sensitivity and permutation analysis complete.")

    # ------------------------------------------------------------------
    # PHASE 5: Generate Final Outputs
    # ------------------------------------------------------------------
    logger.info("--- Phase 5: Generating Final Outputs ---")
    
    # Generate diagnostic plots
    generate_plots_main()
    
    # Generate final results summary
    generate_final_results_main()
    
    # Save final state
    save_state(state, project_root / "state.yaml")
    
    logger.info("Pipeline execution completed successfully.")
    return True


def main():
    """Entry point for the pipeline."""
    setup_logging(level=logging.INFO)
    try:
        success = run_pipeline()
        if success:
            logger.info("Pipeline finished successfully.")
            sys.exit(0)
        else:
            logger.error("Pipeline failed.")
            sys.exit(1)
    except Exception as e:
        logger.exception(f"Pipeline execution failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()