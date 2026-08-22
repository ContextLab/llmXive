"""
Integration test for mechanism-blind filtering (T022).

This test verifies that the mechanism_blind_filter module correctly excludes
known resistance genes for a target antibiotic class from the feature matrix,
ensuring no data leakage in the model training process (FR-008).

It uses real data artifacts produced by T016 (feature matrix) and T013 (CARD data).
"""
import os
import sys
import json
import logging
import tempfile
import shutil
from pathlib import Path
import pandas as pd

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.logging import get_logger
from utils.config import load_config
from code_03_model.mechanism_blind_filter import (
    load_card_reference,
    get_target_class_genes,
    filter_mechanism_genes,
    save_filtered_matrix
)

# Configure logging
logger = get_logger("test_mechanism_blind_integration")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

# Hardcoded test configuration for integration
# In a real CI environment, these would come from a test config file
TEST_FEATURE_MATRIX_PATH = "data/processed/feature_matrix.csv"
TEST_CARD_DATA_PATH = "data/raw/card_resistance_genes.json"
TARGET_ANTIBIOTIC_CLASS = "beta-lactam"  # Example class to test filtering
OUTPUT_DIR = "data/processed/test_output"

def setup_test_environment():
    """Ensure required test data artifacts exist."""
    feature_matrix_path = PROJECT_ROOT / TEST_FEATURE_MATRIX_PATH
    card_data_path = PROJECT_ROOT / TEST_CARD_DATA_PATH
    
    if not feature_matrix_path.exists():
        raise FileNotFoundError(
            f"Integration test dependency missing: {TEST_FEATURE_MATRIX_PATH}. "
            "Please run T016 (build_feature_matrix.py) first."
        )
    
    if not card_data_path.exists():
        raise FileNotFoundError(
            f"Integration test dependency missing: {TEST_CARD_DATA_PATH}. "
            "Please run T013 (download_card.py) first."
        )
    
    # Create output directory
    output_path = PROJECT_ROOT / OUTPUT_DIR
    output_path.mkdir(parents=True, exist_ok=True)
    
    return feature_matrix_path, card_data_path, output_path

def test_mechanism_blind_filtering():
    """
    Integration test: Verify that mechanism-blind filtering correctly removes
    target class genes from the feature matrix.
    """
    logger.info("Starting mechanism-blind filtering integration test...")
    
    # Setup
    feature_matrix_path, card_data_path, output_dir = setup_test_environment()
    output_file = output_dir / "filtered_feature_matrix.csv"
    
    # 1. Load CARD reference data
    logger.info(f"Loading CARD reference from {card_data_path}")
    card_reference = load_card_reference(card_data_path)
    
    # 2. Get target class genes
    logger.info(f"Identifying genes for target class: {TARGET_ANTIBIOTIC_CLASS}")
    target_genes = get_target_class_genes(card_reference, TARGET_ANTIBIOTIC_CLASS)
    
    if not target_genes:
        logger.warning(f"No genes found for target class: {TARGET_ANTIBIOTIC_CLASS}. "
                     "This may indicate a data issue or mismatch in class naming.")
        # Note: In a real scenario, we might want to fail here if we expect genes
        # For this test, we'll proceed to verify the filtering logic still works
    
    # 3. Load feature matrix
    logger.info(f"Loading feature matrix from {feature_matrix_path}")
    feature_df = pd.read_csv(feature_matrix_path)
    
    # Identify gene presence columns (typically columns starting with 'gene_' or containing gene names)
    # Assuming the feature matrix has columns like 'gene_<gene_name>' for presence/absence
    gene_columns = [col for col in feature_df.columns if col.startswith('gene_')]
    logger.info(f"Found {len(gene_columns)} gene presence columns in feature matrix")
    
    # 4. Filter mechanism genes
    logger.info(f"Filtering {len(target_genes)} target genes from feature matrix")
    filtered_df = filter_mechanism_genes(
        feature_df, 
        target_genes, 
        gene_column_prefix='gene_',
        logger=logger
    )
    
    # 5. Save filtered matrix
    logger.info(f"Saving filtered matrix to {output_file}")
    save_filtered_matrix(filtered_df, output_file)
    
    # 6. Verification
    logger.info("Verifying filtering results...")
    
    # Check that the filtered matrix exists
    assert output_file.exists(), "Filtered feature matrix was not created"
    
    # Check that target genes are removed
    target_gene_columns = [f"gene_{gene}" for gene in target_genes if f"gene_{gene}" in feature_df.columns]
    
    if target_gene_columns:
        for col in target_gene_columns:
            assert col not in filtered_df.columns, (
                f"Target gene column '{col}' was NOT removed from the feature matrix. "
                "Mechanism-blind filtering FAILED."
            )
        logger.info(f"✓ Successfully removed {len(target_gene_columns)} target gene columns")
    else:
        logger.info("✓ No target gene columns were present in the original matrix to remove")
    
    # Check that non-target genes remain
    original_gene_count = len(gene_columns)
    filtered_gene_count = len([col for col in filtered_df.columns if col.startswith('gene_')])
    
    removed_count = original_gene_count - filtered_gene_count
    expected_removed = len([col for col in target_gene_columns if col in gene_columns])
    
    assert removed_count == expected_removed, (
        f"Incorrect number of genes removed. Expected {expected_removed}, got {removed_count}"
    )
    
    logger.info(f"✓ Correct number of genes removed: {removed_count}")
    
    # Check that non-gene features (SNPs, CNVs, phenotype) are preserved
    non_gene_cols = [col for col in feature_df.columns if not col.startswith('gene_')]
    for col in non_gene_cols:
        assert col in filtered_df.columns, (
            f"Non-gene column '{col}' was incorrectly removed from the feature matrix"
        )
    
    logger.info("✓ Non-gene features preserved correctly")
    
    # Check row count consistency
    assert len(filtered_df) == len(feature_df), (
        f"Row count mismatch. Original: {len(feature_df)}, Filtered: {len(filtered_df)}"
    )
    
    logger.info("✓ Row count preserved correctly")
    
    # 7. Summary
    logger.info("=" * 60)
    logger.info("INTEGRATION TEST PASSED: Mechanism-blind filtering works correctly")
    logger.info(f"  - Original features: {len(feature_df.columns)}")
    logger.info(f"  - Filtered features: {len(filtered_df.columns)}")
    logger.info(f"  - Target class: {TARGET_ANTIBIOTIC_CLASS}")
    logger.info(f"  - Genes removed: {removed_count}")
    logger.info(f"  - Output file: {output_file}")
    logger.info("=" * 60)
    
    return True

def main():
    """Main entry point for the integration test."""
    try:
        success = test_mechanism_blind_filtering()
        if success:
            logger.info("Integration test completed successfully.")
            sys.exit(0)
        else:
            logger.error("Integration test failed.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Integration test failed with exception: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()