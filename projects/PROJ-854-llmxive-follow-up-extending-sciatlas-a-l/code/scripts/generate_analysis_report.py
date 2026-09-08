import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from src.lib import config

logger = logging.getLogger(__name__)

def load_metrics(filepath: str) -> Dict[str, Any]:
    """Load metrics from JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def generate_report_content(metrics: Dict[str, Any]) -> str:
    """Generate markdown report content."""
    report = "# Analysis Report\n\n"
    report += "## Summary\n\n"
    report += "This report presents the findings of the bridging coefficient analysis.\n"
    report += "All results are labeled as **associational**.\n\n"
    
    report += "## Statistical Metrics\n\n"
    for key, value in metrics.items():
        report += f"- **{key}**: {value}\n"
    
    return report

def main():
    logging.basicConfig(level=logging.INFO)
    
    metrics_path = Path(config.get_artifacts_path()) / "results" / "statistical_metrics.json"
    if not metrics_path.exists():
        logger.error("Metrics file not found. Run statistical analysis first.")
        sys.exit(1)
    
    metrics = load_metrics(str(metrics_path))
    content = generate_report_content(metrics)
    
    report_path = Path(config.get_artifacts_path()) / "results" / "analysis_report.md"
    with open(report_path, 'w') as f:
        f.write(content)
    
    logger.info(f"Report generated at {report_path}")

if __name__ == "__main__":
    main()