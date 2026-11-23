import logging
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np
import pandas as pd
import statsmodels.api as sm
from code.utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class PublicationBiasResult:
    """Result container for publication bias assessment."""
    n_studies: int
    eggers_intercept: Optional[float]
    eggers_p_value: Optional[float]
    eggers_t_stat: Optional[float]
    is_significant_bias: Optional[bool]
    assessment: str
    warning: Optional[str] = None

def perform_eggers_test(
    effect_sizes: List[float],
    standard_errors: List[float]
) -> Tuple[float, float, float]:
    """
    Perform Egger's regression test for funnel plot asymmetry.
    
    Args:
        effect_sizes: List of effect sizes (e.g., Hedges' g).
        standard_errors: List of standard errors corresponding to effect sizes.
        
    Returns:
        Tuple of (intercept, p_value, t_statistic)
        
    Raises:
        ValueError: If inputs are invalid or insufficient for regression.
    """
    if len(effect_sizes) != len(standard_errors):
        raise ValueError("effect_sizes and standard_errors must have the same length.")
    
    n = len(effect_sizes)
    if n < 2:
        raise ValueError("Egger's test requires at least 2 studies.")
        
    # Precision (inverse of standard error)
    precision = 1.0 / np.array(standard_errors)
    effect_arr = np.array(effect_sizes)
    
    # Standard normal deviate (SND) = Effect / SE
    snd = effect_arr / np.array(standard_errors)
    
    # Regression: SND ~ 1 + Precision
    X = sm.add_constant(precision)
    y = snd
    
    try:
        model = sm.OLS(y, X).fit()
        intercept = model.params[0]
        p_value = model.pvalues[0]
        t_stat = model.tvalues[0]
        return float(intercept), float(p_value), float(t_stat)
    except Exception as e:
        logger.error(f"Egger's test regression failed: {e}")
        raise

def assess_publication_bias(
    effect_sizes: List[float],
    standard_errors: List[float],
    threshold_n: int = 10
) -> PublicationBiasResult:
    """
    Assess publication bias with conditional logic based on study count.
    
    Implements FR-014: Suppress funnel plot/Egger's test if N < threshold_n
    and return a descriptive assessment with a warning.
    
    Args:
        effect_sizes: List of effect sizes.
        standard_errors: List of standard errors.
        threshold_n: Minimum number of studies required for statistical tests.
        
    Returns:
        PublicationBiasResult object with assessment and optional warning.
    """
    n = len(effect_sizes)
    
    if n < threshold_n:
        warning_msg = (
            f"Publication bias assessment suppressed: Only {n} studies available. "
            f"Egger's test and funnel plot require at least {threshold_n} studies "
            "to be statistically reliable (FR-014)."
        )
        logger.warning(warning_msg)
        return PublicationBiasResult(
            n_studies=n,
            eggers_intercept=None,
            eggers_p_value=None,
            eggers_t_stat=None,
            is_significant_bias=None,
            assessment="Insufficient studies for statistical assessment of publication bias.",
            warning=warning_msg
        )
    
    try:
        intercept, p_value, t_stat = perform_eggers_test(effect_sizes, standard_errors)
        is_significant = p_value < 0.05
        
        assessment = (
            f"No significant publication bias detected (Egger's intercept={intercept:.3f}, "
            f"p={p_value:.3f})."
            if not is_significant
            else (
                f"Significant publication bias detected (Egger's intercept={intercept:.3f}, "
                f"p={p_value:.3f}). Caution in interpreting pooled effects."
            )
        )
        
        return PublicationBiasResult(
            n_studies=n,
            eggers_intercept=intercept,
            eggers_p_value=p_value,
            eggers_t_stat=t_stat,
            is_significant_bias=is_significant,
            assessment=assessment,
            warning=None
        )
    except Exception as e:
        error_msg = f"Publication bias assessment failed: {str(e)}"
        logger.error(error_msg)
        return PublicationBiasResult(
            n_studies=n,
            eggers_intercept=None,
            eggers_p_value=None,
            eggers_t_stat=None,
            is_significant_bias=None,
            assessment=f"Assessment failed due to error: {str(e)}",
            warning=error_msg
        )

def save_bias_results(result: PublicationBiasResult, output_path: str) -> None:
    """
    Save publication bias results to a JSON file.
    
    Args:
        result: PublicationBiasResult object.
        output_path: Path to the output JSON file.
    """
    import json
    
    data = {
        "n_studies": result.n_studies,
        "eggers_intercept": result.eggers_intercept,
        "eggers_p_value": result.eggers_p_value,
        "eggers_t_stat": result.eggers_t_stat,
        "is_significant_bias": result.is_significant_bias,
        "assessment": result.assessment,
        "warning": result.warning
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Publication bias results saved to {output_path}")

def main() -> None:
    """
    Main entry point for publication bias assessment.
    Loads cleaned studies, calculates effect sizes if needed, and assesses bias.
    """
    from code.analysis.effect_sizes import calculate_effect_sizes_from_studies
    from code.data.models import Study
    from code.utils.config import get_data_path
    
    config = get_data_path()
    studies_path = config / "processed" / "cleaned_studies.csv"
    bias_output_path = config / "processed" / "publication_bias.json"
    
    if not studies_path.exists():
        logger.error(f"Cleaned studies file not found: {studies_path}")
        return
        
    df = pd.read_csv(studies_path)
    
    # Convert DataFrame rows to Study objects
    studies = []
    for _, row in df.iterrows():
        study = Study(
            study_id=row['study_id'],
            author=row['author'],
            year=int(row['year']),
            n_total=int(row['n_total']),
            intervention_n=int(row['intervention_n']),
            control_n=int(row['control_n']),
            mean_intervention=row['mean_intervention'],
            sd_intervention=row['sd_intervention'],
            mean_control=row['mean_control'],
            sd_control=row['sd_control'],
            mindfulness_components=row['mindfulness_components'],
            delivery_format=row['delivery_format'],
            social_skill_domain=row['social_skill_domain'],
            follow_up_months=int(row['follow_up_months']) if pd.notna(row['follow_up_months']) else None
        )
        studies.append(study)
        
    logger.info(f"Loaded {len(studies)} studies for publication bias assessment.")
    
    # Calculate effect sizes
    effect_size_results = calculate_effect_sizes_from_studies(studies)
    
    if not effect_size_results:
        logger.warning("No effect sizes calculated. Cannot assess publication bias.")
        return
        
    effect_sizes = [r.effect_size for r in effect_size_results]
    standard_errors = [r.standard_error for r in effect_size_results]
    
    # Assess bias with threshold N=10 (FR-014)
    bias_result = assess_publication_bias(effect_sizes, standard_errors, threshold_n=10)
    
    # Save results
    save_bias_results(bias_result, str(bias_output_path))
    
    # Print summary
    print("\n" + "="*60)
    print("PUBLICATION BIAS ASSESSMENT SUMMARY")
    print("="*60)
    print(f"Number of studies: {bias_result.n_studies}")
    if bias_result.warning:
        print(f"WARNING: {bias_result.warning}")
    print(f"Assessment: {bias_result.assessment}")
    if bias_result.eggers_intercept is not None:
        print(f"Egger's Intercept: {bias_result.eggers_intercept:.4f}")
        print(f"Egger's p-value: {bias_result.eggers_p_value:.4f}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
