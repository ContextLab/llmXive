"""
Integration test for the full preprocessing pipeline (US1).
Tests the sequence: download -> validate_temporal -> preprocess -> harmonize_labels.

This test verifies:
1. Real data download from Metabolomics Workbench (via study_manifest.json).
2. Temporal consistency validation (pre-challenge profiles exist).
3. Preprocessing pipeline (log-transform, missing value filtering, InChIKey alignment, batch correction).
4. Label harmonization (z-scoring, binary mapping).
5. Output artifact generation and schema compliance.

Prerequisites:
- T012 must have run successfully to populate data/raw/study_manifest.json.
- data/raw/ directory must contain downloaded study files.
"""

import os
import sys
import json
import pytest
import pandas as pd
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.data.download import download_metabolomics_data
from code.data.validate_temporal import validate_temporal_consistency
from code.data.preprocess import preprocess_metabolomics
from code.data.harmonize_labels import harmonize_labels
from code.utils.constants import DATA_RAW_DIR, DATA_PROCESSED_DIR
from code.utils.io import compute_file_hash

# Constants for test paths
STUDY_MANIFEST_PATH = DATA_RAW_DIR / "study_manifest.json"
EXPECTED_OUTPUT_MATRIX = DATA_PROCESSED_DIR / "batch_corrected_matrix.csv"
EXPECTED_OUTPUT_LABELS = DATA_PROCESSED_DIR / "labels.csv"

class TestFullPipelineIntegration:
    """Integration tests for the complete data preprocessing workflow."""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Ensure directories exist and clean up before/after test."""
        # Ensure output directory exists
        DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
        
        # Clean up previous test outputs if they exist
        if EXPECTED_OUTPUT_MATRIX.exists():
            EXPECTED_OUTPUT_MATRIX.unlink()
        if EXPECTED_OUTPUT_LABELS.exists():
            EXPECTED_OUTPUT_LABELS.unlink()
            
        yield
        
        # Cleanup not strictly necessary for CI but good practice
        
    def test_01_download_studies(self):
        """
        Test T012 prerequisite: Download studies based on manifest.
        Verifies that data/raw/ contains study files after execution.
        """
        assert STUDY_MANIFEST_PATH.exists(), "study_manifest.json must exist from T012"
        
        with open(STUDY_MANIFEST_PATH, 'r') as f:
            manifest = json.load(f)
        
        assert isinstance(manifest, list), "Manifest must be a list of studies"
        assert len(manifest) >= 2, "Manifest must contain at least 2 studies"
        
        # Execute download
        # Note: download_metabolomics_data expects a list of study IDs or the manifest path
        # Based on API surface, we assume it takes the manifest path or list
        try:
            download_metabolomics_data(manifest)
        except Exception as e:
            # If download fails due to network/real data issues, we still check for partial success
            # but the test logic depends on having data to process.
            # In a real CI, this would fail loudly if data is missing.
            pytest.fail(f"Data download failed: {e}")
        
        # Verify downloads exist (at least one file per study)
        raw_files = list(DATA_RAW_DIR.glob("*"))
        assert len(raw_files) > 0, "No files downloaded to data/raw/"
        
    def test_02_validate_temporal(self):
        """
        Test temporal consistency validation.
        Verifies that studies contain pre-challenge/baseline metadata.
        """
        if not STUDY_MANIFEST_PATH.exists():
            pytest.skip("Manifest missing, skipping temporal validation")
        
        with open(STUDY_MANIFEST_PATH, 'r') as f:
            manifest = json.load(f)
        
        study_ids = [s['study_id'] for s in manifest]
        
        # Execute temporal validation
        try:
            valid_studies = validate_temporal_consistency(study_ids)
        except Exception as e:
            # If validation fails, the pipeline should halt.
            # We expect this to raise TemporalVerificationError if data is bad.
            # For the integration test, we check that it either passes or fails correctly.
            if "TemporalVerificationError" in str(type(e)):
                pytest.fail(f"Temporal validation failed for study: {e}")
            else:
                raise
        
        # If we reach here, validation passed
        assert len(valid_studies) > 0, "No studies passed temporal validation"
        
    def test_03_preprocess_pipeline(self):
        """
        Test the full preprocessing pipeline:
        - Log transform
        - Missing value filtering
        - InChIKey alignment
        - Batch correction (ComBat)
        
        Outputs: data/processed/batch_corrected_matrix.csv
        """
        if not STUDY_MANIFEST_PATH.exists():
            pytest.skip("Manifest missing")
        
        with open(STUDY_MANIFEST_PATH, 'r') as f:
            manifest = json.load(f)
        
        study_ids = [s['study_id'] for s in manifest]
        
        # Execute preprocessing
        try:
            preprocess_metabolomics(
                study_ids=study_ids,
                output_dir=DATA_PROCESSED_DIR
            )
        except Exception as e:
            pytest.fail(f"Preprocessing pipeline failed: {e}")
        
        # Verify output exists
        assert EXPECTED_OUTPUT_MATRIX.exists(), "batch_corrected_matrix.csv not generated"
        assert EXPECTED_OUTPUT_MATRIX.stat().st_size > 0, "batch_corrected_matrix.csv is empty"
        
        # Verify content structure
        df = pd.read_csv(EXPECTED_OUTPUT_MATRIX)
        assert 'InChIKey' in df.columns or 'metabolite_id' in df.columns, "Missing metabolite identifier"
        assert 'sample_id' in df.columns, "Missing sample_id column"
        
        # Verify no NaN in numeric columns (unless expected)
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            assert df[numeric_cols].isnull().sum().sum() == 0, "Preprocessed matrix contains NaN values"
        
        # Compute hash for artifact tracking
        file_hash = compute_file_hash(str(EXPECTED_OUTPUT_MATRIX))
        assert file_hash is not None, "Failed to compute file hash"
        
    def test_04_harmonize_labels(self):
        """
        Test label harmonization:
        - Binary mapping
        - Z-scoring
        
        Outputs: data/processed/labels.csv
        """
        if not EXPECTED_OUTPUT_MATRIX.exists():
            pytest.skip("Preprocessed matrix missing, skipping label harmonization")
        
        # Execute label harmonization
        try:
            harmonize_labels(
                input_matrix=EXPECTED_OUTPUT_MATRIX,
                output_dir=DATA_PROCESSED_DIR
            )
        except Exception as e:
            pytest.fail(f"Label harmonization failed: {e}")
        
        # Verify output
        assert EXPECTED_OUTPUT_LABELS.exists(), "labels.csv not generated"
        assert EXPECTED_OUTPUT_LABELS.stat().st_size > 0, "labels.csv is empty"
        
        # Verify content
        labels_df = pd.read_csv(EXPECTED_OUTPUT_LABELS)
        assert 'germplasm_id' in labels_df.columns, "Missing germplasm_id"
        assert 'binary_label' in labels_df.columns or 'harmonized_score' in labels_df.columns, \
            "Missing label columns"
        
        # Verify binary labels are 0/1 if present
        if 'binary_label' in labels_df.columns:
            unique_labels = labels_df['binary_label'].unique()
            assert set(unique_labels).issubset({0, 1, 0.0, 1.0}), \
                f"Binary labels must be 0 or 1, found: {unique_labels}"
        
        # Compute hash
        file_hash = compute_file_hash(str(EXPECTED_OUTPUT_LABELS))
        assert file_hash is not None, "Failed to compute label file hash"
    
    def test_05_full_pipeline_e2e(self):
        """
        End-to-end integration test:
        Download -> Validate -> Preprocess -> Harmonize
        
        Verifies the entire chain works together.
        """
        # This test essentially re-runs the sequence to ensure dependencies are met
        # and the final artifacts are consistent.
        
        if not STUDY_MANIFEST_PATH.exists():
            pytest.skip("Manifest missing")
        
        # 1. Download (if not already done by previous tests)
        # 2. Validate
        # 3. Preprocess
        # 4. Harmonize
        
        # Since tests are independent, we rely on the order or re-execution
        # In CI, this might run sequentially.
        
        # Re-run the sequence to ensure state is consistent
        with open(STUDY_MANIFEST_PATH, 'r') as f:
            manifest = json.load(f)
        study_ids = [s['study_id'] for s in manifest]
        
        # Temporal
        validate_temporal_consistency(study_ids)
        
        # Preprocess
        preprocess_metabolomics(study_ids=study_ids, output_dir=DATA_PROCESSED_DIR)
        
        # Harmonize
        harmonize_labels(input_matrix=EXPECTED_OUTPUT_MATRIX, output_dir=DATA_PROCESSED_DIR)
        
        # Final assertions
        assert EXPECTED_OUTPUT_MATRIX.exists()
        assert EXPECTED_OUTPUT_LABELS.exists()
        
        # Verify row counts match
        matrix_df = pd.read_csv(EXPECTED_OUTPUT_MATRIX)
        labels_df = pd.read_csv(EXPECTED_OUTPUT_LABELS)
        
        # Ensure sample IDs align
        matrix_samples = set(matrix_df['sample_id'])
        label_samples = set(labels_df['germplasm_id']) # Assuming mapping is by sample/germplasm
        
        # At least some overlap expected
        overlap = matrix_samples.intersection(label_samples)
        assert len(overlap) > 0, "No sample ID overlap between matrix and labels"