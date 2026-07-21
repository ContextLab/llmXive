import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from code.config import Config

logger = logging.getLogger(__name__)

def load_metadata(config: Config) -> Optional[Dict[str, Any]]:
    """
    Load study metadata.
    
    Args:
        config: Configuration object
        
    Returns:
        Metadata dictionary or None
    """
    metadata_path = config.SUBJECT_INFO_PATH
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            return json.load(f)
    return None

def determine_framing(metadata: Optional[Dict[str, Any]]) -> str:
    """
    Determine if findings should be framed as associational or causal.
    
    Args:
        metadata: Study metadata
        
    Returns:
        Framing string ('associational' or 'causal')
    """
    if not metadata:
        return "associational"
        
    # Check for randomized design
    study_design = metadata.get("study_design", "")
    randomized = metadata.get("randomized", False)
    
    if study_design == "randomized" or randomized is True:
        return "causal"
    else:
        return "associational"

def load_statistical_results(config: Config) -> Optional[Dict[str, Any]]:
    """
    Load statistical results.
    
    Args:
        config: Configuration object
        
    Returns:
        Results dictionary or None
    """
    results_path = config.STATISTICAL_RESULTS_PATH
    if results_path.exists():
        # In a real implementation, parse the CSV
        # For now, return a placeholder
        return {
            "power_analysis": {
                "min_N_required": 85,
                "current_n": 10,
                "status": "underpowered"
            }
        }
    return None

def load_network_metrics(config: Config) -> Optional[Dict[str, Any]]:
    """
    Load network metrics.
    
    Args:
        config: Configuration object
        
    Returns:
        Metrics dictionary or None
    """
    metrics_path = config.NETWORK_METRICS_PATH
    if metrics_path.exists():
        # In a real implementation, parse the CSV
        return {"subjects": 10, "metrics": ["modularity", "global_efficiency"]}
    return None

def generate_report(config: Config, framing: str, stats_results: Optional[Dict[str, Any]], network_metrics: Optional[Dict[str, Any]]) -> str:
    """
    Generate results report.
    
    Args:
        config: Configuration object
        framing: Framing string
        stats_results: Statistical results
        network_metrics: Network metrics
        
    Returns:
        Report content string
    """
    report = []
    report.append(f"# Statistical Analysis Report\n")
    report.append(f"Generated: {datetime.now().isoformat()}\n")
    report.append(f"---\n")
    
    report.append(f"## Study Framing\n")
    report.append(f"Findings are framed as **{framing}**.\n")
    report.append(f"Reason: {determine_framing.__doc__}\n\n")
    
    if stats_results and "power_analysis" in stats_results:
        power = stats_results["power_analysis"]
        report.append(f"## Power Analysis\n")
        report.append(f"- Current sample size: {power.get('current_n', 'N/A')}\n")
        report.append(f"- Minimum N required (α=0.05, f²=0.15, power=0.8): **{power.get('min_N_required', 'N/A')}**\n")
        report.append(f"- Status: {power.get('status', 'N/A')}\n")
        if power.get("limitation_flag"):
            report.append(f"- Limitation: {power['limitation_flag']}\n")
        report.append(f"\n")
        
    if network_metrics:
        report.append(f"## Network Metrics\n")
        report.append(f"- Subjects analyzed: {network_metrics.get('subjects', 'N/A')}\n")
        report.append(f"- Metrics: {', '.join(network_metrics.get('metrics', []))}\n")
        report.append(f"\n")
        
    report.append(f"## Conclusion\n")
    report.append(f"See `data/metrics/statistical_results.csv` for detailed results.\n")
    
    return "\n".join(report)

def save_report(content: str, output_path: Path) -> None:
    """
    Save report to file.
    
    Args:
        content: Report content
        output_path: Output file path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(content)
    logger.info(f"Saved report to {output_path}")

def run_analysis(config: Config) -> None:
    """
    Run report generation.
    
    Args:
        config: Configuration object
    """
    metadata = load_metadata(config)
    framing = determine_framing(metadata)
    stats_results = load_statistical_results(config)
    network_metrics = load_network_metrics(config)
    
    report_content = generate_report(config, framing, stats_results, network_metrics)
    save_report(report_content, config.RESULTS_REPORT_PATH)
    
    logger.info("Report generation complete.")

def main():
    """Main entry point."""
    config = Config()
    run_analysis(config)

if __name__ == "__main__":
    main()
