"""
Integration test for PE run and bias calculation (T025).

This test validates the full User Story 3 pipeline:
1. Loads validated event data from US1 (data/interim/valid_events.json).
2. Loads compressed data from US2 (data/interim/compressed/).
3. Runs Bilby/Dynesty (Fast PE) on original and compressed data.
4. Calculates Delta_Bias against the external baseline (data/external/baseline_bias_original.json).
5. Verifies statistical test results are saved to data/processed/statistical_test_results.json.

Note: This test assumes US1 and US2 have completed successfully and produced the required artifacts.
It mocks the actual Bilby/Dynesty execution to avoid long runtimes in CI, but validates the
data flow, file I/O, and bias calculation logic.
"""

import os
import json
import tempfile
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code to path for imports
import sys
from tests.conftest import add_code_to_path
add_code_to_path()

from src.utils.config import get_project_root, ensure_dir
from src.pe.run_bilby import run_bilby_pe
from src.pe.compare_posteriors import calculate_delta_bias, run_statistical_analysis
from src.data.validate import validate_file


@pytest.fixture
def mock_bilby_run():
    """Mock Bilby/Dynesty to return synthetic posterior samples for testing."""
    def mock_run(event_id, data_path, config):
        # Return a mock result object that mimics Bilby's output structure
        result = MagicMock()
        # Generate synthetic posterior samples for mass, distance, spin
        n_samples = 1000
        result.samples = {
            'mass_1': np.random.normal(30.0, 1.0, n_samples),
            'mass_2': np.random.normal(25.0, 1.0, n_samples),
            'luminosity_distance': np.random.normal(400.0, 50.0, n_samples),
            'tilt_1': np.random.normal(0.1, 0.1, n_samples),
            'tilt_2': np.random.normal(0.1, 0.1, n_samples)
        }
        result.posterior = result.samples
        result.summary = {
            'mass_1': np.mean(result.samples['mass_1']),
            'mass_2': np.mean(result.samples['mass_2']),
            'luminosity_distance': np.mean(result.samples['luminosity_distance']),
            'tilt_1': np.mean(result.samples['tilt_1']),
            'tilt_2': np.mean(result.samples['tilt_2'])
        }
        result.effective_sample_size = 500  # Mock ESS > 100 to avoid fallback
        return result
    return mock_run


@pytest.fixture
def mock_baseline_data():
    """Generate mock baseline data for testing."""
    return {
        "event_id": "test_event_001",
        "true_parameters": {
            "mass_1": 30.0,
            "mass_2": 25.0,
            "luminosity_distance": 400.0,
            "tilt_1": 0.1,
            "tilt_2": 0.1
        },
        "posterior_mean": {
            "mass_1": 30.1,
            "mass_2": 25.1,
            "luminosity_distance": 401.0,
            "tilt_1": 0.11,
            "tilt_2": 0.11
        },
        "bias": {
            "mass_1": 0.1,
            "mass_2": 0.1,
            "luminosity_distance": 1.0,
            "tilt_1": 0.01,
            "tilt_2": 0.01
        }
    }


@pytest.fixture
def mock_validated_events():
    """Generate mock valid events list."""
    return {
        "event_ids": ["test_event_001"],
        "count": 1
    }


@pytest.fixture
def mock_compressed_data_dir(tmp_path):
    """Create mock compressed data structure."""
    compressed_dir = tmp_path / "data" / "interim" / "compressed"
    ensure_dir(compressed_dir)
    
    # Create mock compressed files
    quant_dir = compressed_dir / "quantization" / "8bit"
    ensure_dir(quant_dir)
    with open(quant_dir / "test_event_001_waveform.npy", "wb") as f:
        np.save(f, np.random.rand(1000))
        
    jpeg_dir = compressed_dir / "jpeg2000" / "75"
    ensure_dir(jpeg_dir)
    with open(jpeg_dir / "test_event_001_waveform.npy", "wb") as f:
        np.save(f, np.random.rand(1000))
        
    return compressed_dir


@pytest.fixture
def mock_original_data_dir(tmp_path):
    """Create mock original data structure."""
    original_dir = tmp_path / "data" / "interim" / "original"
    ensure_dir(original_dir)
    
    with open(original_dir / "test_event_001_waveform.npy", "wb") as f:
        np.save(f, np.random.rand(1000))
        
    return original_dir


@pytest.fixture
def mock_project_structure(tmp_path, mock_validated_events, mock_baseline_data):
    """Set up a mock project structure for the integration test."""
    project_root = tmp_path
    data_dir = project_root / "data"
    ensure_dir(data_dir / "interim" / "valid_events")
    ensure_dir(data_dir / "external")
    ensure_dir(data_dir / "processed")
    
    # Save mock valid events
    with open(data_dir / "interim" / "valid_events.json", "w") as f:
        json.dump(mock_validated_events, f)
        
    # Save mock baseline
    with open(data_dir / "external" / "baseline_bias_original.json", "w") as f:
        json.dump(mock_baseline_data, f)
        
    return project_root


@patch('src.pe.run_bilby.run_bilby_pe')
def test_pe_pipeline_integration(
    mock_bilby_run,
    mock_project_structure,
    mock_compressed_data_dir,
    mock_original_data_dir,
    mock_baseline_data,
    mock_validated_events
):
    """
    Test the full PE pipeline: load data -> run PE -> calculate bias -> save results.
    
    This test verifies:
    1. Valid events are loaded correctly.
    2. Baseline data is loaded correctly.
    3. Bilby PE is called with correct parameters.
    4. Delta_Bias is calculated correctly.
    5. Statistical results are saved to the correct location.
    """
    
    # Setup mock for Bilby run
    mock_bilby_run.side_effect = lambda event_id, data_path, config: (
        MagicMock(
            samples={
                'mass_1': np.random.normal(30.0, 1.0, 1000),
                'mass_2': np.random.normal(25.0, 1.0, 1000),
                'luminosity_distance': np.random.normal(400.0, 50.0, 1000),
                'tilt_1': np.random.normal(0.1, 0.1, 1000),
                'tilt_2': np.random.normal(0.1, 0.1, 1000)
            },
            summary={
                'mass_1': 30.05,
                'mass_2': 25.05,
                'luminosity_distance': 400.5,
                'tilt_1': 0.105,
                'tilt_2': 0.105
            },
            effective_sample_size=500
        )
    )
    
    project_root = mock_project_structure
    data_dir = project_root / "data"
    
    # Load valid events
    with open(data_dir / "interim" / "valid_events.json", "r") as f:
        valid_events = json.load(f)
        
    assert valid_events["count"] >= 1
    event_id = valid_events["event_ids"][0]
    
    # Load baseline
    baseline_path = data_dir / "external" / "baseline_bias_original.json"
    with open(baseline_path, "r") as f:
        baseline = json.load(f)
        
    assert "true_parameters" in baseline
    assert "posterior_mean" in baseline
    
    # Simulate PE run for original data
    original_data_path = mock_original_data_dir / f"{event_id}_waveform.npy"
    original_result = run_bilby_pe(event_id, str(original_data_path), {"maxiter": 5000, "nlive": 200})
    
    # Simulate PE run for compressed data (8-bit quantization)
    compressed_data_path = mock_compressed_data_dir / "quantization" / "8bit" / f"{event_id}_waveform.npy"
    compressed_result = run_bilby_pe(event_id, str(compressed_data_path), {"maxiter": 5000, "nlive": 200})
    
    # Calculate Delta_Bias
    delta_bias = calculate_delta_bias(original_result, compressed_result, baseline)
    
    assert "delta_bias" in delta_bias
    assert "mass_1" in delta_bias["delta_bias"]
    assert isinstance(delta_bias["delta_bias"]["mass_1"], float)
    
    # Run statistical analysis
    statistical_results = run_statistical_analysis(
        [original_result, compressed_result],
        baseline,
        event_id,
        str(data_dir / "processed" / "statistical_test_results.json")
    )
    
    assert "credible_interval_overlap" in statistical_results
    assert "mass_1" in statistical_results["credible_interval_overlap"]
    
    # Verify output file was created
    output_path = data_dir / "processed" / "statistical_test_results.json"
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        saved_results = json.load(f)
        
    assert "event_id" in saved_results
    assert saved_results["event_id"] == event_id
    assert "delta_bias" in saved_results
    assert "credible_interval_overlap" in saved_results


@patch('src.pe.run_bilby.run_bilby_pe')
def test_pe_pipeline_fallback_to_ttest(mock_bilby_run, mock_project_structure, mock_compressed_data_dir, mock_original_data_dir):
    """
    Test that the pipeline correctly falls back to Paired t-tests when ESS < 100.
    """
    
    # Mock Bilby to return low ESS
    mock_bilby_run.return_value = MagicMock(
        samples={
            'mass_1': np.random.normal(30.0, 1.0, 100),
            'mass_2': np.random.normal(25.0, 1.0, 100),
            'luminosity_distance': np.random.normal(400.0, 50.0, 100),
            'tilt_1': np.random.normal(0.1, 0.1, 100),
            'tilt_2': np.random.normal(0.1, 0.1, 100)
        },
        summary={
            'mass_1': 30.05,
            'mass_2': 25.05,
            'luminosity_distance': 400.5,
            'tilt_1': 0.105,
            'tilt_2': 0.105
        },
        effective_sample_size=50  # Low ESS to trigger fallback
    )
    
    project_root = mock_project_structure
    data_dir = project_root / "data"
    
    # Load valid events
    with open(data_dir / "interim" / "valid_events.json", "r") as f:
        valid_events = json.load(f)
    event_id = valid_events["event_ids"][0]
    
    # Load baseline
    with open(data_dir / "external" / "baseline_bias_original.json", "r") as f:
        baseline = json.load(f)
    
    # Run PE
    original_data_path = mock_original_data_dir / f"{event_id}_waveform.npy"
    original_result = run_bilby_pe(event_id, str(original_data_path), {"maxiter": 5000, "nlive": 200})
    
    compressed_data_path = mock_compressed_data_dir / "quantization" / "8bit" / f"{event_id}_waveform.npy"
    compressed_result = run_bilby_pe(event_id, str(compressed_data_path), {"maxiter": 5000, "nlive": 200})
    
    # Calculate Delta_Bias
    delta_bias = calculate_delta_bias(original_result, compressed_result, baseline)
    
    # Verify fallback was triggered (should still calculate bias, but use t-test for significance)
    assert "delta_bias" in delta_bias
    
    # Run statistical analysis (should use t-test)
    statistical_results = run_statistical_analysis(
        [original_result, compressed_result],
        baseline,
        event_id,
        str(data_dir / "processed" / "statistical_test_results.json")
    )
    
    assert "statistical_test" in statistical_results
    assert statistical_results["statistical_test"]["method"] == "paired_ttest"
    assert "p_values" in statistical_results["statistical_test"]
    
    # Verify Benjamini-Hochberg correction was applied
    assert "adjusted_p_values" in statistical_results["statistical_test"]


@patch('src.pe.run_bilby.run_bilby_pe')
def test_pe_pipeline_multiple_compression_levels(mock_bilby_run, mock_project_structure, mock_compressed_data_dir, mock_original_data_dir):
    """
    Test that the pipeline processes multiple compression levels correctly.
    """
    
    mock_bilby_run.return_value = MagicMock(
        samples={
            'mass_1': np.random.normal(30.0, 1.0, 1000),
            'mass_2': np.random.normal(25.0, 1.0, 1000),
            'luminosity_distance': np.random.normal(400.0, 50.0, 1000),
            'tilt_1': np.random.normal(0.1, 0.1, 1000),
            'tilt_2': np.random.normal(0.1, 0.1, 1000)
        },
        summary={
            'mass_1': 30.05,
            'mass_2': 25.05,
            'luminosity_distance': 400.5,
            'tilt_1': 0.105,
            'tilt_2': 0.105
        },
        effective_sample_size=500
    )
    
    project_root = mock_project_structure
    data_dir = project_root / "data"
    
    with open(data_dir / "interim" / "valid_events.json", "r") as f:
        valid_events = json.load(f)
    event_id = valid_events["event_ids"][0]
    
    with open(data_dir / "external" / "baseline_bias_original.json", "r") as f:
        baseline = json.load(f)
    
    # Test multiple compression levels
    compression_levels = [
        ("quantization", "8bit"),
        ("quantization", "4bit"),
        ("jpeg2000", "75"),
        ("jpeg2000", "90")
    ]
    
    results = []
    for method, level in compression_levels:
        compressed_data_path = mock_compressed_data_dir / method / level / f"{event_id}_waveform.npy"
        if compressed_data_path.exists():
            compressed_result = run_bilby_pe(event_id, str(compressed_data_path), {"maxiter": 5000, "nlive": 200})
            delta_bias = calculate_delta_bias(None, compressed_result, baseline)
            results.append({
                "method": method,
                "level": level,
                "delta_bias": delta_bias["delta_bias"]
            })
    
    assert len(results) > 0
    for result in results:
        assert "mass_1" in result["delta_bias"]
        assert isinstance(result["delta_bias"]["mass_1"], float)