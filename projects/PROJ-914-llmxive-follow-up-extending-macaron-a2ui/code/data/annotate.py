"""
Manual annotation interface for researchers to label N=500 interaction turns.

This script provides a CLI-based interface for researchers to label interaction
turns from the Macaron-A2UI dataset as "High-Confidence" or "Ambiguous".

Outputs:
- data/annotated_turns.csv: Labeled dataset with N=500 rows
- data/annotation_log.json: Log of annotation actions (optional)

FR-001: Manual annotation interface for researchers
"""

import os
import sys
import json
import argparse
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

import pandas as pd
from utils.logging import get_experiment_logger, log_metric, log_info, log_error

# Constants
TARGET_SAMPLE_SIZE = 500
ANNOTATED_OUTPUT_PATH = "data/annotated_turns.csv"
ANNOTATION_LOG_PATH = "data/annotation_log.json"

# Initialize logger
logger = get_experiment_logger(__name__)

def load_raw_data(raw_csv_path: str) -> pd.DataFrame:
    """
    Load the raw dataset from the CSV file produced by ingest.py.
    
    Args:
        raw_csv_path: Path to the raw CSV file
        
    Returns:
        DataFrame with raw interaction turns
        
    Raises:
        FileNotFoundError: If the raw CSV doesn't exist
        ValueError: If the file is empty or has wrong schema
    """
    if not os.path.exists(raw_csv_path):
        raise FileNotFoundError(f"Raw data file not found: {raw_csv_path}")
    
    df = pd.read_csv(raw_csv_path)
    
    # Validate schema
    required_columns = ['query', 'ground_truth_intent', 'complexity_score']
    missing_cols = set(required_columns) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    if df.empty:
        raise ValueError("Raw data file is empty")
    
    logger.info(f"Loaded {len(df)} rows from {raw_csv_path}")
    return df

def sample_for_annotation(df: pd.DataFrame, n: int = TARGET_SAMPLE_SIZE) -> pd.DataFrame:
    """
    Sample N rows for annotation from the raw dataset.
    
    Args:
        df: Input DataFrame
        n: Number of rows to sample
        
    Returns:
        Sampled DataFrame
    """
    if len(df) < n:
        logger.warning(f"Dataset has {len(df)} rows, sampling all for annotation (requested {n})")
        return df.copy()
    
    # Deterministic sampling for reproducibility
    sampled = df.sample(n=n, random_state=42).reset_index(drop=True)
    logger.info(f"Sampled {n} rows for annotation")
    return sampled

def validate_label(label: str) -> bool:
    """Validate that the label is one of the allowed values."""
    return label in ["High-Confidence", "Ambiguous"]

def interactive_annotation_loop(df: pd.DataFrame) -> pd.DataFrame:
    """
    Interactive CLI loop for manual annotation.
    
    Prompts the user to label each interaction turn as:
    - High-Confidence
    - Ambiguous
    
    Args:
        df: DataFrame with interaction turns to annotate
        
    Returns:
        DataFrame with added 'ground_truth_intent' and 'complexity_score' columns
    """
    logger.info(f"Starting interactive annotation for {len(df)} turns")
    
    annotation_log = []
    annotated_rows = []
    
    print("\n" + "=" * 60)
    print("MACARON-A2UI INTERACTION ANNOTATION INTERFACE")
    print("=" * 60)
    print("\nInstructions:")
    print("  Read each query and label it as:")
    print("    1 - High-Confidence (clear intent, low ambiguity)")
    print("    2 - Ambiguous (unclear intent, high ambiguity)")
    print("    q - Quit and save current progress")
    print("=" * 60 + "\n")
    
    for idx, row in df.iterrows():
        print(f"\n--- Turn {idx + 1}/{len(df)} ---")
        print(f"Query: {row['query'][:100]}{'...' if len(row['query']) > 100 else ''}")
        print(f"Original Intent: {row.get('ground_truth_intent', 'N/A')}")
        print(f"Complexity Score: {row.get('complexity_score', 'N/A')}")
        print("-" * 40)
        
        while True:
            user_input = input("Label (1=High-Confidence, 2=Ambiguous, q=quit): ").strip()
            
            if user_input.lower() == 'q':
                logger.info(f"User quit at turn {idx + 1}. Saving {len(annotated_rows)} annotations.")
                print("\nSaving progress...")
                break
            
            if user_input == '1':
                label = "High-Confidence"
                break
            elif user_input == '2':
                label = "Ambiguous"
                break
            else:
                print("Invalid input. Please enter 1, 2, or q.")
        
        if user_input.lower() == 'q':
            break
        
        # Record annotation
        annotated_row = {
            'query': row['query'],
            'ground_truth_intent': label,
            'complexity_score': row.get('complexity_score', 0),
            'annotated_at': datetime.now(timezone.utc).isoformat(),
            'annotator': 'researcher_manual'
        }
        annotated_rows.append(annotated_row)
        
        # Log annotation action
        annotation_log.append({
            'turn_index': idx,
            'label': label,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        print(f"  -> Labeled as: {label}")
    
    # Add annotation metadata
    if annotated_rows:
        annotated_df = pd.DataFrame(annotated_rows)
        
        # Calculate distribution
        label_counts = annotated_df['ground_truth_intent'].value_counts()
        logger.info(f"Annotation distribution: {label_counts.to_dict()}")
        
        return annotated_df, annotation_log
    
    return None, None

def save_annotated_data(df: pd.DataFrame, output_path: str):
    """
    Save the annotated DataFrame to CSV.
    
    Args:
        df: Annotated DataFrame
        output_path: Path to save the CSV
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} annotated rows to {output_path}")
    log_metric("annotation_total_count", len(df))
    
    # Log label distribution
    label_counts = df['ground_truth_intent'].value_counts()
    for label, count in label_counts.items():
        log_metric(f"annotation_{label.lower().replace('-', '_')}_count", count)

def save_annotation_log(log_data: List[Dict], log_path: str):
    """Save the annotation log to JSON."""
    log_file = Path(log_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    logger.info(f"Saved annotation log to {log_path}")

def main():
    """Main entry point for the annotation script."""
    parser = argparse.ArgumentParser(
        description="Manual annotation interface for Macaron-A2UI interaction turns"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/raw_a2ui_bench.csv",
        help="Path to the raw CSV file from ingest.py"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=ANNOTATED_OUTPUT_PATH,
        help="Path to save the annotated CSV"
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=TARGET_SAMPLE_SIZE,
        help=f"Number of rows to sample for annotation (default: {TARGET_SAMPLE_SIZE})"
    )
    parser.add_argument(
        "--log-path",
        type=str,
        default=ANNOTATION_LOG_PATH,
        help="Path to save the annotation log JSON"
    )
    
    args = parser.parse_args()
    
    logger.info("Starting annotation process")
    log_info("annotation_start", f"Input: {args.input}, Sample size: {args.sample_size}")
    
    try:
        # Load raw data
        raw_df = load_raw_data(args.input)
        
        # Sample for annotation
        sample_df = sample_for_annotation(raw_df, args.sample_size)
        
        # Interactive annotation
        annotated_df, annotation_log = interactive_annotation_loop(sample_df)
        
        if annotated_df is not None and len(annotated_df) > 0:
            # Save results
            save_annotated_data(annotated_df, args.output)
            
            if annotation_log:
                save_annotation_log(annotation_log, args.log_path)
            
            log_info("annotation_complete", f"Annotated {len(annotated_df)} turns")
            print(f"\n✓ Annotation complete. Saved {len(annotated_df)} rows to {args.output}")
        else:
            logger.warning("No annotations were made. No files saved.")
            print("\n✗ No annotations were made.")
            sys.exit(1)
            
    except FileNotFoundError as e:
        log_error("annotation_failed", str(e))
        print(f"\n✗ Error: {e}")
        print("  Please ensure the raw data file exists. Run ingest.py first.")
        sys.exit(1)
    except Exception as e:
        log_error("annotation_failed", str(e))
        logger.exception("Unexpected error during annotation")
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
