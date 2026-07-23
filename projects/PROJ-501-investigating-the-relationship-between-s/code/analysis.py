import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, rankdata
import pingouin as pg
import config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_partial_correlation(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform partial Spearman rank correlation between cumulative_flux and retention_fraction,
    controlling for mass and semi_major_axis.
    
    Args:
        df: DataFrame containing derived physics columns.
        
    Returns:
        Dictionary with 'rho', 'pval', and method details.
    """
    required_cols = ['cumulative_flux', 'retention_fraction', 'mass', 'semi_major_axis']
    if not all(col in df.columns for col in required_cols):
        missing = [c for c in required_cols if c not in df.columns]
        raise ValueError(f"Missing required columns for partial correlation: {missing}")

    # Drop rows with NaN in any of the required columns
    clean_df = df.dropna(subset=required_cols)
    if len(clean_df) < 4:
        logger.warning(f"Insufficient data points ({len(clean_df)}) for partial correlation.")
        return {'rho': None, 'pval': None, 'n': len(clean_df), 'method': 'partial_spearman'}

    # Explicitly rank-transform all variables (FR-006 requirement)
    ranks = clean_df[required_cols].apply(rankdata)
    
    x = ranks['cumulative_flux']
    y = ranks['retention_fraction']
    controls = ranks[['mass', 'semi_major_axis']].values

    # Manual partial correlation calculation using residuals of rank-transformed variables
    # Regress x on controls
    try:
        model_x = pg.linear_regression(controls, x)
        residuals_x = x - model_x['pred']
        
        # Regress y on controls
        model_y = pg.linear_regression(controls, y)
        residuals_y = y - model_y['pred']
        
        # Calculate Spearman correlation on residuals
        rho, pval = spearmanr(residuals_x, residuals_y)
    except Exception as e:
        logger.error(f"Partial correlation calculation failed: {e}")
        return {'rho': None, 'pval': None, 'n': len(clean_df), 'method': 'partial_spearman', 'error': str(e)}

    logger.info(f"Partial Spearman correlation: rho={rho:.4f}, p-value={pval:.4f}")
    return {
        'rho': float(rho),
        'pval': float(pval),
        'n': len(clean_df),
        'method': 'partial_spearman_ranked_residuals'
    }

def run_sensitivity_analysis(df: pd.DataFrame, baselines: Optional[List[float]] = None) -> Dict[str, Any]:
    """
    Re-run correlation with M_atm_initial baselines across a range of low to moderate magnitudes.
    Calculate the variation in correlation coefficients.
    
    Args:
        df: DataFrame containing derived physics columns (including retention_fraction calculated with default baseline).
            Note: To properly test sensitivity, we need to re-calculate retention_fraction for each baseline.
            This function assumes the physics pipeline has already run, but we need to re-derive retention_fraction
            based on different M_atm_initial values.
            
            However, since retention_fraction depends on M_atm_initial = 0.01 * M_p, and we don't have the raw
            intermediate values (integrated mass loss) stored, we need to approximate or re-run the physics model.
            
            Given the constraints, we will:
            1. Assume the current retention_fraction was calculated with baseline 0.01.
            2. For sensitivity, we will re-calculate retention_fraction using the formula:
               Retention_new = 1 - ( (1 - Retention_old) * (Baseline_old / Baseline_new) )
               This is derived from: Retention = 1 - (MassLoss / M_atm_initial)
               => MassLoss = (1 - Retention) * M_atm_initial
               => Retention_new = 1 - (MassLoss / M_atm_initial_new)
                                = 1 - ( (1 - Retention_old) * M_atm_initial_old / M_atm_initial_new )
            3. Run the partial correlation for each new baseline.
            
            If the data does not contain 'mass' (to re-calculate M_atm_initial) or 'cumulative_flux' (to re-run physics),
            we use the approximation above.
            
    Returns:
        Dictionary with 'baselines', 'correlations', and 'variation'.
    """
    required_cols = ['retention_fraction', 'cumulative_flux', 'mass']
    if not all(col in df.columns for col in required_cols):
        missing = [c for c in required_cols if c not in df.columns]
        raise ValueError(f"Missing required columns for sensitivity analysis: {missing}")

    if baselines is None:
        # Define a range of low to moderate magnitudes for M_atm_initial (as fraction of planet mass)
        # Default is 0.01 (1%). Range from 0.005 (0.5%) to 0.05 (5%)
        baselines = [0.005, 0.0075, 0.01, 0.015, 0.02, 0.03, 0.05]
    
    logger.info(f"Running sensitivity analysis with baselines: {baselines}")
    
    results = []
    rho_values = []
    
    # Base baseline used in the original calculation (from config or assumption)
    # The task description says "M_ATM_INITIAL_BASELINE=0.01" in config.py
    base_baseline = 0.01 

    for b in baselines:
        try:
            # Re-calculate retention_fraction for this baseline
            # Formula: Retention_new = 1 - ( (1 - Retention_old) * (base_baseline / b) )
            # This assumes MassLoss is constant and only the initial atmosphere mass changes.
            
            # Handle potential negative retention or >1 due to numerical issues or invalid data
            # If (1 - Retention_old) * (base_baseline / b) > 1, then Retention_new < 0.
            # We should cap it or handle it. But for correlation, we can let it be.
            
            mass_loss_ratio = (1.0 - df['retention_fraction']) * (base_baseline / b)
            retention_new = 1.0 - mass_loss_ratio
            
            # Create a temporary dataframe for this baseline
            temp_df = df.copy()
            temp_df['retention_fraction'] = retention_new
            
            # Run partial correlation
            corr_result = run_partial_correlation(temp_df)
            
            if corr_result['rho'] is not None:
                rho_values.append(corr_result['rho'])
                results.append({
                    'baseline': b,
                    'rho': corr_result['rho'],
                    'pval': corr_result['pval'],
                    'n': corr_result['n']
                })
            else:
                logger.warning(f"Correlation failed for baseline {b}")
                results.append({
                    'baseline': b,
                    'rho': None,
                    'pval': None,
                    'n': corr_result.get('n', 0)
                })
                
        except Exception as e:
            logger.error(f"Error processing baseline {b}: {e}")
            results.append({
                'baseline': b,
                'rho': None,
                'pval': None,
                'n': 0,
                'error': str(e)
            })

    # Calculate variation
    valid_rhos = [r for r in rho_values if r is not None]
    variation = {}
    if len(valid_rhos) >= 2:
        variation['std_dev'] = float(np.std(valid_rhos))
        variation['range'] = float(max(valid_rhos) - min(valid_rhos))
        variation['min'] = float(min(valid_rhos))
        variation['max'] = float(max(valid_rhos))
    else:
        variation['std_dev'] = None
        variation['range'] = None
        variation['min'] = None
        variation['max'] = None

    logger.info(f"Sensitivity analysis complete. Variation (std): {variation.get('std_dev')}")

    return {
        'baselines': baselines,
        'correlations': results,
        'variation': variation
    }

def save_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save results to a JSON file.
    
    Args:
        results: Dictionary containing correlation results and sensitivity data.
        output_path: Path to the output JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")

def run_analysis_pipeline(input_path: str, output_path: str, sensitivity_output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the full analysis pipeline: partial correlation and sensitivity analysis.
    
    Args:
        input_path: Path to the derived physics CSV.
        output_path: Path to save the main correlation results.
        sensitivity_output_path: Optional path to save sensitivity results (if different).
        
    Returns:
        Combined results dictionary.
    """
    logger.info(f"Starting analysis pipeline with input: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Run partial correlation
    main_corr = run_partial_correlation(df)
    
    # Run sensitivity analysis
    sensitivity = run_sensitivity_analysis(df)
    
    # Combine results
    final_results = {
        'partial_correlation': main_corr,
        'sensitivity_analysis': sensitivity
    }
    
    # Save to file
    save_results(final_results, output_path)
    
    return final_results

if __name__ == "__main__":
    # Example usage for direct execution
    input_file = "data/processed/derived_physics.csv"
    output_file = "data/results/correlation_results.json"
    
    if Path(input_file).exists():
        results = run_analysis_pipeline(input_file, output_file)
        print(json.dumps(results, indent=2))
    else:
        logger.error(f"Input file not found: {input_file}")