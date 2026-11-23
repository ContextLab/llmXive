import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

from analysis.slope_extractor import extract_code_size_slope, run_slope_extraction

class TestExtractCodeSizeSlope:
    """Unit tests for code size slope extraction."""

    def test_extract_slope_from_dict_coefficients(self):
        """Test extraction when coefficients are stored as a dictionary."""
        results = {
            'lmer': {
                'coefficients': {
                    'code_lines_changed': {
                        'estimate': 0.025,
                        'p_value': 0.003
                    },
                    'origin_label': {
                        'estimate': -1.5,
                        'p_value': 0.04
                    }
                }
            }
        }
        
        slope_info = extract_code_size_slope(results)
        
        assert slope_info['code_size_slopes']['estimate'] == 0.025
        assert slope_info['code_size_slopes']['p_value'] == 0.003

    def test_extract_slope_from_list_coefficients(self):
        """Test extraction when coefficients are stored as a list."""
        results = {
            'lmer': {
                'coefficients': [
                    {'term': 'code_lines_changed', 'estimate': 0.03, 'p_value': 0.001},
                    {'term': 'reviewer_count', 'estimate': -0.5, 'p_value': 0.02}
                ]
            }
        }
        
        slope_info = extract_code_size_slope(results)
        
        assert slope_info['code_size_slopes']['estimate'] == 0.03
        assert slope_info['code_size_slopes']['p_value'] == 0.001

    def test_extract_simex_corrected_slope(self):
        """Test extraction of SIMEX corrected slope."""
        results = {
            'lmer': {
                'coefficients': {
                    'code_lines_changed': {
                        'estimate': 0.025,
                        'p_value': 0.003
                    }
                }
            },
            'simex_corrected_coefficients': {
                'code_lines_changed': {
                    'estimate': 0.028,
                    'p_value': 0.002
                }
            }
        }
        
        slope_info = extract_code_size_slope(results)
        
        # Should prefer SIMEX corrected value
        assert slope_info['code_size_slopes']['estimate'] == 0.028
        assert slope_info['code_size_slopes']['p_value'] == 0.002

    def test_no_lmer_results(self):
        """Test behavior when LMER results are missing."""
        results = {
            'mann_whitney': {
                'statistic': 1000.0,
                'p_value': 0.05
            }
        }
        
        slope_info = extract_code_size_slope(results)
        
        assert slope_info['code_size_slopes'] is None
        assert 'note' in slope_info

    def test_missing_code_size_coefficient(self):
        """Test behavior when code size coefficient is missing."""
        results = {
            'lmer': {
                'coefficients': {
                    'origin_label': {
                        'estimate': -1.5,
                        'p_value': 0.04
                    }
                }
            }
        }
        
        slope_info = extract_code_size_slope(results)
        
        assert slope_info['code_size_slopes']['estimate'] is None
        assert slope_info['code_size_slopes']['p_value'] is None

class TestRunSlopeExtraction:
    """Unit tests for the run_slope_extraction function."""

    @patch('analysis.slope_extractor.load_analysis_results')
    @patch('analysis.slope_extractor.save_analysis_results')
    def test_run_extraction_success(self, mock_save, mock_load, tmp_path):
        """Test successful extraction and saving."""
        mock_results = {
            'lmer': {
                'coefficients': {
                    'code_lines_changed': {
                        'estimate': 0.025,
                        'p_value': 0.003
                    }
                }
            }
        }
        mock_load.return_value = mock_results
        
        input_path = tmp_path / "input.json"
        output_path = tmp_path / "output.json"
        
        results = run_slope_extraction(input_path, output_path)
        
        mock_load.assert_called_once_with(input_path)
        mock_save.assert_called_once()
        assert 'code_size_slopes' in results
        assert results['code_size_slopes']['estimate'] == 0.025

    @patch('analysis.slope_extractor.load_analysis_results')
    @patch('analysis.slope_extractor.save_analysis_results')
    def test_run_extraction_preserves_existing_data(self, mock_save, mock_load, tmp_path):
        """Test that extraction preserves other analysis results."""
        mock_results = {
            'mann_whitney': {'statistic': 1000.0, 'p_value': 0.05},
            'lmer': {
                'coefficients': {
                    'code_lines_changed': {
                        'estimate': 0.025,
                        'p_value': 0.003
                    }
                }
            }
        }
        mock_load.return_value = mock_results
        
        input_path = tmp_path / "input.json"
        output_path = tmp_path / "output.json"
        
        results = run_slope_extraction(input_path, output_path)
        
        # Verify mann_whitney is still present
        assert 'mann_whitney' in results
        assert results['mann_whitney']['p_value'] == 0.05
        assert 'code_size_slopes' in results