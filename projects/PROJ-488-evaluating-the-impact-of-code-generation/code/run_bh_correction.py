"""
Script to apply Benjamini-Hochberg correction to metric comparison results.
Reads raw p-values from metric analysis, applies correction, and saves results.
"""
import os
import sys
import json
import logging
from pathlib import Path
import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from statistical_analysis import (
    run_mann_whitney_u_analysis,
    run_cliffs_delta_analysis,
    run_benjamini_hochberg_correction_on_metrics
)
from logging_config import setup_logger, get_logger
from checksum import compute_sha256
from state_tracker import update_state_with_artifact, load_state_file, save_state_file

def load_metrics_data(metrics_dir: Path) -> dict:
    """
    Load metric data from CSV files in the metrics directory.
    Returns dictionary with 'human' and 'llm' groups for each metric.
    """
    metrics_data = {}
    
    if not metrics_dir.exists():
        raise FileNotFoundError(f"Metrics directory not found: {metrics_dir}")
    
    # Expected files: cyclomatic_complexity.csv, maintainability_index.csv, etc.
    # Format: snippet_id, group, score
    csv_files = list(metrics_dir.glob("*.csv"))
    
    for csv_file in csv_files:
        metric_name = csv_file.stem
        try:
            df = pd.read_csv(csv_file)
            
            if 'group' not in df.columns or 'score' not in df.columns:
                logging.warning(f"Skipping {csv_file}: missing required columns")
                continue
            
            human_scores = df[df['group'] == 'human']['score'].values
            llm_scores = df[df['group'] == 'llm']['score'].values
            
            metrics_data[metric_name] = {
                'human': np.array(human_scores, dtype=float),
                'llm': np.array(llm_scores, dtype=float)
            }
            
        except Exception as e:
            logging.error(f"Error loading {csv_file}: {e}")
            continue
    
    return metrics_data

def run_bh_correction_pipeline(metrics_dir: Path, output_dir: Path):
    """
    Run the full Benjamini-Hochberg correction pipeline.
    
    1. Load metric data
    2. Run Mann-Whitney U tests
    3. Apply BH correction
    4. Save results
    """
    logger = setup_logger("run_bh_correction")
    logger.info(f"Starting BH correction pipeline")
    logger.info(f"Metrics directory: {metrics_dir}")
    logger.info(f"Output directory: {output_dir}")
    
    # Create output directory if needed
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    metrics_data = load_metrics_data(metrics_dir)
    if not metrics_data:
        logger.error("No valid metric data found. Aborting.")
        sys.exit(1)
    
    logger.info(f"Loaded {len(metrics_data)} metrics")
    
    # Run Mann-Whitney U tests
    logger.info("Running Mann-Whitney U tests...")
    raw_results = run_mann_whitney_u_analysis(metrics_data)
    
    # Run Cliff's Delta analysis
    logger.info("Running Cliff's Delta analysis...")
    cliffs_results = run_cliffs_delta_analysis(metrics_data)
    
    # Apply BH correction
    logger.info("Applying Benjamini-Hochberg correction...")
    corrected_results = run_benjamini_hochberg_correction_on_metrics(raw_results)
    
    # Merge Cliff's Delta results
    for metric in corrected_results:
        if metric in cliffs_results:
            corrected_results[metric].update(cliffs_results[metric])
    
    # Save results to JSON
    output_json = output_dir / "bh_corrected_results.json"
    with open(output_json, 'w') as f:
        json.dump(corrected_results, f, indent=2, default=str)
    
    logger.info(f"Saved corrected results to {output_json}")
    
    # Create summary CSV
    summary_data = []
    for metric, results in corrected_results.items():
        summary_data.append({
            'metric': metric,
            'p_value_raw': results.get('p_value_raw', np.nan),
            'p_value_adjusted': results.get('p_value_adjusted', np.nan),
            'cliffs_delta': results.get('cliffs_delta', np.nan),
            'magnitude': results.get('magnitude', 'unknown'),
            'n_human': results.get('n_human', 0),
            'n_llm': results.get('n_llm', 0)
        })
    
    summary_df = pd.DataFrame(summary_data)
    output_csv = output_dir / "bh_corrected_summary.csv"
    summary_df.to_csv(output_csv, index=False)
    
    logger.info(f"Saved summary to {output_csv}")
    
    # Update state tracker
    try:
        state_file = Path("state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml")
        if state_file.exists():
            update_state_with_artifact(
                state_file,
                artifact_path=str(output_json.relative_to(Path.cwd())),
                artifact_type="statistical_correction",
                description="Benjamini-Hochberg corrected p-values for all metrics"
            )
            logger.info("Updated state file")
    except Exception as e:
        logger.warning(f"Could not update state file: {e}")
    
    # Print summary
    logger.info("=" * 50)
    logger.info("BH Correction Summary")
    logger.info("=" * 50)
    significant_count = 0
    for metric, results in corrected_results.items():
        adj_p = results.get('p_value_adjusted', 1.0)
        delta = results.get('cliffs_delta', 0.0)
        sig = "YES" if adj_p < 0.05 and abs(delta) >= 0.1 else "NO"
        if sig == "YES":
            significant_count += 1
        logger.info(f"{metric}: adj_p={adj_p:.4f}, delta={delta:.4f} [{sig}]")
    
    logger.info(f"Total significant metrics (adj_p < 0.05, |delta| >= 0.1): {significant_count}")
    
    return corrected_results

def main():
    """Main entry point."""
    # Default paths
    metrics_dir = Path("data/metrics")
    output_dir = Path("data/metrics")
    
    # Allow override via command line
    if len(sys.argv) > 1:
        metrics_dir = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_dir = Path(sys.argv[2])
    
    try:
        run_bh_correction_pipeline(metrics_dir, output_dir)
        print("BH correction pipeline completed successfully.")
    except Exception as e:
        logging.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()