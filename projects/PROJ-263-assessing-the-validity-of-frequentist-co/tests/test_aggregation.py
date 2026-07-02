import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np
import pandas as pd

from aggregation import (
    load_coverage_records,
    calculate_mean_deviation,
    create_aggregate_report,
    save_aggregate_report,
    run_aggregation_workflow
)
from data_models.schemas import AggregateReport


@pytest.fixture
def sample_coverage_records():
    """Generate sample coverage records for testing."""
    return [
        {"dataset_id": "wine", "sample_size": 10, "interval_type": "t", "contains_mean": True},
        {"dataset_id": "wine", "sample_size": 10, "interval_type": "t", "contains_mean": False},
        {"dataset_id": "wine", "sample_size": 10, "interval_type": "bootstrap", "contains_mean": True},
        {"dataset_id": "wine", "sample_size": 20, "interval_type": "t", "contains_mean": True},
        {"dataset_id": "ionosphere", "sample_size": 10, "interval_type": "t", "contains_mean": True},
        {"dataset_id": "ionosphere", "sample_size": 10, "interval_type": "t", "contains_mean": True},
        {"dataset_id": "ionosphere", "sample_size": 10, "interval_type": "t", "contains_mean": False},
        {"dataset_id": "ionosphere", "sample_size": 30, "interval_type": "bootstrap", "contains_mean": True},
    ]


@pytest.fixture
def mock_data_dirs(tmp_path):
    """Create temporary data directories with mock files."""
    data_dir = tmp_path / "data"
    processed_dir = data_dir / "processed"
    output_dir = tmp_path / "outputs"
    
    processed_dir.mkdir(parents=True)
    output_dir.mkdir(parents=True)
    
    return {
        "data_dir": str(data_dir),
        "output_dir": str(output_dir),
        "processed_dir": str(processed_dir)
    }


@pytest.fixture
def coverage_records_file(mock_data_dirs, sample_coverage_records):
    """Write sample coverage records to a file."""
    records_path = Path(mock_data_dirs["processed_dir"]) / "coverage_records.json"
    with open(records_path, 'w') as f:
        json.dump(sample_coverage_records, f)
    return records_path


@pytest.fixture
def population_means_file(mock_data_dirs):
    """Write mock population means to a file."""
    means_path = Path(mock_data_dirs["processed_dir"]) / "population_means.json"
    means_data = {
        "wine": {"alcohol": 10.42, "malic_acid": 2.33},
        "ionosphere": {"radar_signal": 0.45}
    }
    with open(means_path, 'w') as f:
        json.dump(means_data, f)
    return means_path


def test_calculate_mean_deviation(sample_coverage_records):
    """Test the mean deviation calculation logic."""
    result = calculate_mean_deviation(sample_coverage_records, nominal_coverage=0.95)
    
    assert 'nominal_coverage' in result
    assert 'overall_mean_deviation' in result
    assert 'overall_abs_mean_deviation' in result
    assert 'coverage_by_configuration' in result
    assert 'detailed_coverage_rates' in result
    
    assert result['nominal_coverage'] == 0.95
    assert result['total_records'] == len(sample_coverage_records)
    assert result['total_datasets'] == 2  # wine and ionosphere
    
    # Check that deviation is calculated correctly
    assert isinstance(result['overall_mean_deviation'], float)
    assert isinstance(result['overall_abs_mean_deviation'], float)


def test_calculate_mean_deviation_empty_records():
    """Test that empty records raise an error."""
    with pytest.raises(ValueError, match="No coverage records provided"):
        calculate_mean_deviation([])


def test_calculate_mean_deviation_missing_column(sample_coverage_records):
    """Test that missing contains_mean column raises an error."""
    bad_records = [{"dataset_id": "test", "sample_size": 10}]
    with pytest.raises(ValueError, match="missing 'contains_mean' column"):
        calculate_mean_deviation(bad_records)


def test_create_aggregate_report(sample_coverage_records):
    """Test aggregate report creation."""
    deviation_results = calculate_mean_deviation(sample_coverage_records)
    report = create_aggregate_report(deviation_results)
    
    assert isinstance(report, dict) or hasattr(report, '__getitem__')
    assert report['report_type'] == 'coverage_aggregation'
    assert 'timestamp' in report
    assert report['datasets_included'] == 2


def test_save_aggregate_report(sample_coverage_records, mock_data_dirs):
    """Test saving the aggregate report."""
    deviation_results = calculate_mean_deviation(sample_coverage_records)
    report = create_aggregate_report(deviation_results)
    
    with patch('aggregation.get_output_dir', return_value=mock_data_dirs["output_dir"]):
        output_path = save_aggregate_report(report)
    
    assert os.path.exists(output_path)
    assert "aggregate_coverage_results.json" in output_path
    
    # Verify content
    with open(output_path, 'r') as f:
        saved_report = json.load(f)
    
    assert saved_report['report_type'] == 'coverage_aggregation'


@patch('aggregation.load_coverage_records')
@patch('aggregation.load_population_means')
@patch('aggregation.save_aggregate_report')
def test_run_aggregation_workflow(mock_save, mock_load_means, mock_load_records, sample_coverage_records, mock_data_dirs):
    """Test the full aggregation workflow."""
    mock_load_records.return_value = sample_coverage_records
    mock_load_means.return_value = {"wine": {}}
    mock_save.return_value = str(Path(mock_data_dirs["output_dir"]) / "aggregate_coverage_results.json")
    
    with patch('aggregation.get_data_dir', return_value=mock_data_dirs["data_dir"]):
        with patch('aggregation.get_output_dir', return_value=mock_data_dirs["output_dir"]):
            report = run_aggregation_workflow(nominal_coverage=0.95)
    
    assert report is not None
    assert report['nominal_coverage'] == 0.95
    mock_load_records.assert_called_once()
    mock_load_means.assert_called_once()
    mock_save.assert_called_once()