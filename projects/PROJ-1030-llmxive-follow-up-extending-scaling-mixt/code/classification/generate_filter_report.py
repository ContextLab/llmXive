import os
import sys
import json
import logging
import argparse
import pandas as pd
from pathlib import Path

def load_csv_safe(path: str) -> pd.DataFrame:
    """
    Safely load a CSV file, returning an empty DataFrame if file doesn't exist.
    
    Args:
        path: Path to CSV file
        
    Returns:
        pd.DataFrame: Loaded DataFrame or empty DataFrame
    """
    if not os.path.exists(path):
        logging.warning(f"File not found: {path}. Returning empty DataFrame.")
        return pd.DataFrame()
    return pd.read_csv(path)

def generate_filter_report(labels_path: str, null_labels_path: str) -> dict:
    """
    Generate a report summarizing the filtering process.
    
    Args:
        labels_path: Path to final labels CSV
        null_labels_path: Path to null labels CSV
        
    Returns:
        dict: Filter report
    """
    labels_df = load_csv_safe(labels_path)
    null_labels_df = load_csv_safe(null_labels_path)
    
    report = {
        "total_samples_in_labels": len(labels_df),
        "total_samples_in_null_labels": len(null_labels_df),
        "total_samples_processed": len(labels_df) + len(null_labels_df),
        "null_reasons": {},
        "label_distribution": {}
    }
    
    # Count null reasons
    if not null_labels_df.empty and 'reason' in null_labels_df.columns:
        null_reasons = null_labels_df['reason'].value_counts().to_dict()
        report["null_reasons"] = {str(k): int(v) for k, v in null_reasons.items()}
    
    # Count label distribution
    if not labels_df.empty and 'label' in labels_df.columns:
        label_dist = labels_df['label'].value_counts().to_dict()
        report["label_distribution"] = {str(k): int(v) for k, v in label_dist.items()}
    
    return report

def main():
    parser = argparse.ArgumentParser(description="Generate filtering report.")
    parser.add_argument("--labels_path", type=str, default="data/processed/labels.csv", help="Path to final labels CSV")
    parser.add_argument("--null_labels_path", type=str, default="data/processed/null_labels.csv", help="Path to null labels CSV")
    parser.add_argument("--output_path", type=str, default="data/processed/filtering_report.json", help="Path to save filtering report")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Generate report
    logging.info("Generating filtering report...")
    report = generate_filter_report(args.labels_path, args.null_labels_path)
    
    # Save report
    with open(args.output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logging.info(f"Saved filtering report to {args.output_path}")
    print(f"Filtering report saved to {args.output_path}")

if __name__ == "__main__":
    main()
