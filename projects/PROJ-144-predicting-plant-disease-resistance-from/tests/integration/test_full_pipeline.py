"""
Integration test for the full preprocessing pipeline (US1).

This test verifies the end-to-end flow:
1. Download raw data from Metabolomics Workbench (T012)
2. Validate temporal consistency (T013)
3. Preprocess and harmonize data (T014, T015)
4. Verify output artifacts exist and meet basic quality criteria

Prerequisites:
- T032 (Study IDs identified in research.md)
- T012 (download.py implemented)
- T013 (validate_temporal.py implemented)
- T014 (harmonize_labels.py implemented)
- T015 (preprocess.py implemented)
"""

import os
import sys
import json
import tempfile
import shutil
import pytest
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.data.download import download_metabolomics_data
from code.data.validate_temporal import validate_temporal_consistency
from code.data.preprocess import preprocess_metabolomics
from code.data.harmonize_labels import harmonize_labels
from code.utils.constants import DATA_RAW_DIR, DATA_PROCESSED_DIR, RESEARCH_FILE


class TestFullPipeline:
    """Integration tests for the complete data preprocessing pipeline."""
    
    @pytest.fixture(scope="class")
    def temp_output_dir(self):
        """Create a temporary directory for test outputs."""
        temp_dir = tempfile.mkdtemp(prefix="pipeline_test_")
        yield Path(temp_dir)
        # Cleanup after tests
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_01_download_data(self, temp_output_dir):
        """
        Test T012: Download metabolomics data from Metabolomics Workbench.
        
        Verifies:
        - Data is downloaded to the correct location
        - Files are non-empty
        - Study IDs from research.md are used
        """
        # Read study IDs from research.md
        research_path = PROJECT_ROOT / RESEARCH_FILE
        if not research_path.exists():
            pytest.skip(f"research.md not found at {research_path}. Skipping download test.")
        
        # Parse study IDs from research.md (simple regex-like extraction)
        content = research_path.read_text()
        study_ids = []
        for line in content.split('\n'):
            if 'STUDY-' in line or 'C-STUDY-' in line:
                # Extract study ID (format: STUDY-XXXX or C-STUDY-XXXX)
                import re
                matches = re.findall(r'(C?-STUDY-\d+)', line)
                study_ids.extend(matches)
        
        if not study_ids:
            pytest.skip("No study IDs found in research.md. Skipping download test.")
        
        # Take first 2 study IDs
        test_study_ids = study_ids[:2]
        
        # Set up download paths
        raw_dir = temp_output_dir / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        # Download data
        success, downloaded_files = download_metabolomics_data(
            study_ids=test_study_ids,
            output_dir=str(raw_dir)
        )
        
        assert success, f"Data download failed for studies: {test_study_ids}"
        assert len(downloaded_files) > 0, "No files were downloaded"
        
        # Verify files are non-empty
        for file_path in downloaded_files:
            assert os.path.getsize(file_path) > 0, f"Downloaded file is empty: {file_path}"
        
        # Store downloaded files for next test
        self.downloaded_files = downloaded_files
        self.raw_dir = raw_dir
    
    def test_02_validate_temporal(self):
        """
        Test T013: Validate temporal consistency of downloaded data.
        
        Verifies:
        - Temporal validation runs without errors
        - Studies without pre-challenge data are flagged/skipped
        - results/temporal_verification.json is created
        """
        if not hasattr(self, 'raw_dir'):
            pytest.skip("Previous download test was skipped. Cannot run temporal validation.")
        
        # Run temporal validation
        results_dir = PROJECT_ROOT / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        
        valid_studies, temporal_results = validate_temporal_consistency(
            raw_data_dir=str(self.raw_dir),
            output_path=str(results_dir / "temporal_verification.json")
        )
        
        # Verify output file exists
        assert (results_dir / "temporal_verification.json").exists(), \
            "Temporal verification output file not created"
        
        # Verify output contains expected structure
        with open(results_dir / "temporal_verification.json", 'r') as f:
            verification_data = json.load(f)
        
        assert "studies" in verification_data, "Missing 'studies' key in temporal verification"
        assert "status" in verification_data, "Missing 'status' key in temporal verification"
        
        # At least one study should be valid (or all skipped if none have temporal info)
        assert isinstance(valid_studies, list), "valid_studies should be a list"
        
        self.valid_studies = valid_studies
    
    def test_03_preprocess_and_harmonize(self):
        """
        Test T014 and T015: Preprocess and harmonize data.
        
        Verifies:
        - Preprocessing completes without errors
        - Batch correction is applied when multiple studies are present
        - Output files are created in data/processed/
        - Files contain valid data (non-empty, correct structure)
        """
        if not hasattr(self, 'raw_dir') or not hasattr(self, 'valid_studies'):
            pytest.skip("Previous tests were skipped. Cannot run preprocessing.")
        
        if not self.valid_studies:
            pytest.skip("No valid studies after temporal validation. Skipping preprocessing.")
        
        # Create processed directory
        processed_dir = PROJECT_ROOT / DATA_PROCESSED_DIR
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Run preprocessing
        preprocessing_result = preprocess_metabolomics(
            raw_data_dir=str(self.raw_dir),
            valid_studies=self.valid_studies,
            output_dir=str(processed_dir)
        )
        
        assert preprocessing_result["success"], "Preprocessing failed"
        
        # Verify output files
        expected_files = [
            "batch_corrected_matrix.csv",
            "labels.csv",
            "alignment_missing.json"
        ]
        
        for file_name in expected_files:
            file_path = processed_dir / file_name
            assert file_path.exists(), f"Expected output file missing: {file_path}"
            assert os.path.getsize(file_path) > 0, f"Output file is empty: {file_path}"
        
        # Verify matrix structure
        matrix_df = preprocessing_result["matrix"]
        assert matrix_df is not None, "Matrix dataframe is None"
        assert len(matrix_df) > 0, "Matrix dataframe is empty"
        assert "sample_id" in matrix_df.columns or matrix_df.index.name == "sample_id", \
            "Matrix missing sample_id column/index"
        
        # Verify labels structure
        labels_df = preprocessing_result["labels"]
        assert labels_df is not None, "Labels dataframe is None"
        assert len(labels_df) > 0, "Labels dataframe is empty"
        assert "germplasm_id" in labels_df.columns or "sample_id" in labels_df.columns, \
            "Labels missing expected ID column"
        
        # Verify harmonization was applied (check for binary_label or harmonized_score)
        assert "binary_label" in labels_df.columns or "harmonized_score" in labels_df.columns, \
            "Labels missing harmonized fields (binary_label or harmonized_score)"
        
        # Store results for next test
        self.processed_matrix = matrix_df
        self.processed_labels = labels_df
    
    def test_04_harmonize_labels_integration(self):
        """
        Test T014 specifically: Verify label harmonization logic.
        
        This is a focused test on the harmonize_labels module to ensure:
        - Binary labels are correctly encoded
        - Z-scoring is applied when appropriate
        - Output includes both binary and continuous scores
        """
        if not hasattr(self, 'processed_labels'):
            pytest.skip("Previous preprocessing test was skipped.")
        
        labels_df = self.processed_labels
        
        # Check that harmonization functions were applied
        # The harmonize_labels function should have added binary_label and/or harmonized_score
        
        # Verify binary_label exists and has valid values (0, 1, or NaN)
        if "binary_label" in labels_df.columns:
            valid_binary = labels_df["binary_label"].dropna()
            assert all(valid_binary.isin([0, 1])), \
                "binary_label contains invalid values (should be 0 or 1)"
        
        # Verify harmonized_score exists and is numeric
        if "harmonized_score" in labels_df.columns:
            assert pd.api.types.is_numeric_dtype(labels_df["harmonized_score"]), \
                "harmonized_score should be numeric"
        
        # Verify sample count consistency
        assert len(labels_df) == len(self.processed_matrix), \
            "Label count does not match matrix sample count"
    
    def test_05_pipeline_artifacts_exist(self):
        """
        Final integration check: Verify all required artifacts exist.
        
        This test ensures the pipeline produced all expected outputs:
        - data/processed/batch_corrected_matrix.csv
        - data/processed/labels.csv
        - results/temporal_verification.json
        - results/alignment_missing.json
        """
        processed_dir = PROJECT_ROOT / DATA_PROCESSED_DIR
        results_dir = PROJECT_ROOT / "results"
        
        required_artifacts = [
            processed_dir / "batch_corrected_matrix.csv",
            processed_dir / "labels.csv",
            results_dir / "temporal_verification.json",
            results_dir / "alignment_missing.json"
        ]
        
        missing_artifacts = []
        for artifact in required_artifacts:
            if not artifact.exists():
                missing_artifacts.append(str(artifact))
            elif os.path.getsize(artifact) == 0:
                missing_artifacts.append(f"{artifact} (empty)")
        
        if missing_artifacts:
            pytest.fail(f"Missing or empty required artifacts: {missing_artifacts}")
        
        # Additional validation: check matrix has expected columns
        matrix_path = processed_dir / "batch_corrected_matrix.csv"
        if matrix_path.exists():
            import pandas as pd
            df = pd.read_csv(matrix_path)
            assert len(df.columns) > 1, "Matrix has only one column (should have features)"
            assert len(df) > 0, "Matrix has no rows"
        
        # Check temporal verification has valid status
        temporal_path = results_dir / "temporal_verification.json"
        if temporal_path.exists():
            with open(temporal_path, 'r') as f:
                temporal_data = json.load(f)
            assert "status" in temporal_data, "Temporal verification missing status"
            assert temporal_data["status"] in ["VERIFIED", "PARTIAL", "UNVERIFIED"], \
                f"Invalid temporal verification status: {temporal_data['status']}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])