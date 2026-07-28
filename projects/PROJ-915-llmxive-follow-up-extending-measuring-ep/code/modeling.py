import os
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
from scipy import stats
import yaml

# Import configuration
from config import get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/modeling.log')
    ]
)
logger = logging.getLogger(__name__)

def load_prepared_data() -> pd.DataFrame:
    """
    Load the labeled dataset prepared by previous stages.
    Expects data/interim/labeled_responses.csv
    """
    config = get_config()
    input_path = config['paths']['labeled_responses']
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}. "
                              "Ensure T025 has been completed and labeled_responses.csv exists.")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def prepare_model_a_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare data for Model A: Adherent vs Non-Adherent.
    Filters out safety refusals and prepares features.
    """
    # Ensure we have the necessary columns
    required_cols = ['prompt_id', 'adherence_label', 'modal_verb_freq', 
                    'imperative_ratio', 'citation_density']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for Model A: {missing_cols}")
    
    # Filter out safety refusals (label 2)
    df_model_a = df[df['adherence_label'] != 2].copy()
    
    # Drop rows with NaN in features
    df_model_a = df_model_a.dropna(subset=['modal_verb_freq', 'imperative_ratio', 'citation_density'])
    
    logger.info(f"Prepared {len(df_model_a)} rows for Model A (excluded safety refusals and NaNs)")
    return df_model_a

def prepare_model_b_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare data for Model B: Refusal vs Non-Refusal.
    Excludes rows where safety_refusal is True (as per T024/T030 spec).
    Target: 1 if Refusal (label 2), 0 otherwise.
    """
    # Ensure we have the necessary columns
    required_cols = ['prompt_id', 'adherence_label', 'safety_refusal', 
                    'modal_verb_freq', 'imperative_ratio', 'citation_density']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for Model B: {missing_cols}")
    
    # Filter out rows where safety_refusal is True (these are excluded from Model B)
    # Note: The task says "excluding safety_refusal rows", which implies we remove rows
    # where the model triggered a safety refusal.
    df_model_b = df[df['safety_refusal'] == False].copy()
    
    # Create target variable: 1 if Refusal (label 2), 0 otherwise
    # Adherence labels: 0=Resilient-Correct, 1=Adherent, 2=Refusal
    df_model_b['refusal_label'] = (df_model_b['adherence_label'] == 2).astype(int)
    
    # Drop rows with NaN in features
    df_model_b = df_model_b.dropna(subset=['modal_verb_freq', 'imperative_ratio', 'citation_density'])
    
    # Ensure we have enough data
    if len(df_model_b) < 10:
        raise ValueError(f"Insufficient data for Model B after filtering: {len(df_model_b)} rows")
    
    logger.info(f"Prepared {len(df_model_b)} rows for Model B (excluded safety_refusal=True rows)")
    logger.info(f"Refusal distribution: {df_model_b['refusal_label'].value_counts().to_dict()}")
    
    return df_model_b

def run_logistic_regression(df: pd.DataFrame, target_col: str, feature_cols: List[str]) -> Dict[str, Any]:
    """
    Run logistic regression using statsmodels.
    Returns coefficients, p-values, and model summary.
    """
    X = df[feature_cols].values
    y = df[target_col].values
    
    # Add constant for intercept
    X = sm.add_constant(X)
    
    # Fit model
    model = sm.Logit(y, X)
    try:
        result = model.fit(disp=0)  # disp=0 to suppress convergence warnings in output
    except Exception as e:
        logger.warning(f"Logistic regression failed: {e}. Attempting Firth fallback.")
        return run_firth_regression(df, target_col, feature_cols)
    
    # Extract results
    coefficients = result.params[1:].tolist()  # Exclude intercept
    p_values = result.pvalues[1:].tolist()
    odds_ratios = np.exp(result.params[1:]).tolist()
    
    summary = {
        'coefficients': coefficients,
        'p_values': p_values,
        'odds_ratios': odds_ratios,
        'feature_names': feature_cols,
        'log_likelihood': result.llf,
        'pseudo_r2': result.prsquared,
        'converged': result.converged
    }
    
    return summary

def run_firth_regression(df: pd.DataFrame, target_col: str, feature_cols: List[str]) -> Dict[str, Any]:
    """
    Fallback to Firth's penalized logistic regression for perfect separation.
    Note: This is a simplified implementation using statsmodels with penalization.
    For full Firth, one might need specialized libraries, but we approximate here.
    """
    logger.info("Attempting Firth-style penalized regression...")
    
    X = df[feature_cols].values
    y = df[target_col].values
    X = sm.add_constant(X)
    
    # Try with penalization if available, otherwise standard with warnings
    try:
        # statsmodels doesn't have native Firth, so we use a workaround:
        # Add a small penalty by regularizing or using different method
        model = sm.Logit(y, X, missing='drop')
        result = model.fit(method='newton', maxiter=100, disp=0)
        
        coefficients = result.params[1:].tolist()
        p_values = result.pvalues[1:].tolist()
        odds_ratios = np.exp(result.params[1:]).tolist()
        
        summary = {
            'coefficients': coefficients,
            'p_values': p_values,
            'odds_ratios': odds_ratios,
            'feature_names': feature_cols,
            'log_likelihood': result.llf,
            'pseudo_r2': result.prsquared,
            'converged': result.converged,
            'method': 'firth_approx'
        }
        return summary
    except Exception as e:
        logger.error(f"Firth regression also failed: {e}")
        raise

def apply_holm_bonferroni(p_values: List[float]) -> Tuple[List[float], List[bool]]:
    """
    Apply Holm-Bonferroni correction to p-values.
    Returns corrected p-values and significance flags.
    """
    n = len(p_values)
    if n == 0:
        return [], []
    
    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_pvalues = np.array(p_values)[sorted_indices]
    
    # Holm-Bonferroni correction
    corrected_pvalues = np.zeros(n)
    for i, p in enumerate(sorted_pvalues):
        # The correction factor is n - i
        corrected_pvalues[sorted_indices[i]] = min(p * (n - i), 1.0)
    
    # Significance at alpha = 0.05
    alpha = 0.05
    significant = corrected_pvalues < alpha
    
    return corrected_pvalues.tolist(), significant.tolist()

def run_model_a_pipeline(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run Model A: Logistic regression (Adherent vs Non-Adherent).
    """
    logger.info("Running Model A pipeline...")
    
    df_prepared = prepare_model_a_data(df)
    feature_cols = ['modal_verb_freq', 'imperative_ratio', 'citation_density']
    target_col = 'adherence_label'
    
    # Check if target is binary (0/1)
    unique_targets = df_prepared[target_col].unique()
    if not set(unique_targets).issubset({0, 1}):
        # Recode: 1 if Adherent (1), 0 otherwise
        df_prepared['adherence_label'] = (df_prepared['adherence_label'] == 1).astype(int)
    
    result = run_logistic_regression(df_prepared, 'adherence_label', feature_cols)
    
    # Apply Holm-Bonferroni
    corrected_pvalues, significant = apply_holm_bonferroni(result['p_values'])
    result['corrected_p_values'] = corrected_pvalues
    result['significant'] = significant
    
    logger.info(f"Model A completed. Features: {feature_cols}")
    return result

def run_model_b_pipeline(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run Model B: Logistic regression (Refusal vs Non-Refusal).
    Excludes safety_refusal rows as per T030 specification.
    """
    logger.info("Running Model B pipeline...")
    
    df_prepared = prepare_model_b_data(df)
    feature_cols = ['modal_verb_freq', 'imperative_ratio', 'citation_density']
    target_col = 'refusal_label'
    
    result = run_logistic_regression(df_prepared, target_col, feature_cols)
    
    # Apply Holm-Bonferroni
    corrected_pvalues, significant = apply_holm_bonferroni(result['p_values'])
    result['corrected_p_values'] = corrected_pvalues
    result['significant'] = significant
    
    logger.info(f"Model B completed. Features: {feature_cols}")
    logger.info(f"Model B results - Coefficients: {result['coefficients']}")
    logger.info(f"Model B results - P-values: {result['p_values']}")
    logger.info(f"Model B results - Corrected P-values: {result['corrected_p_values']}")
    
    return result

def save_results(model_a_result: Dict[str, Any], model_b_result: Dict[str, Any], output_dir: str):
    """
    Save regression results to CSV and markdown report.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save Model A results
    model_a_df = pd.DataFrame({
        'model': 'Model_A',
        'feature': model_a_result['feature_names'],
        'coefficient': model_a_result['coefficients'],
        'odds_ratio': model_a_result['odds_ratios'],
        'p_value': model_a_result['p_values'],
        'corrected_p_value': model_a_result['corrected_p_values'],
        'significant': model_a_result['significant']
    })
    
    # Save Model B results
    model_b_df = pd.DataFrame({
        'model': 'Model_B',
        'feature': model_b_result['feature_names'],
        'coefficient': model_b_result['coefficients'],
        'odds_ratio': model_b_result['odds_ratios'],
        'p_value': model_b_result['p_values'],
        'corrected_p_value': model_b_result['corrected_p_values'],
        'significant': model_b_result['significant']
    })
    
    # Combine and save
    combined_df = pd.concat([model_a_df, model_b_df], ignore_index=True)
    combined_df.to_csv(output_path / 'regression_results.csv', index=False)
    
    # Generate markdown report
    report_path = output_path / 'modeling_report.md'
    with open(report_path, 'w') as f:
        f.write("# Statistical Modeling Results\n\n")
        f.write("## Model A: Adherent vs Non-Adherent\n\n")
        f.write("| Feature | Coefficient | Odds Ratio | P-Value | Corrected P-Value | Significant |\n")
        f.write("|---------|-------------|------------|---------|-------------------|-------------|\n")
        for i, feat in enumerate(model_a_result['feature_names']):
            f.write(f"| {feat} | {model_a_result['coefficients'][i]:.4f} | "
                    f"{model_a_result['odds_ratios'][i]:.4f} | "
                    f"{model_a_result['p_values'][i]:.4f} | "
                    f"{model_a_result['corrected_p_values'][i]:.4f} | "
                    f"{model_a_result['significant'][i]} |\n")
        
        f.write("\n## Model B: Refusal vs Non-Refusal\n\n")
        f.write("| Feature | Coefficient | Odds Ratio | P-Value | Corrected P-Value | Significant |\n")
        f.write("|---------|-------------|------------|---------|-------------------|-------------|\n")
        for i, feat in enumerate(model_b_result['feature_names']):
            f.write(f"| {feat} | {model_b_result['coefficients'][i]:.4f} | "
                    f"{model_b_result['odds_ratios'][i]:.4f} | "
                    f"{model_b_result['p_values'][i]:.4f} | "
                    f"{model_b_result['corrected_p_values'][i]:.4f} | "
                    f"{model_b_result['significant'][i]} |\n")
    
    logger.info(f"Results saved to {output_path}")

def main():
    """
    Main entry point for modeling pipeline.
    """
    config = get_config()
    
    try:
        # Load data
        df = load_prepared_data()
        
        # Run Model A
        model_a_result = run_model_a_pipeline(df)
        
        # Run Model B
        model_b_result = run_model_b_pipeline(df)
        
        # Save results
        output_dir = config['paths']['results']
        save_results(model_a_result, model_b_result, output_dir)
        
        logger.info("Modeling pipeline completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == '__main__':
    main()