"""
00_data_extraction.py

Extracts prompt_embedding, noise_level, routing_label, and velocity_vector
from teacher inference outputs and streams them to a Parquet file.
"""
import argparse
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

# Import project utilities
from utils.config import get_config, get_path
from utils.statistics import save_partial_results
import signal
import time

# Constants
KNOWN_EXPERT_IDS = [
    "expert_0", "expert_1", "expert_2", "expert_3",
    "expert_4", "expert_5", "expert_6", "expert_7"
]

# Global state for partial save
partial_results = {
    "status": "running",
    "processed_count": 0,
    "excluded_count": 0,
    "message": ""
}

def timeout_handler(signum, frame):
    """Handle timeout signal."""
    raise TimeoutError("Data extraction timed out (6-hour limit).")

def setup_timeout(seconds: int):
    """Set up a timeout for the extraction process."""
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

def cancel_timeout():
    """Cancel the active timeout."""
    signal.alarm(0)

def get_known_expert_ids() -> List[str]:
    """Return the list of known expert identifiers."""
    return KNOWN_EXPERT_IDS

def validate_routing_labels(labels: List[str], known_ids: List[str]) -> Dict[str, int]:
    """
    Validate routing labels against known expert IDs.
    Returns a dict with counts of valid and invalid labels.
    """
    valid_count = 0
    invalid_count = 0
    invalid_examples = []

    for label in labels:
        if label in known_ids:
            valid_count += 1
        else:
            invalid_count += 1
            if len(invalid_examples) < 10:
                invalid_examples.append(label)

    return {
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "invalid_examples": invalid_examples
    }

def filter_valid_rows(df: pd.DataFrame, known_ids: List[str]) -> pd.DataFrame:
    """
    Filter the DataFrame to keep only rows with valid routing labels.
    Logs the count of excluded rows.
    """
    valid_mask = df["routing_label"].isin(known_ids)
    invalid_count = (~valid_mask).sum()
    
    if invalid_count > 0:
        print(f"Excluding {invalid_count} rows with undefined routing labels.")
        partial_results["excluded_count"] += invalid_count

    return df[valid_mask].copy()

def load_inference_outputs(input_path: Path) -> pd.DataFrame:
    """
    Load inference outputs from a Parquet file.
    Expects columns: prompt_embedding, noise_level, routing_label, velocity_vector
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Inference output file not found: {input_path}")
    
    print(f"Loading inference outputs from {input_path}...")
    df = pd.read_parquet(input_path)
    
    required_cols = ["prompt_embedding", "noise_level", "routing_label", "velocity_vector"]
    missing_cols = [c for c in required_cols if c not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Inference output missing required columns: {missing_cols}")
    
    print(f"Loaded {len(df)} rows from inference output.")
    return df

def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure extracted features are in the correct format for Parquet storage.
    - prompt_embedding: list of floats
    - noise_level: float
    - routing_label: string
    - velocity_vector: list of floats
    """
    output_df = pd.DataFrame()
    
    # Ensure prompt_embedding is a list (if it's an array)
    if "prompt_embedding" in df.columns:
        output_df["prompt_embedding"] = df["prompt_embedding"].apply(
            lambda x: x.tolist() if isinstance(x, np.ndarray) else x
        )
    
    # Ensure noise_level is float
    output_df["noise_level"] = df["noise_level"].astype(float)
    
    # Ensure routing_label is string
    output_df["routing_label"] = df["routing_label"].astype(str)
    
    # Ensure velocity_vector is a list (if it's an array)
    if "velocity_vector" in df.columns:
        output_df["velocity_vector"] = df["velocity_vector"].apply(
            lambda x: x.tolist() if isinstance(x, np.ndarray) else x
        )
    
    return output_df

def stream_to_parquet(df: pd.DataFrame, output_path: Path, batch_size: int = 1000):
    """
    Stream the DataFrame to a Parquet file in batches to manage memory.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Streaming {len(df)} rows to {output_path}...")
    
    # Write in batches if the dataset is large
    if len(df) > batch_size:
        with pd.ParquetWriter(output_path, df.iloc[:batch_size].to_parquet(engine="pyarrow")) as writer:
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i+batch_size]
                writer.write_table(batch.to_parquet(engine="pyarrow"))
                partial_results["processed_count"] = len(df) # Update progress
                print(f"  Processed {min(i + batch_size, len(df))} / {len(df)} rows.")
    else:
        df.to_parquet(output_path, engine="pyarrow")
        partial_results["processed_count"] = len(df)
        print(f"  Processed {len(df)} rows.")
    
    print(f"Successfully wrote dataset to {output_path}")

def run_data_extraction(
    input_path: str,
    output_path: str,
    timeout_seconds: int = 21600  # 6 hours
):
    """
    Main logic to run data extraction:
    1. Load inference outputs
    2. Validate and filter routing labels
    3. Extract and format features
    4. Stream to Parquet
    """
    config = get_config()
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    # Set up timeout
    setup_timeout(timeout_seconds)
    
    try:
        # 1. Load data
        df = load_inference_outputs(input_file)
        
        # 2. Validate labels
        known_ids = get_known_expert_ids()
        validation_stats = validate_routing_labels(df["routing_label"].tolist(), known_ids)
        print(f"Validation stats: {validation_stats}")
        partial_results["excluded_count"] = validation_stats["invalid_count"]
        
        # 3. Filter invalid rows
        df_filtered = filter_valid_rows(df, known_ids)
        print(f"Filtered dataset size: {len(df_filtered)} rows (excluded {validation_stats['invalid_count']})")
        
        if len(df_filtered) == 0:
            raise ValueError("No valid rows remaining after filtering. Check routing labels.")
        
        # 4. Extract features
        df_extracted = extract_features(df_filtered)
        
        # 5. Stream to Parquet
        stream_to_parquet(df_extracted, output_file)
        
        # Update partial results status
        partial_results["status"] = "completed"
        partial_results["message"] = "Extraction completed successfully."
        
    except TimeoutError as e:
        partial_results["status"] = "partial"
        partial_results["message"] = str(e)
        print(f"ERROR: {e}")
        # Save partial results if we have any processed data
        if partial_results["processed_count"] > 0:
            save_partial_results(partial_results)
        raise
    except Exception as e:
        partial_results["status"] = "error"
        partial_results["message"] = str(e)
        print(f"ERROR: {e}")
        raise
    finally:
        cancel_timeout()
        # Save final status
        save_partial_results(partial_results)

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Extract features from teacher inference outputs.")
    parser.add_argument(
        "--input", 
        type=str, 
        default=str(get_path("data/raw/teacher_ground_truth.parquet")),
        help="Path to input inference output parquet file."
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=str(get_path("data/processed/teacher_routing_dataset.parquet")),
        help="Path to output parquet file."
    )
    parser.add_argument(
        "--timeout", 
        type=int, 
        default=21600,
        help="Timeout in seconds (default: 6 hours)."
    )
    
    args = parser.parse_args()
    
    try:
        run_data_extraction(args.input, args.output, args.timeout)
        print("Data extraction completed successfully.")
        sys.exit(0)
    except Exception as e:
        print(f"Data extraction failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
