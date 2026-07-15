import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.contingency_tables import mcnemar
from scipy.stats import chi2

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class McNemarResult:
    task_id: str
    original_passed: int
    original_failed: int
    perturbed_passed: int
    perturbed_failed: int
    statistic: float
    pvalue: float
    perturbation_type: str

@dataclass
class BonferroniResult:
    original_alpha: float
    corrected_alpha: float
    comparisons: int
    significant_results: List[Dict[str, Any]]

@dataclass
class MixedEffectsResult:
    coefficients: Dict[str, float]
    std_errors: Dict[str, float]
    pvalues: Dict[str, float]
    variance_components: Dict[str, float]
    model_summary: str

@dataclass
class SensitivityAnalysisResult:
    threshold: float
    retained_count: int
    total_candidates: int
    retention_rate: float
    mean_similarity_score: float
    std_similarity_score: float
    pass_at_1_original: float
    pass_at_1_perturbed: float
    degradation: float

def load_results_data(results_path: str) -> pd.DataFrame:
    """Load execution results from JSON into a DataFrame."""
    path = Path(results_path)
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    return pd.DataFrame(data)

def calculate_pass_at_1(df: pd.DataFrame, group_col: str = 'prompt_type') -> Dict[str, float]:
    """Calculate pass@1 rates for each group."""
    if 'passed' not in df.columns:
        raise ValueError("DataFrame must contain 'passed' column")
    
    pass_rates = df.groupby(group_col)['passed'].mean()
    return pass_rates.to_dict()

def mcnemar_test_for_task(task_id: str, df: pd.DataFrame) -> McNemarResult:
    """Perform McNemar's test for a single task."""
    task_data = df[df['task_id'] == task_id]
    
    if task_data.empty:
        raise ValueError(f"No data found for task {task_id}")
    
    # Pivot to create contingency table
    # Rows: Original (Passed, Failed)
    # Cols: Perturbed (Passed, Failed)
    contingency = pd.crosstab(
        task_data['original_result'], 
        task_data['perturbed_result']
    )
    
    # Ensure we have the right structure
    if contingency.shape != (2, 2):
        # Pad with zeros if necessary
        contingency = contingency.reindex(
            index=['passed', 'failed'], 
            columns=['passed', 'failed'], 
            fill_value=0
        )
    
    b = contingency.loc['passed', 'failed']  # Original passed, perturbed failed
    c = contingency.loc['failed', 'passed']  # Original failed, perturbed passed
    
    if b + c == 0:
        return McNemarResult(
            task_id=task_id,
            original_passed=int(contingency.loc['passed', 'passed']) + int(b),
            original_failed=int(contingency.loc['failed', 'failed']) + int(c),
            perturbed_passed=int(contingency.loc['passed', 'passed']) + int(c),
            perturbed_failed=int(contingency.loc['failed', 'failed']) + int(b),
            statistic=0.0,
            pvalue=1.0,
            perturbation_type=task_data['perturbation_type'].iloc[0] if 'perturbation_type' in task_data.columns else 'unknown'
        )
    
    stat, pval = mcnemar(contingency, exact=False)
    
    return McNemarResult(
        task_id=task_id,
        original_passed=int(contingency.loc['passed', 'passed']) + int(b),
        original_failed=int(contingency.loc['failed', 'failed']) + int(c),
        perturbed_passed=int(contingency.loc['passed', 'passed']) + int(c),
        perturbed_failed=int(contingency.loc['failed', 'failed']) + int(b),
        statistic=float(stat),
        pvalue=float(pval),
        perturbation_type=task_data['perturbation_type'].iloc[0] if 'perturbation_type' in task_data.columns else 'unknown'
    )

def aggregate_mcnemar_tests(df: pd.DataFrame) -> List[McNemarResult]:
    """Aggregate McNemar tests across all tasks."""
    task_ids = df['task_id'].unique()
    results = []
    
    for task_id in task_ids:
        try:
            result = mcnemar_test_for_task(task_id, df)
            results.append(result)
        except Exception as e:
            logger.warning(f"McNemar test failed for task {task_id}: {e}")
            continue
    
    return results

def apply_bonferroni_correction(results: List[McNemarResult], alpha: float = 0.05) -> BonferroniResult:
    """Apply Bonferroni correction for multiple comparisons."""
    comparisons = len(results)
    if comparisons == 0:
        return BonferroniResult(
            original_alpha=alpha,
            corrected_alpha=alpha,
            comparisons=0,
            significant_results=[]
        )
    
    corrected_alpha = alpha / comparisons
    
    significant = []
    for r in results:
        if r.pvalue < corrected_alpha:
            significant.append({
                'task_id': r.task_id,
                'pvalue': r.pvalue,
                'statistic': r.statistic,
                'perturbation_type': r.perturbation_type
            })
    
    return BonferroniResult(
        original_alpha=alpha,
        corrected_alpha=corrected_alpha,
        comparisons=comparisons,
        significant_results=significant
    )

def run_mcnemar_analysis(df: pd.DataFrame, alpha: float = 0.05) -> Tuple[List[McNemarResult], BonferroniResult]:
    """Run complete McNemar analysis pipeline."""
    results = aggregate_mcnemar_tests(df)
    corrected = apply_bonferroni_correction(results, alpha)
    return results, corrected

def run_mixed_effects_logistic_regression(df: pd.DataFrame) -> MixedEffectsResult:
    """Run mixed-effects logistic regression with task as random effect."""
    # Prepare data
    df['outcome'] = df['passed'].astype(int)
    df['is_perturbed'] = df['prompt_type'].apply(lambda x: 1 if x == 'perturbed' else 0)
    
    # Create dummy variables for perturbation type
    if 'perturbation_type' in df.columns:
        perturbation_dummies = pd.get_dummies(df['perturbation_type'], prefix='pert_type')
        df = pd.concat([df, perturbation_dummies], axis=1)
    
    # Fixed effects: is_perturbed and perturbation types
    fixed_cols = ['is_perturbed']
    if 'perturbation_type' in df.columns:
        fixed_cols.extend([col for col in df.columns if col.startswith('pert_type')])
    
    # Random effect: task_id
    formula = f"outcome ~ {' + '.join(fixed_cols)}"
    
    try:
        model = sm.MixedLM.from_formula(
            formula,
            df,
            groups=df['task_id'],
            re_formula="1"
        )
        result = model.fit()
        
        return MixedEffectsResult(
            coefficients=result.fe_params.to_dict(),
            std_errors=result.bse_fe.to_dict(),
            pvalues=result.pvalues.to_dict(),
            variance_components={'task_variance': result.cov_re.iloc[0, 0] if hasattr(result, 'cov_re') else 0.0},
            model_summary=str(result.summary())
        )
    except Exception as e:
        logger.error(f"Mixed-effects model failed: {e}")
        return MixedEffectsResult(
            coefficients={},
            std_errors={},
            pvalues={},
            variance_components={},
            model_summary=f"Model fitting failed: {str(e)}"
        )

def run_sensitivity_analysis(
    results_df: pd.DataFrame,
    perturbation_df: pd.DataFrame,
    thresholds: List[float] = [0.90, 0.92, 0.94, 0.95, 0.96, 0.97, 0.98]
) -> List[SensitivityAnalysisResult]:
    """
    Run sensitivity analysis on semantic thresholds.
    
    Args:
        results_df: DataFrame with execution results (passed/failed)
        perturbation_df: DataFrame with perturbation metadata and similarity scores
        thresholds: List of threshold values to test
    
    Returns:
        List of SensitivityAnalysisResult objects for each threshold
    """
    if 'semantic_similarity' not in perturbation_df.columns:
        raise ValueError("perturbation_df must contain 'semantic_similarity' column")
    
    if 'passed' not in results_df.columns:
        raise ValueError("results_df must contain 'passed' column")
    
    sensitivity_results = []
    
    for threshold in thresholds:
        # Filter perturbations that meet the threshold
        filtered_perturbations = perturbation_df[perturbation_df['semantic_similarity'] > threshold]
        total_candidates = len(perturbation_df)
        retained_count = len(filtered_perturbations)
        retention_rate = retained_count / total_candidates if total_candidates > 0 else 0.0
        
        # Calculate similarity statistics for retained
        if retained_count > 0:
            mean_sim = filtered_perturbations['semantic_similarity'].mean()
            std_sim = filtered_perturbations['semantic_similarity'].std()
        else:
            mean_sim = 0.0
            std_sim = 0.0
        
        # Calculate pass@1 for original and perturbed at this threshold
        # Join results with filtered perturbations
        if 'task_id' in filtered_perturbations.columns and 'task_id' in results_df.columns:
            merged = results_df.merge(
                filtered_perturbations[['task_id', 'prompt_type']], 
                on='task_id', 
                how='inner'
            )
            
            if 'prompt_type' in merged.columns:
                pass_rates = merged.groupby('prompt_type')['passed'].mean()
                pass_original = pass_rates.get('original', 0.0)
                pass_perturbed = pass_rates.get('perturbed', 0.0)
            else:
                # Fallback if no prompt_type
                pass_original = results_df[results_df['prompt_type'] == 'original']['passed'].mean() if 'prompt_type' in results_df.columns else 0.0
                pass_perturbed = results_df[results_df['prompt_type'] == 'perturbed']['passed'].mean() if 'prompt_type' in results_df.columns else 0.0
        else:
            # Fallback if no task_id match
            pass_original = results_df[results_df['prompt_type'] == 'original']['passed'].mean() if 'prompt_type' in results_df.columns else 0.0
            pass_perturbed = results_df[results_df['prompt_type'] == 'perturbed']['passed'].mean() if 'prompt_type' in results_df.columns else 0.0
        
        degradation = pass_original - pass_perturbed if pass_original > 0 else 0.0
        
        sensitivity_results.append(SensitivityAnalysisResult(
            threshold=threshold,
            retained_count=retained_count,
            total_candidates=total_candidates,
            retention_rate=retention_rate,
            mean_similarity_score=mean_sim,
            std_similarity_score=std_sim,
            pass_at_1_original=pass_original,
            pass_at_1_perturbed=pass_perturbed,
            degradation=degradation
        ))
    
    return sensitivity_results

def main():
    """Main entry point for statistics analysis."""
    # Example usage
    print("Statistics module loaded successfully")
    print("Available functions:")
    print("  - load_results_data(path)")
    print("  - calculate_pass_at_1(df, group_col)")
    print("  - mcnemar_test_for_task(task_id, df)")
    print("  - aggregate_mcnemar_tests(df)")
    print("  - apply_bonferroni_correction(results, alpha)")
    print("  - run_mcnemar_analysis(df, alpha)")
    print("  - run_mixed_effects_logistic_regression(df)")
    print("  - run_sensitivity_analysis(results_df, perturbation_df, thresholds)")

if __name__ == "__main__":
    main()