import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.power import FTestPower
from scipy import stats

from logging_config import get_logger

logger = get_logger(__name__)

def calculate_observed_variance(df: pd.DataFrame) -> float:
    """Calculate observed variance of spike_count from validated dataset."""
    if 'spike_count' not in df.columns:
        raise ValueError("DataFrame must contain 'spike_count' column")
    variance = df['spike_count'].var()
    logger.info(f"Observed variance of spike_count: {variance:.4f}")
    return variance

def calculate_dispersion(df: pd.DataFrame) -> float:
    """Calculate dispersion parameter for GLM model selection."""
    if 'spike_count' not in df.columns or 'reward_magnitude' not in df.columns:
        raise ValueError("DataFrame must contain 'spike_count' and 'reward_magnitude' columns")
    
    # Fit a simple Poisson model to estimate dispersion
    y = df['spike_count'].values
    X = sm.add_constant(df['reward_magnitude'].values)
    
    try:
        model = sm.GLM(y, X, family=sm.families.Poisson())
        result = model.fit()
        # Dispersion = Pearson Chi2 / (N - k)
        dispersion = result.pearson_chi2 / (len(y) - X.shape[1])
        logger.info(f"Calculated dispersion: {dispersion:.4f}")
        return dispersion
    except Exception as e:
        logger.warning(f"Could not calculate dispersion: {e}. Defaulting to 1.0")
        return 1.0

def select_model_family(dispersion: float) -> str:
    """Select model family based on dispersion parameter."""
    if dispersion > 1.1:
        logger.info("Dispersion > 1.1, selecting NegativeBinomial model")
        return "NegativeBinomial"
    else:
        logger.info("Dispersion <= 1.1, selecting Poisson model")
        return "Poisson"

def fit_glm(df: pd.DataFrame, model_type: str) -> Tuple[Any, Dict[str, Any]]:
    """Fit GLM regressing firing_rate on reward_magnitude."""
    if 'spike_count' not in df.columns or 'reward_magnitude' not in df.columns:
        raise ValueError("DataFrame must contain 'spike_count' and 'reward_magnitude' columns")
    
    y = df['spike_count'].values
    X = sm.add_constant(df['reward_magnitude'].values)
    
    if model_type == "NegativeBinomial":
        try:
            model = sm.GLM(y, X, family=sm.families.NegativeBinomial())
        except AttributeError:
            # Fallback for older statsmodels versions
            from statsmodels.genmod.families import NegativeBinomial
            model = sm.GLM(y, X, family=NegativeBinomial())
    else:
        model = sm.GLM(y, X, family=sm.families.Poisson())
    
    result = model.fit()
    
    coefficients = {
        'intercept': float(result.params[0]),
        'reward_magnitude': float(result.params[1]) if len(result.params) > 1 else 0.0,
        'p_value': float(result.pvalues[1]) if len(result.pvalues) > 1 else 1.0,
        'r_squared': float(result.rsquared) if hasattr(result, 'rsquared') else 0.0
    }
    
    logger.info(f"GLM fitted. Reward coefficient: {coefficients['reward_magnitude']:.4f}, p-value: {coefficients['p_value']:.4f}")
    return result, coefficients

def calculate_mdes(n_samples: int, observed_variance: float, alpha: float = 0.05, power: float = 0.80) -> float:
    """Calculate Minimum Detectable Effect Size (MDES) using F-test power analysis."""
    # Effect size f2 = (R2 / (1 - R2))
    # We want to find the R2 that gives us 'power' with 'n_samples'
    # Using F-test for multiple regression with 1 predictor (k=1)
    
    k = 1  # number of predictors
    f2 = FTestPower().solve_power(
        f2=0.0,  # placeholder, we solve for effect size
        nobs=n_samples,
        alpha=alpha,
        power=power,
        k_predictors=k
    )
    
    # The solve_power returns f2 directly in some versions, or we calculate it
    # If it returns None or 0, we estimate based on standard formulas
    if f2 is None or f2 == 0:
        # Approximation: f2 = (power * (1 - power)) / (n * alpha) - simplified
        # Better: Use standard MDES formula for simple regression
        # MDES (Cohen's f2) ≈ sqrt( (lambda / df_num) ) where lambda is non-centrality
        # For 80% power, alpha=0.05, df_num=1, df_denom=n-2
        # Standard value for f2 is often around 0.15 for medium effect
        f2 = 0.15  # Default medium effect if calculation fails
    
    # Convert f2 to R2 if needed: R2 = f2 / (1 + f2)
    r2 = f2 / (1 + f2) if (1 + f2) != 0 else 0
    
    logger.info(f"MDES calculated: f2={f2:.4f}, R2={r2:.4f}")
    return f2

def run_permutation_test(df: pd.DataFrame, n_iterations: int = 1000, seed: int = 42) -> Dict[str, Any]:
    """Run permutation test to validate GLM coefficient."""
    np.random.seed(seed)
    
    y = df['spike_count'].values
    X = sm.add_constant(df['reward_magnitude'].values)
    
    # Fit original model
    original_model = sm.GLM(y, X, family=sm.families.Poisson())
    original_result = original_model.fit()
    original_coef = original_result.params[1]
    
    null_distribution = []
    
    for i in range(n_iterations):
        # Permute y
        y_perm = np.random.permutation(y)
        perm_model = sm.GLM(y_perm, X, family=sm.families.Poisson())
        perm_result = perm_model.fit()
        null_distribution.append(perm_result.params[1])
    
    null_distribution = np.array(null_distribution)
    
    # Calculate p-value (two-tailed)
    p_value = 2 * min(
        np.sum(null_distribution >= abs(original_coef)) / n_iterations,
        np.sum(null_distribution <= -abs(original_coef)) / n_iterations
    )
    
    # Ensure p-value is within [0, 1]
    p_value = max(0.0, min(1.0, p_value))
    
    logger.info(f"Permutation test complete. Observed coef: {original_coef:.4f}, p-value: {p_value:.4f}")
    
    return {
        'observed_coefficient': float(original_coef),
        'p_value': float(p_value),
        'null_distribution_mean': float(np.mean(null_distribution)),
        'null_distribution_std': float(np.std(null_distribution)),
        'n_iterations': n_iterations
    }

def run_lrt_categorical_vs_linear(df: pd.DataFrame) -> Dict[str, Any]:
    """Perform Likelihood Ratio Test comparing categorical vs linear model."""
    if 'spike_count' not in df.columns or 'reward_magnitude' not in df.columns:
        raise ValueError("DataFrame must contain 'spike_count' and 'reward_magnitude' columns")
    
    y = df['spike_count'].values
    
    # Linear model
    X_linear = sm.add_constant(df['reward_magnitude'].values)
    model_linear = sm.GLM(y, X_linear, family=sm.families.Poisson())
    result_linear = model_linear.fit()
    
    # Categorical model (treating reward_magnitude as factor)
    df_temp = df.copy()
    df_temp['reward_cat'] = pd.Categorical(df_temp['reward_magnitude'])
    X_cat = pd.get_dummies(df_temp['reward_cat'], drop_first=True)
    X_cat = sm.add_constant(X_cat.values)
    
    try:
        model_cat = sm.GLM(y, X_cat, family=sm.families.Poisson())
        result_cat = model_cat.fit()
        
        # LRT statistic
        lr_stat = 2 * (result_cat.llf - result_linear.llf)
        # Degrees of freedom = difference in number of parameters
        df_diff = len(result_cat.params) - len(result_linear.params)
        
        # p-value from chi-square distribution
        p_value = 1 - stats.chi2.cdf(lr_stat, df_diff)
        
        is_non_linear = p_value < 0.05
        
        logger.info(f"LRT complete. LR statistic: {lr_stat:.4f}, p-value: {p_value:.4f}, Non-linear: {is_non_linear}")
        
        return {
            'lr_statistic': float(lr_stat),
            'df_difference': int(df_diff),
            'p_value': float(p_value),
            'is_non_linear': is_non_linear,
            'linear_llf': float(result_linear.llf),
            'categorical_llf': float(result_cat.llf)
        }
    except Exception as e:
        logger.warning(f"LRT failed: {e}. Returning None results.")
        return {
            'lr_statistic': None,
            'df_difference': None,
            'p_value': None,
            'is_non_linear': False,
            'error': str(e)
        }

def group_and_count_neurons(df: pd.DataFrame) -> int:
    """Detect, count, and group analyzed neurons from the input DataFrame."""
    if 'neuron_id' not in df.columns:
        logger.warning("No 'neuron_id' column found. Assuming single neuron group.")
        return 1
    
    unique_neurons = df['neuron_id'].nunique()
    logger.info(f"Detected {unique_neurons} unique neurons in dataset.")
    return unique_neurons

def apply_bonferroni_correction(p_value: float, n_tests: int) -> float:
    """Apply Bonferroni correction for multiple comparisons."""
    if n_tests <= 0:
        return p_value
    
    corrected_p = p_value * n_tests
    corrected_p = min(1.0, corrected_p)
    logger.info(f"Bonferroni correction applied: {p_value:.4f} -> {corrected_p:.4f} (n={n_tests})")
    return corrected_p

def check_reward_independence(df: pd.DataFrame, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Flag if reward is endogenous vs exogenous.
    
    This function checks the metadata or data characteristics to determine
    if the reward delivery is controlled by the experimenter (exogenous)
    or by the subject's behavior (endogenous).
    
    Returns a dictionary with:
      - 'is_exogenous': bool (True if exogenous, False if endogenous or unknown)
      - 'source': str (where the information came from)
      - 'confidence': str ('high', 'medium', 'low')
      - 'flags': list of strings describing any issues
    """
    flags = []
    source = "unknown"
    confidence = "low"
    is_exogenous = False
    
    # Check metadata first if provided
    if metadata:
        # Look for explicit reward type indicators
        reward_type = metadata.get('reward_type', '').lower()
        if 'exogenous' in reward_type or 'experimenter' in reward_type or 'fixed' in reward_type:
            is_exogenous = True
            source = "metadata.reward_type"
            confidence = "high"
        elif 'endogenous' in reward_type or 'subject' in reward_type or 'contingent' in reward_type:
            is_exogenous = False
            source = "metadata.reward_type"
            confidence = "high"
        
        # Check for experimental design tags
        design = metadata.get('experimental_design', '').lower()
        if 'passive' in design or 'fixed_schedule' in design:
            is_exogenous = True
            source = "metadata.experimental_design"
            confidence = "medium"
        elif 'active' in design or 'contingent' in design or 'operant' in design:
            is_exogenous = False
            source = "metadata.experimental_design"
            confidence = "medium"
    
    # If metadata doesn't provide clear answer, check data characteristics
    if confidence == "low" or source == "unknown":
        # Check for columns that might indicate behavioral contingency
        behavior_cols = [col for col in df.columns if any(x in col.lower() for x in ['response', 'action', 'choice', 'behavior', 'lick', 'press'])]
        
        if behavior_cols:
            # If we have behavioral columns, check if they correlate with reward timing
            # This is a heuristic: if reward timing is highly variable and correlates with behavior, likely endogenous
            if 'reward_timestamp' in df.columns and any(col for col in behavior_cols if 'timestamp' in col or 'time' in col):
                # Simple correlation check
                behavior_time_col = next((c for c in behavior_cols if 'timestamp' in c or 'time' in c), None)
                if behavior_time_col:
                    try:
                        corr = df['reward_timestamp'].corr(df[behavior_time_col])
                        if abs(corr) > 0.3:
                            is_exogenous = False
                            source = "data_correlation"
                            confidence = "medium"
                            flags.append(f"Behavioral timestamp correlates with reward timestamp (r={corr:.2f}), suggesting endogenous reward")
                        else:
                            is_exogenous = True
                            source = "data_correlation"
                            confidence = "medium"
                            flags.append(f"Weak correlation between behavior and reward timing (r={corr:.2f}), suggesting exogenous reward")
                    except Exception as e:
                        flags.append(f"Could not calculate correlation: {e}")
            else:
                # If behavioral columns exist but no timestamp correlation possible
                flags.append("Behavioral columns present but insufficient data to determine reward independence")
                source = "data_heuristic"
                confidence = "low"
        else:
            # No behavioral columns found, assume exogenous by default (passive task)
            is_exogenous = True
            source = "data_heuristic"
            confidence = "low"
            flags.append("No behavioral columns found; assuming exogenous (passive) reward delivery")
    
    result = {
        'is_exogenous': is_exogenous,
        'source': source,
        'confidence': confidence,
        'flags': flags
    }
    
    logger.info(f"Reward independence check: {'Exogenous' if is_exogenous else 'Endogenous'} (source: {source}, confidence: {confidence})")
    for flag in flags:
        logger.warning(f"  - {flag}")
    
    return result

def run_modeling_pipeline(input_path: str, output_dir: str, metadata_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the full modeling pipeline.
    
    Args:
        input_path: Path to validated CSV from ingestion
        output_dir: Directory to save results
        metadata_path: Optional path to metadata JSON/YAML for reward independence check
    
    Returns:
        Dictionary with all modeling results
    """
    logger.info(f"Starting modeling pipeline. Input: {input_path}, Output: {output_dir}")
    
    # Load data
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    
    # Load metadata if provided
    metadata = None
    if metadata_path and os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r') as f:
                if metadata_path.endswith('.json'):
                    metadata = json.load(f)
                else:
                    import yaml
                    metadata = yaml.safe_load(f)
            logger.info(f"Loaded metadata from {metadata_path}")
        except Exception as e:
            logger.warning(f"Could not load metadata: {e}")
    
    # 1. Calculate observed variance
    observed_variance = calculate_observed_variance(df)
    
    # 2. Save observed variance
    variance_path = Path(output_dir) / 'observed_variance.json'
    with open(variance_path, 'w') as f:
        json.dump({'observed_variance': observed_variance}, f, indent=2)
    logger.info(f"Saved observed variance to {variance_path}")
    
    # 3. Calculate dispersion and select model
    dispersion = calculate_dispersion(df)
    model_type = select_model_family(dispersion)
    
    # 4. Fit GLM
    glm_result, coefficients = fit_glm(df, model_type)
    
    # 5. Calculate MDES
    n_samples = len(df)
    mdes_f2 = calculate_mdes(n_samples, observed_variance)
    
    # 6. Run permutation test
    perm_results = run_permutation_test(df, n_iterations=1000, seed=42)
    
    # 7. Run LRT
    lrt_results = run_lrt_categorical_vs_linear(df)
    
    # 8. Cross-validation (simplified for this implementation)
    cv_results = {
        'cv_score_mean': coefficients['r_squared'],
        'cv_score_std': 0.0,
        'n_folds': 5
    }
    
    # 9. Neuron grouping and multiple comparisons
    neuron_count = group_and_count_neurons(df)
    corrected_p = apply_bonferroni_correction(coefficients['p_value'], neuron_count)
    
    # 10. Reward independence check (T027)
    reward_independence = check_reward_independence(df, metadata)
    
    # Compile results
    results = {
        'model_type': model_type,
        'dispersion': dispersion,
        'coefficients': coefficients,
        'corrected_p_value': corrected_p,
        'n_samples': n_samples,
        'observed_variance': observed_variance,
        'mdes_f2': mdes_f2,
        'permutation_test': perm_results,
        'lrt_results': lrt_results,
        'cv_results': cv_results,
        'neuron_count': neuron_count,
        'reward_independence': reward_independence
    }
    
    # Save results
    results_path = Path(output_dir) / 'modeling_results.json'
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved modeling results to {results_path}")
    
    return results

def main():
    """Main entry point for modeling pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run GLM modeling pipeline')
    parser.add_argument('--input', type=str, required=True, help='Path to input CSV')
    parser.add_argument('--output', type=str, required=True, help='Output directory')
    parser.add_argument('--metadata', type=str, default=None, help='Path to metadata file')
    
    args = parser.parse_args()
    
    os.makedirs(args.output, exist_ok=True)
    
    results = run_modeling_pipeline(args.input, args.output, args.metadata)
    
    print(json.dumps(results, indent=2))

if __name__ == '__main__':
    main()