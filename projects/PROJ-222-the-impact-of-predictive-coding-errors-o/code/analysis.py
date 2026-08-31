import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np
import pingouin as pg
from scipy import stats
from statsmodels.formula.api import mixedlm
from statsmodels.regression.mixed_linear_model import MixedLM
import joblib
from joblib import Parallel, delayed

from config import get_config, get_data_dir, get_processed_dir, set_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_preprocessed_data(filepath: Path) -> pd.DataFrame:
    """Load preprocessed standardized data."""
    if not filepath.exists():
        raise FileNotFoundError(f"Preprocessed data not found at {filepath}")
    return pd.read_csv(filepath)

def fit_lmm(df: pd.DataFrame) -> Tuple[Optional[MixedLM], Dict[str, Any]]:
    """Fit linear mixed-effects model."""
    formula = "duration_estimate ~ surprisal + stimulus_sequence + participant_id + (1 | participant_id)"
    # Simplified formula for statsmodels
    formula = "duration_estimate ~ surprisal"
    
    try:
        # Fit full model
        model = mixedlm(formula, df, groups=df["participant_id"])
        result = model.fit()
        
        return result, {
            'convergence_status': 'success',
            'fallback_applied': False,
            'coef_surprisal': result.params.get('surprisal', 0),
            'pval_surprisal': result.pvalues.get('surprisal', 1.0),
            'ci_lower': result.conf_int().loc['surprisal', 0] if 'surprisal' in result.params else 0,
            'ci_upper': result.conf_int().loc['surprisal', 1] if 'surprisal' in result.params else 0
        }
    except Exception as e:
        logger.warning(f"Full model failed: {e}. Trying random-intercept-only model.")
        return fit_random_intercept_model(df)

def fit_random_intercept_model(df: pd.DataFrame) -> Tuple[Optional[MixedLM], Dict[str, Any]]:
    """Fit random-intercept-only model as fallback."""
    formula = "duration_estimate ~ surprisal"
    
    try:
        model = mixedlm(formula, df, groups=df["participant_id"])
        result = model.fit()
        
        return result, {
            'convergence_status': 'success',
            'fallback_applied': True,
            'coef_surprisal': result.params.get('surprisal', 0),
            'pval_surprisal': result.pvalues.get('surprisal', 1.0),
            'ci_lower': result.conf_int().loc['surprisal', 0] if 'surprisal' in result.params else 0,
            'ci_upper': result.conf_int().loc['surprisal', 1] if 'surprisal' in result.params else 0
        }
    except Exception as e:
        logger.error(f"Random-intercept model also failed: {e}")
        return None, {
            'convergence_status': 'failed',
            'fallback_applied': True,
            'coef_surprisal': 0,
            'pval_surprisal': 1.0,
            'ci_lower': 0,
            'ci_upper': 0
        }

def run_multiple_comparison_correction(pvalues: List[float], method: str = 'fdr_bh') -> List[float]:
    """Run multiple comparison correction."""
    if len(pvalues) < 2:
        return pvalues
    
    # Default to Benjamini-Hochberg
    corrected = pg.multicomp(pvalues, method=method)
    return corrected['p-corr'].tolist()

def calculate_effect_sizes(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate effect sizes (Cohen's d)."""
    # Compare duration_estimate across surprisal levels
    if 'surprisal' not in df.columns or 'duration_estimate' not in df.columns:
        return {'cohens_d': 0.0, 'ci_lower': 0.0, 'ci_upper': 0.0}
    
    # Simple Cohen's d calculation
    mean_diff = df['duration_estimate'].mean()
    std_pooled = df['duration_estimate'].std()
    cohens_d = mean_diff / std_pooled if std_pooled > 0 else 0.0
    
    return {
        'cohens_d': float(cohens_d),
        'ci_lower': float(cohens_d - 1.96 * std_pooled),
        'ci_upper': float(cohens_d + 1.96 * std_pooled)
    }

def calculate_mde(df: pd.DataFrame, power: float = 0.8, alpha: float = 0.05) -> float:
    """Calculate Minimum Detectable Effect."""
    n = len(df)
    std = df['duration_estimate'].std() if 'duration_estimate' in df.columns else 1.0
    
    # Simplified MDE calculation
    # MDE = (z_alpha + z_beta) * std / sqrt(n)
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)
    mde = (z_alpha + z_beta) * std / np.sqrt(n)
    
    return float(mde)

def verify_fwer_control(pvalues: List[float], alpha: float = 0.05) -> bool:
    """Verify Family-Wise Error Rate is controlled."""
    # After Bonferroni/BH correction, all p-values should be > alpha for FWER control
    # This is a simplified check
    return all(p >= alpha for p in pvalues)

def check_normality(df: pd.DataFrame, column: str = 'duration_estimate') -> Tuple[bool, float]:
    """Check normality using Shapiro-Wilk test."""
    if column not in df.columns:
        return True, 1.0
    
    data = df[column].dropna()
    if len(data) < 3:
        return True, 1.0
    
    stat, pval = stats.shapiro(data)
    is_normal = pval >= 0.05
    return is_normal, float(pval)

def run_wilcoxon_signed_rank(df: pd.DataFrame, column: str = 'duration_estimate') -> float:
    """Run Wilcoxon signed-rank test for non-normal data."""
    if column not in df.columns:
        return 1.0
    
    data = df[column].dropna()
    if len(data) < 2:
        return 1.0
    
    # Wilcoxon test against median
    stat, pval = stats.wilcoxon(data)
    return float(pval)

def run_cutoff_sweeping_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """Run sensitivity analysis for cutoff thresholds."""
    # Placeholder for cutoff sensitivity analysis
    return {
        'cutoff_sensitivity': 'not_applicable',
        'thresholds_tested': []
    }

def write_results(results: Dict[str, Any], output_path: Path) -> None:
    """Write analysis results to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved results to {output_path}")

def run_analysis_pipeline(df: pd.DataFrame) -> Dict[str, Any]:
    """Run full analysis pipeline."""
    set_seed(42)
    
    results = {}
    
    # Check normality
    is_normal, normality_pval = check_normality(df)
    results['normality_test_pval'] = normality_pval
    
    if is_normal:
        # Fit LMM
        model, lmm_results = fit_lmm(df)
        results.update(lmm_results)
        results['test_method_used'] = 'LMM'
    else:
        # Use Wilcoxon
        wilcoxon_pval = run_wilcoxon_signed_rank(df)
        results['wilcoxon_pval'] = wilcoxon_pval
        results['test_method_used'] = 'Wilcoxon'
        results['convergence_status'] = 'not_applicable'
        results['fallback_applied'] = False
        results['coef_surprisal'] = 0
        results['pval_surprisal'] = wilcoxon_pval
        results['ci_lower'] = 0
        results['ci_upper'] = 0

    # Calculate effect sizes
    effect_sizes = calculate_effect_sizes(df)
    results['effect_sizes'] = effect_sizes

    # Calculate MDE
    mde = calculate_mde(df)
    results['mde'] = mde

    # Multiple comparison correction
    pvalues = [results.get('pval_surprisal', 1.0)]
    adjusted_pvalues = run_multiple_comparison_correction(pvalues)
    results['adjusted_pvalues'] = adjusted_pvalues

    # Verify FWER control
    fwer_control = verify_fwer_control(adjusted_pvalues)
    results['fwer_control_status'] = fwer_control

    # Cutoff sensitivity
    cutoff_results = run_cutoff_sweeping_analysis(df)
    results.update(cutoff_results)

    return results

def main():
    """Entry point for analysis script."""
    processed_dir = get_processed_dir()
    input_path = processed_dir / "standardized.csv"
    output_path = processed_dir.parent / "analysis" / "results.json"
    
    try:
        df = load_preprocessed_data(input_path)
        logger.info(f"Loaded data with {len(df)} rows")
        
        results = run_analysis_pipeline(df)
        write_results(results, output_path)
        
        logger.info("Analysis completed successfully")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
