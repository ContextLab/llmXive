import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import numpy as np
import pandas as pd
from scipy import stats
from lifelines import KaplanMeierFitter, CoxPHFitter
from lifelines.utils import concordance_index

from config import get_path, get_config
from logging_config import setup_logging
from analysis.statistical_tests import load_simulation_results, calculate_cohens_d

# Setup logging
logger = setup_logging(__name__)

def load_survival_data(results_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load simulation results and prepare data for survival analysis.
    
    Args:
        results_path: Path to the simulation results file. If None, uses config.
        
    Returns:
        DataFrame with 'time' (token consumption or turns) and 'event' (abstention occurred).
    """
    if results_path is None:
        results_path = get_path("data/results/baseline_comparison.json")
    
    logger.info(f"Loading survival data from {results_path}")
    
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"Results file not found: {results_path}")
    
    # Reuse the existing loader from statistical_tests.py
    data = load_simulation_results(results_path)
    
    # The baseline_comparison.json should contain token consumption and abstention events
    # We expect a structure like:
    # {
    #   "meta_critic": {"token_usage": [...], "abstention_events": [...]},
    #   "baseline": {"token_usage": [...], ...}
    # }
    
    if "meta_critic" not in data or "baseline" not in data:
        raise ValueError("Invalid results format: missing 'meta_critic' or 'baseline' keys")
    
    meta_critic_data = data["meta_critic"]
    baseline_data = data["baseline"]
    
    # Prepare survival data: time = token usage, event = 1 if abstention occurred, 0 otherwise
    # For survival analysis, we treat "abstention" as the event of interest
    # Time to event = token consumption until abstention
    # If no abstention occurred (censored), time = total token consumption, event = 0
    
    survival_data = []
    
    # Meta-critic condition
    if "token_usage" in meta_critic_data and "abstention_events" in meta_critic_data:
        tokens = meta_critic_data["token_usage"]
        events = meta_critic_data.get("abstention_events", [1] * len(tokens))  # Default: all events occurred
        
        for i, (t, e) in enumerate(zip(tokens, events)):
            survival_data.append({
                "condition": "meta_critic",
                "time": t,
                "event": int(e) if isinstance(e, (int, float)) else 1
            })
    
    # Baseline condition
    if "token_usage" in baseline_data:
        tokens = baseline_data["token_usage"]
        # Baseline typically doesn't abstain, so events = 0 (censored)
        # Or if baseline has a different mechanism, adjust accordingly
        events = baseline_data.get("abstention_events", [0] * len(tokens))
        
        for i, (t, e) in enumerate(zip(tokens, events)):
            survival_data.append({
                "condition": "baseline",
                "time": t,
                "event": int(e) if isinstance(e, (int, float)) else 0
            })
    
    df = pd.DataFrame(survival_data)
    
    if df.empty:
        raise ValueError("No survival data found in results file")
    
    logger.info(f"Loaded {len(df)} records for survival analysis")
    return df

def perform_kaplan_meier_analysis(df: pd.DataFrame, output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Perform Kaplan-Meier survival analysis and generate summary statistics.
    
    Args:
        df: DataFrame with 'time', 'event', and 'condition' columns.
        output_path: Path to save the analysis results.
        
    Returns:
        Dictionary containing survival analysis results.
    """
    logger.info("Performing Kaplan-Meier survival analysis")
    
    results = {
        "method": "Kaplan-Meier",
        "conditions": {},
        "median_survival_times": {},
        "concordance_index": None
    }
    
    # Fit KM curves for each condition
    conditions = df["condition"].unique()
    
    for condition in conditions:
        subset = df[df["condition"] == condition]
        
        kmf = KaplanMeierFitter()
        kmf.fit(subset["time"], subset["event"], label=condition)
        
        # Extract median survival time (time at which survival probability = 0.5)
        try:
            median_time = kmf.median_survival_time_
            if pd.notna(median_time):
                results["median_survival_times"][condition] = float(median_time)
            else:
                results["median_survival_times"][condition] = None
        except Exception as e:
            logger.warning(f"Could not compute median survival time for {condition}: {e}")
            results["median_survival_times"][condition] = None
        
        # Store survival curve data
        results["conditions"][condition] = {
            "median_time": results["median_survival_times"][condition],
            "n_observed": int(subset["event"].sum()),
            "n_censored": int((1 - subset["event"]).sum()),
            "total_n": len(subset)
        }
        
        logger.info(f"Condition {condition}: median time = {results['median_survival_times'][condition]}, "
                   f"events = {results['conditions'][condition]['n_observed']}, "
                   f"censored = {results['conditions'][condition]['n_censored']}")
    
    # Compute concordance index (C-index) if we have a covariate
    if len(conditions) > 1:
        # Create a binary covariate for condition
        df_cox = df.copy()
        df_cox["condition_binary"] = (df_cox["condition"] == "meta_critic").astype(int)
        
        try:
            cph = CoxPHFitter()
            cph.fit(df_cox, duration_col="time", event_col="event")
            results["cox_model"] = {
                "concordance_index": float(cph.concordance_index_),
                "coefficients": cph.params_.to_dict(),
                "hazard_ratios": np.exp(cph.params_).to_dict()
            }
            logger.info(f"Cox model C-index: {results['cox_model']['concordance_index']:.4f}")
        except Exception as e:
            logger.warning(f"Cox model fitting failed: {e}")
            results["cox_model"] = None
    
    # Save results
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Survival analysis results saved to {output_path}")
    
    return results

def perform_logrank_test(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform Log-Rank test to compare survival distributions between conditions.
    
    Args:
        df: DataFrame with 'time', 'event', and 'condition' columns.
        
    Returns:
        Dictionary containing log-rank test results.
    """
    logger.info("Performing Log-Rank test")
    
    from lifelines.statistics import logrank_test
    
    conditions = df["condition"].unique()
    
    if len(conditions) < 2:
        logger.warning("Need at least 2 conditions for Log-Rank test")
        return {"skipped": True, "reason": "Less than 2 conditions"}
    
    # Assume first two conditions
    cond1, cond2 = conditions[0], conditions[1]
    
    subset1 = df[df["condition"] == cond1]
    subset2 = df[df["condition"] == cond2]
    
    try:
        # Perform log-rank test
        result = logrank_test(
            subset1["time"], subset2["time"],
            subset1["event"], subset2["event"],
            alpha=0.05
        )
        
        return {
            "method": "Log-Rank Test",
            "comparison": f"{cond1} vs {cond2}",
            "p_value": float(result.p_value),
            "statistic": float(result.statistic),
            "significant_at_0.05": result.p_value < 0.05,
            "significant_at_0.01": result.p_value < 0.01
        }
    except Exception as e:
        logger.error(f"Log-Rank test failed: {e}")
        return {
            "method": "Log-Rank Test",
            "comparison": f"{cond1} vs {cond2}",
            "error": str(e)
        }

def perform_kolmogorov_smirnov_test(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform Two-sample Kolmogorov-Smirnov test on token consumption distributions.
    This explicitly implements FR-005 requirement.
    
    Args:
        df: DataFrame with 'time' (token consumption) and 'condition' columns.
        
    Returns:
        Dictionary containing KS test results.
    """
    logger.info("Performing Two-sample Kolmogorov-Smirnov test (FR-005)")
    
    conditions = df["condition"].unique()
    
    if len(conditions) < 2:
        logger.warning("Need at least 2 conditions for KS test")
        return {"skipped": True, "reason": "Less than 2 conditions"}
    
    cond1, cond2 = conditions[0], conditions[1]
    
    subset1 = df[df["condition"] == cond1]["time"]
    subset2 = df[df["condition"] == cond2]["time"]
    
    try:
        # Perform KS test
        statistic, p_value = stats.ks_2samp(subset1, subset2)
        
        return {
            "method": "Two-sample Kolmogorov-Smirnov Test",
            "comparison": f"{cond1} vs {cond2}",
            "statistic": float(statistic),
            "p_value": float(p_value),
            "null_hypothesis": "Distributions are identical",
            "reject_null_at_0.05": p_value < 0.05,
            "reject_null_at_0.01": p_value < 0.01,
            "interpretation": "Reject null hypothesis (distributions differ)" if p_value < 0.05 
                             else "Fail to reject null hypothesis (distributions similar)"
        }
    except Exception as e:
        logger.error(f"KS test failed: {e}")
        return {
            "method": "Two-sample Kolmogorov-Smirnov Test",
            "comparison": f"{cond1} vs {cond2}",
            "error": str(e)
        }

def perform_mann_whitney_u_test(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform Mann-Whitney U test as an alternative non-parametric test (FR-005).
    
    Args:
        df: DataFrame with 'time' (token consumption) and 'condition' columns.
        
    Returns:
        Dictionary containing Mann-Whitney U test results.
    """
    logger.info("Performing Mann-Whitney U test (FR-005 alternative)")
    
    conditions = df["condition"].unique()
    
    if len(conditions) < 2:
        logger.warning("Need at least 2 conditions for Mann-Whitney U test")
        return {"skipped": True, "reason": "Less than 2 conditions"}
    
    cond1, cond2 = conditions[0], conditions[1]
    
    subset1 = df[df["condition"] == cond1]["time"]
    subset2 = df[df["condition"] == cond2]["time"]
    
    try:
        # Perform Mann-Whitney U test
        statistic, p_value = stats.mannwhitneyu(subset1, subset2, alternative='two-sided')
        
        # Calculate effect size (r)
        n1, n2 = len(subset1), len(subset2)
        z_score = np.sqrt(2 * np.log(n1 + n2)) * (statistic - (n1 * n2) / 2) / np.sqrt((n1 * n2 * (n1 + n2 + 1)) / 12)
        effect_size_r = np.abs(z_score) / np.sqrt(n1 + n2)
        
        return {
            "method": "Mann-Whitney U Test",
            "comparison": f"{cond1} vs {cond2}",
            "statistic": float(statistic),
            "p_value": float(p_value),
            "effect_size_r": float(effect_size_r),
            "null_hypothesis": "Distributions are identical",
            "reject_null_at_0.05": p_value < 0.05,
            "reject_null_at_0.01": p_value < 0.01,
            "interpretation": "Reject null hypothesis (distributions differ)" if p_value < 0.05 
                             else "Fail to reject null hypothesis (distributions similar)"
        }
    except Exception as e:
        logger.error(f"Mann-Whitney U test failed: {e}")
        return {
            "method": "Mann-Whitney U Test",
            "comparison": f"{cond1} vs {cond2}",
            "error": str(e)
        }

def generate_survival_report(df: pd.DataFrame, output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Generate comprehensive survival analysis report including all required tests.
    
    Args:
        df: DataFrame with survival data.
        output_dir: Directory to save output files.
        
    Returns:
        Dictionary containing the full report.
    """
    logger.info("Generating comprehensive survival analysis report")
    
    if output_dir is None:
        output_dir = get_path("data/results")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    report = {
        "summary": {
            "total_records": len(df),
            "conditions": list(df["condition"].unique()),
            "analysis_date": str(pd.Timestamp.now())
        },
        "survival_analysis": None,
        "logrank_test": None,
        "kolmogorov_smirnov_test": None,
        "mann_whitney_u_test": None,
        "conclusion": []
    }
    
    # 1. Kaplan-Meier Analysis
    km_results_path = output_dir / "survival_kaplan_meier.json"
    report["survival_analysis"] = perform_kaplan_meier_analysis(df, km_results_path)
    
    # 2. Log-Rank Test
    lr_results = perform_logrank_test(df)
    report["logrank_test"] = lr_results
    if "p_value" in lr_results:
        report["conclusion"].append(
            f"Log-Rank test: p={lr_results['p_value']:.4f}, "
            f"{'significant' if lr_results.get('significant_at_0.05') else 'not significant'} at α=0.05"
        )
    
    # 3. Kolmogorov-Smirnov Test (FR-005 requirement)
    ks_results = perform_kolmogorov_smirnov_test(df)
    report["kolmogorov_smirnov_test"] = ks_results
    if "p_value" in ks_results:
        report["conclusion"].append(
            f"KS test: p={ks_results['p_value']:.4f}, "
            f"{'reject' if ks_results.get('reject_null_at_0.05') else 'fail to reject'} null hypothesis at α=0.05"
        )
    
    # 4. Mann-Whitney U Test (FR-005 alternative)
    mw_results = perform_mann_whitney_u_test(df)
    report["mann_whitney_u_test"] = mw_results
    if "p_value" in mw_results:
        report["conclusion"].append(
            f"Mann-Whitney U: p={mw_results['p_value']:.4f}, "
            f"{'reject' if mw_results.get('reject_null_at_0.05') else 'fail to reject'} null hypothesis at α=0.05"
        )
    
    # Save full report
    report_path = output_dir / "survival_analysis_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Survival analysis report saved to {report_path}")
    
    return report

def main():
    """Main entry point for survival analysis."""
    logger.info("Starting survival analysis pipeline")
    
    try:
        # Load data
        df = load_survival_data()
        
        # Generate comprehensive report
        report = generate_survival_report(df)
        
        # Print summary
        print("\n=== Survival Analysis Summary ===")
        print(f"Total records: {report['summary']['total_records']}")
        print(f"Conditions: {', '.join(report['summary']['conditions'])}")
        print("\nKey Findings:")
        for finding in report["conclusion"]:
            print(f"  - {finding}")
        
        # Check if null hypothesis is rejected (FR-005 validation)
        ks_p = report.get("kolmogorov_smirnov_test", {}).get("p_value")
        mw_p = report.get("mann_whitney_u_test", {}).get("p_value")
        
        if ks_p is not None and ks_p < 0.05:
            print("\n✓ KS test: Null hypothesis REJECTED (p < 0.05)")
        elif ks_p is not None:
            print(f"\n✗ KS test: Null hypothesis NOT rejected (p = {ks_p:.4f})")
        
        if mw_p is not None and mw_p < 0.05:
            print("✓ Mann-Whitney U test: Null hypothesis REJECTED (p < 0.05)")
        elif mw_p is not None:
            print(f"✗ Mann-Whitney U test: Null hypothesis NOT rejected (p = {mw_p:.4f})")
        
        logger.info("Survival analysis completed successfully")
        
    except Exception as e:
        logger.error(f"Survival analysis failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()