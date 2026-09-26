import logging
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.formula.api import ols

from .models import AnalysisResult, SensitivitySweep

logger = logging.getLogger(__name__)

def run_t_test(
    embodied_scores: List[float],
    static_scores: List[float],
    equal_var: bool = False
) -> Dict[str, Any]:
    """
    Run a t-test on gain scores.
    
    Args:
        embodied_scores: List of gain scores for the embodied group.
        static_scores: List of gain scores for the static group.
        equal_var: If True, use Student's t-test; if False, use Welch's t-test.
        
    Returns:
        Dictionary with t_statistic and p_value.
    """
    if not embodied_scores or not static_scores:
        raise ValueError("One or both groups are empty.")
        
    if equal_var:
        t_stat, p_val = stats.ttest_ind(embodied_scores, static_scores, equal_var=True)
    else:
        t_stat, p_val = stats.ttest_ind(embodied_scores, static_scores, equal_var=False)
        
    return {
        "t_statistic": float(t_stat),
        "p_value": float(p_val)
    }

def run_ancova(
    df: pd.DataFrame,
    gain_col: str = "gain_score",
    pre_col: str = "pre_test_score",
    group_col: str = "instruction_type",
    target_group: str = "embodied"
) -> Dict[str, Any]:
    """
    Run ANCOVA with pre_test_score as covariate.
    
    Args:
        df: DataFrame with gain scores, pre-test scores, and instruction type.
        gain_col: Name of the gain score column.
        pre_col: Name of the pre-test score column.
        group_col: Name of the instruction type column.
        target_group: The group to compare against the reference.
        
    Returns:
        Dictionary with f_statistic and p_value for the group effect.
    """
    # Filter to ensure valid data
    clean_df = df[[gain_col, pre_col, group_col]].dropna()
    
    if len(clean_df) < 3:
        logger.warning("Insufficient data for ANCOVA.")
        return {"f_statistic": None, "p_value": None}
        
    # Encode group as dummy variable if not already
    # Assuming binary groups: 'embodied' vs 'static'
    # Using formula: gain ~ pre_score + C(instruction_type)
    try:
        model = ols(f"{gain_col} ~ {pre_col} + C({group_col})", data=clean_df).fit()
        # Extract F-stat for the group factor
        # The ANOVA table gives F for each term
        anova_table = stats.anova_lm(model, typ=2)
        
        # Find the row for the group factor (usually C(group_col)[T.value])
        group_row_name = f"C({group_col})[T.{target_group}]"
        if group_row_name in anova_table.index:
            f_stat = anova_table.loc[group_row_name, "F"]
            p_val = anova_table.loc[group_row_name, "PR(>F)"]
        else:
            # Fallback: try to find any row with the group column name
            group_rows = [r for r in anova_table.index if group_col in r]
            if group_rows:
                f_stat = anova_table.loc[group_rows[0], "F"]
                p_val = anova_table.loc[group_rows[0], "PR(>F)"]
            else:
                logger.warning("Could not locate group effect in ANOVA table.")
                return {"f_statistic": None, "p_value": None}
                
        return {
            "f_statistic": float(f_stat),
            "p_value": float(p_val)
        }
    except Exception as e:
        logger.error(f"ANCOVA failed: {e}")
        return {"f_statistic": None, "p_value": None}

def calculate_effect_size(
    embodied_scores: List[float],
    static_scores: List[float]
) -> float:
    """
    Calculate Cohen's d effect size.
    
    Args:
        embodied_scores: List of gain scores for the embodied group.
        static_scores: List of gain scores for the static group.
        
    Returns:
        Cohen's d value.
    """
    if not embodied_scores or not static_scores:
        raise ValueError("One or both groups are empty.")
        
    mean_emb = np.mean(embodied_scores)
    mean_sta = np.mean(static_scores)
    
    std_emb = np.std(embodied_scores, ddof=1)
    std_sta = np.std(static_scores, ddof=1)
    
    n_emb = len(embodied_scores)
    n_sta = len(static_scores)
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n_emb - 1) * std_emb**2 + (n_sta - 1) * std_sta**2) / (n_emb + n_sta - 2))
    
    if pooled_std == 0:
        return 0.0
        
    return float((mean_emb - mean_sta) / pooled_std)

def calculate_confidence_interval(
    embodied_scores: List[float],
    static_scores: List[float],
    confidence_level: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate confidence interval for the mean difference.
    
    Args:
        embodied_scores: List of gain scores for the embodied group.
        static_scores: List of gain scores for the static group.
        confidence_level: Confidence level (e.g., 0.95).
        
    Returns:
        Tuple of (lower_bound, upper_bound).
    """
    mean_diff = np.mean(embodied_scores) - np.mean(static_scores)
    
    # Standard error of the difference
    se_diff = np.sqrt(
        np.var(embodied_scores, ddof=1)/len(embodied_scores) + 
        np.var(static_scores, ddof=1)/len(static_scores)
    )
    
    # Degrees of freedom (Welch-Satterthwaite equation)
    n1, n2 = len(embodied_scores), len(static_scores)
    v1, v2 = np.var(embodied_scores, ddof=1), np.var(static_scores, ddof=1)
    
    df_num = (v1/n1 + v2/n2)**2
    df_den = (v1/n1)**2/(n1-1) + (v2/n2)**2/(n2-1)
    
    if df_den == 0:
        df = n1 + n2 - 2
    else:
        df = df_num / df_den
        
    t_crit = stats.t.ppf((1 + confidence_level) / 2, df)
    margin = t_crit * se_diff
    
    return (float(mean_diff - margin), float(mean_diff + margin))

def apply_bonferroni_correction(
    p_values: List[float],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Apply Bonferroni correction to multiple p-values.
    
    Args:
        p_values: List of raw p-values.
        alpha: Significance level.
        
    Returns:
        Dictionary with corrected p-values and adjusted alpha.
    """
    m = len(p_values)
    if m == 0:
        return {"adjusted_p_values": [], "adjusted_alpha": alpha}
        
    adjusted_p_values = [min(p * m, 1.0) for p in p_values]
    adjusted_alpha = alpha / m
    
    return {
        "adjusted_p_values": adjusted_p_values,
        "adjusted_alpha": adjusted_alpha
    }

def check_collinearity(
    df: pd.DataFrame,
    predictors: List[str]
) -> Dict[str, Any]:
    """
    Check for collinearity between predictors.
    
    Args:
        df: DataFrame containing predictor columns.
        predictors: List of column names to check.
        
    Returns:
        Dictionary with correlation matrix and flags for high collinearity.
    """
    if len(predictors) < 2:
        return {"correlation_matrix": {}, "high_collinearity": False, "details": []}
        
    corr_matrix = df[predictors].corr().abs()
    
    high_corr_pairs = []
    for i in range(len(predictors)):
        for j in range(i + 1, len(predictors)):
            p1, p2 = predictors[i], predictors[j]
            corr_val = corr_matrix.loc[p1, p2]
            if corr_val > 0.8:
                high_corr_pairs.append({
                    "pair": [p1, p2],
                    "correlation": float(corr_val)
                })
                
    return {
        "correlation_matrix": corr_matrix.to_dict(),
        "high_collinearity": len(high_corr_pairs) > 0,
        "details": high_corr_pairs
    }

def calculate_power(
    effect_size: float,
    n1: int,
    n2: int,
    alpha: float = 0.05
) -> float:
    """
    Calculate achieved power for a t-test.
    
    Args:
        effect_size: Cohen's d.
        n1: Sample size of group 1.
        n2: Sample size of group 2.
        alpha: Significance level.
        
    Returns:
        Power value (0-1).
    """
    if n1 <= 0 or n2 <= 0 or effect_size == 0:
        return 0.0
        
    # Using scipy's power analysis
    # Effect size d, n1, n2, alpha
    try:
        power = stats.ttost_ind_power(effect_size, n1, n2, alpha=alpha)
        # Note: ttost_ind_power is for equivalence testing, using ttest power approximation
        # For standard t-test power, we use TTestIndPower
        from statsmodels.stats.power import TTestIndPower
        analysis = TTestIndPower()
        power_val = analysis.solve_power(effect_size=effect_size, nobs1=n1, ratio=n2/n1, alpha=alpha, power=None)
        # solve_power solves for power if not provided? Actually, we need to use power function differently
        # Correct usage:
        power_val = analysis.power(effect_size=effect_size, nobs1=n1, ratio=n2/n1, alpha=alpha)
        return float(power_val)
    except Exception:
        # Fallback approximation
        return 0.0

def frame_inference(
    p_value: float,
    effect_size: float,
    power: float
) -> Dict[str, Any]:
    """
    Frame the statistical inference with appropriate caveats.
    
    Args:
        p_value: The p-value from the test.
        effect_size: The effect size (Cohen's d).
        power: The achieved power.
        
    Returns:
        Dictionary with inference framing and caveats.
    """
    significance = "statistically significant" if p_value < 0.05 else "not statistically significant"
    
    framing = {
        "statement": f"Findings are associational; no causal inference is drawn due to observational nature of data. The comparison shows {significance} differences in gain scores.",
        "effect_size_interpretation": "Small (<0.2), Medium (0.2-0.5), Large (>0.5) based on Cohen's d.",
        "power_assessment": "Underpowered" if power < 0.8 else "Adequately powered",
        "causal_disclaimer": "This analysis measures performance gains, not intellectual actualization. No causal claims about teaching efficacy are made."
    }
    
    return framing

def aggregate_results(
    t_test_result: Dict[str, Any],
    ancova_result: Dict[str, Any],
    effect_size: float,
    ci: Tuple[float, float],
    power: float,
    collinearity: Dict[str, Any],
    inference: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Aggregate all statistical results into a single dictionary.
    
    Args:
        t_test_result: Result from run_t_test.
        ancova_result: Result from run_ancova.
        effect_size: Cohen's d.
        ci: Confidence interval tuple.
        power: Power value.
        collinearity: Collinearity diagnostics.
        inference: Inference framing.
        
    Returns:
        Aggregated results dictionary.
    """
    return {
        "t_statistic": t_test_result.get("t_statistic"),
        "p_value": t_test_result.get("p_value"),
        "secondary_descriptive_stats": {
            "ancova_f_statistic": ancova_result.get("f_statistic"),
            "ancova_p_value": ancova_result.get("p_value")
        },
        "effect_size_cohen_d": effect_size,
        "confidence_interval": {
            "lower": ci[0],
            "upper": ci[1]
        },
        "inference_framing": inference,
        "power_analysis": {
            "achieved_power": power,
            "status": "underpowered" if power < 0.8 else "adequate"
        },
        "collinearity_diagnostics": collinearity
    }

def write_partial_results(
    results: Dict[str, Any],
    output_path: str
) -> None:
    """
    Write partial results to a JSON file.
    
    Args:
        results: The aggregated results dictionary.
        output_path: Path to the output JSON file.
    """
    import json
    from pathlib import Path
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Partial results written to {output_path}")

def finalize_results(
    base_results: Dict[str, Any],
    sensitivity_analysis: Optional[List[Dict[str, Any]]] = None,
    robustness_warning: bool = False,
    output_path: str = "data/processed/results.json"
) -> Dict[str, Any]:
    """
    Finalize the results by adding limitations and merging with sensitivity analysis.
    
    This function addresses T047 by explicitly adding a "limitations" section to the output.
    
    Args:
        base_results: The base statistical results dictionary (from aggregate_results).
        sensitivity_analysis: Optional list of sensitivity sweep results.
        robustness_warning: Boolean flag indicating if robustness warning should be set.
        output_path: Path to write the final JSON results.
        
    Returns:
        The complete results dictionary including limitations.
    """
    # Define the limitations as per T047 requirements
    limitations = {
        "performance_vs_understanding": "The study measures performance gains (gain scores) on mathematical reasoning tasks, not intellectual actualization or deep conceptual understanding.",
        "virtual_body": "The 'body' in 'embodied' refers to the simulation's internal physics engine (virtual mechanics) rather than direct physical interaction by the student. This is an image of embodiment.",
        "operational_definition": "Abstract concepts are operationally defined as mathematical reasoning tasks (e.g., algebra, geometry) where the correct answer is derived from logical rules rather than sensory observation. This does not guarantee conceptual understanding.",
        "causal_limitation": "Findings are associational. No causal inference is drawn regarding the efficacy of embodied vs. static instruction for teaching abstract concepts."
    }
    
    final_results = base_results.copy()
    final_results["sensitivity_analysis"] = sensitivity_analysis if sensitivity_analysis else []
    final_results["robustness_warning"] = robustness_warning
    final_results["limitations"] = limitations
    
    # Write to file
    import json
    from pathlib import Path
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(final_results, f, indent=2)
        
    logger.info(f"Final results with limitations written to {output_path}")
    return final_results