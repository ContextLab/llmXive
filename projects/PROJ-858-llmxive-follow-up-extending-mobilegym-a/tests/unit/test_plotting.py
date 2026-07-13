import json
import os
import tempfile
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys_path = Path(__file__).resolve().parents[2]
if str(sys_path) not in __import__('sys').path:
    __import__('sys').path.insert(0, str(sys_path))

from analysis.plotting import (
    extract_plot_data,
    create_success_rate_vs_steps_plot,
    generate_convergence_plot
)


@pytest.fixture
def mock_convergence_results():
    """Create mock convergence results for testing."""
    return {
        "baseline": {
            "runs": [
                {"steps_to_target": 100, "final_success_rate": 0.4},
                {"steps_to_target": 150, "final_success_rate": 0.5},
                {"steps_to_target": 120, "final_success_rate": 0.45}
            ]
        },
        "experimental": {
            "runs": [
                {"steps_to_target": 60, "final_success_rate": 0.7},
                {"steps_to_target": 80, "final_success_rate": 0.75},
                {"steps_to_target": 70, "final_success_rate": 0.68}
            ]
        }
    }


@pytest.fixture
def temp_results_file(mock_convergence_results):
    """Create a temporary JSON file with mock results."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(mock_convergence_results, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def temp_output_file():
    """Create a temporary path for output plot."""
    fd, temp_path = tempfile.mkstemp(suffix='.png')
    os.close(fd)
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)


def test_extract_plot_data(mock_convergence_results):
    """Test extraction of plot data from convergence results."""
    baseline_steps, baseline_rates, experimental_steps, experimental_rates = extract_plot_data(mock_convergence_results)
    
    assert len(baseline_steps) == 3
    assert len(baseline_rates) == 3
    assert len(experimental_steps) == 3
    assert len(experimental_rates) == 3
    
    assert baseline_steps == [100, 150, 120]
    assert baseline_rates == [0.4, 0.5, 0.45]
    assert experimental_steps == [60, 80, 70]
    assert experimental_rates == [0.7, 0.75, 0.68]


def test_extract_plot_data_empty(mock_convergence_results):
    """Test extraction when one set of runs is empty."""
    mock_convergence_results['baseline']['runs'] = []
    
    baseline_steps, baseline_rates, experimental_steps, experimental_rates = extract_plot_data(mock_convergence_results)
    
    assert len(baseline_steps) == 0
    assert len(baseline_rates) == 0
    assert len(experimental_steps) == 3
    assert len(experimental_rates) == 3


def test_create_plot(temp_output_file, mock_convergence_results):
    """Test plot generation."""
    baseline_steps, baseline_rates, experimental_steps, experimental_rates = extract_plot_data(mock_convergence_results)
    
    output_path = create_success_rate_vs_steps_plot(
        baseline_steps,
        baseline_rates,
        experimental_steps,
        experimental_rates,
        temp_output_file,
        title="Test Plot"
    )
    
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0


def test_generate_plot_from_file(temp_results_file, temp_output_file):
    """Test end-to-end plot generation from file."""
    output_path = generate_convergence_plot(
        results_path=temp_results_file,
        output_path=temp_output_file
    )
    
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0
    assert output_path == temp_output_file


def test_generate_plot_missing_file():
    """Test error handling for missing results file."""
    with pytest.raises(FileNotFoundError):
        generate_convergence_plot(
            results_path="nonexistent_file.json",
            output_path="output.png"
        )