#!/usr/bin/env python
"""
Data Streaming Module.
Reads from verified raw datasets and streams samples for processing.
"""
import argparse
import sys
from pathlib import Path
import pandas as pd

def stream_data(project_root: Path, target_samples: int = 1200, seed: int = 42) -> pd.DataFrame:
    """
    Stream samples from raw data files into a unified DataFrame.
    """
    data_raw_dir = project_root / "data" / "raw"
    
    imagenet_path = data_raw_dir / "imagenet_samples.parquet"
    laion_path = data_raw_dir / "laion_samples.parquet"
    
    dfs = []
    
    if imagenet_path.exists():
        df_imagenet = pd.read_parquet(imagenet_path)
        dfs.append(df_imagenet)
    
    if laion_path.exists():
        df_laion = pd.read_parquet(laion_path)
        dfs.append(df_laion)
    
    if not dfs:
        raise FileNotFoundError("No source parquet files found in data/raw/")
    
    combined_df = pd.concat(dfs, ignore_index=True)
    
    # Sample if necessary
    if len(combined_df) > target_samples:
        combined_df = combined_df.sample(n=target_samples, random_state=seed)
    
    return combined_df

def main():
    project_root = Path(__file__).resolve().parent.parent
    output_dir = project_root / "data" / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "combined_samples.parquet"
    
    try:
        df = stream_data(project_root)
        df.to_parquet(output_path, index=False)
        print(f"Streamed {len(df)} samples to {output_path}")
    except Exception as e:
        print(f"Error streaming data: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
