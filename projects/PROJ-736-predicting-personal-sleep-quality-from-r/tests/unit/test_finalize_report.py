"""
Unit tests for T038: Finalize Report functionality.
"""
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.modeling.finalize_report import verify_plot_file, finalize_report
from code.config import get_paths

def test_verify_plot_file_missing_path():
    """Test that verify_plot_file returns False if no path is provided."""
    report = {}
    assert verify_plot_file(report) is False

def test_verify_plot_file_missing_file():
    """Test that verify_plot_file returns False if file does not exist."""
    report = {'visualization': {'file_path': '/nonexistent/path.svg'}}
    assert verify_plot_file(report) is False

def test_verify_plot_file_valid_svg_low_edges():
    """Test SVG validation with low edge count (warning expected)."""
    # Create a temporary SVG with few edges
    with tempfile.NamedTemporaryFile(suffix='.svg', delete=False) as f:
        f.write(b'<svg><line x1="1" y1="1" x2="2" y2="2"/></svg>')
        temp_path = f.name

    try:
        report = {'visualization': {'file_path': temp_path}}
        # Should return True but log a warning (implementation detail)
        assert verify_plot_file(report) is True
    finally:
        os.unlink(temp_path)

def test_verify_plot_file_valid_png():
    """Test PNG validation (exists check only)."""
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        f.write(b'fake_png_data')
        temp_path = f.name

    try:
        report = {'visualization': {'file_path': temp_path}}
        assert verify_plot_file(report) is True
    finally:
        os.unlink(temp_path)

@patch('code.modeling.finalize_report.load_result_report')
@patch('code.modeling.finalize_report.load_model_metrics')
@patch('code.modeling.finalize_report.load_permutation_p_value')
@patch('code.modeling.finalize_report.load_bootstrap_ci')
@patch('code.modeling.finalize_report.load_sensitivity_results')
@patch('code.modeling.finalize_report.save_result_report')
@patch('code.modeling.finalize_report.get_paths')
def test_finalize_report_assembles_all(
    mock_get_paths, mock_save, mock_sens, mock_boot, mock_perm, mock_metrics, mock_load_report
):
    """Test that finalize_report aggregates all partial results."""
    
    # Setup mocks
    mock_load_report.return_value = {'metadata': {}}
    mock_metrics.return_value = {'r_squared': 0.5}
    mock_perm.return_value = 0.01
    mock_boot.return_value = {'ci_95': [0.4, 0.6]}
    mock_sens.return_value = {'grid': []}
    mock_get_paths.return_value = {'results': Path('/tmp/results')}
    mock_save.return_value = None

    # Ensure directory exists for the mock
    os.makedirs('/tmp/results', exist_ok=True)

    try:
        report = finalize_report()
        
        # Verify aggregation
        assert report['model_metrics']['r_squared'] == 0.5
        assert report['permutation_test']['p_value'] == 0.01
        assert report['bootstrap_ci']['ci_95'] == [0.4, 0.6]
        assert report['metadata']['manual_entry'] is False
        
        # Verify save was called
        mock_save.assert_called_once()
    finally:
        import shutil
        if os.path.exists('/tmp/results'):
            shutil.rmtree('/tmp/results')