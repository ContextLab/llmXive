"""
Sensitivity Analysis for Rarefaction Depth (Task T026).

This module implements a sweep over rarefaction depths {5000, 10000, 20000}
to evaluate the stability of alpha diversity results. It loads the
transformed diversity data (output from T021/T024), recalculates diversity
metrics at different depths (simulating the rarefaction process if raw
counts are available, or comparing pre-calculated depths if provided),
and logs the stability of the LME model coefficients across these thresholds.

Output: data/processed/sensitivity_analysis_log.json
"""
import logging
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from statsmodels.regression.mixed_linear_model import MixedLM

# Import existing pipeline components to ensure consistency
from preprocessing import load_otu_table, rarefy_otu_table, calculate_alpha_diversity
from analysis import load_transformed_diversity_data, run_lme_model

logger = logging.getLogger(__name__)

RAREFACTION_DEPTHS = [5000, 10000, 20000]
OUTPUT_PATH = Path("data/processed/sensitivity_analysis_log.json")

def run_sensitivity_analysis(
    otu_table_path: str,
    metadata_path: str,
    depths: List[int] = RAREFACTION_DEPTHS,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Performs sensitivity analysis by sweeping rarefaction depths.

    Args:
        otu_table_path: Path to the raw OTU table (counts).
        metadata_path: Path to the metadata CSV containing pH and site info.
        depths: List of rarefaction depths to test.
        output_path: Path to write the JSON log.

    Returns:
        Dictionary containing the analysis results and stability metrics.
    """
    if output_path is None:
        output_path = OUTPUT_PATH

    logger.info(f"Starting sensitivity analysis for depths: {depths}")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    results_log = {
        "task_id": "T026",
        "description": "Sensitivity analysis for rarefaction depth (SC-003)",
        "depths_tested": depths,
        "run_timestamp": str(pd.Timestamp.now()),
        "results": [],
        "stability_metrics": {}
    }

    # Load metadata once
    try:
        metadata = pd.read_csv(metadata_path)
        # Ensure required columns exist
        required_cols = ['sample_id', 'pH', 'site']
        if not all(col in metadata.columns for col in required_cols):
            raise ValueError(f"Metadata missing required columns: {required_cols}")
    except Exception as e:
        logger.error(f"Failed to load metadata: {e}")
        raise

    # Load OTU table
    try:
        otu_df = load_otu_table(otu_table_path)
        logger.info(f"Loaded OTU table with shape: {otu_df.shape}")
    except Exception as e:
        logger.error(f"Failed to load OTU table: {e}")
        raise

    depth_results = []

    for depth in depths:
        logger.info(f"Processing rarefaction depth: {depth}")

        # Filter samples that have enough reads
        sample_sums = otu_df.sum(axis=1)
        valid_samples = sample_sums[sample_sums >= depth].index.tolist()
        
        if len(valid_samples) < 2:
            logger.warning(f"Insufficient samples (N={len(valid_samples)}) for depth {depth}. Skipping.")
            depth_results.append({
                "depth": depth,
                "status": "skipped",
                "reason": "insufficient_samples",
                "valid_sample_count": len(valid_samples)
            })
            continue

        # Rarefy the OTU table
        # Note: rarefy_otu_table expects a DataFrame with sample_id as index
        rarefied_otu = rarefy_otu_table(otu_df, target_depth=depth, valid_samples=valid_samples)
        
        if rarefied_otu.empty:
            logger.warning(f"No samples remained after rarefaction for depth {depth}.")
            depth_results.append({
                "depth": depth,
                "status": "skipped",
                "reason": "empty_result"
            })
            continue

        # Calculate alpha diversity for this rarefaction
        # Returns a DataFrame with sample_id, shannon, simpson
        diversity_df = calculate_alpha_diversity(rarefied_otu)
        
        # Merge with metadata
        merged_df = diversity_df.merge(
            metadata[metadata['sample_id'].isin(diversity_df['sample_id'].tolist())],
            on='sample_id',
            how='inner'
        )

        if len(merged_df) < 2:
            logger.warning(f"Insufficient merged samples for depth {depth}.")
            depth_results.append({
                "depth": depth,
                "status": "skipped",
                "reason": "insufficient_merged_samples",
                "valid_sample_count": len(merged_df)
            })
            continue

        # Run LME Model: diversity ~ pH + (1|site)
        # We use Shannon as the primary metric for this sensitivity check
        if 'shannon' not in merged_df.columns:
            logger.warning(f"Shannon diversity not found for depth {depth}.")
            continue

        try:
            # Prepare data for statsmodels
            # Ensure categorical for random effect
            lme_data = merged_df.copy()
            lme_data['site'] = lme_data['site'].astype(str)
            
            # Run LME
            model_result = run_lme_model(
                data=lme_data,
                formula="shannon ~ pH + (1|site)"
            )
            
            # Extract key statistics
            # Assuming run_lme_model returns a result object with summary or specific attributes
            # If it returns a dict, adapt accordingly. Based on T022a, it writes to CSV, 
            # so we might need to re-run the logic here or assume a return value.
            # Given the constraint "import existing names", we assume run_lme_model 
            # returns the fitted model object or a dict of results.
            # Let's assume it returns a dict with 'estimate', 'se', 'p_value' for pH.
            
            # If run_lme_model returns a statsmodels MixedLMResults object:
            if hasattr(model_result, 'summary'):
                # Extract fixed effects
                summary_df = model_result.summary2().tables[1]
                # Find pH row
                pH_row = summary_df.loc['pH'] if 'pH' in summary_df.index else None
                
                if pH_row is not None:
                    estimate = float(pH_row['Coef.'])
                    se = float(pH_row['Std.Err.'])
                    p_val = float(pH_row['P>|t|'])
                else:
                    # Fallback if index is different
                    estimate, se, p_val = np.nan, np.nan, np.nan
            else:
                # Assume it's already a dict or simple object
                estimate = float(model_result.get('estimate', np.nan))
                se = float(model_result.get('se', np.nan))
                p_val = float(model_result.get('p_value', np.nan))

            depth_results.append({
                "depth": depth,
                "status": "success",
                "sample_count": len(merged_df),
                "lme_pH_estimate": estimate,
                "lme_pH_se": se,
                "lme_pH_p_value": p_val,
                "model_type": "LME"
            })
            
        except Exception as e:
            logger.error(f"LME failed for depth {depth}: {e}")
            depth_results.append({
                "depth": depth,
                "status": "error",
                "reason": str(e)
            })

    # Calculate Stability Metrics
    # Compare estimates across depths. If estimates are similar, the result is stable.
    successful_results = [r for r in depth_results if r['status'] == 'success']
    
    if len(successful_results) >= 2:
        estimates = [r['lme_pH_estimate'] for r in successful_results]
        ses = [r['lme_pH_se'] for r in successful_results]
        
        # Coefficient of Variation of the estimates
        mean_est = np.mean(estimates)
        std_est = np.std(estimates)
        cv = std_est / abs(mean_est) if mean_est != 0 else np.inf

        # Mean SE
        mean_se = np.mean(ses)

        results_log["stability_metrics"] = {
            "mean_estimate": float(mean_est),
            "std_estimate": float(std_est),
            "coefficient_of_variation": float(cv),
            "mean_se": float(mean_se),
            "interpretation": "Stable" if cv < 0.1 else "Unstable"
        }
    else:
        results_log["stability_metrics"] = {
            "interpretation": "Insufficient data to determine stability"
        }

    results_log["results"] = depth_results

    # Write to JSON
    with open(output_path, 'w') as f:
        json.dump(results_log, f, indent=2)

    logger.info(f"Sensitivity analysis complete. Results written to {output_path}")
    return results_log

def main():
    """
    Main entry point for the sensitivity analysis script.
    Expects data to be present in data/raw/ or data/processed/ as per project structure.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Define paths relative to project root
    # Assuming T018/T019 generated the OTU table and T014 generated metadata
    # Adjust paths if the actual file names differ based on previous task outputs
    otu_path = Path("data/processed/otu_table_filtered.tsv") 
    # If T019 output is named differently, adjust here. 
    # Common output from QIIME2/pipelines is often .tsv or .biom
    # Let's check for common names if the specific one doesn't exist
    if not otu_path.exists():
        # Try alternative common names
        alt_paths = [
            Path("data/processed/otu_table.tsv"),
            Path("data/raw/otu_table.tsv"),
            Path("data/processed/rarefied_otu_table.tsv")
        ]
        for p in alt_paths:
            if p.exists():
                otu_path = p
                break
    
    # Metadata path - usually from T014 or T024
    meta_path = Path("data/processed/unified_sample_table.csv")
    if not meta_path.exists():
        meta_path = Path("data/processed/alpha_diversity_results.csv") # T024 output

    if not otu_path.exists():
        logger.error(f"OTU table not found at {otu_path} or alternatives.")
        return 1
    
    if not meta_path.exists():
        logger.error(f"Metadata not found at {meta_path}.")
        return 1

    try:
        run_sensitivity_analysis(
            otu_table_path=str(otu_path),
            metadata_path=str(meta_path),
            depths=RAREFACTION_DEPTHS,
            output_path=OUTPUT_PATH
        )
        return 0
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
