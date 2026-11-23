"""
Unit tests for dataset availability verification.
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.exceptions import E_DATASET
from code.data.verify_availability import (
    check_geo_availability,
    check_metabolomics_availability,
    generate_availability_report,
    main
)

class TestGeoAvailability:
    """Tests for GEO dataset availability checking."""

    @patch('code.data.verify_availability.search_geo')
    def test_geo_available(self, mock_search):
        """Test successful GEO availability check."""
        mock_search.return_value = [{
            'organism': 'Arabidopsis thaliana',
            'title': 'Herbivore stress response in Arabidopsis',
            'description': 'Insect feeding experiment',
            'sample_count': 24,
            'samples': list(range(24))
        }]

        result = check_geo_availability('GSE21857', 'Arabidopsis thaliana', 'herbivore stress')

        assert result['found'] is True
        assert result['status'] == 'available'
        assert result['organism_match'] is True
        assert result['condition_match'] is True
        assert result['sample_count'] == 24

    @patch('code.data.verify_availability.search_geo')
    def test_geo_not_found(self, mock_search):
        """Test GEO dataset not found."""
        mock_search.return_value = []

        result = check_geo_availability('GSE99999', 'Arabidopsis thaliana', 'herbivore stress')

        assert result['found'] is False
        assert result['status'] == 'not_found'
        assert 'not found' in result['error'].lower()

    @patch('code.data.verify_availability.search_geo')
    def test_geo_wrong_organism(self, mock_search):
        """Test GEO dataset with wrong organism."""
        mock_search.return_value = [{
            'organism': 'Homo sapiens',
            'title': 'Human disease study',
            'description': 'Medical research',
            'sample_count': 50,
            'samples': list(range(50))
        }]

        result = check_geo_availability('GSE12345', 'Arabidopsis thaliana', 'herbivore stress')

        assert result['found'] is True
        assert result['status'] == 'wrong_organism'
        assert result['organism_match'] is False

    @patch('code.data.verify_availability.search_geo')
    def test_geo_insufficient_samples(self, mock_search):
        """Test GEO dataset with insufficient samples."""
        mock_search.return_value = [{
            'organism': 'Arabidopsis thaliana',
            'title': 'Herbivore stress response',
            'description': 'Insect feeding',
            'sample_count': 3,
            'samples': list(range(3))
        }]

        result = check_geo_availability('GSE12345', 'Arabidopsis thaliana', 'herbivore stress')

        assert result['found'] is True
        assert result['status'] == 'insufficient_samples'
        assert result['sample_count'] == 3

class TestMetabolomicsAvailability:
    """Tests for Metabolomics Workbench availability checking."""

    @patch('code.data.verify_availability.fetch_study_metadata')
    def test_metabolomics_available(self, mock_fetch):
        """Test successful Metabolomics Workbench availability check."""
        mock_fetch.return_value = {
            'sample_count': 48,
            'samples': list(range(48)),
            'has_raw_data': True,
            'has_processed_data': True
        }

        result = check_metabolomics_availability('ST002565')

        assert result['found'] is True
        assert result['status'] == 'available'
        assert result['sample_count'] == 48
        assert result['has_metabolite_data'] is True

    @patch('code.data.verify_availability.fetch_study_metadata')
    def test_metabolomics_not_found(self, mock_fetch):
        """Test Metabolomics Workbench study not found."""
        mock_fetch.return_value = None

        result = check_metabolomics_availability('ST99999')

        assert result['found'] is False
        assert result['status'] == 'not_found'
        assert 'not found' in result['error'].lower()

    @patch('code.data.verify_availability.fetch_study_metadata')
    def test_metabolomics_insufficient_samples(self, mock_fetch):
        """Test Metabolomics Workbench with insufficient samples."""
        mock_fetch.return_value = {
            'sample_count': 2,
            'samples': list(range(2)),
            'has_raw_data': True,
            'has_processed_data': True
        }

        result = check_metabolomics_availability('ST12345')

        assert result['found'] is True
        assert result['status'] == 'insufficient_samples'
        assert result['sample_count'] == 2

class TestReportGeneration:
    """Tests for report generation."""

    def test_generate_report_all_available(self):
        """Test report generation when all datasets are available."""
        results = [
            {
                'accession_id': 'GSE21857',
                'source': 'GEO',
                'status': 'available',
                'found': True,
                'organism_match': True,
                'condition_match': True,
                'sample_count': 24,
                'error': None,
                'details': {}
            },
            {
                'accession_id': 'ST002565',
                'source': 'Metabolomics Workbench',
                'status': 'available',
                'found': True,
                'sample_count': 48,
                'has_metabolite_data': True,
                'error': None,
                'details': {}
            }
        ]

        report = generate_availability_report(results)

        assert 'Dataset Availability Report' in report
        assert 'All required datasets are available' in report
        assert 'GSE21857' in report
        assert 'ST002565' in report
        assert 'ABORT' not in report

    def test_generate_report_some_unavailable(self):
        """Test report generation when some datasets are unavailable."""
        results = [
            {
                'accession_id': 'GSE21857',
                'source': 'GEO',
                'status': 'not_found',
                'found': False,
                'organism_match': False,
                'condition_match': False,
                'sample_count': 0,
                'error': 'Study not found',
                'details': {}
            }
        ]

        report = generate_availability_report(results)

        assert 'Dataset Availability Report' in report
        assert 'ABORT TRIGGERED' in report
        assert 'E-DATASET' in report

class TestMainFunction:
    """Tests for main function."""

    @patch('code.data.verify_availability.search_geo')
    @patch('code.data.verify_availability.fetch_study_metadata')
    @patch('builtins.open')
    def test_main_all_available(self, mock_open, mock_fetch, mock_search):
        """Test main function when all datasets are available."""
        mock_search.return_value = [
            {
                'organism': 'Arabidopsis thaliana',
                'title': 'Herbivore stress',
                'description': 'Insect feeding',
                'sample_count': 24,
                'samples': list(range(24))
            },
            {
                'organism': 'Solanum lycopersicum',
                'title': 'Herbivore stress',
                'description': 'Insect feeding',
                'sample_count': 36,
                'samples': list(range(36))
            }
        ]
        mock_fetch.return_value = {
            'sample_count': 48,
            'samples': list(range(48)),
            'has_raw_data': True,
            'has_processed_data': True
        }

        # Should not raise E_DATASET
        results = main()

        assert len(results) == 3
        assert all(r['status'] == 'available' for r in results)

    @patch('code.data.verify_availability.search_geo')
    @patch('code.data.verify_availability.fetch_study_metadata')
    def test_main_dataset_not_found(self, mock_fetch, mock_search):
        """Test main function raises E_DATASET when dataset not found."""
        mock_search.return_value = []  # No results
        mock_fetch.return_value = None

        with pytest.raises(E_DATASET, match="Dataset availability check failed"):
            main()