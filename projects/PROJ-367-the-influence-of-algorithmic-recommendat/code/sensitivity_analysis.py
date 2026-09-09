"""
Sensitivity Analysis Script (T028a)

Executes the sensitivity sweep for semantic similarity thresholds {0.01, 0.05, 0.1}
and outputs a table (CSV) showing the Recommendation_Diversity coefficient and p-value
for each threshold.

This script assumes:
1. The synthetic dataset exists at `data/raw/synthetic_enrollments.csv` (from T014b).
2. The processing pipeline (ingestion, metrics) is functional.
3. The modeling pipeline (PSW/GLS) is functional.

It re-runs the analysis pipeline for each threshold, adjusting the category merging
logic in `metrics.py` via the config, and collects the results.
"""
import os
import sys
import logging
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any

# Project root setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from config import ProjectConfig, setup_logging
from ingestion import load_project_data, ingest_and_clean, validate_schema
from metrics import calculate_batch_diversity_scores, merge_similar_categories
from modeling import run_ps_analysis
from robustness import sensitivity_analysis_thresholds

# Configure logging
logger = setup_logging("sensitivity_analysis")

def run_analysis_for_threshold(config: ProjectConfig, threshold: float) -> Dict[str, Any]:
    """
    Runs the full analysis pipeline for a specific semantic similarity threshold.
    
    Returns a dictionary with the coefficient and p-value for the Recommendation_Diversity predictor.
    """
    logger.info(f"--- Running analysis for threshold: {threshold} ---")
    
    # 1. Update Config for this run
    # We need to temporarily modify the config to reflect the new threshold.
    # Since ProjectConfig is a dataclass, we create a new instance or modify in place if mutable.
    # Assuming ProjectConfig allows modification of threshold or we pass it to functions.
    # For safety, we'll update the config instance used by the pipeline.
    original_threshold = config.semantic_similarity_threshold
    config.semantic_similarity_threshold = threshold
    
    try:
        # 2. Load and Ingest Data
        # We reload data to ensure clean state, though for synthetic data it's static.
        # The ingestion logic uses the config for validation but not for merging (merging is in metrics).
        df = load_project_data(config)
        
        if df is None or df.empty:
            logger.error("No data loaded. Stopping.")
            return {"threshold": threshold, "error": "No data loaded"}

        # 3. Calculate Diversity Scores (This uses the current config threshold)
        # Note: calculate_batch_diversity_scores expects the dataframe and config.
        # It internally calls merge_similar_categories if needed.
        df_processed = calculate_batch_diversity_scores(df, config)
        
        if df_processed is None or df_processed.empty:
            logger.error("Diversity score calculation failed or resulted in empty dataframe.")
            return {"threshold": threshold, "error": "Diversity calculation failed"}

        # 4. Run Propensity Score Analysis (Modeling)
        # This function should return the regression result containing the coefficient and p-value.
        result = run_ps_analysis(df_processed, config)
        
        if result is None:
            logger.warning(f"Modeling failed for threshold {threshold}.")
            return {
                "threshold": threshold,
                "coefficient": None,
                "p_value": None,
                "method": "None",
                "status": "failed"
            }

        # Extract the specific metric for Recommendation_Diversity
        # The result object (RegressionResult or dict) should have these fields.
        # Assuming run_ps_analysis returns a dict or object with 'coefficients' and 'p_values' or similar.
        # Based on T022/T023, the result likely contains the main coefficient of interest.
        # We assume the key is 'recommendation_diversity_score' or similar.
        
        # Let's assume the result is a dictionary or object with:
        # - 'coefficients': dict of {feature: coef}
        # - 'p_values': dict of {feature: pval}
        # - 'method': 'PSW' or 'GLS'
        
        coeff = None
        p_val = None
        method = result.get('method', 'Unknown')
        
        # Attempt to find the coefficient for Recommendation Diversity
        # The feature name in the dataframe is likely 'recommendation_diversity_score'
        feature_name = 'recommendation_diversity_score'
        
        if 'coefficients' in result:
            coeff = result['coefficients'].get(feature_name)
        elif hasattr(result, 'coefficients'):
            coeff = result.coefficients.get(feature_name)
        
        if 'p_values' in result:
            p_val = result['p_values'].get(feature_name)
        elif hasattr(result, 'p_values'):
            p_val = result.p_values.get(feature_name)
        
        return {
            "threshold": threshold,
            "coefficient": coeff,
            "p_value": p_val,
            "method": method,
            "status": "success"
        }

    finally:
        # Restore original threshold
        config.semantic_similarity_threshold = original_threshold

def main():
    logger.info("Starting Sensitivity Analysis (T028a)")
    
    # Load Configuration
    config = ProjectConfig()
    
    # Define thresholds to sweep
    thresholds = [0.01, 0.05, 0.1]
    
    results = []
    
    for t in thresholds:
        res = run_analysis_for_threshold(config, t)
        results.append(res)
        
        if res.get('status') == 'success':
            logger.info(f"Threshold {t}: Coeff={res['coefficient']:.4f}, P={res['p_value']:.4f}")
        else:
            logger.warning(f"Threshold {t}: Failed or incomplete.")
    
    # Convert to DataFrame and Save
    df_results = pd.DataFrame(results)
    
    # Ensure output directory exists
    output_dir = PROJECT_ROOT / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "sensitivity_analysis_table.csv"
    df_results.to_csv(output_path, index=False)
    
    logger.info(f"Sensitivity analysis table saved to: {output_path}")
    
    # Also save a JSON summary for easy parsing by T028b
    json_path = output_dir / "sensitivity_analysis_table.json"
    df_results.to_json(json_path, orient='records', indent=2)
    logger.info(f"Sensitivity analysis table (JSON) saved to: {json_path}")

    return df_results

if __name__ == "__main__":
    main()