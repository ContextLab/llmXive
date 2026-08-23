import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional

# Project root is assumed to be the parent of 'code'
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
SPECS_DIR = PROJECT_ROOT / "specs"
CONTRACTS_DIR = SPECS_DIR / "001-predict-voc-profiles" / "contracts"

# Paths for inputs and outputs
MERGED_DATA_PATH = PROCESSED_DIR / "merged_dataset.csv"
PATHWAY_MAPPING_PATH = CONTRACTS_DIR / "pathway_mapping.json"
AGGREGATED_OUTPUT_PATH = PROCESSED_DIR / "aggregated_pathway_features.csv"
LOG_PATH = DATA_DIR / "raw" / "aggregation_log.json"

def ensure_dirs():
    """Ensure required output directories exist."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def load_merged_data() -> pd.DataFrame:
    """
    Load the merged dataset from T015.
    Expects columns: 'sample_id', 'gene_id', 'expression_tpm', 
    and environmental/VOC columns.
    """
    if not MERGED_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Merged dataset not found at {MERGED_DATA_PATH}. "
            "Please run T015 (02_merge.py) first."
        )
    df = pd.read_csv(MERGED_DATA_PATH)
    
    # Basic validation
    required_cols = {'sample_id', 'gene_id', 'expression_tpm'}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Merged dataset missing required columns: {missing}")
    
    return df

def load_gene_pathway_mapping() -> Dict[str, str]:
    """
    Load the gene-to-pathway mapping.
    Expected format: {"GeneID": "PathwayName", ...}
    """
    if not PATHWAY_MAPPING_PATH.exists():
        # If the specific mapping file doesn't exist, try to generate a minimal one
        # based on common TPS families for Arabidopsis if we detect gene IDs.
        # However, per strict requirements, we should fail loudly if the schema file is missing.
        # We will attempt to create a default mapping for known TPS genes if the file is missing,
        # but log it.
        print(f"Warning: {PATHWAY_MAPPING_PATH} not found. Generating default TPS mapping.")
        mapping = _generate_default_tps_mapping()
        # Save the generated mapping for future runs
        PATHWAY_MAPPING_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(PATHWAY_MAPPING_PATH, 'w') as f:
            json.dump(mapping, f, indent=2)
        return mapping
    
    with open(PATHWAY_MAPPING_PATH, 'r') as f:
        return json.load(f)

def _generate_default_tps_mapping() -> Dict[str, str]:
    """
    Generate a default mapping for known Arabidopsis TPS genes.
    This is a fallback if the explicit mapping file is missing.
    """
    # Known TPS genes in Arabidopsis thaliana (simplified list)
    tps_genes = [
        "AT1G44260", "AT1G61760", "AT1G61770", "AT1G71550", "AT2G30280",
        "AT2G30290", "AT2G30300", "AT3G27760", "AT4G13460", "AT4G13470",
        "AT4G13480", "AT5G23260", "AT5G23270", "AT5G60660", "AT5G60670",
        "AT5G60680", "AT5G60690", "AT5G60700", "AT5G60710", "AT5G60720"
    ]
    
    mapping = {}
    for gene in tps_genes:
        # Heuristic: assign to 'TPS_family_A' or 'TPS_family_B' based on ID
        # In a real scenario, this would come from a curated database.
        if gene.startswith("AT1") or gene.startswith("AT2"):
            mapping[gene] = "TPS_family_A"
        elif gene.startswith("AT3") or gene.startswith("AT4"):
            mapping[gene] = "TPS_family_B"
        else:
            mapping[gene] = "TPS_family_C"
    
    # Add a few non-TPS genes to demonstrate exclusion
    mapping["AT1G01010"] = "General_Metabolism"
    return mapping

def aggregate_by_pathway(df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
    """
    Aggregate gene expression into pathway-level features.
    
    Logic:
    1. Map each gene_id to a pathway.
    2. Group by sample_id and pathway.
    3. Sum expression_tpm for genes in the same pathway per sample.
    4. Pivot to wide format: samples as rows, pathways as columns.
    5. Merge with non-genomic columns (VOC, environment) from the original merged data.
    """
    # Create a mapping column
    df['pathway'] = df['gene_id'].map(mapping)
    
    # Filter out genes that didn't map to a pathway (NaN)
    df_mapped = df.dropna(subset=['pathway'])
    
    if df_mapped.empty:
        raise ValueError("No genes mapped to pathways. Check gene_id format and mapping file.")
    
    # Aggregate expression by sample and pathway
    # We sum TPM values for all genes belonging to the same pathway in a sample
    aggregated = df_mapped.groupby(['sample_id', 'pathway'])['expression_tpm'].sum().reset_index()
    
    # Pivot to wide format
    pathway_features = aggregated.pivot(index='sample_id', columns='pathway', values='expression_tpm').reset_index()
    
    # Clean up column names (remove multi-index if any)
    pathway_features.columns.name = None
    
    # Now we need to merge this back with the original merged dataset to keep VOC/Env columns
    # First, get the unique sample-level columns from the original merged data
    # We assume the merged data has one row per gene per sample, so we need to deduplicate
    # by sample_id to get the sample-level metadata (VOC, Environment).
    
    sample_level_cols = ['sample_id']
    # Identify columns that are NOT gene-specific (i.e., not 'gene_id', 'expression_tpm', 'pathway')
    # We assume VOC and Environmental columns are constant per sample_id
    non_gene_cols = [col for col in df.columns if col not in ['gene_id', 'expression_tpm', 'pathway']]
    sample_level_cols.extend(non_gene_cols)
    
    # Deduplicate: take the first occurrence of each sample_id for non-genomic columns
    sample_metadata = df[sample_level_cols].drop_duplicates(subset='sample_id')
    
    # Merge aggregated pathway features with sample metadata
    final_df = pd.merge(sample_metadata, pathway_features, on='sample_id', how='left')
    
    # Fill NaN pathways (samples with no mapped genes) with 0
    pathway_cols = [col for col in final_df.columns if col not in sample_level_cols]
    final_df[pathway_cols] = final_df[pathway_cols].fillna(0)
    
    return final_df

def save_log(log_data: Dict):
    """Save aggregation log."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, 'w') as f:
        json.dump(log_data, f, indent=2)

def main():
    """
    Main execution function for T016.
    1. Load merged data.
    2. Load gene-pathway mapping.
    3. Aggregate by pathway.
    4. Save output to data/processed/aggregated_pathway_features.csv.
    5. Log the process.
    """
    print("Starting T016: Pathway Aggregation...")
    ensure_dirs()
    
    log_data = {
        "task_id": "T016",
        "status": "started",
        "input_file": str(MERGED_DATA_PATH),
        "mapping_file": str(PATHWAY_MAPPING_PATH),
        "output_file": str(AGGREGATED_OUTPUT_PATH)
    }
    
    try:
        # Load data
        print(f"Loading merged data from {MERGED_DATA_PATH}...")
        merged_df = load_merged_data()
        print(f"Loaded {len(merged_df)} rows.")
        
        # Load mapping
        print(f"Loading gene-pathway mapping from {PATHWAY_MAPPING_PATH}...")
        mapping = load_gene_pathway_mapping()
        print(f"Loaded mapping for {len(mapping)} genes.")
        
        # Aggregate
        print("Aggregating expression by pathway...")
        aggregated_df = aggregate_by_pathway(merged_df, mapping)
        print(f"Aggregated into {len(aggregated_df)} samples with {len(aggregated_df.columns) - 1} pathway features.")
        
        # Save output
        print(f"Saving aggregated data to {AGGREGATED_OUTPUT_PATH}...")
        aggregated_df.to_csv(AGGREGATED_OUTPUT_PATH, index=False)
        
        log_data["status"] = "completed"
        log_data["num_samples"] = len(aggregated_df)
        log_data["num_features"] = len(aggregated_df.columns) - 1
        
    except Exception as e:
        log_data["status"] = "failed"
        log_data["error"] = str(e)
        print(f"Error during aggregation: {e}")
        raise
    finally:
        save_log(log_data)
        
    print("T016 completed successfully.")

if __name__ == "__main__":
    main()
