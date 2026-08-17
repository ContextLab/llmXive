import argparse
import sys
import json
import signal
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
import numpy as np

from utils.config import get_config


class TimeoutError(Exception):
    """Custom timeout exception for pipeline control."""
    pass


def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError("Operation timed out after 6 hours")


def setup_timeout(seconds: int = 21600):
    """Setup a 6-hour timeout (21600 seconds)."""
    try:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
    except AttributeError:
        # SIGALRM not available on Windows
        pass


def cancel_timeout():
    """Cancel the active timeout."""
    try:
        signal.alarm(0)
    except AttributeError:
        pass


def get_known_expert_ids() -> List[str]:
    """
    Return the set of valid expert IDs defined in the DanceOPD architecture.
    These are the only routing_label values considered 'defined'.
    """
    # Based on the project context and typical DanceOPD architecture
    return [
        "expert_text_to_image",
        "expert_editing",
        "expert_inpainting",
        "expert_super_resolution",
        "expert_color_correction",
        "expert_style_transfer",
        "expert_depth_estimation",
        "expert_segmentation"
    ]


def load_inference_outputs(input_path: str) -> pd.DataFrame:
    """
    Load the raw inference outputs from the combined samples.
    Expects a parquet file containing prompt_embedding, noise_level, 
    routing_label, velocity_vector, and source information.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Try loading as parquet first, fallback to csv if needed
    if path.suffix == '.parquet':
        df = pd.read_parquet(path)
    elif path.suffix == '.csv':
        df = pd.read_csv(path)
    else:
        # Try parquet by default for unknown extensions
        try:
            df = pd.read_parquet(path)
        except Exception:
            df = pd.read_csv(path)
    
    return df


def validate_routing_labels(df: pd.DataFrame, known_ids: List[str]) -> pd.DataFrame:
    """
    Validate that routing labels are in the known expert set.
    Returns a boolean mask indicating valid rows.
    """
    valid_set = set(known_ids)
    # Ensure routing_label column exists
    if 'routing_label' not in df.columns:
        raise KeyError("DataFrame must contain 'routing_label' column")
    
    # Check for nulls first
    null_mask = df['routing_label'].isna()
    
    # Check against known IDs
    valid_mask = df['routing_label'].isin(valid_set)
    
    # A row is valid if it has a non-null label AND it is in the known set
    return (~null_mask) & valid_mask


def filter_valid_rows(df: pd.DataFrame, valid_mask: pd.Series) -> pd.DataFrame:
    """
    Filter the DataFrame to keep only valid rows.
    """
    return df[valid_mask].reset_index(drop=True)


def write_exclusion_log(
    total_rows: int, 
    valid_rows: int, 
    excluded_rows: int, 
    reason: str = "undefined_label",
    output_path: str = "data/results/exclusion_log.json"
):
    """
    Write the exclusion log to a JSON file.
    """
    log_entry = {
        "count": excluded_rows,
        "reason": reason,
        "timestamp": pd.Timestamp.now().isoformat(),
        "total_rows_processed": total_rows,
        "valid_rows_kept": valid_rows,
        "excluded_rows": excluded_rows,
        "exclusion_rate": excluded_rows / total_rows if total_rows > 0 else 0.0
    }
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(log_entry, f, indent=2)
    
    return log_entry


def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure feature columns are in the correct format.
    This is a pass-through for now, but can be extended for normalization.
    """
    required_cols = ['prompt_embedding', 'noise_level', 'routing_label', 'velocity_vector']
    for col in required_cols:
        if col not in df.columns:
            raise KeyError(f"Missing required column: {col}")
    return df


def stream_to_parquet(df: pd.DataFrame, output_path: str):
    """
    Write the final dataset to a parquet file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_file, index=False)


def run_data_extraction(
    input_path: str = "data/raw/combined_samples.parquet",
    output_path: str = "data/processed/teacher_routing_dataset.parquet",
    log_path: str = "data/results/exclusion_log.json"
):
    """
    Main pipeline for T013b:
    1. Load raw inference outputs.
    2. Identify undefined routing paths.
    3. Log the exclusion count and details.
    4. Exclude invalid rows.
    5. Verify minimum dataset size (>= 1000).
    6. Save the cleaned dataset.
    """
    print(f"Loading inference outputs from {input_path}...")
    df = load_inference_outputs(input_path)
    total_rows = len(df)
    print(f"Loaded {total_rows} rows.")

    known_ids = get_known_expert_ids()
    print(f"Known expert IDs: {known_ids}")

    print("Validating routing labels...")
    valid_mask = validate_routing_labels(df, known_ids)
    valid_count = valid_mask.sum()
    excluded_count = total_rows - valid_count

    print(f"Valid rows: {valid_count}, Excluded rows: {excluded_count}")

    if excluded_count > 0:
        write_exclusion_log(
            total_rows=total_rows,
            valid_rows=valid_count,
            excluded_rows=excluded_count,
            reason="undefined_label",
            output_path=log_path
        )
        print(f"Exclusion log written to {log_path}")
    else:
        # Log zero exclusions for completeness
        write_exclusion_log(
            total_rows=total_rows,
            valid_rows=valid_count,
            excluded_rows=0,
            reason="none",
            output_path=log_path
        )

    # Filter the dataframe
    df_clean = filter_valid_rows(df, valid_mask)

    # Verify minimum size
    MIN_ROWS = 1000
    if len(df_clean) < MIN_ROWS:
        error_msg = f"Dataset size below {MIN_ROWS} after exclusion. Current size: {len(df_clean)}"
        print(f"ERROR: {error_msg}")
        raise RuntimeError(error_msg)

    print(f"Saving cleaned dataset ({len(df_clean)} rows) to {output_path}...")
    stream_to_parquet(df_clean, output_path)

    print("Data extraction and filtering complete.")
    return df_clean


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Extract and filter teacher routing data")
    parser.add_argument("--input", type=str, default="data/raw/combined_samples.parquet",
                        help="Path to input combined samples")
    parser.add_argument("--output", type=str, default="data/processed/teacher_routing_dataset.parquet",
                        help="Path to output dataset")
    parser.add_argument("--log", type=str, default="data/results/exclusion_log.json",
                        help="Path to exclusion log")
    parser.add_argument("--timeout", type=int, default=21600,
                        help="Timeout in seconds (default 6 hours)")

    args = parser.parse_args()

    setup_timeout(args.timeout)
    try:
        run_data_extraction(
            input_path=args.input,
            output_path=args.output,
            log_path=args.log
        )
    except TimeoutError as e:
        print(f"TIMEOUT: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    finally:
        cancel_timeout()


if __name__ == "__main__":
    main()