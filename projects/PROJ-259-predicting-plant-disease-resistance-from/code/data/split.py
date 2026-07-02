"""
Data splitting module for stratified sampling based on resistance phenotype.

Implements FR-009: Stratified sampling to ensure balanced representation
of resistance phenotypes in training and hold-out sets.
"""
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

from config import get_path, load_config
from utils.logging import setup_logger, log_pipeline_step, log_sample_exclusion
from utils.exceptions import PipelineException, EX_DATA_INTEGRITY, EX_POWER_INSUFFICIENT
from data.manifest import ManifestLoader, load_manifest, get_manifest_source_type

# Default split ratios (resolved from spec [deferred] via plan.md authority)
# Standard practice: 80% training, 20% hold-out
DEFAULT_TRAIN_RATIO = 0.8
DEFAULT_HOLDOUT_RATIO = 0.2
RANDOM_SEED = 42  # For reproducibility

logger = setup_logger(__name__)

def load_processed_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """
    Load preprocessed SNP, metabolite, and phenotype data.
    
    Returns:
        Tuple of (snps_df, metabolites_df, phenotype_series)
        
    Raises:
        PipelineException: If required data files are missing or malformed
    """
    config = load_config()
    
    snp_path = get_path("data", "processed", "snps_aligned.csv")
    metabo_path = get_path("data", "processed", "metabolites_aligned.csv")
    phenotype_path = get_path("data", "processed", "phenotypes_aligned.csv")
    
    # Validate files exist
    missing_files = []
    for path, name in [(snp_path, "SNPs"), (metabo_path, "metabolites"), (phenotype_path, "phenotypes")]:
        if not os.path.exists(path):
            missing_files.append(f"{name}: {path}")
    
    if missing_files:
        raise PipelineException(
            f"Required preprocessed data files missing: {', '.join(missing_files)}",
            code=EX_DATA_INTEGRITY
        )
    
    # Load data
    snps_df = pd.read_csv(snp_path)
    metabolites_df = pd.read_csv(metabo_path)
    phenotype_df = pd.read_csv(phenotype_path)
    
    # Validate phenotype column exists
    if 'resistance' not in phenotype_df.columns:
        raise PipelineException(
            "Phenotype file must contain 'resistance' column",
            code=EX_DATA_INTEGRITY
        )
    
    # Extract phenotype series
    phenotype_series = phenotype_df.set_index('sample_id')['resistance']
    
    # Validate sample alignment
    snp_samples = set(snps_df['sample_id'])
    metabo_samples = set(metabolites_df['sample_id'])
    phenotype_samples = set(phenotype_series.index)
    
    common_samples = snp_samples & metabo_samples & phenotype_samples
    
    if len(common_samples) < 100:
        raise PipelineException(
            f"Insufficient aligned samples: {len(common_samples)} < 100",
            code=EX_POWER_INSUFFICIENT
        )
    
    # Filter to common samples
    snps_df = snps_df[snps_df['sample_id'].isin(common_samples)].set_index('sample_id')
    metabolites_df = metabolites_df[metabolites_df['sample_id'].isin(common_samples)].set_index('sample_id')
    phenotype_series = phenotype_series[phenotype_series.index.isin(common_samples)]
    
    logger.info(f"Loaded {len(common_samples)} aligned samples for splitting")
    
    return snps_df, metabolites_df, phenotype_series

def perform_stratified_split(
    phenotype_series: pd.Series,
    train_ratio: float = DEFAULT_TRAIN_RATIO,
    holdout_ratio: float = DEFAULT_HOLDOUT_RATIO,
    random_state: int = RANDOM_SEED
) -> Tuple[pd.Index, pd.Index, pd.Index]:
    """
    Perform stratified sampling to split data into training and hold-out sets.
    
    Args:
        phenotype_series: Series with sample_id index and resistance phenotype values
        train_ratio: Proportion of data for training (default 0.8)
        holdout_ratio: Proportion of data for hold-out (default 0.2)
        random_state: Random seed for reproducibility (default 42)
        
    Returns:
        Tuple of (train_index, holdout_index, remaining_index)
        
    Raises:
        PipelineException: If stratification fails due to class imbalance
    """
    if not np.isclose(train_ratio + holdout_ratio, 1.0):
        raise PipelineException(
            f"Train and holdout ratios must sum to 1.0, got {train_ratio + holdout_ratio}",
            code=EX_DATA_INTEGRITY
        )
    
    # Validate minimum class representation for stratification
    class_counts = phenotype_series.value_counts()
    min_class_count = class_counts.min()
    
    if min_class_count < 10:
        raise PipelineException(
            f"Insufficient samples for stratification: minimum class count is {min_class_count} < 10",
            code=EX_POWER_INSUFFICIENT
        )
    
    # Perform stratified split
    try:
        train_index, holdout_index = train_test_split(
            phenotype_series.index,
            test_size=holdout_ratio,
            stratify=phenotype_series,
            random_state=random_state
        )
    except ValueError as e:
        raise PipelineException(
            f"Stratified split failed: {str(e)}",
            code=EX_DATA_INTEGRITY
        )
    
    logger.info(f"Split completed: {len(train_index)} training samples, {len(holdout_index)} holdout samples")
    
    # Log class distribution
    train_phenotypes = phenotype_series.loc[train_index]
    holdout_phenotypes = phenotype_series.loc[holdout_index]
    
    logger.info(f"Training set class distribution: {train_phenotypes.value_counts().to_dict()}")
    logger.info(f"Holdout set class distribution: {holdout_phenotypes.value_counts().to_dict()}")
    
    return train_index, holdout_index, pd.Index([])  # No remaining samples

def save_split_indices(
    train_index: pd.Index,
    holdout_index: pd.Index,
    split_config: Dict[str, Any]
) -> None:
    """
    Save split indices to CSV files and update manifest.
    
    Args:
        train_index: Training set sample indices
        holdout_index: Holdout set sample indices
        split_config: Configuration dictionary with split parameters
    """
    config = load_config()
    
    train_path = get_path("data", "processed", "train_indices.csv")
    holdout_path = get_path("data", "processed", "holdout_indices.csv")
    
    # Save indices
    pd.DataFrame({'sample_id': train_index}).to_csv(train_path, index=False)
    pd.DataFrame({'sample_id': holdout_index}).to_csv(holdout_path, index=False)
    
    logger.info(f"Saved training indices to {train_path}")
    logger.info(f"Saved holdout indices to {holdout_path}")
    
    # Update manifest with split information
    manifest_path = get_path("data", "data_manifest.yaml")
    if os.path.exists(manifest_path):
        manifest = load_manifest(manifest_path)
        manifest['split'] = {
            'train_ratio': split_config['train_ratio'],
            'holdout_ratio': split_config['holdout_ratio'],
            'train_samples': len(train_index),
            'holdout_samples': len(holdout_index),
            'random_state': split_config['random_state'],
            'timestamp': pd.Timestamp.now().isoformat()
        }
        
        with open(manifest_path, 'w') as f:
            import yaml
            yaml.dump(manifest, f, default_flow_style=False)
        
        logger.info(f"Updated manifest with split information")

def split_pipeline() -> Dict[str, Any]:
    """
    Execute the complete data splitting pipeline.
    
    Returns:
        Dictionary with split results and metadata
        
    Raises:
        PipelineException: If any step in the pipeline fails
    """
    log_pipeline_step("split_pipeline", "START")
    
    try:
        # Load config and check source type
        config = load_config()
        source_type = get_manifest_source_type()
        
        logger.info(f"Data source type: {source_type}")
        
        # Load processed data
        snps_df, metabolites_df, phenotype_series = load_processed_data()
        
        # Get split ratios from config or use defaults
        train_ratio = config.get('split', {}).get('train_ratio', DEFAULT_TRAIN_RATIO)
        holdout_ratio = config.get('split', {}).get('holdout_ratio', DEFAULT_HOLDOUT_RATIO)
        random_state = config.get('split', {}).get('random_state', RANDOM_SEED)
        
        split_config = {
            'train_ratio': train_ratio,
            'holdout_ratio': holdout_ratio,
            'random_state': random_state,
            'source_type': source_type
        }
        
        # Perform stratified split
        train_index, holdout_index, remaining_index = perform_stratified_split(
            phenotype_series,
            train_ratio=train_ratio,
            holdout_ratio=holdout_ratio,
            random_state=random_state
        )
        
        # Save split indices
        save_split_indices(train_index, holdout_index, split_config)
        
        # Prepare output data
        train_snps = snps_df.loc[train_index]
        train_metabolites = metabolites_df.loc[train_index]
        train_phenotypes = phenotype_series.loc[train_index]
        
        holdout_snps = snps_df.loc[holdout_index]
        holdout_metabolites = metabolites_df.loc[holdout_index]
        holdout_phenotypes = phenotype_series.loc[holdout_index]
        
        result = {
            'success': True,
            'train_samples': len(train_index),
            'holdout_samples': len(holdout_index),
            'train_phenotype_distribution': train_phenotypes.value_counts().to_dict(),
            'holdout_phenotype_distribution': holdout_phenotypes.value_counts().to_dict(),
            'split_config': split_config,
            'paths': {
                'train_snps': get_path("data", "processed", "train_snps.csv"),
                'train_metabolites': get_path("data", "processed", "train_metabolites.csv"),
                'train_phenotypes': get_path("data", "processed", "train_phenotypes.csv"),
                'holdout_snps': get_path("data", "processed", "holdout_snps.csv"),
                'holdout_metabolites': get_path("data", "processed", "holdout_metabolites.csv"),
                'holdout_phenotypes': get_path("data", "processed", "holdout_phenotypes.csv")
            }
        }
        
        # Save split data files
        train_snps.reset_index().to_csv(result['paths']['train_snps'], index=False)
        train_metabolites.reset_index().to_csv(result['paths']['train_metabolites'], index=False)
        train_phenotypes.reset_index(name='resistance').to_csv(result['paths']['train_phenotypes'], index=False)
        
        holdout_snps.reset_index().to_csv(result['paths']['holdout_snps'], index=False)
        holdout_metabolites.reset_index().to_csv(result['paths']['holdout_metabolites'], index=False)
        holdout_phenotypes.reset_index(name='resistance').to_csv(result['paths']['holdout_phenotypes'], index=False)
        
        log_pipeline_step("split_pipeline", "COMPLETE", result)
        
        return result
        
    except PipelineException:
        log_pipeline_step("split_pipeline", "FAILED", {"error": "Pipeline exception"})
        raise
    except Exception as e:
        log_pipeline_step("split_pipeline", "FAILED", {"error": str(e)})
        raise PipelineException(f"Split pipeline failed: {str(e)}", code=EX_DATA_INTEGRITY)

def main():
    """Main entry point for data splitting."""
    logger.info("Starting data splitting pipeline")
    
    try:
        result = split_pipeline()
        logger.info(f"Data splitting completed successfully")
        logger.info(f"Training samples: {result['train_samples']}")
        logger.info(f"Holdout samples: {result['holdout_samples']}")
        
        # Print summary
        print("\n=== Split Summary ===")
        print(f"Training set: {result['train_samples']} samples")
        print(f"  Phenotype distribution: {result['train_phenotype_distribution']}")
        print(f"Holdout set: {result['holdout_samples']} samples")
        print(f"  Phenotype distribution: {result['holdout_phenotype_distribution']}")
        print("====================\n")
        
    except PipelineException as e:
        logger.error(f"Pipeline failed with code {e.code}: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise

if __name__ == "__main__":
    main()
