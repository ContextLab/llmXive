import pandas as pd
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from src.config import load_config
from src.utils.hashing import compute_sha256

logger = logging.getLogger(__name__)

def load_correlation_results() -> Optional[pd.DataFrame]:
    """
    Load the correlation results from the processed data directory.
    
    Returns:
        pd.DataFrame: The correlation results, or None if file not found.
    """
    config = load_config()
    results_path = Path(config['data_dir']) / 'processed' / 'correlation_results.csv'
    
    if not results_path.exists():
        logger.error(f"Correlation results file not found at {results_path}")
        return None
    
    try:
        df = pd.read_csv(results_path)
        logger.info(f"Loaded {len(df)} correlation results from {results_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load correlation results: {e}")
        return None

def load_ingestion_report() -> Optional[Dict[str, Any]]:
    """
    Load the ingestion report from the processed data directory.
    
    Returns:
        Dict[str, Any]: The ingestion report, or None if file not found.
    """
    config = load_config()
    report_path = Path(config['data_dir']) / 'processed' / 'ingestion_report.json'
    
    if not report_path.exists():
        logger.warning(f"Ingestion report not found at {report_path}")
        return None
    
    try:
        with open(report_path, 'r') as f:
            report = json.load(f)
        logger.info(f"Loaded ingestion report from {report_path}")
        return report
    except Exception as e:
        logger.error(f"Failed to load ingestion report: {e}")
        return None

def compile_summary_table(correlation_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compile a summary table of significant correlations.
    
    Args:
        correlation_df: The full correlation results DataFrame.
        
    Returns:
        pd.DataFrame: A summary table of meaningful correlations.
    """
    if correlation_df is None or correlation_df.empty:
        logger.warning("No correlation data available for summary table")
        return pd.DataFrame()
    
    # Filter for meaningful correlations (q-value < 0.05 AND |r| > 0.3)
    meaningful = correlation_df[
        (correlation_df['is_meaningful'] == True) | 
        (correlation_df['q_value'] < 0.05)
    ].copy()
    
    if meaningful.empty:
        logger.info("No significant associations found")
        # Return a DataFrame with the expected columns but no rows
        return pd.DataFrame(columns=[
            'diversity_metric', 'sleep_metric', 'correlation_coefficient', 
            'p_value', 'q_value', 'is_moderate', 'is_meaningful'
        ])
    
    # Select and order relevant columns
    summary_cols = [
        'diversity_metric', 'sleep_metric', 'correlation_coefficient', 
        'p_value', 'q_value', 'is_moderate', 'is_meaningful'
    ]
    available_cols = [col for col in summary_cols if col in meaningful.columns]
    
    summary_table = meaningful[available_cols].sort_values(
        by='q_value', ascending=True
    ).reset_index(drop=True)
    
    logger.info(f"Compiled summary table with {len(summary_table)} meaningful correlations")
    return summary_table

def generate_report_text(
    summary_table: pd.DataFrame,
    ingestion_report: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate a text report summarizing the findings.
    
    Args:
        summary_table: The summary table of correlations.
        ingestion_report: Optional ingestion report with exclusion statistics.
        
    Returns:
        str: The formatted report text.
    """
    lines = []
    lines.append("=" * 80)
    lines.append("GUT MICROBIOME AND SLEEP QUALITY CORRELATION REPORT")
    lines.append("=" * 80)
    lines.append("")
    
    # Ingestion Summary
    lines.append("DATA INGESTION SUMMARY")
    lines.append("-" * 40)
    if ingestion_report:
        total = ingestion_report.get('total_initial_sample_count', 'N/A')
        excluded = ingestion_report.get('excluded_count', 'N/A')
        proportion = ingestion_report.get('exclusion_proportion', 'N/A')
        lines.append(f"Initial samples: {total}")
        lines.append(f"Excluded samples: {excluded}")
        lines.append(f"Exclusion proportion: {proportion}")
    else:
        lines.append("Ingestion report not available.")
    lines.append("")
    
    # Correlation Summary
    lines.append("CORRELATION ANALYSIS RESULTS")
    lines.append("-" * 40)
    
    if summary_table.empty:
        lines.append("No significant associations were found between gut microbiome")
        lines.append("alpha-diversity metrics and sleep quality parameters.")
        lines.append("")
        lines.append("This suggests that, within the constraints of this dataset and")
        lines.append("analysis pipeline, gut microbiome composition (as measured by")
        lines.append("alpha-diversity indices) does not show strong correlations with")
        lines.append("sleep efficiency or sleep duration.")
    else:
        lines.append(f"Found {len(summary_table)} significant correlation(s):")
        lines.append("")
        
        for idx, row in summary_table.iterrows():
            diversity = row.get('diversity_metric', 'Unknown')
            sleep = row.get('sleep_metric', 'Unknown')
            r = row.get('correlation_coefficient', 'N/A')
            p = row.get('p_value', 'N/A')
            q = row.get('q_value', 'N/A')
            moderate = row.get('is_moderate', False)
            meaningful = row.get('is_meaningful', False)
            
            lines.append(f"  {diversity} vs {sleep}:")
            lines.append(f"    Correlation (r): {r}")
            lines.append(f"    P-value: {p}")
            lines.append(f"    Q-value (FDR): {q}")
            lines.append(f"    Moderate (|r|>0.3): {moderate}")
            lines.append(f"    Meaningful (q<0.05 & |r|>0.3): {meaningful}")
            lines.append("")
    
    lines.append("=" * 80)
    lines.append("END OF REPORT")
    lines.append("=" * 80)
    
    return "\n".join(lines)

def save_report(
    report_text: str,
    summary_table: pd.DataFrame,
    output_dir: Optional[Path] = None
) -> Dict[str, str]:
    """
    Save the report artifacts to disk.
    
    Args:
        report_text: The formatted report text.
        summary_table: The summary table DataFrame.
        output_dir: Optional output directory (defaults to config data/processed/).
        
    Returns:
        Dict[str, str]: Paths to saved artifacts.
    """
    config = load_config()
    if output_dir is None:
        output_dir = Path(config['data_dir']) / 'processed'
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    saved_files = {}
    
    # Save text report
    text_path = output_dir / 'final_report.txt'
    with open(text_path, 'w', encoding='utf-8') as f:
        f.write(report_text)
    saved_files['text_report'] = str(text_path)
    logger.info(f"Saved text report to {text_path}")
    
    # Save summary table as CSV
    csv_path = output_dir / 'correlation_summary.csv'
    summary_table.to_csv(csv_path, index=False)
    saved_files['summary_csv'] = str(csv_path)
    logger.info(f"Saved summary table to {csv_path}")
    
    # Save JSON version of summary
    json_path = output_dir / 'correlation_summary.json'
    summary_dict = summary_table.to_dict(orient='records')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(summary_dict, f, indent=2)
    saved_files['summary_json'] = str(json_path)
    logger.info(f"Saved summary JSON to {json_path}")
    
    return saved_files

def run_report_generation() -> Dict[str, Any]:
    """
    Main entry point to compile and save the final report.
    
    Returns:
        Dict[str, Any]: Status and paths of generated artifacts.
    """
    logger.info("Starting report generation...")
    
    # Load inputs
    correlation_df = load_correlation_results()
    ingestion_report = load_ingestion_report()
    
    if correlation_df is None:
        logger.error("Cannot generate report: Correlation results not found")
        return {
            'status': 'failed',
            'reason': 'Correlation results file not found',
            'artifacts': {}
        }
    
    # Compile summary
    summary_table = compile_summary_table(correlation_df)
    
    # Generate report text
    report_text = generate_report_text(summary_table, ingestion_report)
    
    # Save artifacts
    saved_files = save_report(report_text, summary_table)
    
    logger.info("Report generation completed successfully")
    return {
        'status': 'success',
        'artifacts': saved_files,
        'summary_count': len(summary_table)
    }

def main():
    """CLI entry point for report generation."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    result = run_report_generation()
    
    if result['status'] == 'success':
        print("Report generation successful!")
        print(f"Artifacts saved:")
        for name, path in result['artifacts'].items():
            print(f"  - {name}: {path}")
        print(f"Summary count: {result['summary_count']}")
    else:
        print(f"Report generation failed: {result.get('reason', 'Unknown error')}")
        exit(1)

if __name__ == '__main__':
    main()