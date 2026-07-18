import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd

from code.config import get_project_root, ensure_paths_exist
from code.utils.io_utils import ensure_dir, write_csv, compute_sha256
from code.ingestion import process_all_trajectories


def aggregate_seed_logs(
    raw_logs_dir: Path,
    processed_dir: Path,
    output_filename: str = "trajectories_divergence.csv",
    chunk_size: int = 5000
) -> Path:
    """
    Aggregate multiple seed logs into a single processed CSV.

    This function:
    1. Iterates over all trajectory log files in raw_logs_dir.
    2. Processes each log using the existing ingestion logic (compute G(t), dG(t), z-score).
    3. Aggregates the results into a single DataFrame.
    4. Writes the final aggregated DataFrame to data/processed/trajectories_divergence.csv.
    5. Preserves 'seed_id' and 'bias_type' columns for downstream analysis.

    Args:
        raw_logs_dir: Path to the directory containing raw CHERRL log files.
        processed_dir: Path to the directory where the output CSV will be saved.
        output_filename: Name of the output CSV file.
        chunk_size: Number of rows to process before writing intermediate chunks (memory safety).

    Returns:
        Path to the generated output CSV file.
    """
    ensure_dir(processed_dir)
    output_path = processed_dir / output_filename

    # Collect all valid log files
    log_files = sorted([f for f in raw_logs_dir.iterdir() if f.is_file() and f.suffix == '.json'])
    
    if not log_files:
        raise FileNotFoundError(f"No JSON log files found in {raw_logs_dir}")

    print(f"Found {len(log_files)} seed logs to aggregate.")

    all_dfs = []
    total_rows = 0

    # Process each seed log
    for log_file in log_files:
        # Extract seed_id and bias_type from filename or metadata if available
        # Assuming filename format: seed_{id}_{bias_type}.json or similar
        # If metadata is inside, we rely on process_all_trajectories to handle it.
        # For now, we assume the ingestion module handles per-file processing.
        
        try:
            # Use the existing ingestion logic to process this specific file
            # We pass the single file to process_all_trajectories by creating a list
            df = process_all_trajectories([log_file], return_df=True)
            
            if df is not None and not df.empty:
                # Ensure seed_id and bias_type are present
                # If they aren't in the processed df, try to infer from filename
                if 'seed_id' not in df.columns:
                    stem = log_file.stem
                    # Simple heuristic: split by underscore, assume first part is seed
                    parts = stem.split('_')
                    seed_val = parts[0] if len(parts) > 0 else "unknown"
                    df['seed_id'] = seed_val
                
                if 'bias_type' not in df.columns:
                    stem = log_file.stem
                    parts = stem.split('_')
                    # Heuristic: assume last part is bias type
                    bias_val = parts[-1] if len(parts) > 1 else "unknown"
                    df['bias_type'] = bias_val

                all_dfs.append(df)
                total_rows += len(df)
                print(f"Processed {log_file.name}: {len(df)} rows")
            else:
                print(f"Warning: No data extracted from {log_file.name}")

        except Exception as e:
            print(f"Error processing {log_file.name}: {e}")
            # Fail loudly as per constraints
            raise e

    if not all_dfs:
        raise ValueError("No valid data found in any log files.")

    # Concatenate all dataframes
    final_df = pd.concat(all_dfs, ignore_index=True)
    
    # Sort by seed_id and step to ensure consistent ordering
    if 'step' in final_df.columns:
        final_df = final_df.sort_values(by=['seed_id', 'step'])
    else:
        final_df = final_df.sort_values(by=['seed_id'])

    # Ensure column order is logical: seed_id, bias_type, step, G(t), dG(t), z_score, ...
    # Check for required columns
    required_cols = ['seed_id', 'bias_type']
    metric_cols = ['G_t', 'dG_t', 'z_score_G'] # Common names, adjust if ingestion uses different
    
    # Reorder if columns exist
    existing_cols = [c for c in final_df.columns if c in required_cols + metric_cols]
    final_df = final_df[existing_cols + [c for c in final_df.columns if c not in existing_cols]]

    # Write to CSV
    write_csv(final_df, output_path)
    
    # Compute checksum
    checksum = compute_sha256(output_path)
    print(f"Aggregation complete. Output: {output_path}, Rows: {len(final_df)}, SHA256: {checksum}")
    
    return output_path


def main():
    """
    Entry point for the aggregation script.
    """
    project_root = get_project_root()
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    
    ensure_paths_exist()
    
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")
    
    output_path = aggregate_seed_logs(raw_dir, processed_dir)
    print(f"Successfully aggregated trajectories to {output_path}")


if __name__ == "__main__":
    main()
