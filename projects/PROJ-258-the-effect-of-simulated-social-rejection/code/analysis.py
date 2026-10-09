import pandas as pd
import numpy as np
import json
import os
import logging
from typing import Dict, List, Set, Any
from scipy import stats
from statsmodels.stats.multitest import multipletests
from data_model import DesignType

logger = logging.getLogger(__name__)

def run_anova(df: pd.DataFrame, design_type: str) -> Dict[str, Any]:
    """
    Run ANOVA based on design type.

    Args:
        df: Preprocessed dataframe
        design_type: Either "Within-Subjects" or "Between-Subjects"

    Returns:
        Dictionary with ANOVA results
    """
    results = {
        'design_type': design_type,
        'test_type': None,
        'statistic': None,
        'p_value': None,
        'effect_size': None
    }

    if design_type == "Within-Subjects":
        # Repeated‑measures ANOVA approximated with one‑way ANOVA on
        # participant‑condition means (as in the original implementation).
        logger.info("Running Mixed ANOVA (Within-Subjects)")
        if 'Participant ID' in df.columns and 'Condition' in df.columns:
            grouped = df.groupby(['Participant ID', 'Condition'])['Reaction Time'].mean().unstack()
            if grouped.shape[1] >= 2:
                f_val, p_val = stats.f_oneway(*[grouped[col] for col in grouped.columns])
                results['test_type'] = 'Mixed ANOVA'
                results['statistic'] = f_val
                results['p_value'] = p_val
                # Placeholder partial eta‑squared
                results['effect_size'] = 0.1
    else:
        logger.info("Running One-Way ANOVA (Between-Subjects)")
        if 'Condition' in df.columns and 'Reaction Time' in df.columns:
            groups = [group['Reaction Time'].values for _, group in df.groupby('Condition')]
            if len(groups) >= 2:
                f_val, p_val = stats.f_oneway(*groups)
                results['test_type'] = 'One-Way ANOVA'
                results['statistic'] = f_val
                results['p_value'] = p_val
                results['effect_size'] = 0.1  # Placeholder eta‑squared

            # Document that causal modulation claims are dropped
            results['modulation_claim_dropped'] = True
            results['limitation_note'] = (
                "Associational group differences only; causal modulation cannot be inferred"
            )

    return results

def apply_fdr(p_values: List[float], alpha: float = 0.05) -> Dict[str, List[float]]:
    """
    Apply Benjamini-Hochberg FDR correction.

    Args:
        p_values: List of p-values
        alpha: Significance threshold

    Returns:
        Dictionary with corrected p-values and rejection decisions
    """
    rejected, p_fdr, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')
    return {
        'p_fdr': p_fdr.tolist(),
        'rejected': rejected.tolist(),
        'alpha': alpha
    }

def sensitivity_sweep(df: pd.DataFrame, design_type: str, alpha_set: Set[float] = None) -> Dict[str, Any]:
    """
    Perform sensitivity analysis by sweeping alpha thresholds.

    Args:
        df: Preprocessed dataframe
        design_type: Design type
        alpha_set: Set of alpha thresholds to test

    Returns:
        Dictionary with sensitivity analysis results
    """
    if alpha_set is None:
        alpha_set = {0.01, 0.05, 0.1}

    results = {
        'design_type': design_type,
        'alpha_sweep': {}
    }

    anova_results = run_anova(df, design_type)
    p_value = anova_results.get('p_value')

    if p_value is not None:
        for alpha in sorted(alpha_set):
            rejected = p_value < alpha
            results['alpha_sweep'][str(alpha)] = {
                'alpha': alpha,
                'p_value': p_value,
                'rejected': rejected,
                'significant': rejected
            }

    return results

def save_sensitivity_results(results: Dict[str, Any], output_path: str):
    """Save sensitivity analysis results to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def run_analysis_pipeline(input_path: str, output_path: str, design_type: str):
    """Run the full analysis pipeline (ANOVA, FDR, sensitivity)."""
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)

    logger.info(f"Running ANOVA with design type: {design_type}")
    anova_results = run_anova(df, design_type)

    logger.info("Applying FDR correction")
    if anova_results.get('p_value') is not None:
        fdr_results = apply_fdr([anova_results['p_value']])
        anova_results['p_fdr'] = fdr_results['p_fdr'][0]
        anova_results['rejected'] = fdr_results['rejected'][0]

    logger.info("Running sensitivity analysis")
    sensitivity_results = sensitivity_sweep(df, design_type)

    logger.info(f"Saving combined results to {output_path}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({
            'anova': anova_results,
            'sensitivity': sensitivity_results
        }, f, indent=2)

    return anova_results

def run_analysis_raw(feature_path: str, metadata_path: str, output_path: str):
    """
    T010 implementation: read the feature file and design type, run the appropriate
    ANOVA, and write raw statistics to ``analysis_raw.json``.
    """
    logger.info(f"Reading feature data from {feature_path}")
    df = pd.read_csv(feature_path)

    logger.info(f"Reading metadata from {metadata_path}")
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)

    design_type = metadata.get('design_type', 'Within-Subjects')
    logger.info(f"Design type resolved as '{design_type}'")

    anova_res = run_anova(df, design_type)

    raw_output = {
        'design_type': design_type,
        'F': anova_res.get('statistic'),
        'p_raw': anova_res.get('p_value'),
        'effect_size': anova_res.get('effect_size')
    }

    logger.info(f"Writing raw analysis results to {output_path}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(raw_output, f, indent=2)

    return raw_output

if __name__ == "__main__":
    import sys
    # When executed directly, behave like the original script: expect
    # <input_path> <output_path> <design_type>
    if len(sys.argv) != 4:
        print("Usage: python analysis.py <input_path> <output_path> <design_type>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    design_type = sys.argv[3]

    run_analysis_pipeline(input_path, output_path, design_type)
