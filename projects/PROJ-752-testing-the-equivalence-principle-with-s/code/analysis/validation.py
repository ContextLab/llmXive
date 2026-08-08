"""
Validation module for statistical model comparison.

Implements F-test and Bayesian Information Criterion (BIC) comparison
between Null (no equivalence principle violation) and Alternative
(differential acceleration present) models.
"""

import numpy as np
from typing import Tuple, Dict, Any, List, Optional
from dataclasses import dataclass, field
from scipy import stats
import json
import os

from utils.logging import get_logger, AnalysisError
from models.estimator import OrbitSolution

logger = get_logger(__name__)


@dataclass
class ModelComparisonResult:
    """Result of a statistical model comparison."""
    model_null: str
    model_alt: str
    f_statistic: float
    p_value: float
    bic_null: float
    bic_alt: float
    df_null: int
    df_alt: int
    df_diff: int
    ssr_null: float
    ssr_alt: float
    n_observations: int
    conclusion: str  # "reject_null" or "fail_to_reject"
    significance_level: float = 0.05

def compute_ssr(solution: OrbitSolution) -> float:
    """
    Compute Sum of Squared Residuals from an OrbitSolution.

    Args:
        solution: The orbit solution containing residuals.

    Returns:
        Sum of squared residuals.
    """
    if not hasattr(solution, 'residuals') or solution.residuals is None:
        raise AnalysisError("OrbitSolution has no residuals attribute")
    
    residuals = np.array(solution.residuals)
    return float(np.sum(residuals ** 2))

def compute_bic(ssr: float, n_params: int, n_obs: int) -> float:
    """
    Compute Bayesian Information Criterion.

    BIC = n * ln(SSE/n) + k * ln(n)

    Args:
        ssr: Sum of squared residuals.
        n_params: Number of parameters in the model.
        n_obs: Number of observations.

    Returns:
        BIC value.
    """
    if n_obs <= 0 or ssr <= 0:
        raise AnalysisError("Invalid input for BIC calculation")
    
    mse = ssr / n_obs
    bic = n_obs * np.log(mse) + n_params * np.log(n_obs)
    return float(bic)

def perform_f_test(
    ssr_null: float,
    df_null: int,
    ssr_alt: float,
    df_alt: int,
    significance_level: float = 0.05
) -> Tuple[float, float, str]:
    """
    Perform F-test comparing nested models.

    The F-statistic is:
    F = ((SSR_null - SSR_alt) / (df_null - df_alt)) / (SSR_alt / df_alt)

    Args:
        ssr_null: Sum of squared residuals for null model.
        df_null: Degrees of freedom for null model.
        ssr_alt: Sum of squared residuals for alternative model.
        df_alt: Degrees of freedom for alternative model.
        significance_level: Alpha level for test.

    Returns:
        Tuple of (f_statistic, p_value, conclusion).
    """
    if df_alt <= 0:
        raise AnalysisError("Alternative model must have positive degrees of freedom")
    
    df_diff = df_null - df_alt
    if df_diff <= 0:
        raise AnalysisError("Null model must have more degrees of freedom than alternative")
    
    # F-statistic calculation
    numerator = (ssr_null - ssr_alt) / df_diff
    denominator = ssr_alt / df_alt
    
    if denominator <= 0:
        raise AnalysisError("Denominator of F-statistic is non-positive")
    
    f_stat = numerator / denominator
    
    # P-value (one-tailed test)
    p_val = 1.0 - stats.f.cdf(f_stat, df_diff, df_alt)
    
    conclusion = "reject_null" if p_val < significance_level else "fail_to_reject"
    
    logger.info(
        f"F-test: F={f_stat:.4f}, p={p_val:.6f}, "
        f"conclusion={conclusion} (alpha={significance_level})"
    )
    
    return f_stat, p_val, conclusion

def compare_null_vs_alternative(
    solution_null: OrbitSolution,
    solution_alt: OrbitSolution,
    n_observations: int,
    significance_level: float = 0.05
) -> ModelComparisonResult:
    """
    Compare Null model (no EP violation) vs Alternative model (EP violation).

    Args:
        solution_null: Orbit solution for the null hypothesis (no differential acceleration).
        solution_alt: Orbit solution for the alternative hypothesis (with differential acceleration).
        n_observations: Total number of observations used in the fit.
        significance_level: Alpha level for hypothesis testing.

    Returns:
        ModelComparisonResult with F-test and BIC values.
    """
    # Extract SSR and parameters
    ssr_null = compute_ssr(solution_null)
    ssr_alt = compute_ssr(solution_alt)
    
    # Degrees of freedom: n_obs - n_params
    # Null model has 1 fewer parameter (no eta/ac)
    n_params_null = solution_null.n_params if hasattr(solution_null, 'n_params') else 10
    n_params_alt = solution_alt.n_params if hasattr(solution_alt, 'n_params') else 11
    
    df_null = n_observations - n_params_null
    df_alt = n_observations - n_params_alt
    
    logger.info(
        f"Model comparison: Null (df={df_null}, SSR={ssr_null:.4e}) vs "
        f"Alt (df={df_alt}, SSR={ssr_alt:.4e})"
    )
    
    # F-test
    f_stat, p_val, conclusion = perform_f_test(
        ssr_null, df_null, ssr_alt, df_alt, significance_level
    )
    
    # BIC calculation
    bic_null = compute_bic(ssr_null, n_params_null, n_observations)
    bic_alt = compute_bic(ssr_alt, n_params_alt, n_observations)
    
    logger.info(
        f"BIC comparison: Null={bic_null:.4f}, Alt={bic_alt:.4f}, "
        f"delta_BIC={bic_null - bic_alt:.4f}"
    )
    
    return ModelComparisonResult(
        model_null="Null (no EP violation)",
        model_alt="Alternative (EP violation)",
        f_statistic=f_stat,
        p_value=p_val,
        bic_null=bic_null,
        bic_alt=bic_alt,
        df_null=df_null,
        df_alt=df_alt,
        df_diff=df_null - df_alt,
        ssr_null=ssr_null,
        ssr_alt=ssr_alt,
        n_observations=n_observations,
        conclusion=conclusion,
        significance_level=significance_level
    )

def run_validation_analysis(
    solution_null: OrbitSolution,
    solution_alt: OrbitSolution,
    n_observations: int,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run full validation analysis pipeline.

    Args:
        solution_null: Null model solution.
        solution_alt: Alternative model solution.
        n_observations: Number of observations.
        output_path: Optional path to save results as JSON.

    Returns:
        Dictionary containing all comparison metrics.
    """
    result = compare_null_vs_alternative(solution_null, solution_alt, n_observations)
    
    output = {
        "model_null": result.model_null,
        "model_alt": result.model_alt,
        "f_statistic": result.f_statistic,
        "p_value": result.p_value,
        "bic_null": result.bic_null,
        "bic_alt": result.bic_alt,
        "delta_bic": result.bic_null - result.bic_alt,
        "df_null": result.df_null,
        "df_alt": result.df_alt,
        "df_diff": result.df_diff,
        "ssr_null": result.ssr_null,
        "ssr_alt": result.ssr_alt,
        "n_observations": result.n_observations,
        "conclusion": result.conclusion,
        "significance_level": result.significance_level,
        "interpretation": (
            "Evidence for EP violation" if result.conclusion == "reject_null" else
            "No significant evidence for EP violation"
        )
    }
    
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        logger.info(f"Validation results saved to {output_path}")
    
    return output

def main():
    """
    Main entry point for validation analysis.
    
    This function demonstrates the validation workflow with dummy data.
    In production, it would load actual OrbitSolution objects from disk.
    """
    logger.info("Starting validation analysis")
    
    # Create dummy solutions for demonstration
    # In real usage, these would be loaded from data/results/orbit_solutions.json
    class DummySolution:
        def __init__(self, ssr: float, n_params: int):
            self.residuals = np.sqrt(ssr / 100) * np.random.randn(100)
            self.n_params = n_params
    
    # Simulate a case where alternative model fits better
    n_obs = 1000
    solution_null = DummySolution(ssr=1.5 * n_obs, n_params=10)
    solution_alt = DummySolution(ssr=1.0 * n_obs, n_params=11)
    
    try:
        results = run_validation_analysis(
            solution_null,
            solution_alt,
            n_observations=n_obs,
            output_path="data/results/validation_comparison.json"
        )
        
        logger.info(f"Validation complete: {results['conclusion']}")
        logger.info(f"F-statistic: {results['f_statistic']:.4f}, p-value: {results['p_value']:.6f}")
        logger.info(f"BIC delta: {results['delta_bic']:.4f}")
        
        return results
        
    except AnalysisError as e:
        logger.error(f"Validation failed: {e}")
        raise

if __name__ == "__main__":
    main()
