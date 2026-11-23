"""
Module: 03_aggregate.py
Task: T016a
Description: Implements aggregation of gene expression into pathway-level features (TPS family means).
Condition: Only executes if raw feature count > 100.
Output: data/processed/merged_dataset_aggregated.csv
"""
import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Ensure project root is in path for imports if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

# Constants
INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "merged_dataset.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "merged_dataset_aggregated.csv"
LOG_PATH = PROJECT_ROOT / "data" / "results" / "aggregation_log.json"
TPS_REFERENCE_PATH = PROJECT_ROOT / "data" / "reference" / "tps_families.csv"

def ensure_dirs():
    """Ensure output directories exist."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

def load_merged_data():
    """Load the merged dataset from the preprocessing stage."""
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_PATH}. "
                                "Please run code/02_merge.py first.")
    return pd.read_csv(INPUT_PATH)

def load_gene_pathway_mapping():
    """
    Load the mapping of genes to TPS families.
    Expected format: gene_id, tps_family
    """
    if not TPS_REFERENCE_PATH.exists():
        # Fallback: if reference file is missing, we cannot perform aggregation.
        # We return an empty mapping, effectively skipping aggregation.
        return pd.DataFrame(columns=["gene_id", "tps_family"])
    
    return pd.read_csv(TPS_REFERENCE_PATH)

def aggregate_by_pathway(df, mapping):
    """
    Aggregate gene expression (TPM) into pathway-level features (TPS family means).
    
    Logic:
    1. Identify columns representing gene expression (typically numeric, excluding metadata).
    2. Filter columns that exist in the gene mapping.
    3. Group by TPS family and calculate the mean TPM per sample.
    4. Rename columns to 'tps_family_X_mean'.
    5. Append to the original dataframe ONLY if raw feature count > 100.
    """
    if mapping.empty:
        return df, False

    # Identify gene columns (numeric columns that are not metadata)
    # Heuristic: Metadata columns are usually strings or specific known names.
    # We assume gene columns are numeric and match the gene_ids in the mapping.
    gene_columns = [col for col in df.columns if col in mapping['gene_id'].values]
    
    raw_feature_count = len(gene_columns)
    print(f"Detected {raw_feature_count} raw gene features.")

    if raw_feature_count <= 100:
        print(f"Condition met: Raw feature count ({raw_feature_count}) is <= 100. "
              "Skipping aggregation.")
        return df, False

    print(f"Condition met: Raw feature count ({raw_feature_count}) > 100. "
          "Performing aggregation.")

    # Create a temporary dataframe for aggregation
    agg_data = pd.DataFrame(index=df.index)
    
    # Group genes by TPS family
    for family in mapping['tps_family'].unique():
        family_genes = mapping[mapping['tps_family'] == family]['gene_id'].values
        # Filter to only genes present in the dataset
        present_genes = [g for g in family_genes if g in gene_columns]
        
        if present_genes:
            # Calculate mean TPM across these genes for each sample
            mean_col = df[present_genes].mean(axis=1)
            agg_col_name = f"tps_family_{family}_mean"
            agg_data[agg_col_name] = mean_col

    if agg_data.empty:
        print("No valid gene families found for aggregation.")
        return df, False

    # Concatenate original data with aggregated features
    # We keep the original gene columns to preserve data integrity as per "extend" constraint
    final_df = pd.concat([df, agg_data], axis=1)
    
    return final_df, True

def save_log(aggregated, stats):
    """Save a log of the aggregation process."""
    log_data = {
        "timestamp": str(pd.Timestamp.now()),
        "input_file": str(INPUT_PATH),
        "output_file": str(OUTPUT_PATH),
        "aggregated": aggregated,
        "stats": stats
    }
    with open(LOG_PATH, 'w') as f:
        json.dump(log_data, f, indent=2)

def main():
    """Main execution function."""
    ensure_dirs()
    
    try:
        print(f"Loading merged data from {INPUT_PATH}...")
        df = load_merged_data()
        
        print(f"Loading TPS family mapping from {TPS_REFERENCE_PATH}...")
        mapping = load_gene_pathway_mapping()
        
        print("Performing pathway aggregation...")
        result_df, was_aggregated = aggregate_by_pathway(df, mapping)
        
        if was_aggregated:
            print(f"Saving aggregated dataset to {OUTPUT_PATH}...")
            result_df.to_csv(OUTPUT_PATH, index=False)
            
            stats = {
                "original_columns": len(df.columns),
                "new_columns_added": len([c for c in result_df.columns if c.startswith("tps_family_")]),
                "total_columns": len(result_df.columns)
            }
            save_log(True, stats)
            print("Aggregation completed successfully.")
        else:
            print("Aggregation skipped. No output file generated.")
            save_log(False, {"reason": "raw_feature_count <= 100 or no mapping"})
    
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during aggregation: {e}")
        raise

if __name__ == "__main__":
    main()
