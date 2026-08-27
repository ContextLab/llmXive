#!/usr/bin/env python
# Implementation
"""
Data Streaming Module.
Reads from raw data files and streams samples into memory for processing.
"""
import argparse
import sys
from pathlib import Path
import pandas as pd

def stream_data(project_root: Path) -> pd.DataFrame:
    """
    Stream data from raw parquet files.
    Returns a combined DataFrame of samples.
    """
    raw_dir = project_root / "data" / "raw"
    
    imagenet_path = raw_dir / "imagenet_samples.parquet"
    laion_path = raw_dir / "laion_samples.parquet"
    
    samples = []
    
    if imagenet_path.exists():
        df_imagenet = pd.read_parquet(imagenet_path)
        samples.append(df_imagenet)
        print(f"Loaded {len(df_imagenet)} samples from ImageNet.")
    else:
        print(f"Warning: {imagenet_path} not found.")

    if laion_path.exists():
        df_laion = pd.read_parquet(laion_path)
        samples.append(df_laion)
        print(f"Loaded {len(df_laion)} samples from LAION.")
    else:
        print(f"Warning: {laion_path} not found.")

    if not samples:
        raise FileNotFoundError("No raw data files found to stream.")

    combined_df = pd.concat(samples, ignore_index=True)
    
    # Save combined samples for next step
    processed_dir = project_root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    output_path = processed_dir / "combined_samples.parquet"
    combined_df.to_parquet(output_path)
    print(f"Combined samples saved to {output_path}")
    
    return combined_df

def main():
    project_root = Path(__file__).parent.parent
    try:
        stream_data(project_root)
    except Exception as e:
        print(f"Error streaming data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
