import os
import csv
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.anova import AnovaRM
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants for paths (matching project structure)
DATA_PROCESSED_DIR = "data/processed"
AGGREGATED_FILE = os.path.join(DATA_PROCESSED_DIR, "energy_results_aggregated.csv")
STATS_REPORT_FILE = os.path.join(DATA_PROCESSED_DIR, "stats_report.csv")

# Model parameter counts (in millions) - defined in config, hardcoding here for analysis independence
# GPT2-small: 117M, CodeBERT-base: 125M, StarCoder-1B: 1000M (approx 1B)
MODEL_PARAMS_M = {
    "gpt2-small": 117,
    "codert-base": 125,
    "starcoder-1b": 1000
}

def load_data(filepath=None):
    """Load the aggregated energy results from CSV."""
    if filepath is None:
        filepath = AGGREGATED_FILE
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file not found: {filepath}. Ensure US1 inference and aggregation tasks are complete.")
    
    df = pd.read_csv(filepath)
    logger.info(f"Loaded data from {filepath}: {len(df)} rows")
    return df

def run_anova(df):
    """
    Perform Repeated-Measures ANOVA with problem_id as blocking factor.
    """
    logger.info("Running Repeated-Measures ANOVA...")
    
    # Ensure necessary columns exist
    required_cols = ['model_id', 'problem_id', 'energy_kwh']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column '{col}' in data for ANOVA")
    
    # Prepare data for statsmodels
    # AnovaRM expects: dependent, subject, within
    # dependent: energy_kwh
    # subject: problem_id (each problem is a subject measured across models)
    # within: model_id (the repeated measure)
    
    try:
        anova_rm = AnovaRM(df, depvar='energy_kwh', subject='problem_id', within=['model_id'])
        res = anova_rm.fit()
        logger.info("ANOVA Results:\n%s", res)
        return res
    except Exception as e:
        logger.error(f"ANOVA failed: {e}")
        raise

def run_tukey(df):
    """
    Perform post-hoc Tukey HSD test.
    """
    logger.info("Running Tukey HSD post-hoc test...")
    
    # Prepare data: group by model_id
    groups = df.groupby('model_id')['energy_kwh'].apply(list).to_dict()
    
    # Flatten for scipy
    model_labels = list(groups.keys())
    data_arrays = [np.array(groups[m]) for m in model_labels]
    
    if len(data_arrays) < 2:
        logger.warning("Not enough groups for Tukey HSD")
        return None
    
    try:
        # Use pairwise_tukeyhsd from statsmodels if available, else fallback to scipy if simple
        from statsmodels.stats.multicomp import pairwise_tukeyhsd
        
        # Flatten arrays and create labels
        all_values = np.concatenate(data_arrays)
        all_labels = np.concatenate([np.full(len(data_arrays[i]), model_labels[i]) for i in range(len(model_labels))])
        
        tukey = pairwise_tukeyhsd(endog=all_values, groups=all_labels, alpha=0.05)
        logger.info("Tukey HSD Results:\n%s", tukey)
        return tukey
    except Exception as e:
        logger.error(f"Tukey HSD failed: {e}")
        raise

def run_regression(df):
    """
    Implement descriptive linear regression: Parameter Count vs Energy/Token.
    Framed as observational analysis (FR-005, FR-008).
    
    Calculates Energy per Token (Joules) for each model, then regresses
    against Parameter Count (Millions).
    """
    logger.info("Running descriptive linear regression (Parameters vs Energy/Token)...")
    
    # 1. Calculate Energy per Token (Joules) for each model
    # Formula: (energy_kwh * 3,600,000) / tokens_generated
    df['energy_joules'] = df['energy_kwh'] * 3_600_000
    
    # Aggregate by model to get mean energy per token
    model_stats = df.groupby('model_id').agg({
        'energy_joules': 'mean',
        'tokens_generated': 'mean'
    }).reset_index()
    
    model_stats['energy_per_token_j'] = model_stats['energy_joules'] / model_stats['tokens_generated']
    
    # Map model_id to parameter count (Millions)
    # Note: Ensure model_ids in data match keys in MODEL_PARAMS_M
    model_stats['params_m'] = model_stats['model_id'].map(MODEL_PARAMS_M)
    
    if model_stats['params_m'].isnull().any():
        unknown_models = model_stats[model_stats['params_m'].isnull()]['model_id'].unique()
        logger.warning(f"Unknown model parameters for: {unknown_models}. Regression may be incomplete.")
    
    # Drop rows with missing parameter counts
    clean_stats = model_stats.dropna(subset=['params_m', 'energy_per_token_j'])
    
    if len(clean_stats) < 2:
        logger.error("Insufficient data points for regression (need at least 2 models with known params).")
        return None, None
    
    x = clean_stats['params_m'].values
    y = clean_stats['energy_per_token_j'].values
    
    # Perform linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    
    logger.info(f"Regression Results: Slope={slope:.6f}, Intercept={intercept:.6f}, R-squared={r_value**2:.4f}, P-value={p_value:.6f}")
    logger.info("Note: This is an observational analysis. Correlation does not imply causation (FR-008).")
    
    results = {
        'slope': slope,
        'intercept': intercept,
        'r_squared': r_value**2,
        'p_value': p_value,
        'std_err': std_err,
        'n_points': len(clean_stats),
        'model_params': clean_stats[['model_id', 'params_m', 'energy_per_token_j']].to_dict('records')
    }
    
    return results, clean_stats

def main():
    """
    Main entry point for analysis script.
    Executes ANOVA, Tukey HSD, and Regression.
    """
    try:
        # Load data
        df = load_data()
        
        # Run ANOVA
        anova_result = run_anova(df)
        
        # Run Tukey
        tukey_result = run_tukey(df)
        
        # Run Regression
        reg_results, reg_df = run_regression(df)
        
        # Compile a summary report for CSV output
        report_data = []
        
        # ANOVA summary
        if anova_result:
            # Extract F and p-value for model effect (simplified parsing or direct access if possible)
            # statsmodels AnovaRM table access is a bit complex, so we log and assume success if no exception
            report_data.append({
                'analysis_type': 'ANOVA_RepeatedMeasures',
                'statistic': 'F_Model',
                'value': anova_result.fvalues['model_id'],
                'p_value': anova_result.pvalues['model_id']
            })
        
        # Tukey summary (simplified: just note completion)
        if tukey_result:
            report_data.append({
                'analysis_type': 'Tukey_HSD',
                'statistic': 'Completed',
                'value': 1.0,
                'p_value': 0.0 # Placeholder, actual pairwise p-values are in tukey_result
            })
        
        # Regression summary
        if reg_results:
            report_data.append({
                'analysis_type': 'Linear_Regression_Param_vs_EnergyPerToken',
                'statistic': 'Slope',
                'value': reg_results['slope'],
                'p_value': reg_results['p_value']
            })
            report_data.append({
                'analysis_type': 'Linear_Regression_Param_vs_EnergyPerToken',
                'statistic': 'R_Squared',
                'value': reg_results['r_squared'],
                'p_value': None
            })
        
        # Write report
        if report_data:
            report_df = pd.DataFrame(report_data)
            os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
            report_df.to_csv(STATS_REPORT_FILE, index=False)
            logger.info(f"Stats report written to {STATS_REPORT_FILE}")
        
        print("Analysis complete. Check logs and stats_report.csv for details.")
        
    except Exception as e:
        logger.error(f"Analysis pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()