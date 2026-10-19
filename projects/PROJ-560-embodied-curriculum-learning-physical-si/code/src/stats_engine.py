import logging
from typing import List, Tuple, Dict, Any, Optional, Set
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.formula.api import ols
from statsmodels.stats.power import TTestIndPower
from config import INFERENTIAL_FRAMING_STRING

logger = logging.getLogger(__name__)

def run_t_test(pre_scores: List[float], post_scores: List[float], instruction_types: List[str], group_label: str='instruction_type') -> Dict[str, Any]:
    """
    Perform t-test on gain scores between groups.

    Uses Welch's t-test if variances are unequal (Levene's test),
    otherwise Student's t-test.
    """
    # Compute gain scores
    gains = np.array(post_scores) - np.array(pre_scores)
    df = pd.DataFrame({
        'gain_score': gains,
        group_label: instruction_types
    })

    # Split groups
    group_vals = df[group_label].unique()
    if len(group_vals) != 2:
        raise ValueError(f"Expected exactly two instruction types, found {group_vals}")
    g1 = df[df[group_label] == group_vals[0]]['gain_score']
    g2 = df[df[group_label] == group_vals[1]]['gain_score']

    # Levene's test for equal variances
    lev_stat, lev_p = stats.levene(g1, g2)
    equal_var = lev_p >= 0.05

    t_res = stats.ttest_ind(g1, g2, equal_var=equal_var)
    test_type = 'Student' if equal_var else 'Welch'

    return {
        't_statistic': t_res.statistic,
        'p_value': t_res.pvalue,
        'test_type': test_type,
        'degrees_of_freedom': t_res.df if hasattr(t_res, 'df') else None
    }

def run_ancova(pre_scores: List[float], post_scores: List[float], instruction_types: List[str], group_label: str='instruction_type') -> Dict[str, Any]:
    """
    Perform ANCOVA adjusting for pre-test scores.
    """
    df = pd.DataFrame({
        'pre': pre_scores,
        'post': post_scores,
        'gain': np.array(post_scores) - np.array(pre_scores),
        group_label: instruction_types
    })
    # Encode group as categorical
    df[group_label] = df[group_label].astype('category')
    model = ols('post ~ pre + C({})'.format(group_label), data=df).fit()
    anova_table = statsmodels.api.stats.anova_lm(model, typ=2)
    # Extract F and p for the group effect
    group_row = anova_table.loc['C({})'.format(group_label)]
    return {
        'ancova_f_statistic': group_row['F'],
        'ancova_p_value': group_row['PR(>F)'],
        'ancova_effect_size': None  # Placeholder; could compute partial eta-squared
    }

def calculate_effect_size(pre_scores: List[float], post_scores: List[float], instruction_types: List[str]) -> Dict[str, Any]:
    """
    Calculate Cohen's d and 95% confidence interval for the gain scores.
    """
    gains = np.array(post_scores) - np.array(pre_scores)
    df = pd.DataFrame({
        'gain_score': gains,
        'instruction_type': instruction_types
    })
    groups = df['instruction_type'].unique()
    g1 = df[df['instruction_type'] == groups[0]]['gain_score']
    g2 = df[df['instruction_type'] == groups[1]]['gain_score']

    # Pooled standard deviation
    n1, n2 = len(g1), len(g2)
    s1, s2 = g1.std(ddof=1), g2.std(ddof=1)
    s_pooled = np.sqrt(((n1 - 1) * s1 ** 2 + (n2 - 1) * s2 ** 2) / (n1 + n2 - 2))
    d = (g1.mean() - g2.mean()) / s_pooled

    # Confidence interval for d using approximate method
    se = np.sqrt((n1 + n2) / (n1 * n2) + (d ** 2) / (2 * (n1 + n2)))
    ci_low = d - 1.96 * se
    ci_high = d + 1.96 * se

    return {
        'effect_size_cohen_d': d,
        'confidence_interval': (ci_low, ci_high)
    }

def detect_multiple_concepts(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Detect distinct concept columns. For simplicity, any column that is not
    pre_test_score, post_test_score, instruction_type, or gain_score is
    considered a separate concept.
    """
    exclude = {'pre_test_score', 'post_test_score', 'instruction_type', 'gain_score'}
    concept_cols = [c for c in df.columns if c not in exclude]
    return {
        'n_concepts': len(concept_cols),
        'concept_ids': concept_cols
    }

def apply_bonferroni_correction(p_value: float, n_concepts: int) -> float:
    """
    Apply Bonferroni correction to a p-value.
    """
    return min(p_value * n_concepts, 1.0)

def frame_inference() -> str:
    """
    Return the standard inferential framing string.
    """
    return INFERENTIAL_FRAMING_STRING

def check_collinearity(df: pd.DataFrame, predictors: List[str]) -> Dict[str, Any]:
    """
    Check for high collinearity between predictor columns.
    """
    high_corr_pairs = []
    warnings = []
    for i in range(len(predictors)):
        for j in range(i + 1, len(predictors)):
            col1, col2 = predictors[i], predictors[j]
            if col1 in df.columns and col2 in df.columns:
                corr = df[[col1, col2]].corr().iloc[0, 1]
                if abs(corr) > 0.8:
                    high_corr_pairs.append((col1, col2, corr))
    if high_corr_pairs:
        warnings.append(f"High collinearity detected: {high_corr_pairs}")
    return {
        'high_correlation_pairs': high_corr_pairs,
        'warnings': warnings
    }

def calculate_power(pre_scores: List[float], post_scores: List[float], instruction_types: List[str]) -> Dict[str, Any]:
    """
    Calculate achieved statistical power for the observed effect size.
    """
    effect_dict = calculate_effect_size(pre_scores, post_scores, instruction_types)
    d = effect_dict['effect_size_cohen_d']
    # Sample sizes per group
    df = pd.DataFrame({
        'gain': np.array(post_scores) - np.array(pre_scores),
        'instruction_type': instruction_types
    })
    groups = df['instruction_type'].unique()
    n1 = len(df[df['instruction_type'] == groups[0]])
    n2 = len(df[df['instruction_type'] == groups[1]])
    power_analysis = TTestIndPower()
    power = power_analysis.power(effect_size=d, nobs1=n1, nobs2=n2, alpha=0.05, ratio=n2 / n1)
    return {
        'achieved_power': power,
        'is_underpowered': power < 0.80
    }

def aggregate_stats_results(t_test_result: Dict[str, Any],
                           ancova_result: Dict[str, Any],
                           effect_size_result: Dict[str, Any],
                           collinearity_result: Dict[str, Any],
                           power_result: Dict[str, Any],
                           n_concepts: int) -> Dict[str, Any]:
    """
    Combine all statistical results into a single dictionary matching the contract.
    """
    corrected_p = apply_bonferroni_correction(t_test_result['p_value'], n_concepts)
    robustness_flag = False  # placeholder; actual flag comes from sensitivity analysis
    return {
        't_statistic': t_test_result['t_statistic'],
        'p_value': t_test_result['p_value'],
        'corrected_p_value': corrected_p,
        'degrees_of_freedom': t_test_result.get('degrees_of_freedom'),
        'test_type': t_test_result['test_type'],
        'ancova_f_statistic': ancova_result.get('ancova_f_statistic'),
        'ancova_p_value': ancova_result.get('ancova_p_value'),
        'ancova_effect_size': ancova_result.get('ancova_effect_size'),
        'effect_size_cohen_d': effect_size_result['effect_size_cohen_d'],
        'confidence_interval': effect_size_result['confidence_interval'],
        'inference_framing': frame_inference(),
        'collinearity_warnings': collinearity_result['warnings'],
        'power_achieved': power_result['achieved_power'],
        'power_flag': 'underpowered' if power_result['is_underpowered'] else 'adequate',
        'sensitivity_analysis': [],  # to be filled by caller
        'robustness_warning': robustness_flag
    }

def finalize_results(df: pd.DataFrame,
                     sensitivity_results: List[Dict[str, Any]],
                     robustness_warning: bool) -> Dict[str, Any]:
    """
    Run the full statistical pipeline and return a JSON‑serialisable dict.
    """
    # Extract required columns
    pre = df['pre_test_score'].tolist()
    post = df['post_test_score'].tolist()
    instr = df['instruction_type'].tolist()

    # Run analyses
    t_res = run_t_test(pre, post, instr)
    ancova_res = run_ancova(pre, post, instr)
    es_res = calculate_effect_size(pre, post, instr)
    col_res = check_collinearity(df, predictors=['pre_test_score', 'post_test_score'])
    power_res = calculate_power(pre, post, instr)
    concept_info = detect_multiple_concepts(df)

    # Assemble final dict
    final = aggregate_stats_results(
        t_test_result=t_res,
        ancova_result=ancova_res,
        effect_size_result=es_res,
        collinearity_result=col_res,
        power_result=power_res,
        n_concepts=concept_info['n_concepts']
    )
    # Attach sensitivity sweep results
    final['sensitivity_analysis'] = sensitivity_results
    final['robustness_warning'] = robustness_warning
    return final
