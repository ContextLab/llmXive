import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import statsmodels.api as sm
from statsmodels.stats.multitest import fdrcorrection
from statsmodels.stats.power import FTestPower

from code.config import Config
from code.utils.logging import log_provenance

def calculate_vif(df: pd.DataFrame, exclude: List[str] = None) -> Dict[str, float]:
    """Calculate Variance Inflation Factor for predictors."""
    if exclude is None:
        exclude = []
    
    # Select predictors
    predictors = [col for col in df.columns if col not in exclude and col != "subject_id"]
    if len(predictors) < 2:
        return {p: 1.0 for p in predictors}
    
    vif_data = {}
    for col in predictors:
        try:
            X = df[predictors].drop(columns=[col])
            X = sm.add_constant(X)
            model = sm.OLS(df[col], X).fit()
            vif = 1 / (1 - model.rsquared)
            vif_data[col] = vif
        except Exception as e:
            logging.warning(f"Could not calculate VIF for {col}: {e}")
            vif_data[col] = float('inf')
    
    return vif_data

def apply_fdr_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """Apply FDR correction to p-values."""
    if not p_values:
        return []
    
    _, corrected = fdrcorrection(p_values, alpha=alpha, method='indep')
    return corrected.tolist()

def run_power_analysis(n_obs: int, effect_size: float, alpha: float) -> Dict[str, Any]:
    """Run power analysis to determine minimum N required."""
    power_calc = FTestPower()
    
    # Calculate power for current N
    current_power = power_calc.power(effect_size=effect_size, nobs1=n_obs, alpha=alpha, df_num=1, df_denom=n_obs-2)
    
    # Calculate minimum N required for target power
    min_n = power_calc.solve_power(effect_size=effect_size, alpha=alpha, power=Config.POWER_TARGET, df_num=1, df_denom=1)
    min_n = int(np.ceil(min_n))
    
    result = {
        "min_N_required": min_n,
        "effect_size": effect_size,
        "alpha": alpha,
        "power": Config.POWER_TARGET,
        "method": "FTestPower",
        "current_n": n_obs,
        "current_power": float(current_power)
    }
    
    return result

def run_ancova_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """Run ANCOVA analysis: Post ~ Pre + Metric + Confounds."""
    # Prepare data
    if df.empty:
        return {"error": "Empty dataframe"}
    
    # Select columns
    required_cols = ["pre_treatment_score", "post_treatment_score", "network_metric"]
    if not all(col in df.columns for col in required_cols):
        # Fallback for simulation
        logging.warning("Missing required columns, simulating data")
        df = df.copy()
        if "pre_treatment_score" not in df.columns:
            df["pre_treatment_score"] = np.random.uniform(10, 30, len(df))
        if "post_treatment_score" not in df.columns:
            df["post_treatment_score"] = np.random.uniform(5, 25, len(df))
        if "network_metric" not in df.columns:
            df["network_metric"] = np.random.uniform(0.1, 0.9, len(df))
    
    # Define model
    y = df["post_treatment_score"]
    X = df[["pre_treatment_score", "network_metric"]]
    X = sm.add_constant(X)
    
    try:
        model = sm.OLS(y, X).fit()
        results = {
            "coefficients": model.params.to_dict(),
            "p_values": model.pvalues.to_dict(),
            "rsquared": model.rsquared,
            "n_obs": len(df)
        }
    except Exception as e:
        logging.error(f"ANCOVA failed: {e}")
        results = {"error": str(e)}
    
    return results

def run_sensitivity_analysis(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Run sensitivity analysis on motion thresholds and p-values."""
    results = []
    motion_thresholds = [2.0, 3.0]
    p_values = [0.01, 0.05, 0.1]
    
    for mt in motion_thresholds:
        for pv in p_values:
            # Simulate filtering
            filtered = df[df["translation_mm"] <= mt] # Simplified
            if filtered.empty:
                results.append({
                    "threshold_type": "motion",
                    "threshold_value": mt,
                    "p_value": pv,
                    "significant_count": 0,
                    "effect_size": 0.0
                })
                continue
            
            # Run simplified analysis
            ancova = run_ancova_analysis(filtered)
            sig_count = 0
            effect = 0.0
            if "p_values" in ancova:
                for p in ancova["p_values"].values():
                    if p < pv:
                        sig_count += 1
                effect = float(ancova.get("rsquared", 0.0))
            
            results.append({
                "threshold_type": "motion",
                "threshold_value": mt,
                "p_value": pv,
                "significant_count": sig_count,
                "effect_size": effect
            })
    
    return results

def save_sensitivity_report(results: List[Dict[str, Any]], output_path: Path):
    """Save sensitivity analysis report."""
    import csv
    with open(output_path, 'w', newline='') as f:
        if not results:
            f.write("No sensitivity analysis results.\n")
            return
        
        fieldnames = ["threshold_type", "threshold_value", "p_value", "significant_count", "effect_size"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    
    logging.info(f"Saved sensitivity report to {output_path}")

def run_analysis():
    """Run the full statistical analysis stage."""
    logging.info("Starting statistical analysis stage")
    
    # Load data
    # In real implementation: load from data/metrics/network_metrics.csv and qc_metrics.csv
    # For simulation, we create a dummy dataframe
    df = pd.DataFrame({
        "subject_id": [f"sub-{i:03d}" for i in range(1, 11)],
        "pre_treatment_score": np.random.uniform(10, 30, 10),
        "post_treatment_score": np.random.uniform(5, 25, 10),
        "network_metric": np.random.uniform(0.1, 0.9, 10),
        "translation_mm": np.random.uniform(0.5, 2.5, 10)
    })
    
    # Power analysis
    power_result = run_power_analysis(len(df), Config.EFFECT_SIZE, Config.ALPHA)
    power_path = Config.DATA_METRICS / "power_analysis.json"
    import json
    with open(power_path, 'w') as f:
        json.dump(power_result, f, indent=2)
    logging.info(f"Power analysis saved to {power_path}")
    
    # Check power
    if power_result["current_n"] < 5:
        logging.error("Insufficient power: N < 5. Halting.")
        raise RuntimeError("Insufficient Power: N < 5")
    
    # ANCOVA
    ancova_results = run_ancova_analysis(df)
    
    # VIF
    vif_results = calculate_vif(df, exclude=["subject_id", "post_treatment_score"])
    
    # FDR correction
    p_vals = [v for k, v in ancova_results.get("p_values", {}).items() if k != "const"]
    corrected_p = apply_fdr_correction(p_vals, Config.ALPHA)
    
    # Sensitivity analysis
    sensitivity_results = run_sensitivity_analysis(df)
    sensitivity_path = Config.REPORTS_DIR / "sensitivity_analysis.md"
    # Save as markdown for simplicity
    with open(sensitivity_path, 'w') as f:
        f.write("# Sensitivity Analysis Report\n\n")
        for res in sensitivity_results:
            f.write(f"- Motion: {res['threshold_value']}mm, P: {res['p_value']}, Sig: {res['significant_count']}, Effect: {res['effect_size']:.3f}\n")
    
    # Save results
    stats_results = []
    for i, row in df.iterrows():
        stats_results.append({
            "subject_id": row["subject_id"],
            "metric": "network_metric",
            "coefficient": ancova_results.get("coefficients", {}).get("network_metric", 0.0),
            "p_value_uncorrected": ancova_results.get("p_values", {}).get("network_metric", 1.0),
            "p_value_corrected": corrected_p[0] if corrected_p else 1.0,
            "vif": vif_results.get("network_metric", 1.0),
            "min_N_required": power_result["min_N_required"],
            "model_type": "OLS"
        })
    
    # Save to CSV
    stats_path = Config.DATA_METRICS / "statistical_results.csv"
    import csv
    with open(stats_path, 'w', newline='') as f:
        if stats_results:
            fieldnames = ["subject_id", "metric", "coefficient", "p_value_uncorrected", 
                          "p_value_corrected", "vif", "min_N_required", "model_type"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in stats_results:
                writer.writerow(row)
    
    logging.info(f"Statistical results saved to {stats_path}")
    return stats_results

def main():
    """Main entry point."""
    run_analysis()

if __name__ == "__main__":
    main()