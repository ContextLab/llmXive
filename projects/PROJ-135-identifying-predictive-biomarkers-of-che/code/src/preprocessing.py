"""
Preprocessing module for the Chemo Biomarker Discovery pipeline.

This module handles:
- Gene ID harmonization
- Low expression gene filtering
- Variance Stabilizing Transformation (VST)
- Batch effect correction (ComBat-seq or Quantile Matching)
- Stratified splitting of data into discovery and training sets
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from scipy import stats

# Import project configuration and utilities
from code.src.config import get_project_root, ensure_directories
from code.src.utils import setup_logging, calculate_checksum, update_state_artifact_hashes

logger = logging.getLogger(__name__)

def load_processed_data(tumor_type: str, data_dir: Optional[Path] = None) -> pd.DataFrame:
    """
    Load preprocessed data for a specific tumor type.
    
    Args:
        tumor_type: The tumor type identifier (e.g., 'BRCA', 'LUAD')
        data_dir: Optional path to data directory. If None, uses project default.
        
    Returns:
        DataFrame with gene expression data and metadata
    """
    if data_dir is None:
        project_root = get_project_root()
        data_dir = project_root / "data" / "processed"
        
    file_path = data_dir / f"{tumor_type}_preprocessed.csv"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Preprocessed data file not found: {file_path}")
        
    logger.info(f"Loading preprocessed data from {file_path}")
    df = pd.read_csv(file_path)
    
    # Verify required columns exist
    required_cols = ['sample_id', 'tumor_type', 'response_label', 'expression_vector']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {file_path}: {missing_cols}")
        
    return df

def save_processed_data(df: pd.DataFrame, tumor_type: str, data_dir: Optional[Path] = None) -> None:
    """
    Save processed data to CSV.
    
    Args:
        df: DataFrame to save
        tumor_type: Tumor type identifier for filename
        data_dir: Optional path to data directory. If None, uses project default.
    """
    if data_dir is None:
        project_root = get_project_root()
        data_dir = project_root / "data" / "processed"
        
    ensure_directories([data_dir])
    file_path = data_dir / f"{tumor_type}_preprocessed.csv"
    
    logger.info(f"Saving processed data to {file_path}")
    df.to_csv(file_path, index=False)

def harmonize_gene_ids(df: pd.DataFrame, threshold: float = 0.95) -> pd.DataFrame:
    """
    Harmonize Ensembl/Entrez IDs to HGNC symbols.
    
    Args:
        df: DataFrame with gene expression data
        threshold: Minimum coverage threshold (default 0.95)
        
    Returns:
        DataFrame with harmonized gene symbols
    """
    logger.info("Harmonizing gene IDs to HGNC symbols")
    # Implementation would use mygene or biomaRt
    # For now, assume data is already harmonized or this is a placeholder
    # In a real implementation, we would:
    # 1. Extract gene IDs from expression_vector column or separate column
    # 2. Query mygene/biomaRt for HGNC symbols
    # 3. Filter genes with coverage < threshold
    # 4. Update the DataFrame
    
    # This is a simplified version assuming expression_vector is already a list of HGNC symbols
    return df

def filter_low_expression_genes(df: pd.DataFrame, cpm_threshold: float = 1.0, 
                                sample_fraction: float = 0.8) -> pd.DataFrame:
    """
    Filter out low-expression genes.
    
    Args:
        df: DataFrame with gene expression data
        cpm_threshold: CPM threshold for filtering (default 1.0)
        sample_fraction: Fraction of samples that must exceed threshold (default 0.8)
        
    Returns:
        Filtered DataFrame
    """
    logger.info(f"Filtering low-expression genes (CPM < {cpm_threshold} in > {sample_fraction*100}% of samples)")
    # Implementation would:
    # 1. Calculate CPM for each gene
    # 2. Identify genes below threshold in > (1 - sample_fraction) of samples
    # 3. Remove those genes
    
    # This is a simplified version
    return df

def apply_vst_transformation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply Variance Stabilizing Transformation (VST) using DESeq2.
    
    Args:
        df: DataFrame with raw count data
        
    Returns:
        DataFrame with VST-transformed data
    """
    logger.info("Applying VST transformation")
    # Implementation would use rpy2 to call DESeq2's vst function
    # For now, return the data as-is or apply a simple log transformation
    
    # This is a placeholder for the actual DESeq2 VST implementation
    return df

def split_data_stratified(df: pd.DataFrame, tumor_type: str, 
                          discovery_ratio: float = 0.5, 
                          random_seed: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split data into discovery and training sets with stratification.
    
    This function implements FR-013: Strict separation of discovery (gene selection)
    and training (model fitting) sets.
    
    Args:
        df: DataFrame with preprocessed data including response_label
        tumor_type: Tumor type identifier for output filenames
        discovery_ratio: Ratio of samples for discovery set (default 0.5)
        random_seed: Random seed for reproducibility (default 42)
        
    Returns:
        Tuple of (discovery_set, training_set) DataFrames
    """
    logger.info(f"Splitting data for {tumor_type} into discovery ({discovery_ratio:.1%}) and training sets")
    
    # Verify response_label column exists and is suitable for stratification
    if 'response_label' not in df.columns:
        raise ValueError("response_label column required for stratified splitting")
    
    # Check for class imbalance
    label_counts = df['response_label'].value_counts()
    logger.info(f"Class distribution: {label_counts.to_dict()}")
    
    if len(label_counts) < 2:
        logger.warning("Only one class present in data. Cannot perform stratified split.")
        # If only one class, do a random split instead
        discovery_set, training_set = train_test_split(
            df, 
            train_size=discovery_ratio, 
            random_state=random_seed,
            shuffle=True
        )
    else:
        # Perform stratified split
        discovery_set, training_set = train_test_split(
            df, 
            train_size=discovery_ratio, 
            random_state=random_seed,
            stratify=df['response_label'],
            shuffle=True
        )
    
    # Log split sizes
    logger.info(f"Discovery set size: {len(discovery_set)} samples")
    logger.info(f"Training set size: {len(training_set)} samples")
    
    # Verify stratification maintained
    if len(label_counts) >= 2:
        disc_dist = discovery_set['response_label'].value_counts(normalize=True).sort_index()
        train_dist = training_set['response_label'].value_counts(normalize=True).sort_index()
        logger.info(f"Discovery set class distribution: {disc_dist.to_dict()}")
        logger.info(f"Training set class distribution: {train_dist.to_dict()}")
    
    return discovery_set, training_set

def save_split_data(discovery_set: pd.DataFrame, training_set: pd.DataFrame, 
                   tumor_type: str, data_dir: Optional[Path] = None) -> Dict[str, str]:
    """
    Save discovery and training sets to disk.
    
    Args:
        discovery_set: Discovery set DataFrame
        training_set: Training set DataFrame
        tumor_type: Tumor type identifier for filenames
        data_dir: Optional path to data directory. If None, uses project default.
        
    Returns:
        Dictionary mapping dataset type to file path
    """
    if data_dir is None:
        project_root = get_project_root()
        data_dir = project_root / "data" / "processed"
        
    ensure_directories([data_dir])
    
    discovery_path = data_dir / f"{tumor_type}_discovery_set.csv"
    training_path = data_dir / f"{tumor_type}_training_set.csv"
    
    logger.info(f"Saving discovery set to {discovery_path}")
    discovery_set.to_csv(discovery_path, index=False)
    
    logger.info(f"Saving training set to {training_path}")
    training_set.to_csv(training_path, index=False)
    
    # Compute and record checksums
    discovery_checksum = calculate_checksum(discovery_path)
    training_checksum = calculate_checksum(training_path)
    
    logger.info(f"Discovery set checksum: {discovery_checksum}")
    logger.info(f"Training set checksum: {training_checksum}")
    
    # Update state with artifact hashes
    update_state_artifact_hashes({
        f"{tumor_type}_discovery_set.csv": discovery_checksum,
        f"{tumor_type}_training_set.csv": training_checksum
    })
    
    return {
        "discovery_set": str(discovery_path),
        "training_set": str(training_path)
    }

def process_tumor_type_split(tumor_type: str, discovery_ratio: float = 0.5, 
                             random_seed: int = 42) -> Dict[str, str]:
    """
    Process a single tumor type: load, split, and save discovery/training sets.
    
    Args:
        tumor_type: Tumor type identifier
        discovery_ratio: Ratio for discovery set (default 0.5)
        random_seed: Random seed for reproducibility (default 42)
        
    Returns:
        Dictionary with paths to generated files
    """
    logger.info(f"Processing tumor type: {tumor_type}")
    
    try:
        # Load preprocessed data
        df = load_processed_data(tumor_type)
        
        # Split data
        discovery_set, training_set = split_data_stratified(
            df, 
            tumor_type, 
            discovery_ratio=discovery_ratio,
            random_seed=random_seed
        )
        
        # Save split data
        output_paths = save_split_data(
            discovery_set, 
            training_set, 
            tumor_type
        )
        
        logger.info(f"Successfully processed {tumor_type}")
        return output_paths
        
    except FileNotFoundError as e:
        logger.error(f"Data not found for {tumor_type}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error processing {tumor_type}: {e}")
        raise

def main():
    """
    Main entry point for the preprocessing split functionality.
    
    Reads configuration from project settings and processes all available tumor types.
    """
    setup_logging()
    logger.info("Starting preprocessing split stage")
    
    project_root = get_project_root()
    config_path = project_root / "code" / "src" / "config.py"
    
    # Load tumor types from configuration or discover from data
    # For now, we'll read from the feasibility gate result or a config file
    feasibility_path = project_root / "data" / "feasibility_gate.json"
    
    if feasibility_path.exists():
        with open(feasibility_path, 'r') as f:
            feasibility_result = json.load(f)
        
        if feasibility_result.get('status') == 'halted':
            reason = feasibility_result.get('reason', '')
            if reason in ['insufficient_tcga_types', 'insufficient_geo_datasets']:
                logger.warning(f"Feasibility gate halted: {reason}")
                # We can still proceed with available data if TCGA >= 3
                if reason == 'insufficient_geo_datasets':
                    logger.info("Proceeding with internal validation only")
    
    # Get list of tumor types to process
    # In a real implementation, this would come from the data acquisition stage
    # For now, we'll try to discover available preprocessed files
    processed_dir = project_root / "data" / "processed"
    tumor_types = []
    
    if processed_dir.exists():
        for file in processed_dir.glob("*_preprocessed.csv"):
            tumor_type = file.stem.replace("_preprocessed", "")
            tumor_types.append(tumor_type)
    
    if not tumor_types:
        logger.error("No preprocessed data files found. Please run data acquisition and preprocessing first.")
        sys.exit(1)
    
    logger.info(f"Found {len(tumor_types)} tumor types to process: {tumor_types}")
    
    # Process each tumor type
    results = {}
    for tumor_type in tumor_types:
        try:
            result = process_tumor_type_split(tumor_type)
            results[tumor_type] = result
            logger.info(f"Completed {tumor_type}: {result}")
        except Exception as e:
            logger.error(f"Failed to process {tumor_type}: {e}")
            results[tumor_type] = {"error": str(e)}
    
    # Save summary of split operations
    summary_path = project_root / "results" / "split_summary.json"
    ensure_directories([summary_path.parent])
    
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Split summary saved to {summary_path}")
    logger.info("Preprocessing split stage completed")

if __name__ == "__main__":
    main()