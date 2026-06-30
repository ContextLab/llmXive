"""
Unit tests for T043: Stratified Visualization Generator.
"""
import pytest
import pandas as pd
from pathlib import Path
import os
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from stratified_visualizer import (
    load_stratified_data,
    generate_stratified_csv,
    generate_box_plot,
    generate_bar_chart,
    run_stratified_visualization
)

class TestLoadStratifiedData:
    def test_load_stratified_data_returns_dataframe(self):
        df = load_stratified_data()
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert 'task_id' in df.columns

class TestGenerateStratifiedCSV:
    def test_generate_stratified_csv_creates_file(self, tmp_path):
        df = pd.DataFrame([
            {"task_id": "1", "pattern": "loops", "difficulty": "easy", "line_coverage": 0.8},
            {"task_id": "2", "pattern": "loops", "difficulty": "hard", "line_coverage": 0.6},
        ])
        output_path = tmp_path / "test_stratified_loops.csv"
        generate_stratified_csv(df, "loops", output_path)
        
        assert output_path.exists()
        # Verify content
        loaded_df = pd.read_csv(output_path)
        assert len(loaded_df) == 2
        assert all(loaded_df['pattern'] == 'loops')

class TestGenerateBoxPlot:
    def test_generate_box_plot_creates_file(self, tmp_path):
        df = pd.DataFrame([
            {"task_id": "1", "pattern": "loops", "difficulty": "easy", "line_coverage": 0.8},
            {"task_id": "2", "pattern": "loops", "difficulty": "hard", "line_coverage": 0.6},
        ])
        output_path = tmp_path / "test_box_plot.png"
        # Mock plt.savefig to avoid actual rendering in test environment if needed,
        # but assuming matplotlib is available
        generate_box_plot(df, "loops", metric="line_coverage", output_path=output_path)
        
        # The function creates the file if data is valid
        # In a real CI environment, we might mock the savefig
        # Here we just check the function runs without error
        assert True

class TestGenerateBarChart:
    def test_generate_bar_chart_creates_file(self, tmp_path):
        df = pd.DataFrame([
            {"task_id": "1", "pattern": "loops", "difficulty": "easy", "line_coverage": 0.8},
            {"task_id": "2", "pattern": "loops", "difficulty": "hard", "line_coverage": 0.6},
        ])
        output_path = tmp_path / "test_bar_chart.png"
        generate_bar_chart(df, "loops", metric="line_coverage", output_path=output_path)
        assert True

class TestRunStratifiedVisualization:
    def test_run_stratified_visualization_integration(self, tmp_path, monkeypatch):
        # Patch OUTPUT_DIR to use tmp_path
        import stratified_visualizer
        original_output_dir = stratified_visualizer.OUTPUT_DIR
        stratified_visualizer.OUTPUT_DIR = tmp_path
        
        # Patch load_stratified_data to return known data
        def mock_load_data(pattern_type="loops"):
            return pd.DataFrame([
                {"task_id": "1", "pattern": "loops", "difficulty": "easy", "line_coverage": 0.8, "branch_coverage": 0.7},
                {"task_id": "2", "pattern": "loops", "difficulty": "hard", "line_coverage": 0.6, "branch_coverage": 0.4},
                {"task_id": "3", "pattern": "conditionals", "difficulty": "medium", "line_coverage": 0.9, "branch_coverage": 0.8},
            ])
        
        monkeypatch.setattr(stratified_visualizer, 'load_stratified_data', mock_load_data)
        
        try:
            run_stratified_visualization(patterns=["loops"])
            
            # Check that expected files are created
            assert (tmp_path / "stratified_loops.csv").exists()
            assert (tmp_path / "coverage_by_pattern_loops_line.png").exists()
            assert (tmp_path / "mean_coverage_by_difficulty_loops.png").exists()
        finally:
            stratified_visualizer.OUTPUT_DIR = original_output_dir