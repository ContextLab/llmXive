import argparse
import sys
import json
import signal
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
import pyarrow.parquet as pq

from utils.config import get_config

# --- Timeout Handling ---

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

def setup_timeout(seconds: int):
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

def cancel_timeout():
    signal.alarm(0)

# --- Core Logic ---

def get_known_expert_ids() -> List[str]:
    """
    Returns the list of valid expert identifiers.
    In a real system, this might be loaded from a config or model metadata.
    """
    return [
        "expert_text_to_image",
        "expert_editing",
        "expert_inpainting",
        "expert_super_resolution",
        "expert_colorization",
        "expert_depth_estimation",
        "expert_segmentation"
    ]

def load_inference_outputs(input_path: Path) -> pd.DataFrame:
    """
    Loads the raw inference output from T013a (teacher_ground_truth.parquet).
    Expects columns: prompt_embedding, noise_level, routing_label, velocity_vector, source_dataset
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    try:
        df = pd.read_parquet(input_path)
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load parquet file {input_path}: {e}")

def validate_routing_labels(df: pd.DataFrame, known_ids: List[str]) -> pd.DataFrame:
    """
    Validates that routing_label is in the known expert set.
    Returns the filtered dataframe containing only valid rows.
    """
    valid_mask = df['routing_label'].isin(known_ids)
    valid_count = valid_mask.sum()
    invalid_count = (~valid_mask).sum()
    
    if invalid_count > 0:
        print(f"Warning: Excluding {invalid_count} rows with undefined routing labels.")
    
    return df[valid_mask].reset_index(drop=True)

def filter_valid_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Performs additional validation:
    1. Check for nulls in critical columns.
    2. Ensure velocity_vector is not empty.
    """
    critical_cols = ['prompt_embedding', 'noise_level', 'routing_label', 'velocity_vector']
    
    # Check for nulls
    null_mask = df[critical_cols].isnull().any(axis=1)
    if null_mask.any():
        print(f"Warning: Excluding {null_mask.sum()} rows with null values.")
        df = df[~null_mask]
    
    # Check velocity_vector integrity (assuming it's a list or array)
    if 'velocity_vector' in df.columns:
        empty_vec_mask = df['velocity_vector'].apply(lambda x: len(x) == 0 if hasattr(x, '__len__') else False)
        if empty_vec_mask.any():
            print(f"Warning: Excluding {empty_vec_mask.sum()} rows with empty velocity vectors.")
            df = df[~empty_vec_mask]
    
    return df.reset_index(drop=True)

def write_exclusion_log(count: int, reason: str, output_dir: Path):
    """
    Writes the exclusion log to data/results/exclusion_log.json
    """
    log_path = output_dir / "exclusion_log.json"
    log_data = {
        "count": count,
        "reason": reason,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    print(f"Exclusion log written to {log_path}")

def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensures the dataframe has the correct schema for the final dataset.
    Performs type normalization if necessary.
    """
    # Ensure columns exist
    required_cols = ['prompt_embedding', 'noise_level', 'routing_label', 'velocity_vector', 'source_dataset']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Input dataframe missing required columns: {missing_cols}")
    
    # Normalize types (example: ensure noise_level is float)
    if 'noise_level' in df.columns:
        df['noise_level'] = df['noise_level'].astype(float)
    
    return df

def stream_to_parquet(df: pd.DataFrame, output_path: Path):
    """
    Writes the dataframe to a Parquet file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    print(f"Successfully wrote {len(df)} rows to {output_path}")

def run_data_extraction(config: Dict[str, Any]):
    """
    Main orchestration function for T014.
    1. Loads teacher_ground_truth.parquet
    2. Validates and filters routing labels
    3. Extracts features
    4. Writes to data/processed/teacher_routing_dataset.parquet
    """
    input_path = Path(config.get('input_path', 'data/raw/teacher_ground_truth.parquet'))
    output_path = Path(config.get('output_path', 'data/processed/teacher_routing_dataset.parquet'))
    
    print(f"Starting data extraction from {input_path}")
    
    # Pre-check
    if not input_path.exists():
        raise FileNotFoundError(f"Required input file not found: {input_path}. "
                                "Ensure T013a-Generate has completed successfully.")
    
    # Load
    df = load_inference_outputs(input_path)
    print(f"Loaded {len(df)} rows from input.")
    
    initial_count = len(df)
    
    # Validate Routing Labels
    known_ids = get_known_expert_ids()
    df = validate_routing_labels(df, known_ids)
    
    # Log exclusions if any
    if len(df) < initial_count:
        excluded_count = initial_count - len(df)
        write_exclusion_log(excluded_count, "undefined_label", Path("data/results"))
    
    # Filter Valid Rows (nulls, empty vectors)
    df = filter_valid_rows(df)
    
    if len(df) < 1000:
        raise RuntimeError(f"Dataset size below 1000 after exclusion. Current size: {len(df)}. "
                           "T013b/T014 validation failed.")
    
    # Extract Features / Normalize
    df = extract_features(df)
    
    # Stream to Parquet
    stream_to_parquet(df, output_path)
    
    print(f"Data extraction complete. Final dataset size: {len(df)}")
    return df

def main():
    parser = argparse.ArgumentParser(description="Extract and validate teacher routing dataset.")
    parser.add_argument("--input", type=str, default="data/raw/teacher_ground_truth.parquet",
                        help="Path to input parquet file.")
    parser.add_argument("--output", type=str, default="data/processed/teacher_routing_dataset.parquet",
                        help="Path to output parquet file.")
    parser.add_argument("--timeout", type=int, default=3600, help="Timeout in seconds.")
    args = parser.parse_args()
    
    config = {
        "input_path": args.input,
        "output_path": args.output
    }
    
    try:
        setup_timeout(args.timeout)
        run_data_extraction(config)
        cancel_timeout()
    except TimeoutError:
        print("Error: Data extraction timed out.")
        sys.exit(1)
    except Exception as e:
        print(f"Error during data extraction: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()