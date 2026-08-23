import os
import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the module under test using the API surface
from report import (
    load_results,
    generate_correlation_plot,
    generate_pdf
)

@pytest.fixture
def mock_results_dir(tmp_path):
    """Create a mock results directory with required JSON files."""
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    
    # Create correlation results
    corr_results = {
        'motif_0': {
            'pearson_r': 0.45,
            'pearson_p': 0.02,
            'spearman_r': 0.48,
            'spearman_p': 0.015,
            'bonferroni_p': 0.26,
            'significant': False
        },
        'motif_1': {
            'pearson_r': 0.65,
            'pearson_p': 0.001,
            'spearman_r': 0.68,
            'spearman_p': 0.0005,
            'bonferroni_p': 0.013,
            'significant': True
        }
    }
    
    with open(results_dir / 'correlation_results.json', 'w') as f:
        json.dump(corr_results, f)
    
    # Create permutation results
    perm_results = [
        {
            'motif_id': 'motif_1',
            'empirical_p': 0.012,
            'original_r': 0.65
        }
    ]
    
    with open(results_dir / 'permutation_results.json', 'w') as f:
        json.dump(perm_results, f)
    
    # Create power analysis results
    power_results = {
        'min_detectable_r': 0.35,
        'power_level': 0.80,
        'adjusted_alpha': 0.0038,
        'n_subjects': 50,
        'statsmodels_version': '0.13.2',
        'seed': 42
    }
    
    with open(results_dir / 'power_analysis.json', 'w') as f:
        json.dump(power_results, f)
    
    return results_dir

@pytest.fixture
def mock_layout_template(tmp_path):
    """Create a mock layout template file."""
    template = {
        "pages": [
            {
                "type": "title",
                "elements": [
                    {"type": "text", "source_field": "title"}
                ]
            },
            {
                "type": "correlation",
                "elements": [
                    {"type": "plot", "source_field": "correlation_plot"},
                    {"type": "text", "source_field": "statistical_summary"}
                ]
            }
        ]
    }
    
    template_path = tmp_path / "docs" / "report_layout_template.json"
    template_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(template_path, 'w') as f:
        json.dump(template, f)
    
    return str(template_path)

def test_load_results_returns_dict(mock_results_dir):
    """Contract: Verify load_results returns a dict with expected keys."""
    with patch('report.RESULTS_DIR', str(mock_results_dir)):
        results = load_results()
        
        assert isinstance(results, dict)
        assert 'correlation_results' in results
        assert 'permutation_results' in results
        assert 'power_analysis' in results

def test_load_results_raises_file_not_found(tmp_path):
    """Verify FileNotFoundError is raised when required files are missing."""
    with patch('report.RESULTS_DIR', str(tmp_path / 'nonexistent')):
        with pytest.raises(FileNotFoundError):
            load_results()

def test_generate_correlation_plot_returns_path(mock_results_dir):
    """Verify correlation plot generation returns a valid file path."""
    with patch('report.RESULTS_DIR', str(mock_results_dir)):
        with patch('report.figures_dir', str(mock_results_dir.parent / 'figures')):
            plot_path = generate_correlation_plot()
            
            assert isinstance(plot_path, str)
            assert os.path.exists(plot_path)
            assert plot_path.endswith('.png')

def test_generate_pdf_creates_file(mock_results_dir, mock_layout_template):
    """Contract: Verify generate_pdf creates a file <= 5MB."""
    with patch('report.RESULTS_DIR', str(mock_results_dir)):
        with patch('report.DOCS_DIR', str(mock_results_dir.parent / 'docs')):
            with patch('report.figures_dir', str(mock_results_dir.parent / 'figures')):
                pdf_path = generate_pdf()
                
                assert isinstance(pdf_path, str)
                assert os.path.exists(pdf_path)
                assert pdf_path.endswith('.pdf')
                
                # Check file size
                file_size = os.path.getsize(pdf_path)
                assert file_size <= 5 * 1024 * 1024  # 5MB

def test_generate_pdf_includes_mandatory_disclaimer(mock_results_dir, mock_layout_template):
    """Contract: Verify PDF contains mandatory disclaimer string."""
    with patch('report.RESULTS_DIR', str(mock_results_dir)):
        with patch('report.DOCS_DIR', str(mock_results_dir.parent / 'docs')):
            with patch('report.figures_dir', str(mock_results_dir.parent / 'figures')):
                pdf_path = generate_pdf()
                
                # Read PDF content (as text, which works for simple PDFs)
                with open(pdf_path, 'rb') as f:
                    content = f.read()
                
                # Check for disclaimer string (may be encoded differently in PDF)
                disclaimer = "These findings are associational only and do not imply causation."
                assert disclaimer.encode() in content or disclaimer in content.decode('latin-1', errors='ignore')

def test_generate_pdf_validates_layout_template(mock_results_dir, tmp_path):
    """Verify FileNotFoundError is raised if layout template is missing."""
    with patch('report.RESULTS_DIR', str(mock_results_dir)):
        with patch('report.DOCS_DIR', str(tmp_path / 'docs')):
            with patch('report.figures_dir', str(mock_results_dir.parent / 'figures')):
                with pytest.raises(FileNotFoundError):
                    generate_pdf()
