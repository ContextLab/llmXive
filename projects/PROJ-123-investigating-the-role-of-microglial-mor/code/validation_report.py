import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
from datetime import datetime
from code.config import get_path, ensure_dirs
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_cv_results() -> Dict[str, Any]:
    """Load cross-validation results."""
    default_path = get_path('reports', 'cv_results.json')
    if os.path.exists(default_path):
        with open(default_path, 'r') as f:
            return json.load(f)
    else:
        raise FileNotFoundError(f"CV results not found at {default_path}")

def load_sensitivity_results() -> Dict[str, Any]:
    """Load sensitivity analysis results."""
    default_path = get_path('intermediate', 'sensitivity_analysis.json')
    if os.path.exists(default_path):
        with open(default_path, 'r') as f:
            return json.load(f)
    else:
        raise FileNotFoundError(f"Sensitivity results not found at {default_path}")

def generate_validation_report(cv_results: Dict[str, Any], sensitivity_results: Dict[str, Any]) -> str:
    """Generate validation report."""
    report_path = get_path('reports', 'validation_report.md')
    ensure_dirs(report_path)
    
    with open(report_path, 'w') as f:
        f.write("# Validation Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Cross-Validation Results\n")
        f.write(f"- Mean R²: {cv_results.get('r2_mean', 'N/A')}\n")
        f.write(f"- Std R²: {cv_results.get('r2_std', 'N/A')}\n")
        f.write(f"- K-folds: {cv_results.get('k_folds', 'N/A')}\n\n")
        
        f.write("## Sensitivity Analysis\n")
        f.write("- P-value variation across Sholl steps:\n")
        for key, value in sensitivity_results.items():
            if isinstance(value, dict):
                f.write(f"  - {key}: {value}\n")
            else:
                f.write(f"  - {key}: {value}\n")
        
        # Check stability
        r2_std = cv_results.get('r2_std', 0)
        r2_mean = cv_results.get('r2_mean', 1)
        if r2_mean > 0:
            variation = r2_std / r2_mean
            f.write(f"\n- R² variation: {variation:.4f} ({'STABLE' if variation < 0.05 else 'UNSTABLE'})\n")
    
    logger.info(f"Validation report generated at {report_path}")
    return report_path

def run_validation_pipeline() -> Dict[str, str]:
    """Run the validation report pipeline."""
    cv_results = load_cv_results()
    sensitivity_results = load_sensitivity_results()
    
    report_path = generate_validation_report(cv_results, sensitivity_results)
    
    return {'report': report_path}

def main():
    """Main entry point for validation report generation."""
    run_validation_pipeline()

if __name__ == '__main__':
    main()
