"""
Power Analysis Module

Calculates required sample size for Between-Subjects ANOVA design.
Implements the logic for T012-Calc and T012-Runtime.
"""

import json
import logging
import sys
from pathlib import Path

from config import get_project_root, get_data_dir, get_effect_size, get_alpha_level, get_power_target
from analysis.stats import calculate_anova_power, save_power_analysis

logger = logging.getLogger(__name__)

def run_power_analysis():
    """
    Perform power analysis for Between-Subjects ANOVA.
    
    Calculates the required sample size given:
    - Effect size (Cohen's f)
    - Alpha level
    - Target power
    - Number of groups (k=3: Baseline, Enhanced, Reduced)
    
    Writes results to data/analysis/power_report.json.
    """
    logger.info("Starting power analysis calculation...")
    
    effect_size = get_effect_size()
    alpha = get_alpha_level()
    power = get_power_target()
    k = 3  # Number of conditions: Baseline, Enhanced, Reduced
    
    logger.info(f"Parameters: effect_size={effect_size}, alpha={alpha}, power={power}, k={k}")
    
    # Calculate required sample size
    n_total, power_insufficient = calculate_anova_power(
        effect_size=effect_size,
        alpha=alpha,
        power=power,
        k=k
    )
    
    logger.info(f"Calculated total sample size: {n_total}")
    
    # Prepare report data
    report = {
        "n_total_subjects": n_total,
        "effect_size": effect_size,
        "power": power,
        "alpha": alpha,
        "power_insufficient": power_insufficient
    }
    
    # Save report
    output_path = save_power_analysis(report)
    logger.info(f"Power report saved to {output_path}")
    
    return report

def validate_power_analysis():
    """
    Validate the power analysis results against project constraints.
    
    Checks:
    1. Report file exists
    2. power_insufficient is False
    3. n_total_subjects >= 50
    
    Raises SystemExit if validation fails.
    """
    data_dir = get_data_dir()
    report_path = data_dir / "analysis" / "power_report.json"
    
    if not report_path.exists():
        logger.error("Power analysis report not found. Run power analysis first.")
        raise SystemExit("Power Analysis Failed: Report file missing.")
    
    try:
        with open(report_path, 'r') as f:
            report = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load power report: {e}")
        raise SystemExit("Power Analysis Failed: Could not read report.")
    
    # Check power_insufficient flag
    if report.get("power_insufficient", True):
        n = report.get("n_total_subjects", 0)
        logger.error(f"Power analysis indicates insufficient sample size (N={n}).")
        raise SystemExit("Power Analysis Failed: Insufficient sample size (N < 50) or power criteria not met.")
    
    # Check minimum sample size constraint
    n_total = report.get("n_total_subjects", 0)
    if n_total < 50:
        logger.error(f"Calculated sample size ({n_total}) is below minimum threshold (50).")
        raise SystemExit("Power Analysis Failed: Insufficient sample size (N < 50) or power criteria not met.")
    
    logger.info("Power analysis validation passed.")
    return True

def main():
    """
    Main entry point for power analysis.
    Runs calculation and validation.
    """
    # Check if we should only validate or run full analysis
    if len(sys.argv) > 1 and sys.argv[1] == "--validate-only":
        validate_power_analysis()
        return
    
    # Run full analysis
    report = run_power_analysis()
    
    # Validate results
    validate_power_analysis()
    
    logger.info("Power analysis completed successfully.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
