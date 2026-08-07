"""
Integration test for ground truth generation on a small sample.

This test verifies the full pipeline from dataset streaming -> attention extraction
-> feature computation -> merging, ensuring no memory errors occur and the output
contains valid entropy, POS tags, and binary RTPurbo labels.

Prerequisites:
  - T005: Memory-efficient data loader
  - T006: Base data entities
  - T009: Unit tests for feature extraction
  - T011: RULER dataset downloader (must be implemented before this test runs)
  - T012: Attention map generator and RTPurbo indexer
  - T013: Static feature computation
  - T014: Dataset merger
"""
import os
import sys
import tempfile
import shutil
import logging
import pytest
from pathlib import Path
from typing import List, Dict, Any

# Configure logging for the test
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.data_loader import stream_ruler_dataset
from lib.entities import TokenUnit, AttentionMap
from lib.attention_utils import compute_attention_stats
from data.download import download_ruler_sample
from data.extract_ground_truth import generate_attention_maps_and_rtpurbo
from data.compute_features import compute_static_features
from data.merge_datasets import merge_ground_truth_and_features

# Constants for the test
TEST_SAMPLE_SIZE = 2  # Number of documents to process (small sample)
MAX_MEMORY_MB = 7000  # 7GB limit
EXPECTED_COLUMNS = [
    'document_id', 'token_id', 'token_text', 'position',
    'attention_entropy', 'pos_tag', 'perplexity', 'is_rtpurbo_selected'
]

def setup_module(module):
    """Setup test fixtures and directories."""
    logger.info("Setting up integration test fixtures...")
    os.makedirs(project_root / "data" / "intermediate", exist_ok=True)
    os.makedirs(project_root / "data" / "logs", exist_ok=True)

def teardown_module(module):
    """Cleanup test artifacts if needed."""
    logger.info("Cleaning up integration test artifacts...")
    # Optionally clean up temporary files generated during test

@pytest.mark.integration
def test_ground_truth_generation_pipeline():
    """
    Integration test: Run the ground truth generation pipeline on a small sample.
    
    Steps:
    1. Download a small sample of the RULER dataset (streaming).
    2. Generate attention maps and RTPurbo labels (T012).
    3. Compute static features (T013).
    4. Merge datasets (T014).
    5. Verify output structure and content validity.
    """
    logger.info("Starting ground truth generation integration test...")
    
    # Step 1: Download a small sample
    logger.info(f"Step 1: Downloading RULER sample (size={TEST_SAMPLE_SIZE})...")
    sample_data_path = download_ruler_sample(
        num_documents=TEST_SAMPLE_SIZE,
        output_dir=project_root / "data" / "intermediate" / "samples"
    )
    assert sample_data_path.exists(), "Sample data file not created."
    logger.info(f"Sample data downloaded to: {sample_data_path}")
    
    # Step 2: Generate attention maps and RTPurbo labels
    logger.info("Step 2: Generating attention maps and RTPurbo labels...")
    attention_maps_path = project_root / "data" / "intermediate" / "attention_maps.h5"
    ground_truth_path = project_root / "data" / "intermediate" / "ground_truth.csv"
    
    # This should run on CPU-only quantization or sampled subset to fit RAM
    generate_attention_maps_and_rtpurbo(
        input_data_path=sample_data_path,
        attention_output_path=attention_maps_path,
        ground_truth_output_path=ground_truth_path,
        max_memory_mb=MAX_MEMORY_MB
    )
    
    assert attention_maps_path.exists(), "Attention maps file not created."
    assert ground_truth_path.exists(), "Ground truth file not created."
    logger.info(f"Ground truth generated: {ground_truth_path}")
    
    # Step 3: Compute static features
    logger.info("Step 3: Computing static features...")
    features_path = project_root / "data" / "intermediate" / "static_features.csv"
    
    compute_static_features(
        input_data_path=sample_data_path,
        output_path=features_path,
        max_memory_mb=MAX_MEMORY_MB
    )
    
    assert features_path.exists(), "Static features file not created."
    logger.info(f"Static features computed: {features_path}")
    
    # Step 4: Merge datasets
    logger.info("Step 4: Merging ground truth and features...")
    merged_path = project_root / "data" / "intermediate" / "merged_dataset.csv"
    
    merge_ground_truth_and_features(
        ground_truth_path=ground_truth_path,
        features_path=features_path,
        output_path=merged_path
    )
    
    assert merged_path.exists(), "Merged dataset file not created."
    logger.info(f"Merged dataset created: {merged_path}")
    
    # Step 5: Verify output structure and content
    logger.info("Step 5: Verifying output structure and content...")
    import pandas as pd
    df = pd.read_csv(merged_path)
    
    # Check columns
    assert set(df.columns).issuperset(set(EXPECTED_COLUMNS)), \
        f"Missing expected columns. Found: {df.columns.tolist()}, Expected: {EXPECTED_COLUMNS}"
    
    # Check row count (should be > 0)
    assert len(df) > 0, "Merged dataset is empty."
    
    # Check data types and validity
    # Entropy should be non-negative
    assert (df['attention_entropy'] >= 0).all(), "Attention entropy contains negative values."
    
    # POS tags should be non-empty strings
    assert (df['pos_tag'].str.len() > 0).all(), "POS tags contain empty strings."
    
    # RTPurbo labels should be binary (0 or 1)
    assert df['is_rtpurbo_selected'].isin([0, 1]).all(), "RTPurbo labels are not binary."
    
    # Check for NaN values in critical columns
    critical_cols = ['attention_entropy', 'pos_tag', 'perplexity', 'is_rtpurbo_selected']
    for col in critical_cols:
        assert not df[col].isna().any(), f"Critical column '{col}' contains NaN values."
    
    logger.info("Integration test PASSED: All checks successful.")
    print(f"Test passed. Merged dataset has {len(df)} rows and valid data.")

@pytest.mark.integration
def test_memory_usage_during_generation():
    """
    Integration test: Verify that peak memory usage stays below the limit during
    ground truth generation.
    """
    logger.info("Starting memory usage integration test...")
    
    # Import memory tracking
    from lib.data_loader import get_peak_memory_mb
    import tracemalloc
    
    tracemalloc.start()
    
    try:
        # Run the pipeline (reuse logic from above but track memory)
        sample_data_path = download_ruler_sample(
            num_documents=1,  # Even smaller for memory test
            output_dir=project_root / "data" / "intermediate" / "samples"
        )
        
        # Generate attention maps (this is the most memory-intensive step)
        attention_maps_path = project_root / "data" / "intermediate" / "attention_maps.h5"
        ground_truth_path = project_root / "data" / "intermediate" / "ground_truth.csv"
        
        generate_attention_maps_and_rtpurbo(
            input_data_path=sample_data_path,
            attention_output_path=attention_maps_path,
            ground_truth_output_path=ground_truth_path,
            max_memory_mb=MAX_MEMORY_MB
        )
        
        # Check peak memory
        current, peak = tracemalloc.get_traced_memory()
        peak_mb = peak / (1024 * 1024)
        
        logger.info(f"Peak memory usage: {peak_mb:.2f} MB")
        assert peak_mb < MAX_MEMORY_MB, \
            f"Peak memory {peak_mb:.2f} MB exceeded limit of {MAX_MEMORY_MB} MB."
        
        logger.info("Memory usage test PASSED.")
    
    finally:
        tracemalloc.stop()

if __name__ == "__main__":
    # Run the tests manually if executed as a script
    pytest.main([__file__, "-v"])