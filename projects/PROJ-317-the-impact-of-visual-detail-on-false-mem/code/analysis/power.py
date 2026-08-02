import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import numpy as np

from config import get_data_dir, get_project_root
from utils.logging import get_logger

logger = get_logger(__name__)

def run_power_analysis() -> Dict[str, Any]:
    """
    Calculate required sample size for Repeated-Measures ANOVA.
    
    Algorithm:
    1. Read sensitivity_analysis.json (from T012-Sens).
    2. Select effect_size corresponding to minimum required_n >= 50.
    3. If no value satisfies N>=50, select closest N and set power_insufficient=true.
    
    Returns:
        Dict: Power analysis results.
    """
    sensitivity_path = get_data_dir() / "analysis" / "sensitivity_analysis.json"
    
    if not sensitivity_path.exists():
        logger.error(f"Sensitivity analysis file not found: {sensitivity_path}")
        logger.error("Please run T012-Sens first.")
        sys.exit(1)
    
    with open(sensitivity_path, 'r') as f:
        sensitivity_data = json.load(f)
    
    effect_sizes = sensitivity_data['effect_sizes']
    required_ns = sensitivity_data['required_n']
    powers = sensitivity_data['power']
    
    # Find minimum required_n >= 50
    valid_indices = [i for i, n in enumerate(required_ns) if n >= 50]
    
    power_insufficient = False
    selected_idx = None
    
    if valid_indices:
        # Select the one with minimum N >= 50
        selected_idx = min(valid_indices, key=lambda i: required_ns[i])
    else:
        # No N >= 50 found, select closest to 50
        selected_idx = required_ns.index(min(required_ns))
        power_insufficient = True
        logger.warning(f"No sample size >= 50 found. Using closest: N={required_ns[selected_idx]}")
    
    n_total_subjects = required_ns[selected_idx]
    effect_size = effect_sizes[selected_idx]
    power = powers[selected_idx]
    
    results = {
        "n_total_subjects": n_total_subjects,
        "effect_size": effect_size,
        "power": power,
        "alpha": 0.05,
        "power_insufficient": power_insufficient,
        "justification": f"Selected effect size {effect_size:.3f} which requires N={n_total_subjects} for power={power:.3f}. "
                        f"Based on T012-Sens sensitivity analysis. "
                        f"{'Power is insufficient (N < 50).' if power_insufficient else 'Power criteria met.'}"
    }
    
    output_path = get_data_dir() / "analysis" / "power_report.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Power report saved to {output_path}")
    return results

def validate_power_analysis() -> bool:
    """
    Validate that power analysis passed the gate criteria.
    
    Checks:
    1. power_report.json exists.
    2. power_insufficient is false.
    3. n_total_subjects >= 50.
    
    Returns:
        bool: True if validation passes.
    """
    report_path = get_data_dir() / "analysis" / "power_report.json"
    
    if not report_path.exists():
        logger.error("Power report not found. Please run T012-Calc first.")
        return False
    
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    if report.get('power_insufficient', True):
        logger.error(f"Power insufficient: N={report['n_total_subjects']} < 50")
        return False
    
    if report['n_total_subjects'] < 50:
        logger.error(f"Sample size too small: N={report['n_total_subjects']} < 50")
        return False
    
    # Gate passed
    gate_path = get_data_dir() / "analysis" / "power_gate_passed.txt"
    with open(gate_path, 'w') as f:
        f.write("Power analysis validation passed.\n")
    
    log_path = get_data_dir() / "logs" / "power_gate.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'a') as f:
        f.write(f"[PASS] Power gate passed at {Path(__file__).stem}.\n")
    
    logger.info("Power gate passed.")
    return True

def main():
    """
    CLI entry point for power analysis.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run power analysis for Repeated-Measures ANOVA.")
    parser.add_argument("--validate", action="store_true", help="Only validate existing report")
    
    args = parser.parse_args()
    
    if args.validate:
        success = validate_power_analysis()
        sys.exit(0 if success else 1)
    else:
        try:
            run_power_analysis()
            success = validate_power_analysis()
            sys.exit(0 if success else 1)
        except Exception as e:
            logger.error(f"Power analysis failed: {e}", exc_info=True)
            sys.exit(1)

if __name__ == "__main__":
    main()
