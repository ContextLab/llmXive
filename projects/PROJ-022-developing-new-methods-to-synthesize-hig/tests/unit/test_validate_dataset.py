import pytest
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the functions to test
from code.ingestion.validate_dataset import (
    count_valid_records,
    verify_high_performance_bio_membranes,
    generate_missing_data_report,
    validate_dataset
)

# Mock the get_polymer_class_from_smiles function for testing
@pytest.fixture
def mock_smiles_classifier():
    with patch('code.ingestion.validate_dataset.get_polymer_class_from_smiles') as mock_func:
        def side_effect(smiles):
            if 'cellulose' in smiles.lower():
                return 'cellulose'
            elif 'chitosan' in smiles.lower():
                return 'chitosan'
            elif 'lignin' in smiles.lower():
                return 'lignin'
            elif 'petro' in smiles.lower():
                return 'polyimide'
            else:
                return 'unknown'
        mock_func.side_effect = side_effect
        yield mock_func

@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe for testing."""
    data = {
        'smiles': [
            'cellulose_smiles_1', 'cellulose_smiles_2', 'chitosan_smiles_1',
            'lignin_smiles_1', 'petro_smiles_1', 'unknown_smiles_1',
            'cellulose_smiles_3', 'chitosan_smiles_2', 'lignin_smiles_2',
            'cellulose_smiles_4', 'cellulose_smiles_5', 'cellulose_smiles_6',
            'cellulose_smiles_7', 'cellulose_smiles_8', 'cellulose_smiles_9',
            'cellulose_smiles_10', 'cellulose_smiles_11', 'petro_smiles_2',
            'petro_smiles_3', 'petro_smiles_4', 'petro_smiles_5',
            'petro_smiles_6', 'petro_smiles_7', 'petro_smiles_8',
            'petro_smiles_9', 'petro_smiles_10', 'petro_smiles_11',
            'petro_smiles_12', 'petro_smiles_13', 'petro_smiles_14',
            'petro_smiles_15'  # 31 total rows
        ],
        'permeability_barrer': [100, 150, 200, 180, 500, np.nan, 120, 160, 190,
                                130, 140, 145, 155, 165, 175, 185, 195,
                                400, 410, 420, 430, 440, 450, 460, 470, 480, 490, 500, 510, 520, 530],
        'selectivity': [5.0, 6.0, 7.0, 6.5, 3.0, np.nan, 5.5, 6.2, 6.8,
                       5.8, 5.9, 5.95, 6.05, 6.15, 6.25, 6.35, 6.45,
                       2.5, 2.6, 2.7, 2.8, 2.9, 3.0, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8],
        'flux_lmh_bar': [10, 12, 15, 14, 5, np.nan, 11, 13, 14.5,
                        10.5, 11.5, 12, 12.5, 13, 13.5, 14, 14.5,
                        3, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 4.0, 4.1, 4.2, 4.3]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_dataframe_with_missing():
    """Create a sample dataframe with missing values."""
    data = {
        'smiles': ['polymer_1', 'polymer_2', 'polymer_3'],
        'permeability_barrer': [100, np.nan, 200],
        'selectivity': [np.nan, 6.0, 7.0],
        'flux_lmh_bar': [10, 12, np.nan]
    }
    return pd.DataFrame(data)

class TestCountValidRecords:
    def test_count_valid_records_all_present(self, sample_dataframe):
        """Test counting valid records when all have performance data."""
        count = count_valid_records(sample_dataframe)
        assert count == len(sample_dataframe)  # All 31 rows have at least one value

    def test_count_valid_records_with_missing(self, sample_dataframe_with_missing):
        """Test counting valid records with some missing values."""
        count = count_valid_records(sample_dataframe_with_missing)
        # All 3 rows have at least one non-null value
        assert count == 3

    def test_count_valid_records_empty_dataframe(self):
        """Test counting valid records on empty dataframe."""
        df = pd.DataFrame(columns=['permeability_barrer', 'selectivity'])
        count = count_valid_records(df)
        assert count == 0

class TestVerifyHighPerformanceBioMembranes:
    def test_verify_bio_membranes_count(self, sample_dataframe, mock_smiles_classifier):
        """Test counting high-performance bio-membranes."""
        count = verify_high_performance_bio_membranes(sample_dataframe)
        # We have 11 cellulose + 2 chitosan + 2 lignin = 15 bio-membranes with performance data
        assert count >= 10  # Should meet the threshold

    def test_verify_bio_membranes_no_smiles(self):
        """Test when SMILES column is missing."""
        df = pd.DataFrame({'permeability_barrer': [100, 200]})
        count = verify_high_performance_bio_membranes(df)
        assert count == 0

    def test_verify_bio_membranes_no_performance_data(self, mock_smiles_classifier):
        """Test when bio-membranes have no performance data."""
        data = {
            'smiles': ['cellulose_smiles_1', 'cellulose_smiles_2'],
            'permeability_barrer': [np.nan, np.nan],
            'selectivity': [np.nan, np.nan]
        }
        df = pd.DataFrame(data)
        count = verify_high_performance_bio_membranes(df)
        assert count == 0

class TestGenerateMissingDataReport:
    def test_generate_missing_data_report_creates_file(self, tmp_path, sample_dataframe_with_missing):
        """Test that the report file is created."""
        output_path = tmp_path / "missing_report.json"
        generate_missing_data_report(sample_dataframe_with_missing, str(output_path))
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            report = json.load(f)
        
        assert 'generated_at' in report
        assert 'total_records' in report
        assert 'missing_data_summary' in report

    def test_generate_missing_data_report_content(self, tmp_path, sample_dataframe_with_missing):
        """Test the content of the missing data report."""
        output_path = tmp_path / "missing_report.json"
        generate_missing_data_report(sample_dataframe_with_missing, str(output_path))
        
        with open(output_path, 'r') as f:
            report = json.load(f)
        
        # Check specific missing counts
        assert report['missing_data_summary']['permeability_barrer']['missing_count'] == 1
        assert report['missing_data_summary']['selectivity']['missing_count'] == 1
        assert report['missing_data_summary']['flux_lmh_bar']['missing_count'] == 1

class TestValidateDataset:
    def test_validate_dataset_passes(self, sample_dataframe, mock_smiles_classifier, tmp_path):
        """Test successful validation."""
        report_path = tmp_path / "missing_report.json"
        result = validate_dataset(
            sample_dataframe,
            min_valid_records=30,
            min_bio_membranes=10,
            missing_report_path=str(report_path)
        )
        
        assert result['valid'] is True
        assert result['checks']['min_valid_records']['passed'] is True
        assert result['checks']['min_bio_membranes']['passed'] is True
        assert report_path.exists()

    def test_validate_dataset_fails_low_records(self, tmp_path):
        """Test validation fails when records are too few."""
        data = {
            'smiles': ['polymer_1', 'polymer_2'],
            'permeability_barrer': [100, 200]
        }
        df = pd.DataFrame(data)
        report_path = tmp_path / "missing_report.json"
        
        result = validate_dataset(
            df,
            min_valid_records=30,
            missing_report_path=str(report_path)
        )
        
        assert result['valid'] is False
        assert result['checks']['min_valid_records']['passed'] is False

    def test_validate_dataset_fails_low_bio(self, sample_dataframe, mock_smiles_classifier, tmp_path):
        """Test validation fails when bio-membranes are too few."""
        # Modify dataframe to have fewer bio-membranes
        df = sample_dataframe.copy()
        # Change most SMILES to non-bio
        df['smiles'] = ['petro_smiles_' + str(i) for i in range(len(df))]
        
        report_path = tmp_path / "missing_report.json"
        result = validate_dataset(
            df,
            min_bio_membranes=10,
            missing_report_path=str(report_path)
        )
        
        assert result['valid'] is False
        assert result['checks']['min_bio_membranes']['passed'] is False