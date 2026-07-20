import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

import pandas as pd

from code.config import Config
from code.utils.logging import setup_logging

logger = logging.getLogger(__name__)


def load_metadata(metadata_path: Path) -> Dict[str, Any]:
    """
    Load study metadata from a JSON file.

    Args:
        metadata_path: Path to the metadata JSON file.

    Returns:
        Dictionary containing metadata.
    """
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    
    with open(metadata_path, 'r') as f:
        return json.load(f)


def determine_framing(metadata: Dict[str, Any]) -> str:
    """
    Determine the appropriate framing for the report based on metadata.

    Args:
        metadata: Dictionary containing study design information.

    Returns:
        String indicating 'Associational' or 'Causal' (if randomized).
    """
    study_design = metadata.get('study_design', '')
    is_randomized = metadata.get('randomized', False)

    if study_design == 'randomized' or is_randomized is True:
        return "Causal"
    else:
        return "Associational"


def load_statistical_results(results_path: Path) -> pd.DataFrame:
    """
    Load statistical results from a CSV file.

    Args:
        results_path: Path to the statistical results CSV.

    Returns:
        DataFrame containing statistical results.
    """
    if not results_path.exists():
        raise FileNotFoundError(f"Statistical results file not found: {results_path}")
    
    return pd.read_csv(results_path)


def load_network_metrics(metrics_path: Path) -> pd.DataFrame:
    """
    Load network metrics from a CSV file.

    Args:
        metrics_path: Path to the network metrics CSV.

    Returns:
        DataFrame containing network metrics.
    """
    if not metrics_path.exists():
        raise FileNotFoundError(f"Network metrics file not found: {metrics_path}")
    
    return pd.read_csv(metrics_path)


def generate_report(
    metadata: Dict[str, Any],
    stats_results: pd.DataFrame,
    network_metrics: pd.DataFrame,
    framing: str
) -> str:
    """
    Generate a markdown report string.

    Args:
        metadata: Study metadata.
        stats_results: Statistical results DataFrame.
        network_metrics: Network metrics DataFrame.
        framing: Framing string ('Associational' or 'Causal').

    Returns:
        Markdown formatted report string.
    """
    report_lines = [
        f"# Brain Network Dynamics and VR Therapy Response Report",
        f"",
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Framing**: {framing} study",
        f"",
        f"## Study Design",
        f"- Study Type: {metadata.get('study_design', 'N/A')}",
        f"- Randomized: {metadata.get('randomized', 'N/A')}",
        f"",
        f"## Statistical Results",
        f"",
    ]

    if not stats_results.empty:
        report_lines.append("| Metric | Coefficient | P-value | VIF |")
        report_lines.append("|---|---|---|---|")
        for _, row in stats_results.iterrows():
            report_lines.append(
                f"| {row.get('metric', 'N/A')} | {row.get('coefficient', 'N/A'):.4f} | "
                f"{row.get('p_value', 'N/A'):.4f} | {row.get('vif', 'N/A'):.2f} |"
            )
    else:
        report_lines.append("No statistical results available.")

    report_lines.extend([
        "",
        "## Network Metrics Summary",
        "",
    ])

    if not network_metrics.empty:
        report_lines.append(f"- Subjects analyzed: {len(network_metrics)}")
        avg_modularity = network_metrics['modularity_q'].mean()
        avg_global_eff = network_metrics['global_efficiency'].mean()
        report_lines.append(f"- Average Modularity: {avg_modularity:.4f}")
        report_lines.append(f"- Average Global Efficiency: {avg_global_eff:.4f}")
    else:
        report_lines.append("No network metrics available.")

    report_lines.extend([
        "",
        "## Conclusion",
        f"The analysis was framed as {framing.lower()} due to the study design.",
        "Further details on specific metrics and subject-level data are available in the raw output files.",
    ])

    return "\n".join(report_lines)


def save_report(report_content: str, output_path: Path) -> None:
    """
    Save the report content to a markdown file.

    Args:
        report_content: The markdown content of the report.
        output_path: Path to save the report.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(report_content)
    logger.info(f"Report saved to {output_path}")


def run_analysis(
    metadata_path: Path,
    stats_results_path: Path,
    network_metrics_path: Path,
    output_path: Path,
    config: Config
) -> None:
    """
    Run the report generation pipeline.

    Args:
        metadata_path: Path to metadata JSON.
        stats_results_path: Path to statistical results CSV.
        network_metrics_path: Path to network metrics CSV.
        output_path: Path to save the final report.
        config: Configuration object.
    """
    try:
        metadata = load_metadata(metadata_path)
        framing = determine_framing(metadata)
        
        stats_df = load_statistical_results(stats_results_path)
        network_df = load_network_metrics(network_metrics_path)
        
        report = generate_report(metadata, stats_df, network_df, framing)
        save_report(report, output_path)
        
        logger.info("Report generation complete.")
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise


def main():
    """Main entry point for the report generation script."""
    setup_logging()
    config = Config()
    
    metadata_path = Path(config.metadata_path)
    stats_path = Path(config.metrics_output_dir) / "statistical_results.csv"
    network_path = Path(config.metrics_output_dir) / "network_metrics.csv"
    report_path = Path(config.report_output_path)
    
    run_analysis(metadata_path, stats_path, network_path, report_path, config)


if __name__ == "__main__":
    main()
