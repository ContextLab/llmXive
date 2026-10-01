"""
Reporting Module

Generates the final research report framing findings as associational.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import ensure_directories

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_regression_results():
    path = "data/processed/regression_results.json"
    if not Path(path).exists():
        raise FileNotFoundError(f"Regression results not found at {path}")
    with open(path, 'r') as f:
        return json.load(f)

def load_model_config():
    path = "artifacts/model_config.yaml"
    import yaml
    if not Path(path).exists():
        # Try JSON fallback if YAML not generated yet
        path_json = path.replace('.yaml', '.json')
        if Path(path_json).exists():
            with open(path_json, 'r') as f:
                return json.load(f)
        raise FileNotFoundError(f"Model config not found at {path}")
    with open(path, 'r') as f:
        import yaml
        return yaml.safe_load(f)

def load_data_summary():
    path = "data/processed/human_judgments_aggregates.csv"
    import pandas as pd
    if not Path(path).exists():
        return None
    return pd.read_csv(path).describe().to_dict()

def generate_associational_caveat(model_type):
    """Generate a caveat text about the associational nature of the study."""
    return (
        f"Note: This study uses a Generalized Linear Mixed Model ({model_type}) to examine "
        "associations between visual clutter metrics and emotion recognition accuracy. "
        "While the model controls for participant and stimulus variability, "
        "causal inference is limited by the observational nature of the pilot data."
    )

def generate_executive_summary(results, config):
    """Generate an executive summary."""
    model_type = config.get('model_type', 'Unknown')
    status = config.get('convergence_status', 'unknown')
    
    summary = f"Executive Summary:\n"
    summary += f"- Model Type: {model_type}\n"
    summary += f"- Convergence Status: {status}\n"
    
    if 'coefficients' in results:
        summary += f"- Significant predictors found: {len(results['coefficients'])}\n"
    
    summary += f"\n{generate_associational_caveat(model_type)}\n"
    return summary

def generate_detailed_results(results):
    """Generate detailed results section."""
    details = "Detailed Results:\n"
    if 'coefficients' in results:
        for name, val in results['coefficients'].items():
            details += f"  {name}: Beta={val.get('beta', 'N/A')}, p={val.get('p_value', 'N/A')}\n"
    return details

def generate_report():
    """Generate the full report."""
    results = load_regression_results()
    config = load_model_config()
    data_summary = load_data_summary()
    
    report = {
        'title': 'Impact of Visual Crowding on Facial Emotion Recognition',
        'executive_summary': generate_executive_summary(results, config),
        'detailed_results': generate_detailed_results(results),
        'caveat': generate_associational_caveat(config.get('model_type', 'GLMM')),
        'data_summary': str(data_summary) if data_summary else "No data summary available."
    }
    
    return report

def main(args):
    """Main entry point."""
    ensure_directories()
    output_path = "artifacts/final_report.json"
    
    try:
        report = generate_report()
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Final report saved to {output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"Error: {e}")
        logger.error("Cannot generate report without regression results or model config.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate final research report.")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    main(args)
