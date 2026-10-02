"""
Statistical Engine for Embodied Curriculum Learning Analysis.

Implements t-tests, ANCOVA, effect sizes, power analysis, collinearity checks,
and result aggregation for the statistical pipeline.
"""
import logging
from typing import List, Tuple, Dict, Any, Optional, Set
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.formula.api import ols
from statsmodels.stats.power import TTestIndPower

from .config import INFERENTIAL_FRAMING_STRING
from .models import AnalysisResult, SensitivitySweep

logger = logging.getLogger(__name__)

def run_t_test(
    pre_scores: List[float],
    post_scores: List[float],
    instruction_types: List[str],
    group_label: str = "instruction_type"
) -> Dict[str, Any]:
    """
    Perform t-test on gain scores between groups.
    
    Uses Welch's t-test if variances are unequal (Levene's test),
    otherwise Student's t-test.
    
    Args:
        pre_scores: List of pre-test scores.
        post_scores: List of post-test scores.
        instruction_types: List of instruction type labels.
        group_label: Column name for grouping.
        
    Returns:
        Dictionary with t_statistic, p_value, and test_type.
    """
    if len(pre_scores) != len(post_scores) or len(pre_scores) != len(instruction_types):
        raise ValueError("Input lists must have the same length")
        
    df = pd.DataFrame({
        'pre': pre_scores,
        'post': post_scores,
        group_label: instruction_types
    })
    
    # Calculate gain scores
    df['gain'] = df['post'] - df['pre']
    df = df.dropna(subset=['gain'])
    
    if df[group_label].nunique() < 2:
        raise ValueError("Need at least two distinct instruction types for t-test")
        
    groups = df[group_label].unique()
    group1_gain = df[df[group_label] == groups[0]]['gain'].values
    group2_gain = df[df[group_label] == groups[1]]['gain'].values
    
    if len(group1_gain) < 2 or len(group2_gain) < 2:
        raise ValueError("Each group must have at least 2 samples for t-test")
        
    # Levene's test for equality of variances
    levene_stat, levene_p = stats.levene(group1_gain, group2_gain)
    
    if levene_p < 0.05:
        # Unequal variances - Welch's t-test
        t_stat, p_val = stats.ttest_ind(group1_gain, group2_gain, equal_var=False)
        test_type = "Welch's t-test (unequal variances)"
    else:
        # Equal variances - Student's t-test
        t_stat, p_val = stats.ttest_ind(group1_gain, group2_gain, equal_var=True)
        test_type = "Student's t-test (equal variances)"
        
    return {
        't_statistic': float(t_stat),
        'p_value': float(p_val),
        'test_type': test_type,
        'levene_p': float(levene_p)
    }

def run_ancova(
    pre_scores: List[float],
    post_scores: List[float],
    instruction_types: List[str],
    group_label: str = "instruction_type"
) -> Dict[str, Any]:
    """
    Perform Analysis of Covariance (ANCOVA) adjusting for pre-test scores.
    
    This is a secondary descriptive method to address regression to the mean.
    
    Args:
        pre_scores: List of pre-test scores.
        post_scores: List of post-test scores.
        instruction_types: List of instruction type labels.
        group_label: Column name for grouping.
        
    Returns:
        Dictionary with F-statistic, p-value, adjusted means, and model summary.
    """
    if len(pre_scores) != len(post_scores) or len(pre_scores) != len(instruction_types):
        raise ValueError("Input lists must have the same length")
        
    df = pd.DataFrame({
        'post': post_scores,
        'pre': pre_scores,
        group_label: instruction_types
    })
    
    # Drop rows with missing values
    df = df.dropna()
    
    if len(df) < 10:
        logger.warning("Sample size too small for reliable ANCOVA")
        return {
            'f_statistic': None,
            'p_value': None,
            'adjusted_means': {},
            'warning': "Sample size too small for reliable ANCOVA"
        }
        
    # Fit ANCOVA model: post ~ pre + instruction_type
    formula = f"post ~ pre + C({group_label})"
    model = ols(formula, data=df).fit()
    
    # Get adjusted means (least squares means)
    # Using marginal means approach
    lsmeans = model.predict(df)
    adjusted_means = {}
    for grp in df[group_label].unique():
        mask = df[group_label] == grp
        adjusted_means[grp] = float(lsmeans[mask].mean())
        
    f_stat = model.fvalue
    p_val = model.f_pvalue
    
    return {
        'f_statistic': float(f_stat),
        'p_value': float(p_val),
        'adjusted_means': adjusted_means,
        'r_squared': float(model.rsquared),
        'warning': None
    }

def calculate_effect_size(
    pre_scores: List[float],
    post_scores: List[float],
    instruction_types: List[str]
) -> Dict[str, Any]:
    """
    Calculate Cohen's d effect size for gain scores.
    
    Args:
        pre_scores: List of pre-test scores.
        post_scores: List of post-test scores.
        instruction_types: List of instruction type labels.
        
    Returns:
        Dictionary with effect_size_cohen_d and confidence_interval.
    """
    if len(pre_scores) != len(post_scores) or len(pre_scores) != len(instruction_types):
        raise ValueError("Input lists must have the same length")
        
    df = pd.DataFrame({
        'pre': pre_scores,
        'post': post_scores,
        'instruction_type': instruction_types
    })
    
    df['gain'] = df['post'] - df['pre']
    df = df.dropna(subset=['gain'])
    
    groups = df['instruction_type'].unique()
    if len(groups) < 2:
        raise ValueError("Need at least two distinct instruction types")
        
    group1_gain = df[df['instruction_type'] == groups[0]]['gain'].values
    group2_gain = df[df['instruction_type'] == groups[1]]['gain'].values
    
    if len(group1_gain) < 2 or len(group2_gain) < 2:
        raise ValueError("Each group must have at least 2 samples")
        
    # Calculate pooled standard deviation
    n1, n2 = len(group1_gain), len(group2_gain)
    std1, std2 = np.std(group1_gain, ddof=1), np.std(group2_gain, ddof=1)
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        raise ValueError("Pooled standard deviation is zero")
        
    # Cohen's d
    mean_diff = np.mean(group1_gain) - np.mean(group2_gain)
    cohens_d = mean_diff / pooled_std
    
    # Confidence interval for Cohen's d
    # Using non-central t-distribution approximation
    n = n1 + n2
    se_d = np.sqrt((n1 + n2) / (n1 * n2) + cohens_d**2 / (2 * (n1 + n2)))
    ci_lower = cohens_d - 1.96 * se_d
    ci_upper = cohens_d + 1.96 * se_d
    
    return {
        'effect_size_cohen_d': float(cohens_d),
        'confidence_interval': (float(ci_lower), float(ci_upper)),
        'mean_diff': float(mean_diff),
        'pooled_std': float(pooled_std)
    }

def detect_multiple_concepts(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Scan dataset for columns representing distinct mathematical concepts.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        Dictionary with n_concepts and concept_ids.
    """
    concept_columns = []
    
    # Look for columns containing 'concept' or 'topic' in name
    for col in df.columns:
        if 'concept' in col.lower() or 'topic' in col.lower():
            concept_columns.append(col)
            
    # Also check for distinct groups in instruction_type if no concept columns found
    if not concept_columns and 'instruction_type' in df.columns:
        unique_types = df['instruction_type'].unique()
        concept_columns = [f"instruction_{i}" for i in range(len(unique_types))]
        
    return {
        'n_concepts': len(concept_columns),
        'concept_ids': concept_columns
    }

def apply_bonferroni_correction(p_value: float, n_concepts: int) -> float:
    """
    Apply Bonferroni correction to p-value.
    
    Args:
        p_value: Original p-value.
        n_concepts: Number of concepts being tested.
        
    Returns:
        Corrected p-value.
    """
    if n_concepts <= 0:
        raise ValueError("n_concepts must be positive")
        
    corrected_p = p_value * n_concepts
    return min(corrected_p, 1.0)

def frame_inference() -> str:
    """
    Return the standard inferential framing string.
    
    Returns:
        String explicitly labeling findings as associational.
    """
    return INFERENTIAL_FRAMING_STRING

def check_collinearity(df: pd.DataFrame, predictors: List[str]) -> Dict[str, Any]:
    """
    Check for high collinearity between predictors.
    
    Args:
        df: Input DataFrame.
        predictors: List of predictor column names.
        
    Returns:
        Dictionary with high_correlation_pairs and warning.
    """
    high_correlation_pairs = []
    
    if len(predictors) < 2:
        return {
            'high_correlation_pairs': [],
            'warning': "Need at least 2 predictors to check collinearity"
        }
        
    # Calculate correlation matrix
    corr_matrix = df[predictors].corr().abs()
    
    # Find pairs with |r| > 0.8
    for i in range(len(predictors)):
        for j in range(i + 1, len(predictors)):
            col1, col2 = predictors[i], predictors[j]
            corr_val = corr_matrix.loc[col1, col2]
            
            if corr_val > 0.8:
                high_correlation_pairs.append({
                    'pair': [col1, col2],
                    'correlation': float(corr_val)
                })
                
    warning = None
    if high_correlation_pairs:
        warning = f"High collinearity detected between {len(high_correlation_pairs)} predictor pairs"
        
    return {
        'high_correlation_pairs': high_correlation_pairs,
        'warning': warning
    }

def calculate_power(
    pre_scores: List[float],
    post_scores: List[float],
    instruction_types: List[str]
) -> Dict[str, Any]:
    """
    Calculate achieved power for the t-test.
    
    Args:
        pre_scores: List of pre-test scores.
        post_scores: List of post-test scores.
        instruction_types: List of instruction type labels.
        
    Returns:
        Dictionary with achieved_power and is_underpowered.
    """
    if len(pre_scores) != len(post_scores) or len(pre_scores) != len(instruction_types):
        raise ValueError("Input lists must have the same length")
        
    df = pd.DataFrame({
        'pre': pre_scores,
        'post': post_scores,
        'instruction_type': instruction_types
    })
    
    df['gain'] = df['post'] - df['pre']
    df = df.dropna(subset=['gain'])
    
    groups = df['instruction_type'].unique()
    if len(groups) < 2:
        return {
            'achieved_power': 0.0,
            'is_underpowered': True,
            'warning': "Need at least two distinct instruction types"
        }
        
    group1_gain = df[df['instruction_type'] == groups[0]]['gain'].values
    group2_gain = df[df['instruction_type'] == groups[1]]['gain'].values
    
    n1, n2 = len(group1_gain), len(group2_gain)
    n_total = n1 + n2
    
    if n_total < 20:
        return {
            'achieved_power': 0.0,
            'is_underpowered': True,
            'warning': "Sample size too small for power analysis"
        }
        
    # Calculate effect size (Cohen's d)
    mean1, mean2 = np.mean(group1_gain), np.mean(group2_gain)
    std1, std2 = np.std(group1_gain, ddof=1), np.std(group2_gain, ddof=1)
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return {
            'achieved_power': 0.0,
            'is_underpowered': True,
            'warning': "Pooled standard deviation is zero"
        }
        
    effect_size = abs(mean1 - mean2) / pooled_std
    
    # Calculate power
    power_analysis = TTestIndPower()
    try:
        power = power_analysis.solve_power(
            effect_size=effect_size,
            nobs1=n1,
            alpha=0.05,
            power=None,
            ratio=n2/n1
        )
    except Exception as e:
        logger.warning(f"Power calculation failed: {e}")
        return {
            'achieved_power': 0.0,
            'is_underpowered': True,
            'warning': "Power calculation failed"
        }
        
    is_underpowered = power < 0.80
    
    return {
        'achieved_power': float(power),
        'is_underpowered': is_underpowered
    }

def aggregate_stats_results(
    t_test_result: Dict[str, Any],
    ancova_result: Optional[Dict[str, Any]],
    effect_size_result: Dict[str, Any],
    power_result: Dict[str, Any],
    collinearity_result: Dict[str, Any],
    n_concepts: int
) -> Dict[str, Any]:
    """
    Aggregate all statistical results into a single dictionary structure.
    
    This combines t-test (primary), ANCOVA (secondary), effect sizes,
    power analysis, and collinearity diagnostics.
    
    Args:
        t_test_result: Dictionary from run_t_test.
        ancova_result: Dictionary from run_ancova (optional).
        effect_size_result: Dictionary from calculate_effect_size.
        power_result: Dictionary from calculate_power.
        collinearity_result: Dictionary from check_collinearity.
        n_concepts: Number of concepts for Bonferroni correction.
        
    Returns:
        Dictionary containing all aggregated results.
    """
    # Apply Bonferroni correction if needed
    corrected_p_value = t_test_result['p_value']
    if n_concepts > 1:
        corrected_p_value = apply_bonferroni_correction(
            t_test_result['p_value'], n_concepts
        )
        
    # Build the aggregated result
    aggregated = {
        't_statistic': t_test_result['t_statistic'],
        'p_value': t_test_result['p_value'],
        'corrected_p_value': corrected_p_value,
        'test_type': t_test_result['test_type'],
        'effect_size_cohen_d': effect_size_result['effect_size_cohen_d'],
        'confidence_interval': effect_size_result['confidence_interval'],
        'inference_framing': frame_inference(),
        'ancova_results': ancova_result,
        'power_analysis': power_result,
        'collinearity_diagnostics': collinearity_result,
        'n_concepts': n_concepts
    }
    
    logger.info(f"Aggregated statistical results: t={aggregated['t_statistic']:.3f}, "
               f"p={aggregated['p_value']:.3f}, d={aggregated['effect_size_cohen_d']:.3f}")
               
    return aggregated

def write_partial_results(
    aggregated_results: Dict[str, Any],
    output_path: str
) -> None:
    """
    Write aggregated results to a JSON file.
    
    Args:
        aggregated_results: Dictionary from aggregate_stats_results.
        output_path: Path to output JSON file.
    """
    import json
    from pathlib import Path
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(aggregated_results, f, indent=2, default=str)
        
    logger.info(f"Partial results written to {output_path}")

def finalize_results(
    us2_results: Dict[str, Any],
    sensitivity_results: List[Dict[str, Any]],
    robustness_warning: bool,
    output_path: str
) -> None:
    """
    Merge US2 results with sensitivity analysis for final report.
    
    Args:
        us2_results: Dictionary from write_partial_results (US2).
        sensitivity_results: List of sensitivity sweep results.
        robustness_warning: Boolean flag for robustness warning.
        output_path: Path to final results JSON file.
    """
    import json
    from pathlib import Path
    
    final_report = {
        't_statistic': us2_results.get('t_statistic'),
        'p_value': us2_results.get('p_value'),
        'corrected_p_value': us2_results.get('corrected_p_value'),
        'effect_size_cohen_d': us2_results.get('effect_size_cohen_d'),
        'confidence_interval': us2_results.get('confidence_interval'),
        'inference_framing': us2_results.get('inference_framing'),
        'ancova_results': us2_results.get('ancova_results'),
        'sensitivity_analysis': sensitivity_results,
        'robustness_warning': robustness_warning
    }
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(final_report, f, indent=2, default=str)
        
    logger.info(f"Final results written to {output_path}")