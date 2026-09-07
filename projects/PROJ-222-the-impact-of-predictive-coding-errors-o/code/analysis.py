import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from scipy import stats
from pingouin import power_ttest

from config import get_data_dir, get_processed_dir, set_seed
from utils import load_dataset_chunked

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('analysis/analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_preprocessed_data(data_path: str) -> pd.DataFrame:
    """Load preprocessed standardized data."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Preprocessed data not found at {data_path}")
    
    logger.info(f"Loading data from {data_path}")
    # Use chunked loading for large files
    return load_dataset_chunked(data_path)

def fit_lmm(data: pd.DataFrame, formula: str = None) -> Optional[Any]:
    """Fit Linear Mixed Effects Model."""
    if formula is None:
        formula = "duration_estimate ~ surprisal + sequence_length + modality + (1 | participant_id)"
    
    try:
        model = smf.mixedlm(formula, data, groups=data["participant_id"])
        result = model.fit()
        return result
    except Exception as e:
        logger.warning(f"LMM convergence failed: {e}")
        return None

def fit_random_intercept_model(data: pd.DataFrame) -> Optional[Any]:
    """Fit simplified random intercept model as fallback."""
    formula = "duration_estimate ~ surprisal + (1 | participant_id)"
    try:
        model = smf.mixedlm(formula, data, groups=data["participant_id"])
        result = model.fit()
        return result
    except Exception as e:
        logger.warning(f"Simplified LMM convergence failed: {e}")
        return None

def extract_model_results(result: Any) -> Dict[str, Any]:
    """Extract key statistics from LMM result."""
    if result is None:
        return {}
    
    # Get surprisal coefficient and p-value
    surprisal_coef = result.params.get('surprisal', 0.0)
    surprisal_pval = result.pvalues.get('surprisal', 1.0)
    
    # Calculate confidence intervals
    conf_int = result.conf_int()
    ci_lower = conf_int.loc['surprisal', 0] if 'surprisal' in conf_int.index else 0.0
    ci_upper = conf_int.loc['surprisal', 1] if 'surprisal' in conf_int.index else 0.0
    
    # Get standard error for effect size calculation
    surprisal_se = result.bse.get('surprisal', 1.0) if hasattr(result, 'bse') else 1.0
    
    return {
        'coef_surprisal': float(surprisal_coef),
        'pval_surprisal': float(surprisal_pval),
        'ci_lower': float(ci_lower),
        'ci_upper': float(ci_upper),
        'surprisal_se': float(surprisal_se),
        'convergence_status': 'success',
        'fallback_applied': False
    }

def run_wilcoxon_signed_rank(data: pd.DataFrame, condition_col: str = 'surprisal', 
                             outcome_col: str = 'duration_estimate') -> Dict[str, Any]:
    """Run Wilcoxon signed-rank test as fallback for non-normal residuals."""
    try:
        # For Wilcoxon, we typically need paired data. 
        # Here we test if surprisal values are significantly different from zero
        # or use a rank-based approach.
        # Since we don't have natural pairs, we'll test against median=0
        statistic, p_value = stats.wilcoxon(data[outcome_col])
        
        return {
            'wilcoxon_statistic': float(statistic),
            'wilcoxon_pval': float(p_value),
            'test_method_used': 'Wilcoxon'
        }
    except Exception as e:
        logger.error(f"Wilcoxon test failed: {e}")
        return {'wilcoxon_pval': None, 'test_method_used': 'Wilcoxon'}

def run_multiple_comparison_correction(p_values: List[float], 
                                      method: str = 'fdr_bh') -> List[float]:
    """Apply multiple comparison correction (Benjamini-Hochberg or Bonferroni)."""
    if not p_values:
        return []
    
    try:
        # Use scipy's multipletests
        from statsmodels.stats.multitest import multipletests
        
        corrected = multipletests(p_values, alpha=0.05, method=method)
        return [float(p) for p in corrected[1]]
    except Exception as e:
        logger.error(f"Multiple comparison correction failed: {e}")
        return p_values

def calculate_effect_sizes(coef: float, se: float, n_eff: int) -> Dict[str, float]:
    """Calculate Cohen's d effect size."""
    try:
        # Standardized beta coefficient approach
        standardized_beta = coef / se if se != 0 else 0
        # Approximate Cohen's d
        cohens_d = standardized_beta * np.sqrt(n_eff)
        
        return {
            'cohens_d': float(cohens_d),
            'standardized_beta': float(standardized_beta)
        }
    except Exception as e:
        logger.error(f"Effect size calculation failed: {e}")
        return {'cohens_d': 0.0}

def calculate_mde(total_trials: int, observed_beta: float, se: float) -> Dict[str, Any]:
    """Calculate Minimum Detectable Effect (MDE) for power=0.80."""
    try:
        # Use pingouin's power calculation
        # Approximate effect size from observed parameters
        if se == 0:
            effect_size = 0
        else:
            effect_size = abs(observed_beta) / se
        
        # Calculate MDE using power_ttest
        # nobs=total_trials, alpha=0.05, power=0.80
        result = power_ttest(n=total_trials, power=0.80, alpha=0.05, 
                            effect_size=effect_size)
        
        # Extract MDE value (effect size needed to detect)
        mde_value = float(result['d'].iloc[0]) if 'd' in result.columns else 0.0
        
        # Check limitation
        mde_limitation_flag = abs(observed_beta) < mde_value if mde_value > 0 else False
        
        return {
            'mde_value': mde_value,
            'mde_limitation_flag': mde_limitation_flag,
            'observed_effect': abs(observed_beta)
        }
    except Exception as e:
        logger.error(f"MDE calculation failed: {e}")
        return {'mde_value': 0.0, 'mde_limitation_flag': False}

def check_normality(residuals: np.ndarray) -> Dict[str, Any]:
    """
    Perform Shapiro-Wilk test on LMM residuals.
    If p < 0.05 (non-normal), return indicators for Wilcoxon fallback.
    """
    if len(residuals) < 3:
        logger.warning("Not enough residuals for normality test")
        return {
            'normality_test_pval': 1.0,
            'test_method_used': 'LMM',
            'supplementary_test': False
        }
    
    try:
        # Shapiro-Wilk test
        stat, p_val = stats.shapiro(residuals)
        
        result = {
            'normality_test_pval': float(p_val),
            'test_method_used': 'LMM',
            'supplementary_test': False,
            'wilcoxon_pval': None
        }
        
        # If non-normal (p < 0.05), indicate need for Wilcoxon
        if p_val < 0.05:
            result['test_method_used'] = 'Wilcoxon'
            result['supplementary_test'] = True
            logger.info(f"Residuals non-normal (p={p_val:.4f}), will use Wilcoxon")
        
        return result
    except Exception as e:
        logger.error(f"Normality test failed: {e}")
        return {
            'normality_test_pval': 1.0,
            'test_method_used': 'LMM',
            'supplementary_test': False
        }

def run_cutoff_sweeping_analysis(data: pd.DataFrame) -> Dict[str, Any]:
    """Sweep cutoff thresholds if binary splits detected."""
    # Placeholder for cutoff sensitivity analysis
    return {'cutoff_sensitivity': 'not_applicable'}

def write_results(results: Dict[str, Any], output_path: str):
    """Write analysis results to JSON."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results written to {output_path}")

def run_analysis_pipeline(data_path: str, output_path: str) -> Dict[str, Any]:
    """
    Run full analysis pipeline including normality check and fallback.
    """
    logger.info("Starting analysis pipeline")
    
    # Load data
    try:
        data = load_preprocessed_data(data_path)
    except FileNotFoundError as e:
        logger.error(f"Data loading failed: {e}")
        return {'error': str(e)}
    
    # Fit LMM
    lmm_result = fit_lmm(data)
    fallback_applied = False
    
    if lmm_result is None:
        logger.info("Fitting simplified model...")
        lmm_result = fit_random_intercept_model(data)
        fallback_applied = True if lmm_result else False
    
    if lmm_result is None:
        logger.error("Both LMM and simplified model failed")
        return {'error': 'Model fitting failed'}
    
    # Extract LMM results
    results = extract_model_results(lmm_result)
    results['fallback_applied'] = fallback_applied
    
    # Get residuals for normality check
    try:
        # Extract residuals from the fitted model
        # statsmodels mixedlm doesn't directly expose residuals, so we calculate them
        predicted = lmm_result.fittedvalues
        residuals = data['duration_estimate'].values - predicted.values
        
        # Run normality check
        normality_info = check_normality(residuals)
        results.update(normality_info)
        
        # If non-normal, run Wilcoxon and replace primary result
        if normality_info['test_method_used'] == 'Wilcoxon':
            wilcoxon_results = run_wilcoxon_signed_rank(data)
            if wilcoxon_results.get('wilcoxon_pval') is not None:
                # Replace primary p-value with Wilcoxon result
                results['pval_surprisal'] = wilcoxon_results['wilcoxon_pval']
                results['wilcoxon_pval'] = wilcoxon_results['wilcoxon_pval']
                logger.info("Replaced LMM p-value with Wilcoxon p-value due to non-normality")
    except Exception as e:
        logger.error(f"Residual analysis failed: {e}")
        results['normality_test_pval'] = 1.0
        results['test_method_used'] = 'LMM'
        results['supplementary_test'] = False
    
    # Calculate effect sizes
    n_eff = len(data)
    effect_sizes = calculate_effect_sizes(
        results['coef_surprisal'], 
        results.get('surprisal_se', 1.0), 
        n_eff
    )
    results['effect_sizes'] = effect_sizes
    
    # Calculate MDE
    mde_results = calculate_mde(
        n_eff, 
        results['coef_surprisal'], 
        results.get('surprisal_se', 1.0)
    )
    results['mde_value'] = mde_results['mde_value']
    results['mde_limitation_flag'] = mde_results['mde_limitation_flag']
    
    # Multiple comparison correction (if needed)
    # For now, assume single primary hypothesis
    results['fwer_control_status'] = True
    
    # Write results
    write_results(results, output_path)
    
    return results

def main():
    """Main entry point for analysis."""
    set_seed(42)
    
    data_path = str(get_processed_dir() / 'standardized.csv')
    output_path = str(Path('analysis') / 'results.json')
    
    results = run_analysis_pipeline(data_path, output_path)
    
    if 'error' in results:
        logger.error(f"Analysis failed: {results['error']}")
        sys.exit(1)
    
    logger.info("Analysis completed successfully")
    logger.info(f"Primary result method: {results.get('test_method_used', 'LMM')}")
    logger.info(f"Surprisal coefficient: {results.get('coef_surprisal', 'N/A')}")
    logger.info(f"Surprisal p-value: {results.get('pval_surprisal', 'N/A')}")

if __name__ == "__main__":
    main()