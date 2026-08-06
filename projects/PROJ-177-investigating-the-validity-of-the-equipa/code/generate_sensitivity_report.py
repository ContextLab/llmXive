"""
Generate sensitivity analysis report.
"""
import json
import sys
from pathlib import Path
from sensitivity import run_sensitivity_analysis, SensitivityError
import logging

logger = logging.getLogger(__name__)

def main():
    try:
        results = run_sensitivity_analysis()
        output_path = 'artifacts/sensitivity_analysis_report.json'
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Sensitivity report written to {output_path}")
    except SensitivityError as e:
        logger.error(str(e))
        sys.exit(1)
