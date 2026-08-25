import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

DATA_RAW.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

def load_stage1_data():
    """Loads normalized data from stage 1."""
    path = DATA_PROCESSED / "normalized_data.csv"
    if not path.exists():
        # Fallback to raw if normalized not found (for testing)
        path = DATA_RAW / "synthetic_arabidopsis_v1.csv"
    return pd.read_csv(path)

def filter_environmental(data):
    """
    T015a: Filter samples missing 'temperature' OR 'light_intensity'.
    """
    required = ['temperature', 'light_intensity']
    missing = [c for c in required if c not in data.columns]
    if missing:
        print(f"Warning: Required columns {missing} not found. Skipping filter.")
        return data
    
    # Drop rows where temperature or light_intensity is NaN
    filtered = data.dropna(subset=required)
    print(f"Filtered environmental data: {len(data)} -> {len(filtered)}")
    
    output_path = DATA_RAW / "filtered_env_data.csv"
    filtered.to_csv(output_path, index=False)
    return filtered

def filter_replicates(data):
    """
    T015b: Exclude conditions with <3 biological replicates.
    Assumes 'treatment' is the condition column.
    """
    if 'treatment' not in data.columns:
        print("Warning: 'treatment' column not found. Skipping replicate filter.")
        return data
    
    counts = data['treatment'].value_counts()
    valid_treatments = counts[counts >= 3].index
    filtered = data[data['treatment'].isin(valid_treatments)]
    
    print(f"Filtered replicates: {len(data)} -> {len(filtered)}")
    
    output_path = DATA_RAW / "filtered_replicates_data.csv"
    filtered.to_csv(output_path, index=False)
    return filtered

def merge_dataframes(genomic_df, voc_df):
    """
    T015c: Join genomic and VOC data on exact sample ID match.
    """
    # Assuming both have 'sample_id'
    if 'sample_id' not in genomic_df.columns or 'sample_id' not in voc_df.columns:
        # If no sample_id, assume row order matches (risky but for fallback)
        # Or raise error
        raise ValueError("Both dataframes must have 'sample_id' column.")
    
    merged = pd.merge(genomic_df, voc_df, on='sample_id', how='inner')
    print(f"Merged data: {len(genomic_df)} x {len(voc_df)} -> {len(merged)}")
    
    output_path = DATA_RAW / "joined_data.csv"
    merged.to_csv(output_path, index=False)
    return merged

def main():
    """
    Main entry point for merging.
    Produces data/processed/merged_dataset.csv
    """
    try:
        # Load stage 1 (normalized)
        data = load_stage1_data()
        
        # Filter Env
        data = filter_environmental(data)
        
        # Filter Replicates
        data = filter_replicates(data)
        
        # If data is split into genomic and VOC, we would merge here.
        # Assuming the input from 01_ingest is already a single table with both.
        # We just ensure the final output is saved as merged_dataset.csv
        
        output_path = DATA_PROCESSED / "merged_dataset.csv"
        data.to_csv(output_path, index=False)
        print(f"Final merged dataset saved to {output_path}")
        
    except Exception as e:
        print(f"Error in merge: {e}")
        raise

if __name__ == "__main__":
    main()
