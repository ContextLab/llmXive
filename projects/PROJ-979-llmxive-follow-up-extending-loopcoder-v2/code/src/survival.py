import json
import csv
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import numpy as np
from lifelines import KaplanMeierFitter, CoxPHFitter
from lifelines.statistics import logrank_test
from scipy.stats import spearmanr

logger = logging.getLogger(__name__)

def load_entropy_results(path: str) -> pd.DataFrame:
    """Load entropy results from CSV."""
    if not Path(path).exists():
        raise FileNotFoundError(f"Entropy results not found at {path}")
    return pd.read_csv(path)

def load_convergence_results(path: str) -> pd.DataFrame:
    """Load convergence results from CSV."""
    if not Path(path).exists():
        raise FileNotFoundError(f"Convergence results not found at {path}")
    return pd.read_csv(path)

def prepare_survival_data(entropy_df: pd.DataFrame, convergence_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge entropy and convergence data for survival analysis.
    Expected columns in convergence_df: task_id, time_to_event, censored
    Expected columns in entropy_df: task_id, entropy
    """
    merged = pd.merge(entropy_df, convergence_df, on='task_id', how='inner')
    
    # Prepare survival data: event is NOT censored (True if event occurred)
    # In lifelines, event_observed=True means the event happened (not censored)
    merged['event_observed'] = ~merged['censored']
    
    return merged

def fit_kaplan_meier(df: pd.DataFrame, duration_col: str = 'time_to_event', 
                     event_col: str = 'event_observed') -> KaplanMeierFitter:
    """Fit Kaplan-Meier estimator."""
    kmf = KaplanMeierFitter()
    kmf.fit(durations=df[duration_col], event_observed=df[event_col])
    return kmf

def fit_cox_model(df: pd.DataFrame, duration_col: str = 'time_to_event',
                 event_col: str = 'event_observed', 
                 covariates: List[str] = ['entropy']) -> CoxPHFitter:
    """Fit Cox Proportional Hazards model."""
    cph = CoxPHFitter()
    # Select only the columns we need
    data_for_cox = df[covariates + [duration_col, event_col]].copy()
    cph.fit(data_for_cox, duration_col=duration_col, event_col=event_col)
    return cph

def calculate_concordance_index(cph: CoxPHFitter) -> float:
    """Calculate concordance index for the Cox model."""
    return cph.concordance_index_

def perform_power_analysis(survival_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform power analysis based on observed effect size.
    This is a simplified placeholder for actual power calculation.
    """
    # In a real implementation, we would use statsmodels or similar
    return {
        "power_analysis": "Placeholder - requires sample size and effect size calculation",
        "note": "Full power analysis requires additional statistical tools"
    }

def run_survival_analysis(entropy_path: str, convergence_path: str, 
                         output_path: str) -> Dict[str, Any]:
    """
    Run full survival analysis including KM and Cox PH.
    """
    logger.info(f"Loading entropy results from {entropy_path}")
    entropy_df = load_entropy_results(entropy_path)
    
    logger.info(f"Loading convergence results from {convergence_path}")
    convergence_df = load_convergence_results(convergence_path)
    
    logger.info("Preparing survival data")
    survival_df = prepare_survival_data(entropy_df, convergence_df)
    
    logger.info("Fitting Kaplan-Meier estimator")
    kmf = fit_kaplan_meier(survival_df)
    
    logger.info("Fitting Cox PH model")
    cph = fit_cox_model(survival_df)
    
    concordance = calculate_concordance_index(cph)
    
    results = {
        "concordance_index": concordance,
        "cox_model_summary": cph.summary.to_dict(),
        "km_median_survival": kmf.median_survival_time_,
        "sample_size": len(survival_df),
        "events_observed": int(survival_df['event_observed'].sum())
    }
    
    # Save results
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Survival analysis results saved to {output_path}")
    return results

def apply_holm_bonferroni(pvalues: List[float]) -> List[Dict[str, Any]]:
    """Apply Holm-Bonferroni correction to a list of p-values."""
    n = len(pvalues)
    if n == 0:
        return []
    
    # Sort p-values and keep track of original indices
    sorted_indices = sorted(range(n), key=lambda i: pvalues[i])
    sorted_pvalues = [pvalues[i] for i in sorted_indices]
    
    adjusted = []
    for i, p in enumerate(sorted_pvalues):
        # Holm-Bonferroni: p * (n - i)
        adjusted_p = min(p * (n - i), 1.0)
        adjusted.append({
            "original_index": sorted_indices[i],
            "original_pvalue": p,
            "adjusted_pvalue": adjusted_p
        })
    
    # Sort back to original order
    adjusted.sort(key=lambda x: x["original_index"])
    return adjusted

def check_cox_assumptions(cph: CoxPHFitter, df: pd.DataFrame, 
                         duration_col: str = 'time_to_event',
                         event_col: str = 'event_observed') -> Dict[str, Any]:
    """
    Check proportional hazards assumption for Cox PH model.
    Returns a dictionary with assumption check results and recommendations.
    """
    try:
        # lifelines provides check_assumptions method
        # This returns a dictionary with test results for each covariate
        assumptions = cph.check_assumptions(
            df[[duration_col, event_col] + ['entropy']],
            duration_col=duration_col,
            event_col=event_col,
            p_value_threshold=0.05
        )
        
        # The check_assumptions method prints warnings but we need to capture results
        # We'll re-run the check and capture the output
        import io
        import sys
        
        captured_output = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured_output
        
        try:
            cph.check_assumptions(
                df[[duration_col, event_col] + ['entropy']],
                duration_col=duration_col,
                event_col=event_col,
                p_value_threshold=0.05,
                show_plots=False
            )
        finally:
            sys.stdout = old_stdout
        
        output_text = captured_output.getvalue()
        
        # Parse the output to extract p-values and test results
        # This is a simplified parser - in production, use the actual return values
        results = {
            "assumptions_checked": True,
            "covariates": ['entropy'],
            "proportional_hazards_violated": False,
            "violations": [],
            "recommendations": [],
            "raw_output": output_text
        }
        
        # Check for violations in the output text
        if "PH test" in output_text:
            # Parse p-values from output
            lines = output_text.split('\n')
            for line in lines:
                if 'entropy' in line and 'p-value' in line:
                    # Extract p-value
                    try:
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if 'p-value' in part:
                                p_val = float(parts[i+1])
                                if p_val < 0.05:
                                    results["proportional_hazards_violated"] = True
                                    results["violations"].append({
                                        "covariate": "entropy",
                                        "p_value": p_val,
                                        "test": "Schoenfeld residuals"
                                    })
                                    results["recommendations"].append(
                                        "Consider using Time-Varying Coefficients or "
                                        "Accelerated Failure Time (AFT) model instead."
                                    )
                    except (ValueError, IndexError):
                        pass
        
        # If no specific violations found but assumptions_checked is True
        if not results["violations"] and results["assumptions_checked"]:
            results["recommendations"].append(
                "Proportional hazards assumption appears to hold for the tested covariates."
            )
        
        return results
        
    except Exception as e:
        logger.error(f"Error checking Cox assumptions: {e}")
        return {
            "assumptions_checked": False,
            "error": str(e),
            "recommendations": [
                "Could not verify assumptions. Consider manual inspection of Schoenfeld residuals.",
                "Alternative: Use non-parametric methods or AFT models."
            ]
        }

def main():
    """Main entry point for survival analysis with assumption checking."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run survival analysis with assumption checking")
    parser.add_argument("--entropy", type=str, required=True, 
                       help="Path to entropy results CSV")
    parser.add_argument("--convergence", type=str, required=True,
                       help="Path to convergence results CSV")
    parser.add_argument("--output", type=str, required=True,
                       help="Path to output JSON file")
    parser.add_argument("--assumptions-output", type=str, 
                       default="data/processed/survival_assumptions.json",
                       help="Path to save assumption check results")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    # Run survival analysis
    results = run_survival_analysis(
        args.entropy,
        args.convergence,
        args.output
    )
    
    # Load the data again for assumption checking
    entropy_df = load_entropy_results(args.entropy)
    convergence_df = load_convergence_results(args.convergence)
    survival_df = prepare_survival_data(entropy_df, convergence_df)
    
    # Fit Cox model for assumption checking
    cph = fit_cox_model(survival_df)
    
    # Check assumptions
    assumption_results = check_cox_assumptions(cph, survival_df)
    
    # Save assumption results
    assumptions_file = Path(args.assumptions_output)
    assumptions_file.parent.mkdir(parents=True, exist_ok=True)
    with open(assumptions_file, 'w') as f:
        json.dump(assumption_results, f, indent=2, default=str)
    
    logger.info(f"Assumption check results saved to {args.assumptions_output}")
    
    # Print summary
    print("\n=== Survival Analysis Assumption Check Summary ===")
    print(f"Assumptions checked: {assumption_results['assumptions_checked']}")
    print(f"PH assumption violated: {assumption_results.get('proportional_hazards_violated', False)}")
    if assumption_results.get('violations'):
        print("Violations found:")
        for v in assumption_results['violations']:
            print(f"  - {v['covariate']}: p={v['p_value']:.4f}")
    if assumption_results.get('recommendations'):
        print("Recommendations:")
        for r in assumption_results['recommendations']:
            print(f"  - {r}")
    
    return results

if __name__ == "__main__":
    main()
