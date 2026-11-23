"""
Unit tests for visualization module.
"""
import os
import tempfile
import pandas as pd
import pytest
import numpy as np

# Mock matplotlib backend before importing viz
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

from code.analysis.viz import calculate_pareto_frontier, load_metrics_data, plot_pareto_frontier

class TestParetoFrontier:
    def test_calculate_pareto_frontier_basic(self):
        """Test basic Pareto calculation."""
        data = {
            'latency_ms': [100, 200, 300, 400],
            'alignment_score': [0.9, 0.8, 0.7, 0.6]
        }
        df = pd.DataFrame(data)
        frontier = calculate_pareto_frontier(df)
        
        # All points should be on frontier here (latency increases, score decreases)
        # Point 1: (100, 0.9) -> Max align so far 0.9. Keep.
        # Point 2: (200, 0.8) -> Max align so far 0.9. 0.8 < 0.9. Drop?
        # Wait, logic check:
        # Sorted: (100, 0.9), (200, 0.8), (300, 0.7), (400, 0.6)
        # 1. (100, 0.9). Max=0.9. Keep.
        # 2. (200, 0.8). 0.8 < 0.9. Drop (dominated by 100, 0.9).
        # 3. (300, 0.7). 0.7 < 0.9. Drop.
        # 4. (400, 0.6). 0.6 < 0.9. Drop.
        # Result: Only (100, 0.9). Correct.
        
        assert len(frontier) == 1
        assert frontier.iloc[0]['latency_ms'] == 100
        assert frontier.iloc[0]['alignment_score'] == 0.9

    def test_calculate_pareto_frontier_mixed(self):
        """Test mixed scenario."""
        # Point A: (100, 0.5)
        # Point B: (200, 0.9) -> Better score, higher latency. Not dominated by A.
        # Point C: (300, 0.4) -> Worse score, higher latency. Dominated by A? Yes (100 < 300, 0.5 > 0.4).
        data = {
            'latency_ms': [100, 200, 300],
            'alignment_score': [0.5, 0.9, 0.4]
        }
        df = pd.DataFrame(data)
        frontier = calculate_pareto_frontier(df)
        
        # Sorted: (100, 0.5), (200, 0.9), (300, 0.4)
        # 1. (100, 0.5). Keep. Max=0.5.
        # 2. (200, 0.9). 0.9 > 0.5. Keep. Max=0.9.
        # 3. (300, 0.4). 0.4 < 0.9. Drop.
        # Result: (100, 0.5) and (200, 0.9).
        
        assert len(frontier) == 2
        assert frontier.iloc[0]['latency_ms'] == 100
        assert frontier.iloc[1]['latency_ms'] == 200

    def test_empty_dataframe(self):
        df = pd.DataFrame(columns=['latency_ms', 'alignment_score'])
        frontier = calculate_pareto_frontier(df)
        assert frontier.empty

class TestLoadMetricsData:
    def test_load_valid_csv(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("latency_ms,alignment_score,density\n100,0.9,1\n200,0.8,2\n")
            temp_path = f.name
        
        try:
            df = load_metrics_data(temp_path)
            assert len(df) == 2
            assert 'latency_ms' in df.columns
            assert 'alignment_score' in df.columns
        finally:
            os.unlink(temp_path)

    def test_load_missing_file(self):
        with pytest.raises(FileNotFoundError):
            load_metrics_data("nonexistent_file.csv")

    def test_load_missing_columns(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("latency_ms,some_other_col\n100,0.9\n")
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError):
                load_metrics_data(temp_path)
        finally:
            os.unlink(temp_path)

class TestPlotGeneration:
    def test_plot_pareto_creates_file(self):
        data = {
            'latency_ms': [100, 200, 300, 400],
            'alignment_score': [0.9, 0.8, 0.7, 0.6]
        }
        df = pd.DataFrame(data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_pareto.png")
            result_path = plot_pareto_frontier(df, output_path)
            
            assert os.path.exists(result_path)
            assert os.path.getsize(result_path) > 0
            plt.close('all') # Clean up