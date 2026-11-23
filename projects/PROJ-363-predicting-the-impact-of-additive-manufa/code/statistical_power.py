import os
import sys
import json
import logging
import numpy as np
from scipy.stats import ttest_1samp, f_oneway
from pathlib import Path

# Import from utils for logging setup
from utils import setup_logging

def calculate_effect_size(mean_diff, std_dev, n):
    """
    Calculate Cohen's d effect size.
    mean_diff: Difference between means
    std_dev: Standard deviation of the sample
    n: Sample size
    """
    if std_dev == 0:
        return 0.0
    return mean_diff / std_dev

def calculate_power(effect_size, n, alpha=0.05):
    """
    Estimate statistical power for a t-test given effect size and sample size.
    This is a simplified approximation.
    """
    # Approximation: Power ~ Phi( sqrt(n)*|d| - z_{1-alpha/2} )
    # Using standard normal CDF approximation
    from scipy.stats import norm
    z_alpha = norm.ppf(1 - alpha/2)
    non_central = np.sqrt(n) * abs(effect_size)
    power = norm.cdf(non_central - z_alpha) + norm.cdf(-non_central - z_alpha)
    return max(0.0, min(1.0, power))

def analyze_power_from_permutation_report(report_path, output_path):
    """
    Analyze the permutation importance report to calculate statistical power.
    Reads the report, computes effect sizes and power for each feature,
    and writes a summary JSON.
    """
    if not os.path.exists(report_path):
        logging.error(f"Permutation report not found: {report_path}")
        return

    with open(report_path, 'r') as f:
        report = json.load(f)

    # Assume report structure: {"results": [{"feature": name, "mean_importance": val, "std_importance": val, "p_value": val}]}
    # Or similar structure from T033b/T033c.
    # We need to infer the structure. Let's assume it contains a list of feature stats.
    
    results = report.get('results', [])
    if not results:
        # Try alternative key if standard one fails
        results = report.get('feature_importance', [])
    
    power_analysis = {
        "features": [],
        "summary": {
            "high_power_features": 0,
            "low_power_features": 0,
            "average_power": 0.0
        }
    }

    powers = []
    for res in results:
        feature_name = res.get('feature') or res.get('name')
        mean_imp = res.get('mean_importance') or res.get('importance_mean')
        std_imp = res.get('std_importance') or res.get('importance_std')
        p_val = res.get('p_value')
        n_samples = res.get('n_samples', len(results)) # Approximation if not explicit

        if mean_imp is None or std_imp is None:
            continue

        # Effect size: Cohen's d relative to zero (null hypothesis)
        # d = mean / std
        effect_size = calculate_effect_size(mean_imp, std_imp, n_samples)
        
        # Calculate power
        power = calculate_power(effect_size, n_samples)
        powers.append(power)

        status = "High" if power > 0.8 else "Low"
        if status == "High":
            power_analysis["summary"]["high_power_features"] += 1
        else:
            power_analysis["summary"]["low_power_features"] += 1

        power_analysis["features"].append({
            "feature": feature_name,
            "effect_size": round(effect_size, 4),
            "power": round(power, 4),
            "p_value": p_val,
            "status": status
        })

    if powers:
        power_analysis["summary"]["average_power"] = round(np.mean(powers), 4)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(power_analysis, f, indent=2)
    
    logging.info(f"Statistical power analysis saved to {output_path}")

def main():
    logger = setup_logging()
    logger.info("Starting Statistical Power Analysis")

    # Determine paths based on project structure
    base_dir = Path(__file__).parent.parent
    reports_dir = base_dir / "results" / "reports"
    output_path = reports_dir / "statistical_power_analysis.json"

    # Identify which permutation report to use (selected model vs non-selected)
    # We should analyze the selected model's report primarily, but can do both if available.
    # Let's look for the unified statistical analysis files generated in T033c/T033b
    raw_report = reports_dir / "unified_statistical_analysis_raw.json"
    derived_report = reports_dir / "unified_statistical_analysis_derived.json"
    
    # Check which one exists and is relevant (based on selected model)
    selected_model_file = base_dir / "state" / "selected_model.yaml"
    use_raw = True
    if selected_model_file.exists():
        # Simple check: if 'derived' is mentioned in the yaml content, use derived
        with open(selected_model_file, 'r') as f:
            content = f.read().lower()
            if 'derived' in content and 'raw' not in content:
                use_raw = False
    
    target_report = raw_report if use_raw else derived_report
    
    if not target_report.exists():
        # Fallback: try to find any unified report
        all_reports = list(reports_dir.glob("unified_statistical_analysis_*.json"))
        if all_reports:
            target_report = all_reports[0]
            logging.warning(f"Selected model report not found, using {target_report}")
        else:
            logging.error("No unified statistical analysis report found. Cannot perform power analysis.")
            sys.exit(1)

    logger.info(f"Analyzing power from report: {target_report}")
    analyze_power_from_permutation_report(str(target_report), str(output_path))
    logger.info("Statistical Power Analysis Complete")

if __name__ == "__main__":
    main()
