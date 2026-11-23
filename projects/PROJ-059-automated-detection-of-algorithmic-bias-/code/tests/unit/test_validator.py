"""
Unit tests for the validator module (User Story 4).

These tests verify:
- Loading validation dataset
- Running VADER validation
- Threshold validation logic
- Pipeline execution
"""
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import json
import sys
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.bias_pipeline.validator import (
    load_validation_dataset,
    run_vader_validation,
    validate_threshold,
    run_validation_pipeline
)
from src.bias_pipeline.error_handler import ExecutionError

@pytest.fixture
def sample_validation_data():
    """Create a temporary CSV with sample validation data."""
    data = [
        {'comment': 'This code is terrible and buggy.', 'label': 0},
        {'comment': 'Great work on this implementation!', 'label': 1},
        {'comment': 'The variable naming is confusing.', 'label': 0},
        {'comment': 'Excellent performance optimization.', 'label': 1},
        {'comment': 'This is a mess.', 'label': 0},
    ]
    return pd.DataFrame(data)

@pytest.fixture
def temp_csv_file(sample_validation_data):
    """Create a temporary CSV file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_validation_data.to_csv(f, index=False)
        return Path(f.name)

class TestLoadValidationDataset:
    """Tests for load_validation_dataset function."""
    
    def test_load_valid_dataset(self, temp_csv_file, sample_validation_data):
        """Test loading a valid dataset."""
        df = load_validation_dataset(temp_csv_file)
        assert len(df) == len(sample_validation_data)
        assert 'comment' in df.columns
        assert 'label' in df.columns
        
        # Check labels are 0 or 1
        assert df['label'].isin([0, 1]).all()
    
    def test_load_missing_file(self):
        """Test loading a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_validation_dataset(Path("non_existent_file.csv"))
    
    def test_load_missing_columns(self, temp_csv_file):
        """Test loading a file with missing columns raises ValueError."""
        # Create a file with wrong columns
        wrong_data = pd.DataFrame({'wrong_col': [1, 2, 3]})
        wrong_data.to_csv(temp_csv_file, index=False)
        
        with pytest.raises(ValueError):
            load_validation_dataset(temp_csv_file)
    
    def test_load_invalid_labels(self, temp_csv_file):
        """Test loading a file with invalid labels raises ValueError."""
        # Create a file with invalid labels
        invalid_data = pd.DataFrame({
            'comment': ['test'],
            'label': [2]  # Invalid label
        })
        invalid_data.to_csv(temp_csv_file, index=False)
        
        with pytest.raises(ValueError):
            load_validation_dataset(temp_csv_file)

class TestRunVaderValidation:
    """Tests for run_vader_validation function."""
    
    @patch('src.bias_pipeline.validator.analyze_sentiment')
    def test_vader_validation_computation(self, mock_analyze_sentiment, sample_validation_data):
        """Test VADER validation computes correct Kappa."""
        # Mock VADER to return fixed sentiment scores
        mock_analyze_sentiment.side_effect = [
            {'compound': -0.5},  # Negative -> 0
            {'compound': 0.8},   # Positive -> 1
            {'compound': -0.3},  # Negative -> 0
            {'compound': 0.9},   # Positive -> 1
            {'compound': -0.6},  # Negative -> 0
        ]
        
        kappa, results = run_vader_validation(sample_validation_data)
        
        assert isinstance(kappa, float)
        assert 0 <= kappa <= 1
        assert 'kappa_score' in results
        assert results['n_samples'] == 5
        
        # Check predictions match expected
        expected_predictions = [0, 1, 0, 1, 0]
        assert results['predictions'] == expected_predictions
    
    def test_vader_validation_empty_dataframe(self):
        """Test VADER validation on empty dataframe raises ValueError."""
        empty_df = pd.DataFrame(columns=['comment', 'label'])
        
        with pytest.raises(ValueError):
            run_vader_validation(empty_df)

class TestValidateThreshold:
    """Tests for validate_threshold function."""
    
    def test_validate_pass(self):
        """Test validation passes when Kappa >= threshold."""
        result = validate_threshold(0.7, threshold=0.6)
        assert result is True
    
    def test_validate_fail(self):
        """Test validation fails when Kappa < threshold."""
        with pytest.raises(ExecutionError):
            validate_threshold(0.5, threshold=0.6)
    
    def test_validate_exact_threshold(self):
        """Test validation passes when Kappa == threshold."""
        result = validate_threshold(0.6, threshold=0.6)
        assert result is True

class TestValidationPipeline:
    """Tests for run_validation_pipeline function."""
    
    @patch('src.bias_pipeline.validator.analyze_sentiment')
    def test_full_pipeline_success(self, mock_analyze_sentiment, temp_csv_file):
        """Test full pipeline runs successfully."""
        # Mock VADER to return scores that result in high Kappa
        mock_analyze_sentiment.side_effect = [
            {'compound': -0.5},
            {'compound': 0.8},
            {'compound': -0.3},
            {'compound': 0.9},
            {'compound': -0.6},
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "results.json"
            
            result = run_validation_pipeline(
                data_path=temp_csv_file,
                output_path=output_path
            )
            
            assert result['status'] == 'PASSED'
            assert 'kappa_score' in result
            assert output_path.exists()
    
    @patch('src.bias_pipeline.validator.analyze_sentiment')
    def test_full_pipeline_failure(self, mock_analyze_sentiment, temp_csv_file):
        """Test full pipeline fails when Kappa < threshold."""
        # Mock VADER to return scores that result in low Kappa
        mock_analyze_sentiment.side_effect = [
            {'compound': 0.5},  # Positive but should be negative
            {'compound': -0.5}, # Negative but should be positive
            {'compound': 0.5},
            {'compound': -0.5},
            {'compound': 0.5},
        ]
        
        with pytest.raises(ExecutionError):
            run_validation_pipeline(data_path=temp_csv_file)
    
    def test_pipeline_missing_data(self):
        """Test pipeline fails when data is missing."""
        with pytest.raises(FileNotFoundError):
            run_validation_pipeline(data_path=Path("non_existent.csv"))