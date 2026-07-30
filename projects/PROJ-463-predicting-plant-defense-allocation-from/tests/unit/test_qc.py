import pytest
import pandas as pd
import numpy as np
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.data.qc import check_replicates, check_metadata_completeness, run_qc_pipeline
from src.utils.config import get_data_path

class TestQC:
    """Test suite for QC pipeline functions."""

    @pytest.fixture
    def sample_studies(self):
        """Create sample study data for testing."""
        return [
            {
                'accession_id': 'SRP001',
                'species': 'Arabidopsis thaliana',
                'tissue': 'leaf',
                'treatment': 'herbivory',
                'replicates': 3
            },
            {
                'accession_id': 'SRP002',
                'species': 'Solanum lycopersicum',
                'tissue': 'leaf',
                'treatment': 'control',
                'replicates': 1  # Should be excluded
            },
            {
                'accession_id': 'SRP003',
                'species': 'Zea mays',
                'tissue': '',  # Missing tissue
                'treatment': 'herbivory',
                'replicates': 4
            },
            {
                'accession_id': 'SRP004',
                'species': 'Oryza sativa',
                'tissue': 'root',
                'treatment': 'drought',
                'replicates': 2
            },
            {
                'accession_id': 'SRP005',
                'species': 'Brassica rapa',
                'tissue': 'leaf',
                'treatment': '',  # Missing treatment
                'replicates': 5
            }
        ]

    @pytest.fixture
    def temp_manifest_file(self, sample_studies):
        """Create a temporary manifest file."""
        manifest_data = {
            'studies': sample_studies,
            'generated_at': '2024-01-01T00:00:00'
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(manifest_data, f)
            temp_path = Path(f.name)
        
        yield temp_path
        
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_check_replicates_inclusion(self, sample_studies):
        """Test that studies with sufficient replicates are included."""
        included, excluded = check_replicates(sample_studies, min_replicates=2)
        
        included_ids = [s['accession_id'] for s in included]
        excluded_ids = [e['accession_id'] for e in excluded]
        
        assert 'SRP001' in included_ids
        assert 'SRP004' in included_ids
        assert 'SRP002' in excluded_ids
        assert len(included) == 4
        assert len(excluded) == 1

    def test_check_replicates_exclusion_reason(self, sample_studies):
        """Test that excluded studies have correct exclusion reason."""
        included, excluded = check_replicates(sample_studies, min_replicates=2)
        
        assert len(excluded) == 1
        assert excluded[0]['species'] == 'Solanum lycopersicum'
        assert 'Insufficient biological replicates' in excluded[0]['exclusion_reason']
        assert '1 < 2' in excluded[0]['exclusion_reason']

    def test_check_metadata_completeness(self, sample_studies):
        """Test metadata completeness checking."""
        included, excluded = check_metadata_completeness(sample_studies)
        
        included_ids = [s['accession_id'] for s in included]
        excluded_ids = [e['accession_id'] for e in excluded]
        
        # SRP001 and SRP004 should pass
        assert 'SRP001' in included_ids
        assert 'SRP004' in included_ids
        
        # SRP003 (missing tissue) and SRP005 (missing treatment) should fail
        assert 'SRP003' in excluded_ids
        assert 'SRP005' in excluded_ids

    def test_check_metadata_completeness_empty_string(self, sample_studies):
        """Test that empty strings are treated as missing."""
        included, excluded = check_metadata_completeness(sample_studies)
        
        # SRP003 has empty tissue
        assert any(e['species'] == 'Zea mays' for e in excluded)
        assert any('tissue' in e['exclusion_reason'] for e in excluded if e['species'] == 'Zea mays')

    def test_run_qc_pipeline_full(self, sample_studies, temp_manifest_file, temp_output_dir):
        """Test the full QC pipeline execution."""
        output_path = temp_output_dir / 'post_qc_species_list.json'
        
        result = run_qc_pipeline(
            input_manifest_path=temp_manifest_file,
            output_path=output_path
        )
        
        # Verify output file exists
        assert output_path.exists()
        
        # Verify result structure
        assert 'generated_at' in result
        assert 'total_studies_processed' in result
        assert 'included_count' in result
        assert 'excluded_count' in result
        assert 'studies' in result
        
        # Verify counts
        assert result['total_studies_processed'] == 5
        # After replicate check: 4 remain (SRP002 excluded)
        # After metadata check: 2 remain (SRP003, SRP005 excluded)
        assert result['included_count'] == 2
        assert result['excluded_count'] == 3

    def test_run_qc_pipeline_output_format(self, sample_studies, temp_manifest_file, temp_output_dir):
        """Test that output file contains correct schema."""
        output_path = temp_output_dir / 'post_qc_species_list.json'
        
        run_qc_pipeline(
            input_manifest_path=temp_manifest_file,
            output_path=output_path
        )
        
        with open(output_path, 'r') as f:
            output_data = json.load(f)
        
        # Check each study entry has required fields
        for study in output_data['studies']:
            assert 'species' in study
            assert 'accession_id' in study
            assert 'exclusion_reason' in study
            assert 'included' in study
            
            if study['included']:
                assert study['exclusion_reason'] is None
            else:
                assert study['exclusion_reason'] is not None
                assert len(study['exclusion_reason']) > 0

    def test_run_qc_pipeline_no_manifest(self, temp_output_dir):
        """Test that pipeline fails gracefully when no manifest exists."""
        output_path = temp_output_dir / 'post_qc_species_list.json'
        
        with pytest.raises(FileNotFoundError, match="No data manifest found"):
            run_qc_pipeline(output_path=output_path)

    def test_run_qc_pipeline_with_synthetic_manifest(self, temp_output_dir):
        """Test pipeline with synthetic manifest structure."""
        synthetic_manifest = {
            'file_name': 'synthetic_study.json',
            'accession_id': 'SYNTH_001',
            'species': 'Arabidopsis thaliana',
            'tissue': 'leaf',
            'treatment': 'herbivory',
            'replicates': 3,
            'source_type': 'synthetic'
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(synthetic_manifest, f)
            temp_path = Path(f.name)
        
        try:
            output_path = temp_output_dir / 'post_qc_species_list.json'
            result = run_qc_pipeline(input_manifest_path=temp_path, output_path=output_path)
            
            assert result['included_count'] == 1
            assert result['excluded_count'] == 0
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_check_replicates_zero_replicates(self):
        """Test handling of zero replicates."""
        studies = [{'accession_id': 'X', 'replicates': 0, 'species': 'Test'}]
        included, excluded = check_replicates(studies)
        
        assert len(included) == 0
        assert len(excluded) == 1
        assert '0 < 2' in excluded[0]['exclusion_reason']

    def test_check_metadata_completeness_none_values(self):
        """Test handling of None values in metadata."""
        studies = [
            {'accession_id': 'X', 'species': None, 'tissue': 'leaf', 'treatment': 'herbivory', 'replicates': 2}
        ]
        included, excluded = check_metadata_completeness(studies)
        
        assert len(included) == 0
        assert len(excluded) == 1
        assert 'species' in excluded[0]['exclusion_reason']