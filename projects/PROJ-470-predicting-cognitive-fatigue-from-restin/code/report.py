import os
import sys
import yaml
from pathlib import Path
import pandas as pd
import numpy as np
import logging
from utils.logging import get_logger

def load_config(config_path="code/config.yaml"):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_analysis_results(file_path):
    """Load correlation results."""
    if not Path(file_path).exists():
        return None
    return pd.read_csv(file_path)

def calculate_effect_size(r):
    """Calculate Cohen's d approximation from correlation r."""
    # Simple approximation: d = 2r / sqrt(1-r^2)
    if abs(r) >= 1:
        return np.nan
    return (2 * r) / np.sqrt(1 - r**2)

def generate_report(results, config, logger):
    """Generate final report."""
    if results is None or results.empty:
        logger.warning("No results to report.")
        return {"status": "no_data"}
    
    report = {
        "summary": {
            "total_tests": len(results),
            "significant": results['significant'].sum() if 'significant' in results.columns else 0
        },
        "details": results.to_dict(orient='records')
    }
    return report

def main():
    config = load_config()
    logger = get_logger("report", config)
    logger.info("Generating report.")
    
    results = load_analysis_results("data/analysis/correlation_results.csv")
    report = generate_report(results, config, logger)
    
    output_path = Path(config['paths']['analysis_data']) / "final_report.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    import json
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Report saved to {output_path}")

if __name__ == "__main__":
    main()
