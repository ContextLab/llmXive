"""
Report generation module for the Gut Microbiome and Sleep Quality study.

This module compiles correlation results and ingestion metrics into a
human-readable summary report and a structured JSON summary.
"""

import pandas as pd
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from src.config import load_config

# Configure logger
logger = logging.getLogger(__name__)

def load_correlation_results(file_path: str) -> pd.DataFrame:
    """
    Load correlation results from CSV.
    
    Args:
        file_path: Path to the correlation results CSV file.
        
    Returns:
        DataFrame containing correlation results.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or malformed.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Correlation results file not found: {file_path}")
    
    df = pd.read_csv(path)
    if df.empty:
        logger.warning("Correlation results file is empty.")
        return pd.DataFrame()
        
    return df

def load_ingestion_report(file_path: str) -> Dict[str, Any]:
    """
    Load ingestion report from JSON.
    
    Args:
        file_path: Path to the ingestion report JSON file.
        
    Returns:
        Dictionary containing ingestion metrics.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is malformed.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Ingestion report file not found: {file_path}")
        
    with open(path, 'r') as f:
        return json.load(f)

def compile_summary_table(correlation_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compile a summary table of significant correlations.
    
    Filters for meaningful correlations (q-value < 0.05 AND |r| > 0.3)
    and formats the output for reporting.
    
    Args:
        correlation_df: DataFrame with correlation results.
        
    Returns:
        DataFrame with significant correlations formatted for display.
    """
    if correlation_df.empty:
        return pd.DataFrame()
        
    # Filter for meaningful correlations
    significant = correlation_df[
        (correlation_df['is_meaningful'] == True) | 
        (correlation_df['is_moderate'] == True)
    ].copy()
    
    if significant.empty:
        logger.info("No significant or moderate correlations found.")
        return significant
        
    # Sort by absolute correlation coefficient (descending)
    significant['abs_r'] = significant['r'].abs()
    significant = significant.sort_values('abs_r', ascending=False)
    
    # Select and rename columns for report
    report_cols = ['metric_pair', 'r', 'p_value', 'q_value', 'is_moderate', 'is_meaningful']
    available_cols = [c for c in report_cols if c in significant.columns]
    
    return significant[available_cols]

def generate_report_text(
    summary_df: pd.DataFrame, 
    ingestion_report: Dict[str, Any],
    timestamp: Optional[datetime] = None
) -> str:
    """
    Generate a human-readable text report.
    
    Args:
        summary_df: DataFrame of significant correlations.
        ingestion_report: Dictionary with ingestion metrics.
        timestamp: Optional timestamp for the report header.
        
    Returns:
        Formatted string containing the full report.
    """
    if timestamp is None:
        timestamp = datetime.now()
        
    lines = []
    lines.append("=" * 60)
    lines.append("GUT MICROBIOME AND SLEEP QUALITY CORRELATION STUDY")
    lines.append("FINAL REPORT")
    lines.append(f"Generated: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)
    lines.append("")
    
    # Ingestion Summary
    lines.append("1. DATA INGESTION SUMMARY")
    lines.append("-" * 40)
    total_initial = ingestion_report.get('total_initial_sample_count', 0)
    excluded = ingestion_report.get('excluded_count', 0)
    proportion = ingestion_report.get('exclusion_proportion', 0.0)
    
    lines.append(f"   Initial Samples: {total_initial}")
    lines.append(f"   Excluded Samples: {excluded}")
    lines.append(f"   Exclusion Rate: {proportion:.2%}")
    lines.append("")
    
    # Correlation Results
    lines.append("2. CORRELATION ANALYSIS RESULTS")
    lines.append("-" * 40)
    
    if summary_df.empty:
        lines.append("   No significant or moderate associations found.")
        lines.append("   (Criteria: |r| > 0.3 AND q-value < 0.05)")
    else:
        lines.append(f"   Found {len(summary_df)} significant/moderate correlation(s):")
        lines.append("")
        
        for _, row in summary_df.iterrows():
            pair = row.get('metric_pair', 'Unknown Pair')
            r_val = row.get('r', 0.0)
            q_val = row.get('q_value', 1.0)
            significance = "Meaningful" if row.get('is_meaningful') else "Moderate"
            
            lines.append(f"   - {pair}")
            lines.append(f"     Correlation (r): {r_val:.4f}")
            lines.append(f"     Adjusted p-value (q): {q_val:.4f}")
            lines.append(f"     Significance: {significance}")
            lines.append("")
    
    lines.append("=" * 60)
    lines.append("END OF REPORT")
    lines.append("=" * 60)
    
    return "\n".join(lines)

def save_report(text_content: str, json_summary: Dict[str, Any], output_dir: str) -> tuple:
    """
    Save the report as a text file and the summary as a JSON file.
    
    Args:
        text_content: The formatted report text.
        json_summary: Dictionary containing structured summary data.
        output_dir: Directory to save the files.
        
    Returns:
        Tuple of (text_file_path, json_file_path)
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    text_file = output_path / f"report_{timestamp}.txt"
    json_file = output_path / f"report_summary_{timestamp}.json"
    
    with open(text_file, 'w') as f:
        f.write(text_content)
        
    with open(json_file, 'w') as f:
        json.dump(json_summary, f, indent=2, default=str)
        
    logger.info(f"Report saved to {text_file} and {json_file}")
    
    return str(text_file), str(json_file)

def run_report_generation(
    correlation_file: str,
    ingestion_file: str,
    output_dir: str
) -> tuple:
    """
    Main function to orchestrate report generation.
    
    Args:
        correlation_file: Path to correlation results CSV.
        ingestion_file: Path to ingestion report JSON.
        output_dir: Directory to save the final report.
        
    Returns:
        Tuple of (text_file_path, json_file_path)
    """
    try:
        # Load data
        logger.info(f"Loading correlation results from {correlation_file}")
        corr_df = load_correlation_results(correlation_file)
        
        logger.info(f"Loading ingestion report from {ingestion_file}")
        ingest_rep = load_ingestion_report(ingestion_file)
        
        # Compile summary
        logger.info("Compiling summary table...")
        summary_df = compile_summary_table(corr_df)
        
        # Generate text
        logger.info("Generating report text...")
        report_text = generate_report_text(summary_df, ingest_rep)
        
        # Prepare JSON summary
        json_summary = {
            "report_generated_at": datetime.now().isoformat(),
            "ingestion_metrics": ingest_rep,
            "significant_correlations_count": len(summary_df),
            "correlations": summary_df.to_dict(orient='records')
        }
        
        # Save
        logger.info(f"Saving report to {output_dir}")
        text_path, json_path = save_report(report_text, json_summary, output_dir)
        
        return text_path, json_path
        
    except FileNotFoundError as e:
        logger.error(f"Input file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise

def main():
    """Entry point for the report generation script."""
    config = load_config()
    
    # Set up logging
    log_level = getattr(logging, config.get('LOG_LEVEL', 'INFO'))
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Define paths
    # Assuming standard project structure
    base_dir = Path(config.get('PROJECT_ROOT', '.'))
    data_dir = base_dir / 'data' / 'processed'
    
    correlation_file = data_dir / 'correlation_results.csv'
    ingestion_file = data_dir / 'ingestion_report.json'
    output_dir = data_dir
    
    # Check if input files exist
    if not correlation_file.exists():
        logger.error(f"Correlation results not found at {correlation_file}. "
                     "Please ensure T024 has completed successfully.")
        return 1
        
    if not ingestion_file.exists():
        logger.error(f"Ingestion report not found at {ingestion_file}. "
                     "Please ensure T017 has completed successfully.")
        return 1
    
    try:
        text_path, json_path = run_report_generation(
            str(correlation_file),
            str(ingestion_file),
            str(output_dir)
        )
        logger.info(f"Report generation complete. Text: {text_path}, JSON: {json_path}")
        return 0
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())