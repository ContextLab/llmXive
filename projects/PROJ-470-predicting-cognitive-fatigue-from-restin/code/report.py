import os
import sys
import yaml
from pathlib import Path
import pandas as pd
import numpy as np
import logging

# Configure logging to match project standard
def setup_logger(name: str, log_file: str = None, level=logging.INFO):
    """Set up a logger with file and console handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if logger.hasHandlers():
        logger.handlers.clear()
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    return logger

def load_config(config_path: str = "code/config.yaml"):
    """Load configuration from YAML file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_analysis_results(results_dir: str = "data/analysis"):
    """Load all analysis result CSV files from the specified directory."""
    results = {}
    results_path = Path(results_dir)
    
    if not results_path.exists():
        logging.warning(f"Analysis results directory not found: {results_dir}")
        return results
    
    for csv_file in results_path.glob("*.csv"):
        try:
            df = pd.read_csv(csv_file)
            results[csv_file.stem] = df
        except Exception as e:
            logging.error(f"Failed to load {csv_file}: {e}")
    
    return results

def load_sensitivity_table(file_path: str = "data/analysis/sensitivity_table.csv"):
    """Load the sensitivity analysis table."""
    if not os.path.exists(file_path):
        logging.warning(f"Sensitivity table not found: {file_path}")
        return None
    
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        logging.error(f"Failed to load sensitivity table: {e}")
        return None

def calculate_effect_size(r_value: float):
    """Calculate Cohen's d-like effect size from correlation coefficient."""
    if r_value is None or np.isnan(r_value):
        return None
    # Simplified approximation for effect size interpretation
    return abs(r_value)

def render_markdown_table(df: pd.DataFrame, title: str = None) -> str:
    """Render a pandas DataFrame as a markdown table."""
    if df is None or df.empty:
        return "No data available."
    
    md_str = df.to_markdown(index=False)
    if title:
        return f"### {title}\n\n{md_str}\n"
    return md_str

def generate_report(analysis_results: dict = None, output_path: str = "docs/final_report.md"):
    """Generate the final markdown report from analysis results."""
    if analysis_results is None:
        analysis_results = load_analysis_results()
    
    report_lines = []
    report_lines.append("# Cognitive Fatigue Analysis Report\n")
    report_lines.append("This report summarizes the correlation analysis between EEG complexity metrics and fatigue scores.\n")
    
    # Render each analysis table
    for name, df in analysis_results.items():
        if not df.empty:
            report_lines.append(f"## {name.replace('_', ' ').title()}\n")
            report_lines.append(render_markdown_table(df))
            report_lines.append("\n")
    
    # Specific handling for sensitivity table if present
    if "sensitivity_table" in analysis_results:
        report_lines.append("## Sensitivity Analysis\n")
        report_lines.append(render_markdown_table(analysis_results["sensitivity_table"], "Sensitivity Thresholds"))
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write("\n".join(report_lines))
    
    logging.info(f"Report generated: {output_path}")
    return output_path

def main():
    """Main entry point for report generation."""
    config = load_config()
    logger = setup_logger("report", "logs/report.log")
    
    # Load all analysis results
    analysis_results = load_analysis_results()
    
    if not analysis_results:
        logger.warning("No analysis results found to generate report.")
        # Create a minimal report indicating no data
        generate_report({}, "docs/final_report.md")
        return
    
    # Generate the final report
    output_path = generate_report(analysis_results)
    print(f"Report successfully generated at: {output_path}")

if __name__ == "__main__":
    main()
