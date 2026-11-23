"""
T068: Implement Resource Usage Correlation Analysis.

Investigates if baseline resource usage (CPU/RAM) correlates with failure types or success rates.
Joins baseline_resource_metrics.json, baseline_results.json, and failure_cases.json.
Outputs data/derived/resource_correlation_report.json.
"""
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from scipy import stats

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging import get_logger, log_stage_start, log_stage_end
from utils.config import TIMEOUT_SECONDS

logger = get_logger(__name__)

INPUT_METRICS_PATH = Path("data/derived/baseline_resource_metrics.json")
INPUT_RESULTS_PATH = Path("data/derived/baseline_results.json")
INPUT_FAILURE_CASES_PATH = Path("data/derived/failure_cases.json")
OUTPUT_REPORT_PATH = Path("data/derived/resource_correlation_report.json")

def load_json_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_failure_cases(path: Path) -> Dict[str, str]:
    """Load failure cases and return a mapping of task_id -> failure_type."""
    data = load_json_file(path)
    if isinstance(data, list):
        return {item['task_id']: item.get('annotated_structural_feature', 'Unknown') for item in data}
    elif isinstance(data, dict):
        # Handle case where data is a dict keyed by task_id
        return {k: v.get('annotated_structural_feature', 'Unknown') for k, v in data.items()}
    else:
        raise ValueError(f"Unexpected format in {path}")

def calculate_correlation(x: List[float], y: List[float]) -> Tuple[float, float]:
    """Calculate Pearson correlation and p-value."""
    if len(x) < 2 or len(y) < 2:
        return 0.0, 1.0
    try:
        corr, p_val = stats.pearsonr(x, y)
        if np.isnan(corr):
            return 0.0, 1.0
        return corr, p_val
    except Exception as e:
        logger.warning(f"Correlation calculation failed: {e}")
        return 0.0, 1.0

def analyze_resource_correlation() -> Dict[str, Any]:
    """Main logic to analyze resource correlation."""
    logger.info("Starting resource correlation analysis.")

    # Load inputs
    try:
        metrics_data = load_json_file(INPUT_METRICS_PATH)
        results_data = load_json_file(INPUT_RESULTS_PATH)
        failure_types_map = load_failure_cases(INPUT_FAILURE_CASES_PATH)
    except FileNotFoundError as e:
        logger.error(str(e))
        raise

    # Normalize inputs to list of dicts if necessary
    if isinstance(metrics_data, dict) and 'metrics' in metrics_data:
        metrics_list = metrics_data['metrics']
    elif isinstance(metrics_data, list):
        metrics_list = metrics_data
    else:
        metrics_list = [metrics_data]

    if isinstance(results_data, dict) and 'results' in results_data:
        results_list = results_data['results']
    elif isinstance(results_data, list):
        results_list = results_data
    else:
        results_list = [results_data]

    # Create DataFrames for merging
    df_metrics = pd.DataFrame(metrics_list)
    df_results = pd.DataFrame(results_list)

    # Ensure task_id exists in both
    if 'task_id' not in df_metrics.columns:
        raise ValueError("baseline_resource_metrics.json missing 'task_id' column")
    if 'task_id' not in df_results.columns:
        raise ValueError("baseline_results.json missing 'task_id' column")

    # Merge metrics and results
    df_merged = pd.merge(df_metrics, df_results, on='task_id', how='inner')

    if df_merged.empty:
        logger.warning("No matching task_ids between metrics and results.")
        report = {
            "status": "incomplete",
            "reason": "No matching task IDs found between metrics and results.",
            "sample_size": 0,
            "correlations": {}
        }
        return report

    # Map failure types
    df_merged['failure_type'] = df_merged['task_id'].map(failure_types_map).fillna('Unknown')

    # Identify numeric resource columns
    resource_cols = ['peak_memory_mb', 'cpu_time_seconds']
    available_resource_cols = [col for col in resource_cols if col in df_merged.columns]

    if not available_resource_cols:
        logger.warning("No resource columns (peak_memory_mb, cpu_time_seconds) found.")
        report = {
            "status": "incomplete",
            "reason": "No resource columns found in metrics.",
            "sample_size": len(df_merged),
            "correlations": {}
        }
        return report

    correlations = {}

    # 1. Correlation with Success (Binary: 0/1)
    if 'success' in df_merged.columns:
        success_vals = df_merged['success'].astype(int)
        for col in available_resource_cols:
            corr, p_val = calculate_correlation(df_merged[col].dropna(), success_vals.dropna())
            key = f"{col}_vs_success"
            correlations[key] = {
                "correlation": round(corr, 4),
                "p_value": round(p_val, 4),
                "interpretation": "Significant" if p_val < 0.05 else "Not Significant"
            }

    # 2. Correlation with Time-to-Pivot (Continuous)
    if 'time_to_pivot' in df_merged.columns:
        ttp_vals = pd.to_numeric(df_merged['time_to_pivot'], errors='coerce')
        for col in available_resource_cols:
            valid_pairs = df_merged[[col, 'time_to_pivot']].dropna()
            if len(valid_pairs) > 1:
                corr, p_val = calculate_correlation(valid_pairs[col], valid_pairs['time_to_pivot'])
                key = f"{col}_vs_time_to_pivot"
                correlations[key] = {
                    "correlation": round(corr, 4),
                    "p_value": round(p_val, 4),
                    "interpretation": "Significant" if p_val < 0.05 else "Not Significant"
                }

    # 3. Grouped Analysis by Failure Type
    # Compare mean resource usage across failure types (ANOVA or Kruskal-Wallis)
    grouped_analysis = {}
    for col in available_resource_cols:
        if col in df_merged.columns:
            groups = df_merged.groupby('failure_type')[col].apply(list)
            if len(groups) > 1:
                try:
                    # Kruskal-Wallis H-test (non-parametric ANOVA)
                    k_stat, k_p = stats.kruskal(*[g for g in groups.values if len(g) > 0])
                    grouped_analysis[f"{col}_by_failure_type"] = {
                        "statistic": round(k_stat, 4),
                        "p_value": round(k_p, 4),
                        "interpretation": "Significant difference" if k_p < 0.05 else "No significant difference"
                    }
                except Exception as e:
                    logger.warning(f"Kruskal-Wallis failed for {col}: {e}")

    # Summary Statistics
    summary = {
        "total_tasks_analyzed": len(df_merged),
        "unique_failure_types": df_merged['failure_type'].nunique(),
        "resource_columns_analyzed": available_resource_cols
    }

    report = {
        "status": "complete",
        "summary": summary,
        "correlations": correlations,
        "grouped_analysis": grouped_analysis
    }

    return report

def main():
    log_stage_start("T068", "Resource Correlation Analysis")
    try:
        report = analyze_resource_correlation()
        
        # Ensure output directory exists
        OUTPUT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        with open(OUTPUT_REPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report written to {OUTPUT_REPORT_PATH}")
        log_stage_end("T068", "Success")
        return 0
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        log_stage_end("T068", "Failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())