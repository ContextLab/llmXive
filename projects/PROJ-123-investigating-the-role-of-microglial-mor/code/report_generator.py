import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime
from code.config import get_path, ensure_dirs
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_regression_results() -> Dict[str, Any]:
    """Load regression results from JSON file."""
    default_path = get_path('reports', 'regression_results.json')
    if os.path.exists(default_path):
        with open(default_path, 'r') as f:
            return json.load(f)
    else:
        raise FileNotFoundError(f"Regression results not found at {default_path}")

def load_vif_check() -> Dict[str, Any]:
    """Load VIF check results from JSON file."""
    default_path = get_path('intermediate', 'vif_check.json')
    if os.path.exists(default_path):
        with open(default_path, 'r') as f:
            return json.load(f)
    else:
        raise FileNotFoundError(f"VIF check results not found at {default_path}")

def determine_causality_warning(metadata: Dict[str, Any]) -> bool:
    """Determine if causality warning is needed."""
    return not metadata.get('randomized', False)

def generate_markdown_report(results: Dict[str, Any]) -> str:
    """Generate markdown report from analysis results."""
    report_path = get_path('reports', 'regression_results.md')
    ensure_dirs(report_path)
    
    with open(report_path, 'w') as f:
        f.write("# Regression Analysis Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Regression Results\n")
        if 'regression' in results:
            reg = results['regression']
            f.write(f"- R²: {reg.get('r2', 'N/A')}\n")
            f.write(f"- Adjusted R²: {reg.get('adj_r2', 'N/A')}\n")
            f.write(f"- Interaction p-value: {reg.get('interaction_p_value', 'N/A')}\n\n")
        
        f.write("## VIF Check\n")
        if 'vif_check' in results:
            vif = results['vif_check']
            f.write(f"- Max VIF: {vif.get('max_vif', 'N/A')}\n")
            f.write(f"- PCA Applied: {vif.get('trigger_pca', False)}\n\n")
        
        f.write("## Cross-Validation\n")
        if 'cv' in results:
            cv = results['cv']
            f.write(f"- Mean R²: {cv.get('r2_mean', 'N/A')}\n")
            f.write(f"- Std R²: {cv.get('r2_std', 'N/A')}\n\n")
        
        # Add causality warning if needed
        if determine_causality_warning(results.get('metadata', {})):
            f.write("## Warning\n")
            f.write("Associational findings only; causality not inferred.\n")
    
    logger.info(f"Markdown report generated at {report_path}")
    return report_path

def generate_json_report(results: Dict[str, Any]) -> str:
    """Generate JSON report from analysis results."""
    report_path = get_path('reports', 'regression_results.json')
    ensure_dirs(report_path)
    
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"JSON report generated at {report_path}")
    return report_path

def run_report_pipeline(results: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """Run the report generation pipeline."""
    if results is None:
        results = load_regression_results()
    
    outputs = {}
    outputs['markdown'] = generate_markdown_report(results)
    outputs['json'] = generate_json_report(results)
    
    return outputs

def main():
    """Main entry point for report generation."""
    run_report_pipeline()

if __name__ == '__main__':
    main()
