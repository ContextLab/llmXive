import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from scipy import stats

from utils.config import get_config
from analysis.significance import check_significance

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_analysis_data(input_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load the analysis results containing review duration and author type.
    Expected columns: ['review_duration', 'author_type', 'repo_stars']
    """
    if input_path is None:
        config = get_config()
        input_path = config.get('paths', {}).get('analysis_results', 'data/processed/analysis_results.parquet')
    
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Analysis results file not found: {input_path}")
    
    logger.info(f"Loading analysis data from {input_path}")
    df = pd.read_parquet(path)
    
    required_cols = {'review_duration', 'author_type', 'repo_stars'}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Missing required columns in analysis results: {missing}")
    
    return df

def stratify_by_stars(df: pd.DataFrame, n_strata: int = 5) -> List[pd.DataFrame]:
    """
    Stratify the dataframe into exactly n_strata subsets based on repo_stars quartiles.
    Returns a list of DataFrames, one for each stratum.
    """
    if n_strata != 5:
        logger.warning(f"Requested {n_strata} strata, but specification requires exactly 5. Using 5.")
        n_strata = 5

    # Create quantile-based bins. 
    # We use 'qcut' to ensure roughly equal-sized groups based on star counts.
    # If there are not enough unique values, we fall back to equal-width bins or a warning.
    try:
        df['star_quartile'] = pd.qcut(df['repo_stars'], q=n_strata, labels=False, duplicates='drop')
    except ValueError:
        # Fallback if qcut fails due to insufficient unique values
        logger.warning("qcut failed (insufficient unique values), using equal-width bins.")
        df['star_quartile'] = pd.cut(df['repo_stars'], bins=n_strata, labels=False, include_lowest=True)
    
    unique_quartiles = sorted(df['star_quartile'].unique())
    strata = []
    
    # Ensure we have exactly 5 strata. If qcut produced fewer due to duplicates,
    # we might need to handle this, but the task requires checking consistency across
    # "exactly 5 subsets". We will iterate over the available unique quartiles.
    # If fewer than 5 exist, we still process what we have, but the consistency check
    # will be based on the actual number of subsets found.
    # However, the spec says "exactly 5". We will force 5 bins if possible, 
    # or warn if the data cannot support 5 distinct groups.
    
    if len(unique_quartiles) < n_strata:
        logger.warning(f"Data only supports {len(unique_quartiles)} distinct star strata, not {n_strata}.")
    
    for i in range(n_strata):
        subset = df[df['star_quartile'] == i].copy()
        if not subset.empty:
            strata.append(subset)
        else:
            # If a bin is empty, we might skip it or handle it. 
            # For the consistency check, we usually need valid subsets.
            # We'll log and continue.
            logger.warning(f"Stratum {i} is empty.")
    
    return strata

def run_sensitivity_analysis_on_subset(subset: pd.DataFrame, author_col: str = 'author_type', 
                                       outcome_col: str = 'review_duration', 
                                       alpha: float = 0.05) -> Optional[Dict[str, Any]]:
    """
    Run a statistical test (t-test or Mann-Whitney U) on a single subset.
    Returns a dict with p-value and significance flag, or None if subset is invalid.
    """
    if subset.empty:
        return None

    # Group by author_type
    groups = subset.groupby(author_col)[outcome_col].apply(list).to_dict()
    
    # We expect 'human' and 'llm-like'
    if 'human' not in groups or 'llm-like' not in groups:
        logger.warning("Subset does not contain both 'human' and 'llm-like' groups.")
        return None
    
    human_data = np.array(groups['human'])
    llm_data = np.array(groups['llm-like'])
    
    if len(human_data) < 2 or len(llm_data) < 2:
        logger.warning("One of the groups has fewer than 2 samples. Cannot run test.")
        return None

    # Check normality (Shapiro-Wilk)
    # Note: Shapiro-Wilk is sensitive to sample size. For large N, it often rejects normality.
    # We'll use a pragmatic approach: if p > 0.05 for both, assume normal.
    try:
        _, p_human = stats.shapiro(human_data)
        _, p_llm = stats.shapiro(llm_data)
    except ValueError:
        # Shapiro-Wilk fails if n > 5000 in some scipy versions, or n < 3
        # Fallback to non-parametric if we can't test
        p_human, p_llm = 0.0, 0.0 

    normal_human = p_human > alpha
    normal_llm = p_llm > alpha

    if normal_human and normal_llm:
        # T-test
        stat, p_val = stats.ttest_ind(human_data, llm_data, equal_var=False) # Welch's t-test
    else:
        # Mann-Whitney U
        stat, p_val = stats.mannwhitneyu(human_data, llm_data, alternative='two-sided')

    is_significant = check_significance(p_val, alpha)
    
    return {
        "p_value": float(p_val),
        "is_significant": is_significant,
        "test_used": "t-test" if (normal_human and normal_llm) else "mann-whitney-u"
    }

def run_sensitivity_analysis(input_path: Optional[str] = None, 
                             output_path: Optional[str] = None,
                             alpha: float = 0.05,
                             consistency_threshold: float = 0.80) -> Dict[str, Any]:
    """
    Main function to run sensitivity analysis across star-count strata.
    Checks if p < 0.05 in >= 80% of the subsets.
    
    Args:
        input_path: Path to the analysis results parquet file.
        output_path: Path to write the sensitivity_summary.json.
        alpha: Significance level.
        consistency_threshold: Required proportion of significant results (default 0.80).
    
    Returns:
        Dict containing the consistency check results.
    """
    df = load_analysis_data(input_path)
    strata = stratify_by_stars(df)
    
    logger.info(f"Stratified data into {len(strata)} subsets.")
    
    if len(strata) == 0:
        raise ValueError("No valid strata found for sensitivity analysis.")

    results = []
    significant_count = 0
    
    for i, subset in enumerate(strata):
        logger.info(f"Processing stratum {i+1}/{len(strata)}...")
        res = run_sensitivity_analysis_on_subset(subset, alpha=alpha)
        
        if res:
            res['stratum_index'] = i
            results.append(res)
            if res['is_significant']:
                significant_count += 1
        else:
            # If a subset yields no result (e.g., empty or invalid), 
            # we might count it as non-significant or skip it. 
            # The spec says "check if p < 0.05 in >= 80% of exactly 5 subsets".
            # If a subset is invalid, it cannot produce a p < 0.05. 
            # We will treat it as a failure to meet the condition for that subset.
            results.append({
                'stratum_index': i,
                'p_value': None,
                'is_significant': False,
                'test_used': 'skipped',
                'reason': 'Invalid subset'
            })
    
    total_subsets = len(results)
    if total_subsets == 0:
        raise ValueError("No valid results from any stratum.")

    proportion_significant = significant_count / total_subsets
    consistent = proportion_significant >= consistency_threshold
    
    summary = {
        "total_subsets": total_subsets,
        "significant_count": significant_count,
        "proportion_significant": float(proportion_significant),
        "consistency_threshold": consistency_threshold,
        "consistent": consistent,
        "alpha": alpha,
        "subset_results": results
    }
    
    if output_path is None:
        config = get_config()
        output_path = config.get('paths', {}).get('sensitivity_summary', 'data/processed/sensitivity_summary.json')
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Sensitivity summary written to {output_path}")
    logger.info(f"Consistency Check: {significant_count}/{total_subsets} ({proportion_significant:.2%}) significant. "
                f"Threshold: {consistency_threshold}. Result: {'CONSISTENT' if consistent else 'INCONSISTENT'}")
    
    return summary

def main():
    """Entry point for the sensitivity analysis script."""
    config = get_config()
    input_path = config.get('paths', {}).get('analysis_results', 'data/processed/analysis_results.parquet')
    output_path = config.get('paths', {}).get('sensitivity_summary', 'data/processed/sensitivity_summary.json')
    
    try:
        result = run_sensitivity_analysis(input_path=input_path, output_path=output_path)
        if not result['consistent']:
            logger.warning("Sensitivity analysis failed consistency check.")
            # Do not exit here, as this function is often called by main.py which handles the gate.
            # But for standalone execution, we might want to warn loudly.
        return result
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()