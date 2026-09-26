import json
import pytest
import tempfile
from pathlib import Path

from src.data.qc import (
    check_replicates,
    check_metadata_completeness,
    run_qc_pipeline,
    save_post_qc_species_list
)


class TestQCPipeline:
    """Unit tests for QC pipeline functions."""

    def test_check_replicates_sufficient(self):
        """Test that studies with sufficient replicates pass."""
        study = {'replicates': 3}
        is_valid, reason = check_replicates(study)
        assert is_valid is True
        assert reason is None

    def test_check_replicates_insufficient(self):
        """Test that studies with insufficient replicates fail."""
        study = {'replicates': 1}
        is_valid, reason = check_replicates(study)
        assert is_valid is False
        assert 'Insufficient replicates' in reason

    def test_check_replicates_missing(self):
        """Test that studies with missing replicate count fail."""
        study = {}
        is_valid, reason = check_replicates(study)
        assert is_valid is False
        assert 'Missing replicate count' in reason

    def test_check_metadata_completeness_complete(self):
        """Test that studies with complete metadata pass."""
        study = {'species': 'Arabidopsis thaliana', 'tissue': 'leaf', 'treatment': 'herbivory'}
        is_valid, reason = check_metadata_completeness(study)
        assert is_valid is True
        assert reason is None

    def test_check_metadata_completeness_missing_species(self):
        """Test that studies with missing species fail."""
        study = {'tissue': 'leaf', 'treatment': 'herbivory'}
        is_valid, reason = check_metadata_completeness(study)
        assert is_valid is False
        assert 'Missing or empty metadata field: species' in reason

    def test_check_metadata_completeness_empty_tissue(self):
        """Test that studies with empty tissue fail."""
        study = {'species': 'Arabidopsis thaliana', 'tissue': '', 'treatment': 'herbivory'}
        is_valid, reason = check_metadata_completeness(study)
        assert is_valid is False
        assert 'Missing or empty metadata field: tissue' in reason

    def test_run_qc_pipeline(self):
        """Test the full QC pipeline."""
        # Create a temporary verification report
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            report_path = tmpdir_path / 'metadata_verification_report.json'
            
            report_data = {
                'studies': [
                    {
                        'accession_id': 'SRP001',
                        'species': 'Arabidopsis thaliana',
                        'tissue': 'leaf',
                        'treatment': 'herbivory',
                        'replicates': 3,
                        'exclusion_reason': None
                    },
                    {
                        'accession_id': 'SRP002',
                        'species': 'Solanum lycopersicum',
                        'tissue': 'leaf',
                        'treatment': 'herbivory',
                        'replicates': 1,
                        'exclusion_reason': None
                    },
                    {
                        'accession_id': 'SRP003',
                        'species': 'Zea mays',
                        'tissue': 'leaf',
                        'treatment': 'herbivory',
                        'replicates': 2,
                        'exclusion_reason': 'Missing tissue metadata'
                    }
                ]
            }
            
            with open(report_path, 'w') as f:
                json.dump(report_data, f)
            
            # Run QC pipeline
            results = run_qc_pipeline(report_path)
            
            # Verify results
            assert 'Arabidopsis thaliana' in results['included_species']
            assert 'Solanum lycopersicum' not in results['included_species']
            assert 'Zea mays' not in results['included_species']
            
            assert len(results['exclusions']) == 2
            assert results['exclusions'][0]['species'] == 'Solanum lycopersicum'
            assert 'Insufficient replicates' in results['exclusions'][0]['reason']
            assert results['exclusions'][1]['species'] == 'Zea mays'
            assert 'Missing tissue metadata' in results['exclusions'][1]['reason']

    def test_save_post_qc_species_list(self):
        """Test saving the post-QC species list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            output_path = tmpdir_path / 'post_qc_species_list.json'
            
            results = {
                'included_species': ['Arabidopsis thaliana'],
                'exclusions': [
                    {'species': 'Solanum lycopersicum', 'reason': 'Insufficient replicates'}
                ]
            }
            
            save_post_qc_species_list(results, output_path)
            
            # Verify file was created
            assert output_path.exists()
            
            # Verify contents
            with open(output_path, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data == results