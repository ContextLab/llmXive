import os
import sys
import logging
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Local imports from existing API surface
from config import ProjectConfig, setup_logging
from ingestion import load_project_data, DataSchemaError
from merger import merge_similar_categories
from metrics import calculate_diversity_score
from modeling import fit_weighted_regression, RegressionResult

# Setup logging
logger = setup_logging("sensitivity_analysis")

def run_analysis_for_threshold(
    df: pd.DataFrame,
    threshold: float,
    config: ProjectConfig
) -> Optional[Dict[str, Any]]:
    """
    Run the full analysis pipeline for a single semantic similarity threshold.
    
    1. Merge categories based on the threshold.
    2. Calculate diversity scores on merged data.
    3. Fit the weighted regression model.
    4. Return the coefficient and p-value for the Recommendation_Diversity variable.
    
    Args:
        df: Cleaned dataframe with 'recommended_categories' and 'enrolled_categories' lists.
        threshold: Semantic similarity threshold for merging.
        config: Project configuration object.
        
    Returns:
        Dictionary with threshold, coefficient, p_value, and status.
        Returns None if the model fitting fails (e.g., insufficient data).
    """
    try:
        logger.info(f"Processing threshold: {threshold}")
        
        # 1. Merge categories
        # We need to create a copy to avoid modifying the original dataframe during the sweep
        df_temp = df.copy()
        
        # Apply merging to both recommendation and enrollment columns
        # The merge_similar_categories function from merger.py expects a list of unique categories
        # and returns a mapping. We need to apply this mapping to the dataframe.
        
        # Extract all unique categories from both columns
        all_recs = set()
        all_enr = set()
        for _, row in df_temp.iterrows():
            if isinstance(row['recommended_categories'], list):
                all_recs.update(row['recommended_categories'])
            if isinstance(row['enrolled_categories'], list):
                all_enr.update(row['enrolled_categories'])
                
        all_categories = list(all_recs.union(all_enr))
        
        if not all_categories:
            logger.warning("No categories found to merge.")
            return None
            
        merge_map = merge_similar_categories(all_categories, threshold)
        
        # Apply merge map to dataframe
        def apply_merge(cat_list, merge_map):
            if not isinstance(cat_list, list):
                return []
            return [merge_map.get(c, c) for c in cat_list]
        
        df_temp['recommended_categories_merged'] = df_temp['recommended_categories'].apply(
            lambda x: apply_merge(x, merge_map)
        )
        df_temp['enrolled_categories_merged'] = df_temp['enrolled_categories'].apply(
            lambda x: apply_merge(x, merge_map)
        )
        
        # 2. Calculate Diversity Scores
        # Using the merged columns
        df_temp['recommendation_diversity_score'] = df_temp['recommended_categories_merged'].apply(
            lambda x: calculate_diversity_score(x) if x else None
        )
        df_temp['learner_diversity_score'] = df_temp['enrolled_categories_merged'].apply(
            lambda x: calculate_diversity_score(x) if x else None
        )
        
        # Drop rows with missing diversity scores for regression
        df_model = df_temp.dropna(subset=['recommendation_diversity_score', 'learner_diversity_score'])
        
        if len(df_model) < 10:
            logger.warning(f"Insufficient data for regression at threshold {threshold} (N={len(df_model)}). Skipping.")
            return None
        
        # 3. Fit Weighted Regression
        # We are modeling Learner Diversity as a function of Recommendation Diversity
        # The specific model setup (propensity scores) is handled inside fit_weighted_regression
        # which expects specific column names or handles the derivation internally.
        
        # Prepare data for modeling
        # Assuming fit_weighted_regression expects 'recommended_categories_merged' or similar
        # We pass the dataframe with the merged columns and scores
        
        try:
            result: RegressionResult = fit_weighted_regression(
                df_model, 
                outcome_col='learner_diversity_score',
                treatment_col='recommendation_diversity_score'
            )
            
            return {
                "threshold": threshold,
                "coefficient": result.coefficient,
                "p_value": result.p_value,
                "standard_error": result.standard_error,
                "n_samples": len(df_model),
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Model fitting failed at threshold {threshold}: {e}")
            return {
                "threshold": threshold,
                "coefficient": None,
                "p_value": None,
                "standard_error": None,
                "n_samples": len(df_model),
                "status": "failed",
                "error": str(e)
            }
            
    except Exception as e:
        logger.error(f"Unexpected error processing threshold {threshold}: {e}")
        return None

def main():
    """
    Main entry point for sensitivity analysis.
    Sweeps thresholds, runs analysis, and outputs results to CSV.
    """
    config = ProjectConfig()
    logger.info("Starting Sensitivity Analysis Sweep")
    
    # Load data
    data_path = config.data_processed_path / "cleaned_data.parquet"
    if not data_path.exists():
        logger.error(f"Cleaned data not found at {data_path}. Run ingestion first.")
        sys.exit(1)
        
    df = load_project_data(data_path)
    
    # Define threshold sweep range
    # Low to moderate values as per task description
    # Sentence transformer cosine similarity ranges from -1 to 1.
    # "Low to moderate" usually implies the lower end of the similarity scale where merging happens.
    # We'll sweep from 0.0 (no merge unless identical) to 0.6 (moderate similarity).
    # Step size 0.1
    thresholds = [round(x, 2) for x in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6]]
    
    results = []
    for t in thresholds:
        res = run_analysis_for_threshold(df, t, config)
        if res:
            results.append(res)
            
    if not results:
        logger.error("No results generated from sensitivity sweep.")
        sys.exit(1)
        
    # Create DataFrame and save
    results_df = pd.DataFrame(results)
    
    # Ensure output directory exists
    results_path = config.data_processed_path / "sensitivity_analysis.csv"
    results_df.to_csv(results_path, index=False)
    logger.info(f"Sensitivity analysis results saved to {results_path}")
    
    # Check for sensitivity warning (p-value flip)
    significant = results_df['p_value'].notna() & (results_df['p_value'] < 0.05)
    if significant.any() and (~significant).any():
        # Check if it flips from True to False or vice versa as threshold increases
        # Sort by threshold to ensure order
        results_df_sorted = results_df.sort_values('threshold')
        significant_series = results_df_sorted['p_value'] < 0.05
        
        # Detect changes
        changes = significant_series.diff().abs()
        if changes.any():
            logger.warning("SENSITIVITY WARNING: Statistical significance flips across thresholds.")
            logger.warning(f"Significance pattern: {significant_series.tolist()}")
    
    return results_df

if __name__ == "__main__":
    main()
