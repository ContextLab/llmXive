import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from code.utils.config import set_global_seed
from code.utils.logger import get_logger, log_analysis_result
from code.labeling.classify import load_keywords, count_keyword_matches, classify_pr

logger = get_logger(__name__)

def load_human_labeled_sample(input_path: str) -> pd.DataFrame:
    """
    Load the human-labeled CSV sample generated in T017b.
    
    Args:
        input_path: Path to the CSV file (e.g., docs/reports/audit_sample_labeled.csv)
        
    Returns:
        DataFrame containing PR data with human labels.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Human labeled sample not found at {input_path}. "
                                "Ensure T017b has been run successfully.")
    
    df = pd.read_csv(path)
    
    required_cols = ['pr_id', 'commit_message', 'heuristic_label', 'human_label']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in human labeled sample: {missing_cols}")
    
    # Ensure labels are consistent strings for comparison
    df['heuristic_label'] = df['heuristic_label'].astype(str).str.strip().str.lower()
    df['human_label'] = df['human_label'].astype(str).str.strip().str.lower()
    
    return df

def calculate_audit_accuracy(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compare heuristic classification against human labels to calculate accuracy.
    
    Args:
        df: DataFrame with 'heuristic_label' and 'human_label' columns.
        
    Returns:
        Dictionary containing accuracy metrics.
    """
    total_count = len(df)
    if total_count == 0:
        return {
            "total_samples": 0,
            "accuracy": 0.0,
            "agreements": 0,
            "disagreements": 0,
            "status": "failed",
            "message": "No samples to evaluate."
        }
    
    agreements = (df['heuristic_label'] == df['human_label']).sum()
    accuracy = agreements / total_count
    
    # Breakdown by class if possible
    class_metrics = {}
    for label in df['human_label'].unique():
        subset = df[df['human_label'] == label]
        if len(subset) > 0:
            subset_accuracy = (subset['heuristic_label'] == subset['human_label']).mean()
            class_metrics[label] = {
                "count": len(subset),
                "accuracy": subset_accuracy
            }
    
    result = {
        "total_samples": int(total_count),
        "agreements": int(agreements),
        "disagreements": int(total_count - agreements),
        "accuracy": float(accuracy),
        "status": "success",
        "class_breakdown": class_metrics
    }
    
    return result

def write_audit_accuracy_report(metrics: Dict[str, Any], output_path: str) -> None:
    """
    Write the audit accuracy metrics to a JSON file.
    
    Args:
        metrics: Dictionary of metrics from calculate_audit_accuracy.
        output_path: Path to the output JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Audit accuracy report written to {output_path}")
    log_analysis_result(logger, "audit_accuracy", metrics)

def run_audit_accuracy_pipeline(
    input_csv: str = "docs/reports/audit_sample_labeled.csv",
    output_json: str = "docs/reports/audit_accuracy.json"
) -> Dict[str, Any]:
    """
    Main pipeline function to ingest human labels, compare with heuristics,
    and generate the accuracy report.
    
    Args:
        input_csv: Path to the human-labeled CSV.
        output_json: Path for the output JSON report.
        
    Returns:
        The calculated metrics dictionary.
    """
    logger.info(f"Starting audit accuracy pipeline. Input: {input_csv}")
    
    # Load data
    df = load_human_labeled_sample(input_csv)
    logger.info(f"Loaded {len(df)} labeled samples.")
    
    # Calculate metrics
    metrics = calculate_audit_accuracy(df)
    
    # Write report
    write_audit_accuracy_report(metrics, output_json)
    
    logger.info(f"Audit accuracy: {metrics['accuracy']:.4f} ({metrics['agreements']}/{metrics['total_samples']})")
    
    return metrics

# Note: The main entry point for this specific logic is run_audit_accuracy_pipeline.
# It is typically called from code/data/run_pipeline.py after T017b completes.
def main():
    """Entry point for direct execution."""
    set_global_seed(42)
    run_audit_accuracy_pipeline()

if __name__ == "__main__":
    main()