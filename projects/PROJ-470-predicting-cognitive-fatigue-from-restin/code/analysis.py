"""
Analysis module for correlating complexity metrics with fatigue scores.
Implements Pearson/Spearman correlation per FR-004.
"""
import os
import sys
import json
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from scipy import stats

def load_config(config_path="code/config.yaml"):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_logger(name):
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def validate_metadata(metadata_path):
    """Validate metadata has required fatigue columns."""
    if not os.path.exists(metadata_path):
        return False, "Metadata file not found."
    
    df = pd.read_csv(metadata_path)
    # Check for paired or baseline fatigue columns
    paired_cols = ['pre_fatigue', 'fatigue_pre', 'baseline_fatigue', 
                   'post_fatigue', 'fatigue_post', 'end_fatigue']
    baseline_cols = ['baseline_fatigue', 'fatigue_baseline']
    
    has_paired = any(col in df.columns for col in paired_cols)
    has_baseline = any(col in df.columns for col in baseline_cols)
    
    if not has_paired and not has_baseline:
        return False, "No fatigue rating columns found in metadata."
    
    return True, "Valid."

def run_correlation_analysis(lzc_path, metadata_path, pe_path=None):
    """Run Pearson/Spearman correlation between complexity and fatigue.
    
    Handles paired (delta) analysis if pre/post ratings exist,
    otherwise falls back to cross-sectional (baseline) analysis.
    Excludes participants with missing fatigue ratings.
    """
    if not os.path.exists(lzc_path):
        raise FileNotFoundError(f"Features file not found: {lzc_path}")
    
    logger = setup_logger("analysis")
    
    # Load complexity metrics
    lzc_df = pd.read_csv(lzc_path)
    
    # Load metadata
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    metadata = pd.read_csv(metadata_path)
    
    # Identify fatigue columns
    paired_cols = ['pre_fatigue', 'fatigue_pre', 'baseline_fatigue', 
                   'post_fatigue', 'fatigue_post', 'end_fatigue']
    baseline_cols = ['baseline_fatigue', 'fatigue_baseline']
    
    # Determine analysis mode
    has_paired = any(col in metadata.columns for col in paired_cols)
    has_baseline = any(col in metadata.columns for col in baseline_cols)
    
    if not has_paired and not has_baseline:
        raise ValueError("No valid fatigue columns found for analysis.")
    
    # Prepare fatigue data
    if has_paired:
        # Find pre and post columns
        pre_col = next((c for c in paired_cols if c in metadata.columns and 'pre' in c.lower()), None)
        post_col = next((c for c in paired_cols if c in metadata.columns and 'post' in c.lower()), None)
        
        if not pre_col or not post_col:
            # Fallback to any paired-looking columns
            pre_candidates = [c for c in metadata.columns if 'pre' in c.lower()]
            post_candidates = [c for c in metadata.columns if 'post' in c.lower()]
            if pre_candidates and post_candidates:
                pre_col = pre_candidates[0]
                post_col = post_candidates[0]
            else:
                raise ValueError("Could not identify paired fatigue columns.")
        
        # Merge with metadata to get fatigue scores
        merged = lzc_df.merge(metadata[['participant_id', pre_col, post_col]], on='participant_id', how='inner')
        
        # Exclude participants with missing ratings
        initial_count = len(merged)
        merged = merged.dropna(subset=[pre_col, post_col])
        excluded_count = initial_count - len(merged)
        
        if excluded_count > 0:
            logger.warning(f"Excluded {excluded_count} participants with missing fatigue ratings.")
            # Log exclusions
            excluded_participants = lzc_df[~lzc_df['participant_id'].isin(merged['participant_id'])]['participant_id'].tolist()
            exclusion_log_path = "data/processed/analysis_exclusions.csv"
            Path(exclusion_log_path).parent.mkdir(parents=True, exist_ok=True)
            exclusion_df = pd.DataFrame({
                'participant_id': excluded_participants,
                'exclusion_reason': 'missing_paired_fatigue_ratings',
                'timestamp': pd.Timestamp.now().isoformat()
            })
            exclusion_df.to_csv(exclusion_log_path, index=False)
        
        if len(merged) == 0:
            raise ValueError("No participants with complete paired fatigue data after exclusion.")
        
        # Calculate delta fatigue
        merged['fatigue_delta'] = merged[post_col] - merged[pre_col]
        
        # Calculate complexity metrics per participant (average across channels)
        complexity_avg = merged.groupby('participant_id')['lzc_value'].mean().reset_index()
        complexity_avg.columns = ['participant_id', 'avg_lzc']
        
        # Merge back
        analysis_df = complexity_avg.merge(merged[['participant_id', 'fatigue_delta']].drop_duplicates(), on='participant_id')
        
        # Run correlation
        if len(analysis_df) < 3:
            raise ValueError("Insufficient data for correlation analysis.")
        
        r, p = stats.pearsonr(analysis_df['avg_lzc'], analysis_df['fatigue_delta'])
        method = "Pearson (Paired Delta)"
        
    else:
        # Cross-sectional analysis
        baseline_col = next((c for c in baseline_cols if c in metadata.columns), None)
        if not baseline_col:
            raise ValueError("Could not identify baseline fatigue column.")
        
        merged = lzc_df.merge(metadata[['participant_id', baseline_col]], on='participant_id', how='inner')
        
        # Exclude participants with missing ratings
        initial_count = len(merged)
        merged = merged.dropna(subset=[baseline_col])
        excluded_count = initial_count - len(merged)
        
        if excluded_count > 0:
            logger.warning(f"Excluded {excluded_count} participants with missing fatigue ratings.")
            exclusion_log_path = "data/processed/analysis_exclusions.csv"
            Path(exclusion_log_path).parent.mkdir(parents=True, exist_ok=True)
            excluded_participants = lzc_df[~lzc_df['participant_id'].isin(merged['participant_id'])]['participant_id'].tolist()
            exclusion_df = pd.DataFrame({
                'participant_id': excluded_participants,
                'exclusion_reason': 'missing_baseline_fatigue_rating',
                'timestamp': pd.Timestamp.now().isoformat()
            })
            exclusion_df.to_csv(exclusion_log_path, index=False)
        
        if len(merged) == 0:
            raise ValueError("No participants with baseline fatigue data after exclusion.")
        
        # Calculate complexity metrics per participant (average across channels)
        complexity_avg = merged.groupby('participant_id')['lzc_value'].mean().reset_index()
        complexity_avg.columns = ['participant_id', 'avg_lzc']
        
        # Merge back
        analysis_df = complexity_avg.merge(merged[['participant_id', baseline_col]].drop_duplicates(), on='participant_id')
        analysis_df.columns = ['participant_id', 'avg_lzc', 'baseline_fatigue']
        
        # Run correlation
        if len(analysis_df) < 3:
            raise ValueError("Insufficient data for correlation analysis.")
        
        r, p = stats.pearsonr(analysis_df['avg_lzc'], analysis_df['baseline_fatigue'])
        method = "Pearson (Cross-Sectional)"
    
    # Prepare results
    results = {
        'method': method,
        'correlation_coefficient': float(r),
        'p_value': float(p),
        'n_participants': len(analysis_df),
        'excluded_count': excluded_count if 'excluded_count' in locals() else 0,
        'interpretation': 'associational'
    }
    
    return results

def run_benjamini_hochberg(p_values, alpha=0.05):
    """Apply BH correction for multiple comparisons."""
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_indices]
    
    adjusted_p = np.zeros(n)
    for i, p in enumerate(sorted_p):
        adjusted_p[i] = p * n / (i + 1)
    
    adjusted_p = np.minimum.accumulate(adjusted_p[::-1])[::-1]
    adjusted_p = np.minimum(adjusted_p, 1.0)
    
    return {
        'original_p': p_values,
        'adjusted_p': adjusted_p.tolist(),
        'significant': (adjusted_p <= alpha).tolist()
    }

def calculate_vif(data):
    """Calculate Variance Inflation Factor."""
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    from statsmodels.tools.tools import add_constant
    
    if len(data.columns) < 2:
        return {}
    
    X = add_constant(data)
    vif_data = {}
    for i, col in enumerate(X.columns):
        if col != 'const':
            vif_data[col] = variance_inflation_factor(X.values, i)
    
    return vif_data

def main():
    logger = setup_logger("analysis")
    logger.info("Starting analysis pipeline.")

    lzc_path = "data/processed/lzc_metrics.csv"
    metadata_path = "data/raw/metadata.csv"

    if not os.path.exists(lzc_path):
        logger.error(f"Features file not found: {lzc_path}")
        sys.exit(1)

    try:
        # Validate metadata
        valid, msg = validate_metadata(metadata_path)
        if not valid:
            logger.error(f"Metadata validation failed: {msg}")
            # Write validation report
            report = {
                'status': 'fail',
                'message': msg,
                'timestamp': pd.Timestamp.now().isoformat()
            }
            with open('validation_report.json', 'w') as f:
                json.dump(report, f)
            sys.exit(1)

        # Run analysis
        result = run_correlation_analysis(lzc_path, metadata_path)
        logger.info(f"Analysis complete: {result}")
        
        # Save results
        output_path = "data/analysis/correlation_results.json"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
            
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        # Write error to validation report
        report = {
            'status': 'error',
            'message': str(e),
            'timestamp': pd.Timestamp.now().isoformat()
        }
        with open('validation_report.json', 'w') as f:
            json.dump(report, f)
        sys.exit(1)

if __name__ == "__main__":
    main()
