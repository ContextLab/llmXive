import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Set, Any
import logging
from scipy import stats
from statsmodels.stats.multitest import multipletests

from config import get_path
from data_model import DesignType, AnalysisResult

logger = logging.getLogger(__name__)

def run_anova(df: pd.DataFrame, design_type: str) -> Dict[str, Any]:
    """
    Execute ANOVA based on design type.
    design_type: 'Within-Subjects' or 'Between-Subjects'
    Returns a dictionary of results including F-stat, p-values, and effect sizes.
    """
    results = {}
    
    if design_type == "Within-Subjects":
        # Mixed ANOVA: Repeated measures on Condition (Cyberball, Reward)
        # Assuming df has columns: 'ParticipantID', 'Condition', 'Mood', 'ReactionTime'
        # Grouping by ParticipantID for repeated measures
        pivot_df = df.pivot_table(
            index='ParticipantID', 
            columns='Condition', 
            values='Mood', 
            aggfunc='mean'
        )
        
        if pivot_df.shape[0] < 2 or pivot_df.shape[1] < 2:
            logger.warning("Insufficient data for Mixed ANOVA.")
            return {"error": "Insufficient data for Mixed ANOVA"}

        # Simple repeated measures ANOVA using scipy
        # scipy.stats.f_oneway does not handle repeated measures directly, 
        # so we use a simplified approach or statsmodels for full mixed model.
        # For this implementation, we'll use a basic repeated measures approach
        # by calculating differences or using statsmodels if available.
        # Here, we approximate with a paired t-test for each condition pair if needed,
        # but for ANOVA, we'll assume a structure suitable for statsmodels if complex.
        # Given constraints, we perform a one-way repeated measures ANOVA manually
        # or use statsmodels if imported. Let's use statsmodels for accuracy.
        
        try:
            from statsmodels.stats.anova import AnovaRM
            anova_model = AnovaRM(df, 'Mood', 'ParticipantID', within=['Condition'])
            anova_res = anova_model.fit()
            results['anova'] = anova_res.summary()
            results['f_stat'] = anova_res.anova_table['F value']['Condition']
            results['p_value'] = anova_res.anova_table['Pr > F']['Condition']
            results['effect_size'] = "Partial Eta Squared" # Placeholder for calculation
        except ImportError:
            logger.error("statsmodels not available for Mixed ANOVA.")
            return {"error": "statsmodels required for Mixed ANOVA"}

    elif design_type == "Between-Subjects":
        # One-Way ANOVA: Grouped by Condition (if Condition represents groups)
        # Or if we are comparing two distinct groups (e.g., Rejection vs Control)
        # Assuming 'Condition' defines the groups
        groups = [group["Mood"].values for name, group in df.groupby('Condition')]
        
        if len(groups) < 2:
            logger.warning("Insufficient groups for One-Way ANOVA.")
            return {"error": "Insufficient groups for One-Way ANOVA"}

        f_stat, p_val = stats.f_oneway(*groups)
        results['f_stat'] = f_stat
        results['p_value'] = p_val
        results['effect_size'] = "Eta Squared" # Placeholder
        logger.info(f"Between-Subjects ANOVA: F={f_stat:.4f}, p={p_val:.4f}")
    else:
        raise ValueError(f"Unknown design_type: {design_type}")

    return results

def apply_fdr(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.
    Returns adjusted p-values.
    """
    if not p_values:
        return []
    
    # multipletests returns (reject, p_corrected, p_corrected, alphacSidak, alphacBonf)
    # We need the second element: p_corrected (FDR adjusted)
    _, p_corrected, _, _ = multipletests(p_values, method='fdr_bh')
    return p_corrected.tolist()

def sensitivity_sweep(df: pd.DataFrame, alpha_set: Set[float]) -> pd.DataFrame:
    """
    Perform a sensitivity analysis by running the ANOVA at different alpha thresholds.
    
    Args:
        df: Preprocessed dataframe with 'ParticipantID', 'Condition', 'Mood'.
        alpha_set: Set of alpha thresholds (e.g., {0.01, 0.05, 0.1}).
        
    Returns:
        A DataFrame containing the results (F-stat, p-value, significance) for each alpha.
    """
    # Determine design type from the data or assume it's passed/contextual
    # For this function, we assume the design_type is already determined (e.g., from ingestion)
    # and we are just re-evaluating significance at different thresholds.
    # However, the ANOVA result (F and p) is independent of alpha.
    # The sweep checks if the result is significant at each alpha.
    
    # We need to run the ANOVA first to get the base statistics.
    # Since run_anova returns a dict, we extract the necessary stats.
    # We assume the design_type is "Within-Subjects" or "Between-Subjects" based on context.
    # If not passed, we might need to infer or default. 
    # For robustness, let's infer from the data structure if possible, 
    # but the task implies we are sweeping alpha on an existing analysis.
    # Let's assume we re-run the analysis to get the stats, then apply alphas.
    
    # Re-run analysis to get F and p
    # We need to know the design_type. Let's assume it's 'Within-Subjects' if ParticipantID exists as repeated,
    # else 'Between-Subjects'. Or we can check the unique conditions.
    # For simplicity, we'll assume the design_type is passed or inferred from the data's structure.
    # Since the function signature doesn't include design_type, we infer it.
    
    design_type = "Within-Subjects" if 'ParticipantID' in df.columns and df['ParticipantID'].nunique() > 1 else "Between-Subjects"
    
    # Run the ANOVA to get the base statistics
    anova_results = run_anova(df, design_type)
    
    if 'error' in anova_results:
        logger.error(f"Sensitivity sweep failed: {anova_results['error']}")
        return pd.DataFrame()

    f_stat = anova_results.get('f_stat')
    p_value = anova_results.get('p_value')
    
    if f_stat is None or p_value is None:
        logger.error("Could not extract F-stat or p-value for sensitivity sweep.")
        return pd.DataFrame()

    results = []
    for alpha in sorted(alpha_set):
        is_significant = p_value < alpha
        results.append({
            'alpha': alpha,
            'f_statistic': f_stat,
            'p_value': p_value,
            'significant': is_significant,
            'design_type': design_type
        })

    return pd.DataFrame(results)

def save_sensitivity_results(results_df: pd.DataFrame, output_path: str):
    """
    Save the sensitivity sweep results to a CSV file.
    """
    results_df.to_csv(output_path, index=False)
    logger.info(f"Sensitivity results saved to {output_path}")

def run_analysis_pipeline(df: pd.DataFrame, design_type: str, output_dir: str) -> Dict[str, Any]:
    """
    Main entry point for running the full analysis pipeline including ANOVA, FDR, and sensitivity.
    """
    # 1. Run ANOVA
    anova_res = run_anova(df, design_type)
    if 'error' in anova_res:
        return anova_res

    # 2. Collect p-values (if multiple, though here we have one primary)
    # For a single ANOVA, we might have multiple tests (e.g., main effects, interactions)
    # Assuming we extract the primary p-value for the condition effect.
    primary_p = anova_res.get('p_value')
    if primary_p is None:
        return {"error": "No p-value found in ANOVA results"}

    # 3. Apply FDR (even for single test, it's good practice to have the pipeline)
    # If there were multiple p-values, we'd pass the list. Here, we pass a list of one.
    p_fdr = apply_fdr([primary_p])[0]

    # 4. Sensitivity Sweep
    alpha_set = {0.01, 0.05, 0.1}
    sensitivity_df = sensitivity_sweep(df, alpha_set)
    
    # 5. Compile final results
    final_results = {
        'anova': anova_res,
        'p_fdr': p_fdr,
        'sensitivity_sweep': sensitivity_df.to_dict(orient='records')
    }

    # 6. Save outputs
    if output_dir:
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Save sensitivity results
        sens_path = os.path.join(output_dir, 'sensitivity_sweep.csv')
        sensitivity_df.to_csv(sens_path, index=False)
        
        # Save final JSON (simplified for this example)
        import json
        final_json_path = os.path.join(output_dir, 'analysis_results.json')
        # Convert non-serializable objects
        serializable_res = {
            'f_stat': float(anova_res.get('f_stat')),
            'p_value': float(anova_res.get('p_value')),
            'p_fdr': float(p_fdr),
            'design_type': design_type,
            'sensitivity_sweep': sensitivity_df.to_dict(orient='records')
        }
        with open(final_json_path, 'w') as f:
            json.dump(serializable_res, f, indent=2)
        
        logger.info(f"Analysis results saved to {output_dir}")

    return final_results
