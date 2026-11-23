import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

from utils.config import get_config, ensure_directories
from analysis.statistical_test import run_full_analysis

logger = logging.getLogger(__name__)

def load_analysis_data(input_path: str) -> pd.DataFrame:
    """
    Load the merged features dataset.
    Exits if file is missing or empty.
    """
    path = Path(input_path)
    if not path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    try:
        df = pd.read_parquet(path)
    except Exception as e:
        logger.error(f"Failed to read parquet file {input_path}: {e}")
        raise e

    if df.empty:
        logger.error(f"Input file {input_path} is empty.")
        raise ValueError(f"Input file {input_path} is empty.")

    return df

def load_covariate_config(config_path: str) -> List[str]:
    """
    Load the list of covariates to use for stratification.
    """
    path = Path(config_path)
    if not path.exists():
        logger.error(f"Covariate config not found: {config_path}")
        raise FileNotFoundError(f"Covariate config not found: {config_path}")
    
    with open(path, 'r') as f:
        config = json.load(f)
    
    # Expecting a list of column names, e.g., ['file_size', 'complexity_score', 'activity_level']
    # The task description says "columns defined in ... for complexity and size".
    # We assume the config contains the relevant columns.
    if 'covariates' in config:
        return config['covariates']
    elif isinstance(config, list):
        return config
    else:
        # Fallback or error if structure is unexpected
        logger.warning(f"Covariate config at {config_path} does not contain 'covariates' key or is not a list. Attempting to use keys.")
        if isinstance(config, dict):
            return list(config.keys())
        raise ValueError(f"Could not parse covariate list from {config_path}")

def stratify_by_complexity_size(df: pd.DataFrame, covariates: List[str]) -> Dict[str, pd.DataFrame]:
    """
    Stratify the dataframe by quantiles of the specified covariates (complexity and size).
    Returns a dictionary mapping subset names to DataFrames.
    """
    # We need to create a combined stratification key.
    # Strategy: Create quantile bins for each specified covariate, then combine them.
    # To ensure we get enough subsets, we might need to adjust the number of bins (q) or combine columns.
    
    logger.info(f"Stratifying by covariates: {covariates}")
    
    # Filter to ensure columns exist
    valid_covariates = [col for col in covariates if col in df.columns]
    if not valid_covariates:
        raise ValueError(f"No valid covariates found in dataframe. Available: {list(df.columns)}. Required: {covariates}")
    
    # We will create a multi-level quantile index.
    # To guarantee at least 5 subsets, we might need to use a higher 'q' or a different strategy.
    # A robust strategy: Create bins for the FIRST two valid covariates (assuming complexity and size are first).
    # If only one is available, use a higher q.
    
    bins = {}
    for i, col in enumerate(valid_covariates[:2]): # Take up to 2 columns for stratification
        # Use qcut to create equal-sized bins. 
        # If we have 2 columns and q=3, we get 9 subsets. If q=2, we get 4 (too few).
        # Let's try q=3 first. If that yields <5, we adjust.
        q = 3
        try:
            bins[col] = pd.qcut(df[col], q=q, labels=False, duplicates='drop')
        except ValueError:
            # If qcut fails due to duplicates, try fewer bins
            try:
                bins[col] = pd.qcut(df[col], q=2, labels=False, duplicates='drop')
            except ValueError:
                logger.warning(f"Could not bin {col} even with q=2. Using a single bin.")
                bins[col] = pd.Series(0, index=df.index)
    
    # Combine bins into a single group key
    # If we have 2 columns, we can map (bin1, bin2) to a unique integer
    if len(bins) >= 2:
        # Create a combined key: bin1 * N_bins2 + bin2
        # We need to know the number of bins for the second column
        n_bins_2 = bins[valid_covariates[1]].nunique()
        combined_key = bins[valid_covariates[0]] * n_bins_2 + bins[valid_covariates[1]]
    elif len(bins) == 1:
        combined_key = bins[valid_covariates[0]]
    else:
        combined_key = pd.Series(0, index=df.index)
    
    # Group by the combined key
    groups = {}
    for group_id, group_df in df.groupby(combined_key):
        groups[f"subset_{group_id}"] = group_df

    return groups

def stratify_by_stars(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Fallback: Stratify by repository_star_count quartiles.
    """
    if 'repository_star_count' not in df.columns:
        logger.error("Fallback stratification requires 'repository_star_count' column, which is missing.")
        raise ValueError("Missing 'repository_star_count' column for fallback stratification.")
    
    try:
        # Use q=4 for quartiles
        df['star_quartile'] = pd.qcut(df['repository_star_count'], q=4, labels=False, duplicates='drop')
    except ValueError:
        # If duplicates prevent 4 quartiles, try fewer
        try:
            df['star_quartile'] = pd.qcut(df['repository_star_count'], q=2, labels=False, duplicates='drop')
        except ValueError:
            logger.warning("Could not bin star_count. Using a single bin.")
            df['star_quartile'] = 0
    
    groups = {}
    for group_id, group_df in df.groupby('star_quartile'):
        groups[f"star_subset_{group_id}"] = group_df
    
    return groups

def run_sensitivity_analysis_on_subset(subset_df: pd.DataFrame, treatment_col: str = 'author_type', 
                                      outcome_col: str = 'review_duration', 
                                      alpha: float = 0.05) -> Dict[str, Any]:
    """
    Run the statistical test on a single subset.
    Returns a dict with p-value and significance flag.
    """
    # Filter for the two groups (e.g., 'human' vs 'llm-like' or 'llm-prompt')
    # The exact treatment values depend on the data. We assume 'author_type' or 'generation_source' 
    # has at least two distinct values.
    # For this specific task, we are comparing LLM vs Human.
    
    # Determine the column to use for treatment
    treatment_col_to_use = treatment_col if treatment_col in subset_df.columns else 'generation_source'
    
    if treatment_col_to_use not in subset_df.columns:
        logger.warning(f"Treatment column {treatment_col_to_use} not found in subset. Skipping.")
        return {"p_value": None, "is_significant": False}
    
    # Get unique groups
    groups = subset_df[treatment_col_to_use].dropna().unique()
    if len(groups) < 2:
        logger.warning(f"Subset has fewer than 2 treatment groups ({groups}). Skipping.")
        return {"p_value": None, "is_significant": False}
    
    # We need to define which group is 'treatment' and which is 'control'.
    # Assuming 'human' is control and anything else is treatment.
    control_group = 'human'
    if control_group not in groups:
        # If 'human' is not present, try to find a logical control.
        # Fallback: take the first two groups alphabetically.
        control_group = sorted(groups)[0]
    
    treatment_group = [g for g in groups if g != control_group][0]
    
    control_data = subset_df[subset_df[treatment_col_to_use] == control_group][outcome_col].dropna()
    treatment_data = subset_df[subset_df[treatment_col_to_use] == treatment_group][outcome_col].dropna()
    
    if len(control_data) < 5 or len(treatment_data) < 5:
        logger.warning(f"Subset has too few samples for {treatment_col_to_use}={control_group} ({len(control_data)}) or {treatment_group} ({len(treatment_data)}). Skipping.")
        return {"p_value": None, "is_significant": False}
    
    try:
        result = run_full_analysis(
            control_data=control_data,
            treatment_data=treatment_data,
            alpha=alpha
        )
        return {
            "p_value": result.get('p_value'),
            "is_significant": result.get('is_significant', False)
        }
    except Exception as e:
        logger.warning(f"Statistical test failed on subset: {e}")
        return {"p_value": None, "is_significant": False}

def run_sensitivity_analysis(
    input_path: str,
    config_path: str,
    output_path: str,
    alpha: float = 0.05,
    min_subsets: int = 5,
    consistency_threshold: float = 0.80
) -> Dict[str, Any]:
    """
    Main function to run sensitivity analysis.
    1. Load data.
    2. Stratify by complexity/size.
    3. If < min_subsets, fallback to star_count.
    4. If still < min_subsets, FAIL.
    5. Run test on each subset.
    6. Calculate consistency.
    7. Write output JSON.
    """
    logger.info(f"Starting sensitivity analysis. Input: {input_path}, Config: {config_path}")
    
    # Load data
    df = load_analysis_data(input_path)
    covariates = load_covariate_config(config_path)
    
    # Strategy 1: Complexity/Size
    subsets = {}
    try:
        subsets = stratify_by_complexity_size(df, covariates)
        logger.info(f"Complexity/Size stratification yielded {len(subsets)} subsets.")
    except Exception as e:
        logger.warning(f"Complexity/Size stratification failed: {e}. Falling back to star count.")
    
    # Check subset count
    if len(subsets) < min_subsets:
        logger.info(f"Complexity/Size yielded {len(subsets)} subsets (< {min_subsets}). Fallback to star_count.")
        try:
            subsets = stratify_by_stars(df)
            logger.info(f"Star count stratification yielded {len(subsets)} subsets.")
        except Exception as e:
            logger.error(f"Star count stratification failed: {e}.")
            raise RuntimeError(f"Insufficient data for sensitivity analysis (requires ≥{min_subsets} subsets).")
    
    if len(subsets) < min_subsets:
        logger.error(f"Both stratification methods yielded < {min_subsets} subsets.")
        raise RuntimeError(f"Insufficient data for sensitivity analysis (requires ≥{min_subsets} subsets).")
    
    # Run analysis on each subset
    results = []
    significant_count = 0
    
    for name, subset_df in subsets.items():
        logger.info(f"Analyzing subset: {name} (size: {len(subset_df)})")
        res = run_sensitivity_analysis_on_subset(subset_df, alpha=alpha)
        results.append({
            "subset_name": name,
            "size": len(subset_df),
            "p_value": res["p_value"],
            "is_significant": res["is_significant"]
        })
        
        if res["p_value"] is not None and res["p_value"] < alpha:
            significant_count += 1
    
    total_subsets = len(subsets)
    consistency_ratio = significant_count / total_subsets if total_subsets > 0 else 0.0
    is_consistent = (consistency_ratio >= consistency_threshold) and (total_subsets >= min_subsets)
    
    summary = {
        "total_subsets": total_subsets,
        "significant_count": significant_count,
        "consistency_ratio": consistency_ratio,
        "consistency_threshold": consistency_threshold,
        "consistent": is_consistent,
        "min_subsets_required": min_subsets,
        "alpha": alpha,
        "subset_details": results
    }
    
    # Write output
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Sensitivity analysis complete. Consistent: {is_consistent}. Output: {output_path}")
    return summary

def main():
    """
    Entry point for the sensitivity analysis script.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    config = get_config()
    input_path = config.get('paths', {}).get('merged_features', 'data/processed/merged_features.parquet')
    config_path = config.get('paths', {}).get('covariate_config', 'data/processed/covariate_config.json')
    output_path = config.get('paths', {}).get('sensitivity_summary', 'data/processed/sensitivity_summary.json')
    
    try:
        run_sensitivity_analysis(
            input_path=input_path,
            config_path=config_path,
            output_path=output_path,
            alpha=0.05,
            min_subsets=5,
            consistency_threshold=0.80
        )
        logger.info("Sensitivity analysis completed successfully.")
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()