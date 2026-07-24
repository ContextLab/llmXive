import os
import sys
import json
import yaml
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from scipy import stats
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.formula.api import ols

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/analysis.log')
    ]
)
logger = logging.getLogger(__name__)

def load_config(config_path='code/config.yaml'):
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def validate_metadata(metadata_df):
    """
    Check for columns representing paired pre/post fatigue ratings.
    Returns:
        str: 'paired', 'cross_sectional', or 'none'
        dict: validation details
    """
    # Define possible column names for fatigue ratings
    pre_fatigue_cols = ['pre_fatigue', 'fatigue_pre', 'baseline_fatigue']
    post_fatigue_cols = ['post_fatigue', 'fatigue_post', 'end_fatigue']

    # Find matching columns
    available_pre = [col for col in pre_fatigue_cols if col in metadata_df.columns]
    available_post = [col for col in post_fatigue_cols if col in metadata_df.columns]

    validation_info = {
        'available_pre_columns': available_pre,
        'available_post_columns': available_post,
        'has_baseline_fatigue': any(col in metadata_df.columns for col in ['baseline_fatigue', 'pre_fatigue', 'fatigue_pre']),
        'has_baseline_complexity': False, # Will be set later
        'participant_count': len(metadata_df)
    }

    if available_pre and available_post:
        logger.info(f"Found paired data: pre={available_pre[0]}, post={available_post[0]}")
        return 'paired', validation_info
    elif validation_info['has_baseline_fatigue']:
        logger.info("Found baseline fatigue data for cross-sectional analysis")
        return 'cross_sectional', validation_info
    else:
        logger.error("No valid fatigue rating columns found")
        return 'none', validation_info

def run_benjamini_hochberg(p_values, alpha=0.05):
    """
    Apply Benjamini-Hochberg correction for multiple comparisons.
    """
    rejected, p_corrected, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')
    return rejected, p_corrected

def run_correlation_analysis(lzc_df, pe_df, metadata_df, mode='paired'):
    """
    Run correlation analysis based on mode.
    
    Args:
        lzc_df: DataFrame with LZC metrics
        pe_df: DataFrame with PE metrics
        metadata_df: DataFrame with fatigue ratings
        mode: 'paired' or 'cross_sectional'
        
    Returns:
        dict: Analysis results
    """
    results = {
        'mode': mode,
        'correlations': [],
        'excluded_count': 0
    }

    # Merge complexity metrics with metadata
    # Assuming lzc_df and pe_df have 'participant_id' and 'channel' columns
    # We need to aggregate complexity metrics per participant (e.g., mean across channels)
    
    if mode == 'paired':
        # Identify pre and post columns
        pre_col = next((col for col in ['pre_fatigue', 'fatigue_pre', 'baseline_fatigue'] if col in metadata_df.columns), None)
        post_col = next((col for col in ['post_fatigue', 'fatigue_post', 'end_fatigue'] if col in metadata_df.columns), None)
        
        if not pre_col or not post_col:
            raise ValueError("Required paired fatigue columns not found")
        
        # Calculate delta fatigue
        metadata_df['fatigue_delta'] = metadata_df[post_col] - metadata_df[pre_col]
        
        # Calculate delta complexity (mean across channels)
        lzc_mean = lzc_df.groupby('participant_id')['lzc_value'].mean().reset_index()
        lzc_mean.rename(columns={'lzc_value': 'lzc_mean'}, inplace=True)
        
        pe_mean = pe_df.groupby('participant_id')['pe_value'].mean().reset_index()
        pe_mean.rename(columns={'pe_value': 'pe_mean'}, inplace=True)
        
        # Merge with metadata
        analysis_df = metadata_df.merge(lzc_mean, on='participant_id', how='inner')
        analysis_df = analysis_df.merge(pe_mean, on='participant_id', how='inner')
        
        # Exclude participants with missing fatigue ratings
        initial_count = len(analysis_df)
        analysis_df = analysis_df.dropna(subset=['fatigue_delta', 'lzc_mean', 'pe_mean'])
        results['excluded_count'] = initial_count - len(analysis_df)
        
        if len(analysis_df) == 0:
            logger.error("No participants with complete data for paired analysis")
            return results
        
        # Calculate correlations
        lzc_corr = stats.pearsonr(analysis_df['lzc_mean'], analysis_df['fatigue_delta'])
        pe_corr = stats.pearsonr(analysis_df['pe_mean'], analysis_df['fatigue_delta'])
        
        results['correlations'].append({
            'metric': 'LZC',
            'r': lzc_corr.statistic,
            'p': lzc_corr.pvalue,
            'n': len(analysis_df)
        })
        results['correlations'].append({
            'metric': 'PE',
            'r': pe_corr.statistic,
            'p': pe_corr.pvalue,
            'n': len(analysis_df)
        })
        
        # Optional ANCOVA
        try:
            model = ols('fatigue_post ~ fatigue_pre + lzc_mean', data=analysis_df).fit()
            results['ancova'] = {
                'lzc_coef': model.params['lzc_mean'],
                'lzc_p': model.pvalues['lzc_mean'],
                'r_squared': model.rsquared
            }
        except Exception as e:
            logger.warning(f"ANCOVA failed: {e}")
            
    elif mode == 'cross_sectional':
        # Use baseline fatigue
        baseline_col = next((col for col in ['baseline_fatigue', 'pre_fatigue', 'fatigue_pre'] if col in metadata_df.columns), None)
        
        if not baseline_col:
            raise ValueError("Required baseline fatigue column not found")
        
        # Calculate mean complexity per participant
        lzc_mean = lzc_df.groupby('participant_id')['lzc_value'].mean().reset_index()
        lzc_mean.rename(columns={'lzc_value': 'lzc_mean'}, inplace=True)
        
        pe_mean = pe_df.groupby('participant_id')['pe_value'].mean().reset_index()
        pe_mean.rename(columns={'pe_value': 'pe_mean'}, inplace=True)
        
        # Merge with metadata
        analysis_df = metadata_df.merge(lzc_mean, on='participant_id', how='inner')
        analysis_df = analysis_df.merge(pe_mean, on='participant_id', how='inner')
        
        # Exclude participants with missing fatigue ratings
        initial_count = len(analysis_df)
        analysis_df = analysis_df.dropna(subset=[baseline_col, 'lzc_mean', 'pe_mean'])
        results['excluded_count'] = initial_count - len(analysis_df)
        
        if len(analysis_df) == 0:
            logger.error("No participants with complete data for cross-sectional analysis")
            return results
        
        # Calculate correlations
        lzc_corr = stats.pearsonr(analysis_df['lzc_mean'], analysis_df[baseline_col])
        pe_corr = stats.pearsonr(analysis_df['pe_mean'], analysis_df[baseline_col])
        
        results['correlations'].append({
            'metric': 'LZC',
            'r': lzc_corr.statistic,
            'p': lzc_corr.pvalue,
            'n': len(analysis_df)
        })
        results['correlations'].append({
            'metric': 'PE',
            'r': pe_corr.statistic,
            'p': pe_corr.pvalue,
            'n': len(analysis_df)
        })
    
    return results

def calculate_vif(df, feature_cols):
    """
    Calculate Variance Inflation Factor for collinearity diagnostics.
    """
    X = df[feature_cols].values
    vif_data = []
    for i, col in enumerate(feature_cols):
        vif = variance_inflation_factor(X, i)
        vif_data.append({'feature': col, 'vif': vif})
        if vif >= 5:
            logger.warning(f"High collinearity detected for {col}: VIF = {vif:.2f}")
    return pd.DataFrame(vif_data)

def main():
    """Main entry point for analysis pipeline."""
    logger.info("Starting analysis pipeline.")
    
    # Load configuration
    config = load_config()
    
    # Define paths
    lzc_path = Path('data/processed/lzc_metrics.csv')
    pe_path = Path('data/processed/pe_metrics.csv')
    metadata_path = Path('data/processed/metadata.csv')
    output_dir = Path('data/analysis')
    output_dir.mkdir(exist_ok=True)
    
    # Check for required input files
    if not lzc_path.exists():
        logger.error(f"Complexity metrics file not found: {lzc_path}")
        sys.exit(1)
    if not pe_path.exists():
        logger.error(f"PE metrics file not found: {pe_path}")
        sys.exit(1)
    if not metadata_path.exists():
        logger.error(f"Metadata file not found: {metadata_path}")
        sys.exit(1)
    
    # Load data
    lzc_df = pd.read_csv(lzc_path)
    pe_df = pd.read_csv(pe_path)
    metadata_df = pd.read_csv(metadata_path)
    
    # Validate metadata for fatigue ratings
    mode, validation_info = validate_metadata(metadata_df)
    
    if mode == 'none':
        # Write validation report and exit
        report = {
            'status': 'fail',
            'message': 'Required fatigue rating columns missing',
            'available_variables': validation_info['available_pre_columns'] + validation_info['available_post_columns'],
            'participant_count': validation_info['participant_count']
        }
        with open('data/analysis/validation_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        logger.error("Validation failed: No valid fatigue ratings found")
        sys.exit(1)
    
    # Run correlation analysis
    logger.info(f"Running {mode} correlation analysis")
    results = run_correlation_analysis(lzc_df, pe_df, metadata_df, mode=mode)
    
    # Save correlation results
    results_path = output_dir / 'correlation_results.json'
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Correlation results saved to {results_path}")
    
    # Apply Benjamini-Hochberg correction if we have multiple tests
    if results['correlations']:
        p_values = [corr['p'] for corr in results['correlations']]
        rejected, p_corrected = run_benjamini_hochberg(p_values)
        
        # Update results with corrected p-values
        for i, corr in enumerate(results['correlations']):
            corr['p_corrected'] = p_corrected[i]
            corr['significant'] = rejected[i]
        
        # Save BH corrected results
        bh_path = output_dir / 'bh_corrected_results.json'
        with open(bh_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Benjamini-Hochberg corrected results saved to {bh_path}")
    
    # Calculate VIF if we have multiple metrics
    if mode == 'paired' and 'ancova' in results:
        # Prepare data for VIF
        lzc_mean = lzc_df.groupby('participant_id')['lzc_value'].mean().reset_index()
        pe_mean = pe_df.groupby('participant_id')['pe_value'].mean().reset_index()
        
        analysis_df = metadata_df.merge(lzc_mean, on='participant_id', how='inner')
        analysis_df = analysis_df.merge(pe_mean, on='participant_id', how='inner')
        analysis_df = analysis_df.dropna(subset=['lzc_value', 'pe_value'])
        
        if len(analysis_df) > 0:
            vif_df = calculate_vif(analysis_df, ['lzc_value', 'pe_value'])
            vif_path = output_dir / 'vif_report.csv'
            vif_df.to_csv(vif_path, index=False)
            logger.info(f"VIF report saved to {vif_path}")
    
    logger.info("Analysis pipeline completed successfully.")

if __name__ == '__main__':
    main()
