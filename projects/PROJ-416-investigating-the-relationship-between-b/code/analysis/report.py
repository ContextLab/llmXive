import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from code.config import Config
from code.utils.logging import log_provenance

logger = logging.getLogger(__name__)
config = Config()

def load_metadata() -> Dict[str, Any]:
    """Load dataset metadata from verified_sources.json."""
    verified_path = Path(config.VERIFIED_SOURCES_PATH)
    if not verified_path.exists():
        raise FileNotFoundError(f"Verified sources file not found: {verified_path}")
    
    with open(verified_path, 'r') as f:
        return json.load(f)

def load_statistical_results() -> Dict[str, Any]:
    """Load statistical results from CSV."""
    stats_path = Path(config.STATISTICAL_RESULTS_PATH)
    if not stats_path.exists():
        logger.warning(f"Statistical results file not found: {stats_path}")
        return {}
    
    # For simplicity, returning a dict structure; in production would parse CSV
    return {"results_loaded": True}

def load_network_metrics() -> Dict[str, Any]:
    """Load network metrics from CSV."""
    metrics_path = Path(config.NETWORK_METRICS_PATH)
    if not metrics_path.exists():
        logger.warning(f"Network metrics file not found: {metrics_path}")
        return {}
    
    return {"metrics_loaded": True}

def load_power_analysis() -> Dict[str, Any]:
    """Load power analysis results from JSON."""
    power_path = Path(config.POWER_ANALYSIS_PATH)
    if not power_path.exists():
        logger.warning(f"Power analysis file not found: {power_path}")
        return {}
    
    with open(power_path, 'r') as f:
        return json.load(f)

def determine_framing(metadata: Dict[str, Any]) -> str:
    """Determine if findings should be framed as associational or causal."""
    study_design = metadata.get('study_design')
    randomized = metadata.get('randomized')
    
    # Rule: If study_design is not 'randomized' OR randomized is not true, frame as associational
    if study_design != 'randomized' or randomized is not True:
        return "ASSOCIATIONAL"
    return "CAUSAL"

def generate_report_header(metadata: Dict[str, Any]) -> str:
    """Generate the Data Source section for the report."""
    source_name = metadata.get('source_name', 'Unknown')
    dataset_id = metadata.get('dataset_id', 'Unknown')
    dataset_version = metadata.get('dataset_version', 'Unknown')
    download_date = metadata.get('download_date', 'Unknown')
    verified_date = metadata.get('verified_date', 'Unknown')
    
    header = f"""# Brain Network Dynamics and VR Therapy Response Analysis Report

## Data Source

- **Source Name**: {source_name}
- **Dataset ID**: {dataset_id}
- **Dataset Version**: {dataset_version}
- **Download Date**: {download_date}
- **Verified Date**: {verified_date}

---

## Methodological Constraints

"""
    return header

def generate_report(
    metadata: Dict[str, Any],
    stats_results: Dict[str, Any],
    network_metrics: Dict[str, Any],
    power_analysis: Dict[str, Any]
) -> str:
    """Generate the full results report."""
    report_lines = []
    
    # Add Data Source section
    report_lines.append(generate_report_header(metadata))
    
    # Add framing statement
    framing = determine_framing(metadata)
    report_lines.append(f"## Framing\n\nFindings are framed as **{framing}**.\n\n")
    
    # Add power analysis details
    report_lines.append("## Power Analysis\n\n")
    if power_analysis:
        report_lines.append(f"- Minimum N Required: {power_analysis.get('min_N_required', 'N/A')}\n")
        report_lines.append(f"- Effect Size: {power_analysis.get('effect_size', 'N/A')}\n")
        report_lines.append(f"- Status: {power_analysis.get('status', 'N/A')}\n")
        if 'warning_message' in power_analysis:
            report_lines.append(f"- Warning: {power_analysis['warning_message']}\n")
    report_lines.append("\n")
    
    # Add statistical results summary
    report_lines.append("## Statistical Results\n\n")
    if stats_results:
        report_lines.append("Results have been computed and saved to `data/metrics/statistical_results.csv`.\n")
    else:
        report_lines.append("No statistical results available.\n")
    report_lines.append("\n")
    
    # Add network metrics summary
    report_lines.append("## Network Metrics\n\n")
    if network_metrics:
        report_lines.append("Network metrics have been computed and saved to `data/metrics/network_metrics.csv`.\n")
    else:
        report_lines.append("No network metrics available.\n")
    
    return "".join(report_lines)

def save_report(report_content: str, output_path: str) -> None:
    """Save the report to the specified path."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write(report_content)
    
    logger.info(f"Report saved to {output_path}")

def run_analysis() -> None:
    """Main entry point for report generation."""
    log_provenance("report_generation", "Starting report generation")
    
    try:
        # Load all required data
        metadata = load_metadata()
        stats_results = load_statistical_results()
        network_metrics = load_network_metrics()
        power_analysis = load_power_analysis()
        
        # Generate report
        report = generate_report(metadata, stats_results, network_metrics, power_analysis)
        
        # Save report
        save_report(report, config.REPORTS_RESULTS_PATH)
        
        log_provenance("report_generation", "Report generation completed successfully")
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise

def main() -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO)
    run_analysis()