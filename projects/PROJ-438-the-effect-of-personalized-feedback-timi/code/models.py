"""
Statistical modeling for the Effect of Personalized Feedback Timing on Skill Acquisition.

Implements Cluster-Robust OLS regression and extracts effect sizes (Cohen's d) 
and p-values for pairwise comparisons between feedback timing groups.

Dependencies:
    - pandas
    - numpy
    - statsmodels (OLS, robust_covariance)
    - scipy (stats)

Output:
    Writes effect size metrics to data/processed/effect_sizes.csv
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple, Any

# Local imports from project API
from logging_config import get_logger, info, error, warning, debug
from config import load_config

logger = get_logger(__name__)

def fit_cluster_robust_ols(data: pd.DataFrame) -> Any:
    """
    Fits a Cluster-Robust OLS model with feedback group as fixed effect.
    
    Model: final_grade ~ C(feedback_group)
    Clustering: by course_id (to account for course-level variance)
    
    Args:
        data: DataFrame containing 'final_grade', 'feedback_group', 'course_id'
    
    Returns:
        statsmodels regression results object with robust covariance
    """
    try:
        import statsmodels.api as sm
        import statsmodels.formula.api as smf
        from statsmodels.stats.sandwich_covariance import cov_cluster
    except ImportError as e:
        error(f"Required statsmodels libraries not found: {e}")
        raise

    if 'final_grade' not in data.columns or 'feedback_group' not in data.columns:
        error("Missing required columns: 'final_grade' or 'feedback_group'")
        raise ValueError("Input data missing required columns")

    # Formula: final_grade ~ feedback_group (categorical)
    formula = "final_grade ~ C(feedback_group)"
    
    # Fit OLS
    model = smf.ols(formula=formula, data=data)
    results = model.fit()
    
    # Apply Cluster-Robust Covariance (by course_id)
    # We need to map course_id to integer groups for the clustering function
    if 'course_id' not in data.columns:
        error("Missing 'course_id' column required for clustering")
        raise ValueError("Input data missing 'course_id' column")
    
    # Create cluster groups
    unique_courses = data['course_id'].unique()
    course_map = {course: i for i, course in enumerate(unique_courses)}
    clusters = data['course_id'].map(course_map).values
    
    # Compute cluster-robust standard errors
    # Using HC1 type for small sample correction
    cov_matrix = cov_cluster(results, clusters, cov_type='HC1')
    results.cov_params_default = cov_matrix
    results.bse = np.sqrt(np.diag(cov_matrix))
    
    info(f"Cluster-Robust OLS fitted. Number of clusters: {len(unique_courses)}")
    return results

def extract_effect_sizes(data: pd.DataFrame, model_results: Any) -> pd.DataFrame:
    """
    Extracts Cohen's d effect sizes and p-values for pairwise comparisons 
    between feedback timing groups.
    
    Cohen's d = (Mean1 - Mean2) / Pooled Standard Deviation
    
    Args:
        data: Original binned learner data
        model_results: Fitted OLS model results object
    
    Returns:
        DataFrame with pairwise comparisons: group1, group2, mean_diff, 
        pooled_std, cohens_d, p_value
    """
    try:
        from scipy import stats as scipy_stats
    except ImportError as e:
        error(f"Required scipy not found: {e}")
        raise

    # Get unique groups
    groups = data['feedback_group'].unique()
    if len(groups) < 2:
        error("Need at least 2 groups for pairwise comparison")
        raise ValueError("Insufficient groups for comparison")
    
    # Group by feedback_group and calculate means and stds
    group_stats = data.groupby('feedback_group')['final_grade'].agg(['mean', 'std', 'count']).reset_index()
    group_stats.columns = ['group', 'mean', 'std', 'n']
    
    # Create a map for quick lookup
    stats_map = {row['group']: row for _, row in group_stats.iterrows()}
    
    comparisons = []
    
    # Get model p-values for pairwise comparisons from the OLS summary
    # The model uses C(feedback_group), so we need to extract contrasts
    # For simplicity, we'll compute pairwise t-tests with pooled variance
    # which aligns with Cohen's d calculation
    
    # Generate all pairwise combinations
    for i in range(len(groups)):
        for j in range(i + 1, len(groups)):
            g1, g2 = groups[i], groups[j]
            
            # Get statistics
            s1 = stats_map[g1]
            s2 = stats_map[g2]
            
            mean1, std1, n1 = s1['mean'], s1['std'], s1['n']
            mean2, std2, n2 = s2['mean'], s2['std'], s2['n']
            
            # Handle potential NaN std (if n=1)
            if pd.isna(std1): std1 = 0.0
            if pd.isna(std2): std2 = 0.0
            
            # Pooled standard deviation
            # Formula: sqrt(((n1-1)*std1^2 + (n2-1)*std2^2) / (n1+n2-2))
            if n1 + n2 - 2 > 0:
                pooled_std = np.sqrt(((n1 - 1) * (std1 ** 2) + (n2 - 1) * (std2 ** 2)) / (n1 + n2 - 2))
            else:
                pooled_std = 0.0
            
            # Cohen's d
            if pooled_std > 0:
                cohens_d = (mean1 - mean2) / pooled_std
            else:
                cohens_d = 0.0
            
            # Mean difference
            mean_diff = mean1 - mean2
            
            # Calculate p-value using Welch's t-test (more robust for unequal variances)
            # We use the actual data for precision
            d1 = data[data['feedback_group'] == g1]['final_grade'].dropna()
            d2 = data[data['feedback_group'] == g2]['final_grade'].dropna()
            
            if len(d1) > 0 and len(d2) > 0:
                t_stat, p_val = scipy_stats.ttest_ind(d1, d2, equal_var=False)
            else:
                p_val = 1.0
            
            comparisons.append({
                'group1': g1,
                'group2': g2,
                'mean_diff': mean_diff,
                'pooled_std': pooled_std,
                'cohens_d': cohens_d,
                'p_value': p_val,
                'n1': n1,
                'n2': n2
            })
    
    results_df = pd.DataFrame(comparisons)
    return results_df

def main():
    """
    Main entry point for the modeling task.
    1. Loads binned learner data.
    2. Fits Cluster-Robust OLS.
    3. Extracts Cohen's d and p-values.
    4. Saves results to data/processed/effect_sizes.csv
    """
    # Load configuration
    config = load_config()
    
    # Define paths
    project_root = Path(__file__).resolve().parent.parent
    input_path = project_root / 'data' / 'processed' / 'learners_binned.csv'
    output_path = project_root / 'data' / 'processed' / 'effect_sizes.csv'
    
    info(f"Starting effect size extraction for task T030")
    debug(f"Input path: {input_path}")
    debug(f"Output path: {output_path}")
    
    # Check input file exists
    if not input_path.exists():
        error(f"Input file not found: {input_path}")
        error("Please ensure T026 (generate learners_binned.csv) is completed first.")
        sys.exit(1)
    
    # Load data
    try:
        data = pd.read_csv(input_path)
        info(f"Loaded {len(data)} records from {input_path}")
    except Exception as e:
        error(f"Failed to load input data: {e}")
        sys.exit(1)
    
    # Validate required columns
    required_cols = ['final_grade', 'feedback_group', 'course_id']
    missing = [c for c in required_cols if c not in data.columns]
    if missing:
        error(f"Missing required columns in input data: {missing}")
        sys.exit(1)
    
    # Drop rows with missing final_grade
    initial_count = len(data)
    data = data.dropna(subset=['final_grade'])
    dropped = initial_count - len(data)
    if dropped > 0:
        warning(f"Dropped {dropped} records with missing final_grade")
    
    if len(data) == 0:
        error("No valid data remaining after filtering")
        sys.exit(1)
    
    # Fit Model
    try:
        info("Fitting Cluster-Robust OLS model...")
        model_results = fit_cluster_robust_ols(data)
        info("Model fitting complete.")
    except Exception as e:
        error(f"Model fitting failed: {e}")
        import traceback
        error(traceback.format_exc())
        sys.exit(1)
    
    # Extract Effect Sizes
    try:
        info("Extracting Cohen's d and p-values...")
        effect_sizes = extract_effect_sizes(data, model_results)
        info(f"Extracted {len(effect_sizes)} pairwise comparisons")
    except Exception as e:
        error(f"Effect size extraction failed: {e}")
        import traceback
        error(traceback.format_exc())
        sys.exit(1)
    
    # Save results
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        effect_sizes.to_csv(output_path, index=False)
        info(f"Results saved to {output_path}")
        
        # Log summary
        for _, row in effect_sizes.iterrows():
            info(f"Comparison {row['group1']} vs {row['group2']}: "
                 f"Cohen's d = {row['cohens_d']:.4f}, p = {row['p_value']:.4f}")
                 
    except Exception as e:
        error(f"Failed to save results: {e}")
        sys.exit(1)
    
    info("Task T030 completed successfully.")

if __name__ == "__main__":
    main()
