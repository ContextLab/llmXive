import argparse
import sys
import json
import signal
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from utils.config import get_config

# --- Timeout Handling ---

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out after 6 hours")

def setup_timeout(seconds: int):
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

def cancel_timeout():
    signal.alarm(0)

# --- Configuration & Constants ---

def get_known_expert_ids() -> List[str]:
    """
    Returns the list of valid expert IDs defined in the DanceOPD configuration.
    These are the only allowed values for 'routing_label'.
    """
    config = get_config()
    # Default known experts based on DanceOPD architecture
    # If config specifies them, use those; otherwise fallback to standard set
    if hasattr(config, 'TEACHER_ROUTING_EXPERTS'):
        return config.TEACHER_ROUTING_EXPERTS
    return [
        "expert_text_to_image",
        "expert_editing",
        "expert_inpainting",
        "expert_super_resolution",
        "expert_colorization",
        "expert_style_transfer"
    ]

# --- Data Loading ---

def load_inference_outputs(input_path: str) -> pd.DataFrame:
    """
    Loads the raw inference output from T012/T013a.
    Expected columns: prompt_embedding, noise_level, routing_label, velocity_vector, source (optional)
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Inference output file not found: {input_path}")

    if path.suffix == '.parquet':
        return pd.read_parquet(path)
    elif path.suffix == '.csv':
        return pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")

# --- Validation & Filtering ---

def validate_routing_labels(df: pd.DataFrame, known_ids: List[str]) -> pd.DataFrame:
    """
    Validates that routing_label values are in the known set.
    Returns a boolean mask of valid rows.
    """
    valid_mask = df['routing_label'].isin(known_ids)
    invalid_count = (~valid_mask).sum()
    if invalid_count > 0:
        print(f"Warning: Found {invalid_count} rows with undefined routing labels.")
    return valid_mask

def filter_valid_rows(df: pd.DataFrame, valid_mask: pd.Series) -> pd.DataFrame:
    """
    Returns a new dataframe containing only valid rows.
    """
    return df[valid_mask].reset_index(drop=True)

def write_exclusion_log(exclusion_path: str, count: int, reason: str):
    """
    Logs the count of excluded rows to a JSON file.
    """
    log_entry = {
        "count": int(count),
        "reason": reason,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    Path(exclusion_path).parent.mkdir(parents=True, exist_ok=True)
    with open(exclusion_path, 'w') as f:
        json.dump(log_entry, f, indent=2)
    print(f"Exclusion log written to {exclusion_path}")

# --- Feature Extraction & Streaming ---

def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts and normalizes the required features for the dataset.
    Ensures types are consistent for Parquet storage.
    
    Input: DataFrame with raw inference outputs
    Output: DataFrame with cleaned, typed columns
    """
    # Ensure columns exist
    required_cols = ['prompt_embedding', 'noise_level', 'routing_label', 'velocity_vector']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    # Clean up the dataframe
    # Convert embeddings/vectors to lists for Parquet compatibility if they are numpy arrays
    # Note: PyArrow handles numpy arrays well, but explicit list conversion ensures portability
    
    def ensure_list(x):
        if isinstance(x, (list, tuple)):
            return list(x)
        if hasattr(x, 'tolist'): # numpy array or torch tensor
            return x.tolist()
        return x

    # Apply safe conversion
    # We assume prompt_embedding and velocity_vector are arrays/lists
    # We assume noise_level is scalar, routing_label is string
    
    df['prompt_embedding'] = df['prompt_embedding'].apply(ensure_list)
    df['velocity_vector'] = df['velocity_vector'].apply(ensure_list)
    
    # Ensure noise_level is float
    df['noise_level'] = df['noise_level'].astype(float)
    
    # Ensure routing_label is string
    df['routing_label'] = df['routing_label'].astype(str)

    # Select and order columns for the final dataset
    output_df = df[['prompt_embedding', 'noise_level', 'routing_label', 'velocity_vector']].copy()
    
    return output_df

def stream_to_parquet(df: pd.DataFrame, output_path: str):
    """
    Streams the dataframe to a Parquet file.
    Creates parent directories if they don't exist.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Use PyArrow for efficient writing
    table = pa.Table.from_pandas(df)
    pq.write_table(table, path)
    print(f"Dataset successfully written to {output_path}")
    print(f"Total rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")

# --- Main Execution Logic ---

def run_data_extraction(input_path: str, output_path: str, timeout_seconds: int = 21600):
    """
    Orchestrates the extraction pipeline:
    1. Load raw inference outputs.
    2. Validate routing labels against known experts.
    3. Filter out invalid rows.
    4. Extract and normalize features.
    5. Stream to Parquet.
    """
    print(f"Starting data extraction from {input_path}...")
    
    # Setup timeout
    setup_timeout(timeout_seconds)
    
    try:
        # 1. Load
        print("Loading inference outputs...")
        raw_df = load_inference_outputs(input_path)
        print(f"Loaded {len(raw_df)} rows.")

        # 2. Validate
        print("Validating routing labels...")
        known_ids = get_known_expert_ids()
        valid_mask = validate_routing_labels(raw_df, known_ids)
        
        invalid_count = (~valid_mask).sum()
        if invalid_count > 0:
            exclusion_log_path = str(Path(output_path).parent / "exclusion_log.json")
            write_exclusion_log(exclusion_log_path, int(invalid_count), "undefined_label")
        
        # 3. Filter
        print("Filtering invalid rows...")
        valid_df = filter_valid_rows(raw_df, valid_mask)
        
        if len(valid_df) < 1000:
            raise ValueError(f"Dataset size {len(valid_df)} after filtering is below minimum requirement of 1000.")

        # 4. Extract Features
        print("Extracting and normalizing features...")
        final_df = extract_features(valid_df)

        # 5. Stream to Parquet
        print("Writing to Parquet...")
        stream_to_parquet(final_df, output_path)
        
        print("Data extraction completed successfully.")
        
    except TimeoutError:
        print("ERROR: Data extraction timed out.")
        # In a real scenario, we might save partial results here if we were streaming row-by-row
        # For this batch implementation, we just report the failure.
        sys.exit(1)
    finally:
        cancel_timeout()

def main():
    parser = argparse.ArgumentParser(description="Extract and validate teacher routing dataset.")
    parser.add_argument("--input", type=str, required=True, help="Path to raw inference output (parquet/csv)")
    parser.add_argument("--output", type=str, required=True, help="Path to output parquet file")
    parser.add_argument("--timeout", type=int, default=21600, help="Timeout in seconds (default: 6h)")
    
    args = parser.parse_args()
    
    run_data_extraction(args.input, args.output, args.timeout)

if __name__ == "__main__":
    main()
