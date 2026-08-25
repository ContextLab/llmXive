import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_RESULTS = PROJECT_ROOT / "data" / "results"

def ensure_dirs():
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    DATA_RESULTS.mkdir(parents=True, exist_ok=True)

def load_merged_data():
    path = DATA_PROCESSED / "merged_dataset.csv"
    if not path.exists():
        raise FileNotFoundError(f"merged_dataset.csv not found at {path}")
    return pd.read_csv(path)

def load_gene_pathway_mapping():
    # Placeholder: In real scenario, load from reference file
    return {}

def aggregate_by_pathway(df, mapping):
    # Placeholder: Return df as is if no mapping
    return df

def save_log(log_data):
    path = DATA_RESULTS / "aggregation_log.json"
    with open(path, 'w') as f:
        json.dump(log_data, f, indent=2)

def main():
    try:
        ensure_dirs()
        df = load_merged_data()
        mapping = load_gene_pathway_mapping()
        aggregated = aggregate_by_pathway(df, mapping)
        
        # Save aggregated features
        aggregated.to_csv(DATA_PROCESSED / "pathway_aggregated_features.csv", index=False)
        print("Aggregation completed.")
    except Exception as e:
        print(f"Error in aggregation: {e}")
        raise

if __name__ == "__main__":
    main()
