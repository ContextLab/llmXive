"""
Generate the significance stability report (T036).

This script loads the results metrics (T035) and explicitly documents
the stability metric and flip rate in a dedicated CSV report file.

It implements:
- FR-007: Mandate calculation of 'significance flip rate' and 'significance stability'.
- SC-003: Report the proportion of shifts where p < 0.05 (stability) and where the conclusion changes (flip rate).

Output:
- data/processed/significance_stability_report.csv
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from logging_config import get_logger, info, warning, error, debug
from config import load_config

# Ensure the code directory is in the path for imports
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

logger = get_logger(__name__)

def load_results_metrics():
    """Load the merged metrics from T035."""
    config = load_config()
    # Path relative to project root
    project_root = code_dir.parent
    metrics_path = project_root / "data" / "processed" / "results_metrics.csv"
    
    if not metrics_path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {metrics_path}. "
            "Ensure T035 (generate_results_metrics.py) has been run successfully."
        )
    
    df = pd.read_csv(metrics_path)
    logger.info(f"Loaded {len(df)} rows from {metrics_path}")
    return df

def generate_stability_report(df_metrics):
    """
    Extract stability and flip rate metrics from the results dataframe.
    
    Expected columns in df_metrics (from T035):
    - comparison: string identifying the pairwise comparison (e.g., "Immediate vs Delayed")
    - stability_metric: float (proportion of shifts where p < 0.05)
    - flip_rate: float (proportion of shifts where conclusion changes)
    
    Returns a new DataFrame formatted for the report.
    """
    required_cols = ['comparison', 'stability_metric', 'flip_rate']
    missing_cols = [c for c in required_cols if c not in df_metrics.columns]
    
    if missing_cols:
        raise ValueError(
            f"Input metrics file is missing required columns: {missing_cols}. "
            "Ensure T035 produced valid output."
        )
    
    # Select and rename columns for clarity in the final report
    report_df = df_metrics[required_cols].copy()
    report_df.columns = [
        'comparison_group',
        'significance_stability_proportion',
        'significance_flip_rate'
    ]
    
    # Add metadata columns
    report_df['metric_type'] = 'stability_and_flip_rate'
    report_df['source_task'] = 'T035'
    report_df['target_task'] = 'T036'
    
    # Calculate summary statistics across all comparisons
    avg_stability = report_df['significance_stability_proportion'].mean()
    avg_flip_rate = report_df['significance_flip_rate'].mean()
    
    # Append a summary row
    summary_row = pd.DataFrame([{
        'comparison_group': 'OVERALL_AVERAGE',
        'significance_stability_proportion': avg_stability,
        'significance_flip_rate': avg_flip_rate,
        'metric_type': 'summary',
        'source_task': 'T035',
        'target_task': 'T036'
    }])
    
    final_report = pd.concat([report_df, summary_row], ignore_index=True)
    
    return final_report

def save_report(report_df):
    """Save the report to the specified output path."""
    project_root = code_dir.parent
    output_path = project_root / "data" / "processed" / "significance_stability_report.csv"
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report_df.to_csv(output_path, index=False)
    logger.info(f"Stability report saved to {output_path}")
    return output_path

def main():
    """Main entry point for T036."""
    logger.info("Starting T036: Generate Significance Stability Report")
    
    try:
        # 1. Load input
        metrics_df = load_results_metrics()
        
        # 2. Generate report
        report_df = generate_stability_report(metrics_df)
        
        # 3. Save output
        output_path = save_report(report_df)
        
        # 4. Log summary
        info(f"Report generated successfully. Rows: {len(report_df)}")
        info(f"Output: {output_path}")
        
        # Print a preview to stdout
        print("\n--- Significance Stability Report Preview ---")
        print(report_df.to_string(index=False))
        print("---------------------------------------------\n")
        
    except FileNotFoundError as e:
        error(f"Data file missing: {e}")
        raise
    except ValueError as e:
        error(f"Data validation error: {e}")
        raise
    except Exception as e:
        error(f"Unexpected error during T036 execution: {e}")
        raise

if __name__ == "__main__":
    main()