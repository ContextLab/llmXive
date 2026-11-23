import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime

# Configuration paths (relative to project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"
REPORT_FILE = DATA_RESULTS_DIR / "summary_report.txt"
CORRELATION_RESULTS_FILE = DATA_RESULTS_DIR / "correlation_results.csv"
META_ANALYSIS_FILE = DATA_RESULTS_DIR / "meta_analysis_results.csv"
SENSITIVITY_FILE = DATA_RESULTS_DIR / "sensitivity_analysis.csv"

# Ensure logging is configured
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(PROJECT_ROOT / "data" / "logs" / "reporting.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_correlation_results() -> Optional[pd.DataFrame]:
    """Load correlation results from CSV."""
    if not CORRELATION_RESULTS_FILE.exists():
        logger.warning(f"Correlation results file not found: {CORRELATION_RESULTS_FILE}")
        return None
    try:
        df = pd.read_csv(CORRELATION_RESULTS_FILE)
        logger.info(f"Loaded correlation results: {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"Failed to load correlation results: {e}")
        return None


def load_meta_analysis_results() -> Optional[pd.DataFrame]:
    """Load meta-analysis results from CSV."""
    if not META_ANALYSIS_FILE.exists():
        logger.warning(f"Meta-analysis results file not found: {META_ANALYSIS_FILE}")
        return None
    try:
        df = pd.read_csv(META_ANALYSIS_FILE)
        logger.info(f"Loaded meta-analysis results: {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"Failed to load meta-analysis results: {e}")
        return None


def load_sensitivity_analysis() -> Optional[pd.DataFrame]:
    """Load sensitivity analysis results from CSV."""
    if not SENSITIVITY_FILE.exists():
        logger.warning(f"Sensitivity analysis file not found: {SENSITIVITY_FILE}")
        return None
    try:
        df = pd.read_csv(SENSITIVITY_FILE)
        logger.info(f"Loaded sensitivity analysis results: {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"Failed to load sensitivity analysis results: {e}")
        return None


def classify_correlation(r_value: float) -> str:
    """
    Classify the strength of correlation based on absolute r value.
    
    Logic: Flag |r| >= 0.3 as 'moderate'.
    """
    abs_r = abs(r_value)
    if abs_r >= 0.5:
        return "strong"
    elif abs_r >= 0.3:
        return "moderate"
    elif abs_r >= 0.1:
        return "weak"
    else:
        return "negligible"


def generate_summary_report_data(
    correlation_df: Optional[pd.DataFrame] = None,
    meta_df: Optional[pd.DataFrame] = None,
    sensitivity_df: Optional[pd.DataFrame] = None
) -> Dict[str, Any]:
    """
    Generate table data for the summary report.
    
    Returns a dictionary containing:
    - repo_correlation_table: Markdown table string for per-repo stats
    - meta_analysis_table: Markdown table string for meta-analysis
    - sensitivity_table: Markdown table string for sensitivity analysis
    - timestamp: Generation timestamp
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_data = {
        "timestamp": timestamp,
        "repo_correlation_table": "",
        "meta_analysis_table": "",
        "sensitivity_table": ""
    }

    # 1. Per-Repo Correlation Table
    # Format: Markdown table with columns: repo_id, r, p, significance
    if correlation_df is not None and not correlation_df.empty:
        # Ensure we have the right columns. 
        # Based on T020: metric_type, r_value, p_value, n, threshold.
        # We need to aggregate or select specific rows if multiple metrics exist.
        # Assuming we want the primary Pearson correlation for each repo.
        # If 'repo_id' is not in the dataframe, we might need to infer it or 
        # the dataframe structure from T020 might be different (e.g., aggregated per repo).
        # Let's assume the dataframe has a 'repo_id' column or we iterate rows.
        
        # If the dataframe doesn't have repo_id, we assume each row is a distinct study/repo.
        if 'repo_id' not in correlation_df.columns:
            # Fallback: create a generic ID or assume the input structure
            # For this implementation, we assume the data comes from a process that 
            # generated one row per repo or we filter for 'pearson' and take the first.
            # Let's assume the T020 output includes a 'repo_id' or we use an index.
            # To be safe, let's look for a column that looks like an ID or use the index.
            # If the schema from T020 is strictly `metric_type, r_value, p_value, n, threshold`,
            # and no repo_id, we might be aggregating across all repos in one table.
            # However, the task T028a asks for `repo_id` column.
            # Let's assume the previous step (T020) or the data loading logic 
            # ensures `repo_id` is present, or we construct it if missing.
            
            # If missing, we'll create a placeholder column to satisfy the table format.
            # In a real pipeline, T020 should have preserved the repo_id.
            if 'repo_id' not in correlation_df.columns:
                logger.warning("repo_id column missing in correlation results. Using index.")
                correlation_df = correlation_df.reset_index()
                correlation_df['repo_id'] = correlation_df['index'].apply(lambda x: f"repo_{x}")
                correlation_df.drop(columns=['index'], inplace=True)

        # Filter for Pearson if available, or use all
        pearson_rows = correlation_df[correlation_df['metric_type'] == 'pearson'] if 'metric_type' in correlation_df.columns else correlation_df
        
        if pearson_rows.empty:
            pearson_rows = correlation_df

        # Select columns: repo_id, r_value, p_value
        # Calculate significance
        rows_data = []
        for _, row in pearson_rows.iterrows():
            r_val = row.get('r_value', 0.0)
            p_val = row.get('p_value', 1.0)
            repo_id = row.get('repo_id', 'unknown')
            significance = classify_correlation(r_val)
            
            # Determine if significant (p < 0.05)
            sig_flag = "Yes" if p_val < 0.05 else "No"
            
            rows_data.append({
                "repo_id": repo_id,
                "r": f"{r_val:.4f}",
                "p": f"{p_val:.4f}",
                "significance": f"{significance} ({sig_flag})"
            })
        
        if rows_data:
            report_data["repo_correlation_table"] = _rows_to_markdown_table(
                rows_data, 
                columns=["repo_id", "r", "p", "significance"]
            )
        else:
            report_data["repo_correlation_table"] = "No correlation data found."
    else:
        report_data["repo_correlation_table"] = "No correlation data found."

    # 2. Meta-Analysis Table
    if meta_df is not None and not meta_df.empty:
        rows_data = []
        for _, row in meta_df.iterrows():
            rows_data.append({
                "method": row.get('method', 'Unknown'),
                "combined_r": f"{row.get('combined_r', 0):.4f}",
                "combined_se": f"{row.get('combined_se', 0):.4f}",
                "p_value": f"{row.get('p_value', 1):.4f}",
                "k_studies": str(row.get('k_studies', 0))
            })
        report_data["meta_analysis_table"] = _rows_to_markdown_table(
            rows_data,
            columns=["method", "combined_r", "combined_se", "p_value", "k_studies"]
        )
    else:
        report_data["meta_analysis_table"] = "No meta-analysis data found."

    # 3. Sensitivity Analysis Table
    if sensitivity_df is not None and not sensitivity_df.empty:
        rows_data = []
        for _, row in sensitivity_df.iterrows():
            rows_data.append({
                "threshold": str(row.get('threshold', 0)),
                "r_value": f"{row.get('r_value', 0):.4f}",
                "p_value": f"{row.get('p_value', 1):.4f}",
                "n": str(row.get('n', 0))
            })
        report_data["sensitivity_table"] = _rows_to_markdown_table(
            rows_data,
            columns=["threshold", "r_value", "p_value", "n"]
        )
    else:
        report_data["sensitivity_table"] = "No sensitivity analysis data found."

    return report_data


def _rows_to_markdown_table(rows: List[Dict], columns: List[str]) -> str:
    """Helper to convert list of dicts to a Markdown table string."""
    if not rows:
        return ""
    
    # Header
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    
    # Rows
    body_lines = []
    for row in rows:
        row_str = "| " + " | ".join([str(row.get(col, "")) for col in columns]) + " |"
        body_lines.append(row_str)
    
    return "\n".join([header, separator] + body_lines)


def save_summary_report(report_data: Dict[str, Any], output_path: Optional[Path] = None) -> bool:
    """
    Save the summary report to a text file.
    """
    if output_path is None:
        output_path = REPORT_FILE
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Summary Report\n")
            f.write(f"Generated: {report_data['timestamp']}\n\n")
            
            f.write("## Per-Repo Correlation Analysis\n")
            f.write("Correlation between code churn and technical debt per repository.\n\n")
            f.write(report_data["repo_correlation_table"] + "\n\n")
            
            f.write("## Meta-Analysis Results\n")
            f.write("Combined correlation across studies using Fisher's Z transformation.\n\n")
            f.write(report_data["meta_analysis_table"] + "\n\n")
            
            f.write("## Sensitivity Analysis\n")
            f.write("Correlation stability across different LOC thresholds.\n\n")
            f.write(report_data["sensitivity_table"] + "\n\n")
            
            f.write("---\n")
            f.write("End of Report\n")
        
        logger.info(f"Summary report saved to: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save summary report: {e}")
        return False


def run_reporting() -> bool:
    """
    Main entry point for the reporting task.
    Loads data, generates report data, and saves the report.
    """
    logger.info("Starting reporting task...")
    
    # Load data
    correlation_df = load_correlation_results()
    meta_df = load_meta_analysis_results()
    sensitivity_df = load_sensitivity_analysis()
    
    # Generate report data
    report_data = generate_summary_report_data(correlation_df, meta_df, sensitivity_df)
    
    # Save report
    success = save_summary_report(report_data)
    
    if success:
        logger.info("Reporting task completed successfully.")
    else:
        logger.error("Reporting task failed.")
        
    return success


def main():
    """CLI entry point."""
    run_reporting()


if __name__ == "__main__":
    main()