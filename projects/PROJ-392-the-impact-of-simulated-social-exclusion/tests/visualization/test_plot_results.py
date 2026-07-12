"""
Unit tests for plot_results module.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from visualization.plot_results import (
    load_summary_statistics,
    calculate_sem,
    get_significance_annotation,
    prepare_plot_data,
    create_bar_plot,
    run_visualization,
    main
)


class TestCalculateSem:
    def test_calculate_sem_normal(self):
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        sem = calculate_sem(values)
        expected_std = np.std(values, ddof=1)
        expected_sem = expected_std / np.sqrt(len(values))
        assert np.isclose(sem, expected_sem)

    def test_calculate_sem_single_value(self):
        values = [1.0]
        sem = calculate_sem(values)
        assert sem == 0.0

    def test_calculate_sem_empty(self):
        values = []
        sem = calculate_sem(values)
        assert sem == 0.0


class TestGetSignificanceAnnotation:
    def test_highly_significant(self):
        assert get_significance_annotation(0.0001) == "***"

    def test_significant_p001(self):
        assert get_significance_annotation(0.005) == "**"

    def test_significant_p05(self):
        assert get_significance_annotation(0.03) == "*"

    def test_not_significant(self):
        assert get_significance_annotation(0.1) == "ns"

    def test_boundary_values(self):
        assert get_significance_annotation(0.001) == "***"
        assert get_significance_annotation(0.01) == "**"
        assert get_significance_annotation(0.05) == "*"


class TestPreparePlotData:
    def test_prepare_plot_data_basic(self):
        data = [
            {
                'roi': 'VS',
                'event_type': 'anticipation',
                'group': 'excluded',
                'mean': 0.5,
                'sem': 0.1,
                'n': 20,
                'p_value': 0.03
            },
            {
                'roi': 'VS',
                'event_type': 'anticipation',
                'group': 'included',
                'mean': 0.8,
                'sem': 0.12,
                'n': 20,
                'p_value': 0.03
            }
        ]
        
        result = prepare_plot_data(data)
        
        assert 'VS' in result
        assert 'anticipation' in result['VS']
        assert 'excluded' in result['VS']['anticipation']
        assert 'included' in result['VS']['anticipation']
        assert np.isclose(result['VS']['anticipation']['excluded']['mean'], 0.5)
        assert np.isclose(result['VS']['anticipation']['included']['mean'], 0.8)


class TestLoadSummaryStatistics:
    def test_load_summary_statistics(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{'roi': 'VS', 'mean': 0.5}], f)
            temp_path = Path(f.name)
        
        try:
            result = load_summary_statistics(temp_path)
            assert len(result) == 1
            assert result[0]['roi'] == 'VS'
        finally:
            os.unlink(temp_path)

    def test_load_summary_statistics_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_summary_statistics(Path("/nonexistent/file.json"))


class TestCreateBarPlot:
    def test_create_bar_plot_saves_file(self):
        plot_data = {
            'VS': {
                'anticipation': {
                    'excluded': {'mean': 0.5, 'sem': 0.1, 'n': 20, 'p_value': 0.03},
                    'included': {'mean': 0.8, 'sem': 0.12, 'n': 20, 'p_value': 0.03}
                }
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_plot.png"
            create_bar_plot(plot_data, output_path)
            
            assert output_path.exists()
            assert output_path.stat().st_size > 0


class TestRunVisualization:
    def test_run_visualization_end_to_end(self):
        # Create temporary summary statistics
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "summary_statistics.json"
            output_file = Path(tmpdir) / "output.png"
            
            test_data = [
                {
                    'roi': 'VS',
                    'event_type': 'anticipation',
                    'group': 'excluded',
                    'mean': 0.5,
                    'sem': 0.1,
                    'n': 20,
                    't_statistic': 2.1,
                    'p_value': 0.03,
                    'cohens_d': 0.5
                },
                {
                    'roi': 'VS',
                    'event_type': 'anticipation',
                    'group': 'included',
                    'mean': 0.8,
                    'sem': 0.12,
                    'n': 20,
                    't_statistic': 2.1,
                    'p_value': 0.03,
                    'cohens_d': 0.5
                },
                {
                    'roi': 'OFC',
                    'event_type': 'receipt',
                    'group': 'excluded',
                    'mean': 0.3,
                    'sem': 0.08,
                    'n': 20,
                    't_statistic': 1.2,
                    'p_value': 0.25,
                    'cohens_d': 0.2
                },
                {
                    'roi': 'OFC',
                    'event_type': 'receipt',
                    'group': 'included',
                    'mean': 0.35,
                    'sem': 0.09,
                    'n': 20,
                    't_statistic': 1.2,
                    'p_value': 0.25,
                    'cohens_d': 0.2
                }
            ]
            
            with open(input_file, 'w') as f:
                json.dump(test_data, f)
            
            result = run_visualization(input_file, output_file)
            
            assert result == str(output_file)
            assert output_file.exists()
            assert output_file.stat().st_size > 0


class TestMain:
    def test_main_success(self, caplog):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "summary_statistics.json"
            output_file = Path(tmpdir) / "output.png"
            
            test_data = [
                {
                    'roi': 'VS',
                    'event_type': 'anticipation',
                    'group': 'excluded',
                    'mean': 0.5,
                    'sem': 0.1,
                    'n': 20,
                    't_statistic': 2.1,
                    'p_value': 0.03,
                    'cohens_d': 0.5
                },
                {
                    'roi': 'VS',
                    'event_type': 'anticipation',
                    'group': 'included',
                    'mean': 0.8,
                    'sem': 0.12,
                    'n': 20,
                    't_statistic': 2.1,
                    'p_value': 0.03,
                    'cohens_d': 0.5
                }
            ]
            
            with open(input_file, 'w') as f:
                json.dump(test_data, f)
            
            with patch('sys.argv', ['plot_results.py', '--input', str(input_file), '--output', str(output_file)]):
                main()
            
            assert output_file.exists()