import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for report generation
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

def load_correlation_results(filepath: str) -> pd.DataFrame:
    """Load correlation results from CSV."""
    path = Path(filepath)
    if not path.exists():
        logger.warning(f"Correlation results file not found: {filepath}")
        return pd.DataFrame()
    try:
        df = pd.read_csv(filepath)
        logger.info(f"Loaded {len(df)} correlation results from {filepath}")
        return df
    except Exception as e:
        logger.error(f"Error reading correlation results: {e}")
        return pd.DataFrame()

def load_ingestion_report(filepath: str) -> Dict[str, Any]:
    """Load ingestion report from JSON."""
    path = Path(filepath)
    if not path.exists():
        logger.warning(f"Ingestion report file not found: {filepath}")
        return {}
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        logger.info(f"Loaded ingestion report from {filepath}")
        return data
    except Exception as e:
        logger.error(f"Error reading ingestion report: {e}")
        return {}

def load_plot_files(directory: str) -> List[str]:
    """Load list of plot files from directory."""
    path = Path(directory)
    if not path.exists():
        logger.warning(f"Plot directory not found: {directory}")
        return []
    try:
        files = [str(f) for f in path.glob("*.png") if f.is_file()]
        logger.info(f"Found {len(files)} plot files in {directory}")
        return sorted(files)
    except Exception as e:
        logger.error(f"Error listing plot files: {e}")
        return []

def generate_html_report(
    correlation_results: pd.DataFrame,
    ingestion_report: Dict[str, Any],
    plot_files: List[str],
    output_path: str
) -> None:
    """Generate a comprehensive HTML report."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Determine status
    if not ingestion_report:
        status = "blocked"
        reason = "No verified data source found"
        summary_html = "<p style='color: red;'><strong>Project Blocked:</strong> No verified data source found.</p>"
    elif not correlation_results.empty:
        status = "success"
        significant = correlation_results[
            (correlation_results['is_moderate'] == True) &
            (correlation_results['is_meaningful'] == True)
        ]
        summary_html = f"""
        <p>Analysis completed successfully.</p>
        <p>Total correlations tested: <strong>{len(correlation_results)}</strong></p>
        <p>Significant associations found: <strong>{len(significant)}</strong></p>
        """
        if len(significant) == 0:
            summary_html += "<p style='color: orange;'><strong>No significant associations</strong> were found between alpha-diversity indices and sleep metrics.</p>"
    else:
        status = "success"
        summary_html = """
        <p>Analysis completed, but no correlations were generated.</p>
        <p style='color: orange;'><strong>No significant associations</strong> to report.</p>
        """

    # Build table HTML
    if not correlation_results.empty:
        table_html = correlation_results.to_html(index=False, classes='data-table', border=1)
    else:
        table_html = "<p>No correlation data available.</p>"

    # Build plots HTML
    plots_html = ""
    if plot_files:
        plots_html = "<h3>Generated Plots</h3><div style='display: flex; flex-wrap: wrap; gap: 20px;'>"
        for plot_path in plot_files:
            # Convert absolute path to relative for HTML if possible, or keep absolute if local
            # For safety in this context, we assume the report is viewed locally or paths are accessible
            plots_html += f"""
            <div style='text-align: center;'>
                <img src="{plot_path}" alt="Plot" style="max-width: 400px; border: 1px solid #ddd;">
                <p>{Path(plot_path).name}</p>
            </div>
            """
        plots_html += "</div>"
    else:
        plots_html = "<p>No plots generated.</p>"

    # Ingestion details
    ingestion_details = "<p>Ingestion report data not available.</p>"
    if ingestion_report:
        ingestion_details = f"""
        <h4>Ingestion Details</h4>
        <ul>
            <li>Status: {ingestion_report.get('status', 'N/A')}</li>
            <li>Measurement Status: {ingestion_report.get('measurement_status', 'N/A')}</li>
            <li>Total Initial Samples: {ingestion_report.get('total_initial_sample_count', 'N/A')}</li>
            <li>Excluded Count: {ingestion_report.get('excluded_count', 'N/A')}</li>
        </ul>
        """
        if ingestion_report.get('reason'):
            ingestion_details += f"<p><strong>Reason:</strong> {ingestion_report['reason']}</p>"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Gut Microbiome & Sleep Quality - Final Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; color: #333; }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #2c3e50; padding-bottom: 10px; }}
            h2 {{ color: #34495e; margin-top: 30px; }}
            h3 {{ color: #7f8c8d; }}
            .data-table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
            .data-table th, .data-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            .data-table th {{ background-color: #f2f2f2; }}
            .data-table tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .status-blocked {{ color: #c0392b; font-weight: bold; }}
            .status-success {{ color: #27ae60; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>Gut Microbiome Composition and Sleep Quality Analysis</h1>
        <p><em>Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>

        <h2>Summary</h2>
        {summary_html}

        <h2>Correlation Results</h2>
        {table_html}

        <h2>Visualizations</h2>
        {plots_html}

        <h2>Data Ingestion Report</h2>
        {ingestion_details}

        <footer>
            <p><small>Report generated by llmXive pipeline (Task T031).</small></p>
        </footer>
    </body>
    </html>
    """

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    logger.info(f"HTML report saved to {output_path}")

def run_final_report_generation(
    correlation_results_path: str = "data/processed/correlation_results.csv",
    ingestion_report_path: str = "data/processed/ingestion_report.json",
    plots_directory: str = "data/processed/plots",
    output_path: str = "data/processed/final_report.html"
) -> None:
    """Orchestrate the loading of data and generation of the final report."""
    logger.info("Starting final report generation...")

    # Load data
    correlation_results = load_correlation_results(correlation_results_path)
    ingestion_report = load_ingestion_report(ingestion_report_path)
    plot_files = load_plot_files(plots_directory)

    # Generate report
    generate_html_report(
        correlation_results=correlation_results,
        ingestion_report=ingestion_report,
        plot_files=plot_files,
        output_path=output_path
    )

    logger.info("Final report generation completed.")

def main():
    """Entry point for the script."""
    logging.basicConfig(level=logging.INFO)
    run_final_report_generation()

if __name__ == "__main__":
    main()
