"""
Aggregation of gene expression into pathway-level features.

This module implements the dimensionality reduction step for User Story 1 (T016).
It loads the merged dataset from T015, maps individual genes to biological pathways
(specifically Terpene Synthase families), and aggregates expression values by
summing or averaging within each pathway family per sample.

Output:
    data/processed/pathway_aggregated.csv: Merged dataset with pathway-level features.
    data/processed/aggregation_mapping.json: The mapping used for reproducibility.
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Project root path calculation
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"

# Ensure output directories exist
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Known Terpene Synthase (TPS) families for Arabidopsis thaliana
# Based on TAIR and standard literature (e.g., Degenhardt et al., 2009)
# Format: Gene Symbol -> Family
TPS_MAPPING = {
    # TPS-a subfamily
    "TPS01": "TPS-a",
    "TPS02": "TPS-a",
    "TPS03": "TPS-a",
    "TPS04": "TPS-a",
    "TPS05": "TPS-a",
    "TPS06": "TPS-a",
    "TPS07": "TPS-a",
    "TPS08": "TPS-a",
    "TPS09": "TPS-a",
    "TPS10": "TPS-a",
    "TPS11": "TPS-a",
    "TPS12": "TPS-a",
    "TPS13": "TPS-a",
    "TPS14": "TPS-a",
    "TPS15": "TPS-a",
    "TPS16": "TPS-a",
    "TPS17": "TPS-a",
    "TPS18": "TPS-a",
    "TPS19": "TPS-a",
    "TPS20": "TPS-a",
    # TPS-b subfamily
    "TPS21": "TPS-b",
    "TPS22": "TPS-b",
    "TPS23": "TPS-b",
    "TPS24": "TPS-b",
    "TPS25": "TPS-b",
    "TPS26": "TPS-b",
    "TPS27": "TPS-b",
    "TPS28": "TPS-b",
    "TPS29": "TPS-b",
    "TPS30": "TPS-b",
    # TPS-e/f subfamily
    "TPS31": "TPS-e/f",
    "TPS32": "TPS-e/f",
    "TPS33": "TPS-e/f",
    "TPS34": "TPS-e/f",
    "TPS35": "TPS-e/f",
    "TPS36": "TPS-e/f",
    "TPS37": "TPS-e/f",
    "TPS38": "TPS-e/f",
    "TPS39": "TPS-e/f",
    "TPS40": "TPS-e/f",
    # TPS-g subfamily
    "TPS41": "TPS-g",
    "TPS42": "TPS-g",
    "TPS43": "TPS-g",
    "TPS44": "TPS-g",
    # TPS-h subfamily
    "TPS45": "TPS-h",
    "TPS46": "TPS-h",
    # Add generic mappings if gene symbols in data differ slightly (e.g., At3g27760 -> TPS01)
    # For this implementation, we assume the input data uses standard gene symbols
    # or we perform a lookup if a mapping file is provided.
}

def load_merged_data() -> pd.DataFrame:
    """
    Loads the merged dataset produced by T015 (code/02_merge.py).
    Expected file: data/processed/merged_dataset.csv
    """
    input_path = PROCESSED_DIR / "merged_dataset.csv"
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Please ensure T015 (code/02_merge.py) has been executed successfully."
        )
    
    df = pd.read_csv(input_path)
    return df

def load_gene_pathway_mapping() -> dict:
    """
    Loads or generates the mapping from Gene Symbol to Pathway Family.
    Returns a dictionary: {gene_symbol: family_name}
    """
    # In a real production scenario, this might be loaded from a file
    # or queried from a database. Here we use the hardcoded mapping defined above.
    # We extend it with a catch-all for non-TPS genes to 'Other' if desired,
    # but for this task, we focus on TPS families.
    return TPS_MAPPING.copy()

def aggregate_by_pathway(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """
    Aggregates gene expression columns into pathway-level features.
    
    Logic:
    1. Identify columns in the dataframe that correspond to genes in the mapping.
    2. Group these columns by their assigned pathway family.
    3. For each sample (row), sum the expression values of all genes in a family
       to create a single 'Pathway_Family' column.
    4. Keep non-gene columns (metadata, VOC targets, environmental data) intact.
    
    Args:
        df: The merged dataframe from T015.
        mapping: Dict mapping gene symbols to pathway families.
    
    Returns:
        A new dataframe with pathway-aggregated features.
    """
    # Identify gene columns (assuming they are numeric and match keys in mapping)
    gene_cols = [col for col in df.columns if col in mapping]
    
    if not gene_cols:
        print("Warning: No gene columns found in the dataframe matching the mapping.")
        # Return a copy to avoid modification issues, though no aggregation happens
        return df.copy()
    
    # Create a DataFrame for aggregation
    # We need to map column names to their group keys
    gene_series = df[gene_cols]
    group_keys = [mapping[col] for col in gene_cols]
    
    # Aggregate by summing (common for pathway activity)
    # axis=1 aggregates columns into rows
    pathway_data = gene_series.groupby(group_keys, axis=1).sum()
    
    # Rename columns to be explicit: "Pathway_TPS-a"
    pathway_data.columns = [f"Pathway_{col}" for col in pathway_data.columns]
    
    # Identify non-gene columns to keep (metadata, VOC targets, environmental)
    # We exclude the gene columns we just aggregated
    keep_cols = [col for col in df.columns if col not in gene_cols]
    
    # Concatenate metadata/targets with new pathway features
    result_df = pd.concat([df[keep_cols].reset_index(drop=True), 
                           pathway_data.reset_index(drop=True)], 
                          axis=1)
    
    return result_df

def main():
    """
    Main entry point for the aggregation task (T016).
    1. Loads merged data from T015.
    2. Loads/Defines the gene-to-pathway mapping.
    3. Aggregates expression by pathway.
    4. Saves the result to data/processed/pathway_aggregated.csv.
    5. Saves the mapping used to data/processed/aggregation_mapping.json.
    """
    print("Starting T016: Pathway Aggregation...")
    
    try:
        # Step 1: Load Data
        print(f"Loading merged dataset from {PROCESSED_DIR / 'merged_dataset.csv'}...")
        df_merged = load_merged_data()
        print(f"Loaded {len(df_merged)} rows and {len(df_merged.columns)} columns.")
        
        # Step 2: Load Mapping
        mapping = load_gene_pathway_mapping()
        print(f"Loaded mapping for {len(mapping)} genes.")
        
        # Step 3: Aggregate
        print("Aggregating gene expression by pathway family...")
        df_aggregated = aggregate_by_pathway(df_merged, mapping)
        print(f"Aggregated dataset has {len(df_aggregated.columns)} columns.")
        
        # Step 4: Save Output
        output_path = PROCESSED_DIR / "pathway_aggregated.csv"
        df_aggregated.to_csv(output_path, index=False)
        print(f"Saved aggregated data to {output_path}")
        
        # Step 5: Save Mapping for Reproducibility
        mapping_path = PROCESSED_DIR / "aggregation_mapping.json"
        with open(mapping_path, 'w') as f:
            json.dump(mapping, f, indent=2)
        print(f"Saved mapping to {mapping_path}")
        
        print("T016 completed successfully.")
        
    except Exception as e:
        print(f"Error during T016 execution: {e}")
        raise

if __name__ == "__main__":
    main()
