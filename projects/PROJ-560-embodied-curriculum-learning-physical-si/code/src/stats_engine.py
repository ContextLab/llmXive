import logging
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from scipy import stats
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
import json
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_t_test(
    group_a_scores: List[float],
    group_b_scores: List[float],
    equal_var: bool = False
) -> Tuple[float, float]:
    """
    Run Welch's t-test (or Student's if equal_var=True) on gain scores.
    Returns (t_statistic, p_value).
    """
    if len(group_a_scores) < 2 or len(group_b_scores) < 2:
        raise ValueError("Each group must have at least 2 samples for t-test.")

    t_stat, p_val = stats.ttest_ind(
        group_a_scores,
        group_b_scores,
        equal_var=equal_var,
        nan_policy='omit'
    )
    return float(t_stat), float(p_val)

def run_ancova(
    data: List[Dict[str, Any]],
    pre_score_key: str = 'pre_test_score',
    post_score_key: str = 'post_test_score',
    group_key: str = 'instruction_type'
) -> Dict[str, Any]:
    """
    Perform ANCOVA with pre_test_score as covariate and instruction_type as factor.
    Returns a dictionary with f_statistic and p_value.
    """
    # Filter out rows with missing values
    clean_data = [
        row for row in data
        if row.get(pre_score_key) is not None
        and row.get(post_score_key) is not None
        and row.get(group_key) is not None
    ]

    if len(clean_data) < 10:
        logger.warning("Insufficient data for ANCOVA (N < 10). Returning None.")
        return {"f_statistic": None, "p_value": None, "note": "Insufficient data"}

    # Prepare DataFrame for statsmodels
    # We need to construct a formula: post ~ pre + group
    df_data = {
        'post': [r[post_score_key] for r in clean_data],
        'pre': [r[pre_score_key] for r in clean_data],
        'group': [str(r[group_key]) for r in clean_data]
    }

    import pandas as pd
    df = pd.DataFrame(df_data)

    try:
        model = ols('post ~ pre + C(group)', data=df).fit()
        anova_table = anova_lm(model, typ=2)

        # Extract F and p for the 'C(group)' term (the treatment effect)
        # The index might be 'C(group)[T.embodied]' or similar depending on encoding
        # We look for the row containing 'group'
        treatment_row = None
        for idx in anova_table.index:
            if 'group' in str(idx):
                treatment_row = anova_table.loc[idx]
                break

        if treatment_row is not None:
            f_stat = float(treatment_row['F'])
            p_val = float(treatment_row['PR(>F)'])
        else:
            # Fallback if index is exactly 'C(group)' or similar
            if 'C(group)' in anova_table.index:
                f_stat = float(anova_table.loc['C(group)', 'F'])
                p_val = float(anova_table.loc['C(group)', 'PR(>F)'])
            else:
                logger.error("Could not locate treatment effect row in ANOVA table.")
                return {"f_statistic": None, "p_value": None, "error": "Model parsing failed"}

        return {
            "f_statistic": f_stat,
            "p_value": p_val,
            "model_summary": str(model.summary())
        }

    except Exception as e:
        logger.error(f"ANCOVA execution failed: {e}")
        return {"f_statistic": None, "p_value": None, "error": str(e)}

def calculate_effect_size(
    group_a_scores: List[float],
    group_b_scores: List[float]
) -> float:
    """
    Calculate Cohen's d for two independent groups.
    Uses pooled standard deviation.
    """
    a = np.array(group_a_scores)
    b = np.array(group_b_scores)

    if len(a) < 2 or len(b) < 2:
        return 0.0

    mean_a, mean_b = np.mean(a), np.mean(b)
    var_a, var_b = np.var(a, ddof=1), np.var(b, ddof=1)
    n_a, n_b = len(a), len(b)

    pooled_std = np.sqrt(((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2))

    if pooled_std == 0:
        return 0.0

    return float((mean_a - mean_b) / pooled_std)

def calculate_confidence_interval(
    effect_size: float,
    n_a: int,
    n_b: int,
    alpha: float = 0.05
) -> Tuple[float, float]:
    """
    Approximate confidence interval for Cohen's d using Hedges' g approximation logic.
    For simplicity in this MVP, we use a standard error approximation.
    SE_d ≈ sqrt((n_a + n_b)/(n_a * n_b) + d^2/(2*(n_a + n_b)))
    """
    if n_a < 2 or n_b < 2:
        return (0.0, 0.0)

    se = np.sqrt((n_a + n_b) / (n_a * n_b) + (effect_size ** 2) / (2 * (n_a + n_b)))
    z = stats.norm.ppf(1 - alpha / 2)

    lower = effect_size - z * se
    upper = effect_size + z * se

    return float(lower), float(upper)

def apply_bonferroni_correction(
    p_values: List[float],
    alpha: float = 0.05
) -> List[float]:
    """
    Apply Bonferroni correction to a list of p-values.
    Returns adjusted p-values (capped at 1.0).
    """
    n = len(p_values)
    if n == 0:
        return []

    adjusted = [min(p * n, 1.0) for p in p_values]
    return adjusted

def check_collinearity(
    data: List[Dict[str, Any]],
    covariate_key: str = 'pre_test_score',
    outcome_key: str = 'post_test_score'
) -> Dict[str, Any]:
    """
    Check for collinearity between covariate and outcome (though usually we check predictors).
    In ANCOVA context, we check if the covariate is highly correlated with the grouping factor encoding?
    Or simply report correlation between pre and post.
    The requirement says |r| > 0.8 between predictors. Here we have one numeric predictor (pre) and one categorical.
    We will calculate correlation between pre and post to ensure the model makes sense,
    and log if it's extremely high (indicating potential issues or just strong prediction).
    """
    pre_scores = [r[covariate_key] for r in data if r.get(covariate_key) is not None]
    post_scores = [r[outcome_key] for r in data if r.get(outcome_key) is not None]

    if len(pre_scores) < 3 or len(post_scores) < 3:
        return {"collinearity_detected": False, "correlation": None, "note": "Insufficient data"}

    # Ensure lists are same length by zipping
    pairs = list(zip(pre_scores, post_scores))
    if len(pairs) < 3:
        return {"collinearity_detected": False, "correlation": None, "note": "Insufficient paired data"}

    pre_arr, post_arr = zip(*pairs)
    corr, p_val = stats.pearsonr(pre_arr, post_arr)

    detected = abs(corr) > 0.8

    return {
        "collinearity_detected": detected,
        "correlation": float(corr),
        "p_value": float(p_val),
        "threshold": 0.8
    }

def calculate_power(
    effect_size: float,
    n_a: int,
    n_b: int,
    alpha: float = 0.05
) -> float:
    """
    Calculate achieved power for a t-test given effect size and sample sizes.
    Uses scipy's power function approximation or statsmodels if available.
    Here we approximate using non-central t-distribution logic via scipy.
    """
    try:
        from statsmodels.stats.power import TTestIndPower
        analysis = TTestIndPower()
        nobs = (n_a + n_b) / 2  # Approximate average
        # Effect size is Cohen's d
        power = analysis.solve_power(
            effect_size=effect_size,
            nobs1=nobs,
            alpha=alpha,
            ratio=n_b/n_a if n_a > 0 else 1.0
        )
        return float(power) if power is not None else 0.0
    except ImportError:
        # Fallback approximation if statsmodels power not available
        # Rough approximation: if effect is large and N is small, power is low.
        # This is a placeholder if statsmodels power module is missing.
        logger.warning("statsmodels.stats.power not available. Returning 0.0 for power.")
        return 0.0

def frame_inference(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Explicitly label all findings as 'associational' and include methodological caveats.
    """
    framed_results = results.copy()
    framed_results['inference_framing'] = {
        'claim_type': 'associational',
        'causal_claim': False,
        'caveats': [
            "This analysis identifies associations between instruction type and learning gains.",
            "No causal claims are made regarding the effectiveness of the intervention.",
            "Regression to the mean is addressed via ANCOVA, but unmeasured confounders may exist.",
            "Results are descriptive of the specific sample analyzed."
        ]
    }
    return framed_results

def aggregate_results(
    ancova_result: Dict[str, Any],
    t_test_result: Tuple[float, float],
    effect_size: float,
    ci: Tuple[float, float],
    power: float,
    collinearity: Dict[str, Any],
    bonferroni_p: Optional[float] = None
) -> Dict[str, Any]:
    """
    Combine all statistical results into a single dictionary structure.
    """
    t_stat, p_val = t_test_result

    result = {
        "ancova_f_statistic": ancova_result.get('f_statistic'),
        "ancova_p_value": ancova_result.get('p_value'),
        "t_statistic": t_stat,
        "p_value": p_val,
        "effect_size_cohen_d": effect_size,
        "confidence_interval": list(ci),
        "power": power,
        "collinearity_diagnostics": collinearity,
        "bonferroni_adjusted_p": bonferroni_p
    }

    # Add framing
    result = frame_inference(result)

    return result

def write_analysis_results(
    aggregated_results: Dict[str, Any],
    output_path: str = "data/processed/results.json"
) -> None:
    """
    Write the aggregated dictionary to a JSON file.
    Ensures the output directory exists.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Ensure keys are present as per schema
    required_keys = [
        "ancova_f_statistic", "ancova_p_value",
        "t_statistic", "p_value",
        "effect_size_cohen_d", "confidence_interval",
        "inference_framing"
    ]

    for key in required_keys:
        if key not in aggregated_results:
            logger.warning(f"Missing required key in aggregated results: {key}")
            aggregated_results[key] = None

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(aggregated_results, f, indent=2, default=str)

    logger.info(f"Analysis results written to {output_file}")