import pytest
import pandas as pd
import numpy as np
import json
import tempfile
from pathlib import Path
import sys
import os

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.qc import check_replicates, check_metadata_completeness, run_qc_pipeline

class TestQC:
    
    @pytest.fixture
    def sample_metadata(self):
        return pd.DataFrame({
            'species': ['Arabidopsis thaliana', 'Arabidopsis thaliana', 'Solanum lycopersicum', 'Zea mays'],
            'tissue': ['leaf', 'root', 'leaf', None],
            'treatment': ['herbivore', 'herbivore', 'herbivore', 'herbivore'],
            'replicates': [3, 1, 2, 2]
        })

    def test_check_replicates_pass(self, sample_metadata):
        # Test with 3 replicates (pass)
        valid_df, exclusions = check_replicates(sample_metadata, min_replicates=2)
        assert len(valid_df) == 3
        assert len(exclusions) == 1
        assert "Insufficient biological replicates" in exclusions[0]['exclusion_reason']
        assert exclusions[0]['species'] == 'Arabidopsis thaliana'

    def test_check_replicates_all_fail(self, sample_metadata):
        # Set min_replicates high to fail all
        valid_df, exclusions = check_replicates(sample_metadata, min_replicates=10)
        assert len(valid_df) == 0
        assert len(exclusions) == 4

    def test_check_metadata_completeness_pass(self, sample_metadata):
        # All have tissue and treatment except one
        valid_df, exclusions = check_metadata_completeness(sample_metadata)
        # Zea mays has None tissue, so it should be excluded
        # Solanum and Arabidopsis (root) pass
        assert len(valid_df) == 3
        assert len(exclusions) == 1
        assert "Missing required metadata" in exclusions[0]['exclusion_reason']
        assert "tissue" in exclusions[0]['exclusion_reason']

    def test_run_qc_pipeline_integration(self, sample_metadata, tmp_path):
        # Create a temporary manifest-like file
        manifest_data = {
            "studies": sample_metadata.to_dict(orient='records'),
            "mode": "synthetic"
        }
        
        manifest_path = tmp_path / "test_manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f)
        
        # Create a dummy verification report to satisfy the pipeline's check
        verification_path = tmp_path / "processed"
        verification_path.mkdir()
        verification_file = verification_path / "metadata_verification_report.json"
        with open(verification_file, 'w') as f:
            json.dump({"studies": sample_metadata.to_dict(orient='records')}, f)

        # Mock the data path
        import src.utils.config as config
        original_get_data_path = config.get_data_path
        config.get_data_path = lambda: str(tmp_path)

        try:
            result = run_qc_pipeline(input_manifest_path=str(manifest_path))
            
            assert "post_qc_species_list" in result
            assert "excluded_studies" in result
            assert result["total_passed_studies"] == 3 # 3 passed: Arabidopsis(leaf), Arabidopsis(root), Solanum
            assert result["total_input_studies"] == 4
            
            # Check output file creation
            output_file = tmp_path / "processed" / "post_qc_species_list.json"
            assert output_file.exists()
            
            with open(output_file, 'r') as f:
                saved_data = json.load(f)
            assert saved_data == result
            
        finally:
            config.get_data_path = original_get_data_path