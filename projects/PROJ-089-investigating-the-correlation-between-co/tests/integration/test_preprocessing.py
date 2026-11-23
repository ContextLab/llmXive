"""
Integration tests for preprocessing module.

Tests the full preprocessing pipeline end-to-end.
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import os

from preprocessing import run_preprocessing, validate_raw_metrics

class TestPreprocessingIntegration:
    @pytest.fixture
    def sample_input_csv(self, tmp_path):
        """Create a sample input CSV file."""
        input_path = tmp_path / "input_metrics.csv"
        
        data = {
            'file_path': [
                'src/main.py',
                'src/utils.py',
                'lib/helper.js',
                'node_modules/pkg/index.js',
                'tests/test_main.py',
                'docs/readme.md',
                'app/App.java',
                'src/components/App.tsx',
                'build/output.class',
                'data/file.csv',
            ],
            'total_lines_changed': [10, 15, 20, 100, 8, 30, 15, 12, 200, 50],
            'debt_score': [2, 3, 5, 50, 2, 8, 3, 4, 100, 10],
            'avg_loc': [50, 60, 100, 500, 40, 150, 80, 60, 600, 200],
            'contributor_count': [3, 2, 2, 10, 1, 3, 2, 2, 15, 5],
        }
        
        df = pd.DataFrame(data)
        df.to_csv(input_path, index=False)
        return input_path
    
    def test_full_pipeline(self, sample_input_csv, tmp_path):
        """Test the full preprocessing pipeline."""
        output_dir = tmp_path / "processed"
        
        results = run_preprocessing(
            input_path=sample_input_csv,
            output_dir=output_dir,
            thresholds=[5, 10, 20]
        )
        
        # Check results structure
        assert 'input_rows' in results
        assert 'after_filter_rows' in results
        assert 'datasets_generated' in results
        assert 'output_files' in results
        
        # Check input rows
        assert results['input_rows'] == 10
        
        # Check that datasets were generated
        assert results['datasets_generated'] == 3
        
        # Check output files exist
        for output_file in results['output_files']:
            assert Path(output_file).exists()
        
        # Check that non-source files were filtered
        # Expected to filter: node_modules, tests, build, data (non-source), docs (markdown)
        # Remaining: src/main.py, src/utils.py, lib/helper.js, app/App.java, src/components/App.tsx
        assert results['after_filter_rows'] <= 5
    
    def test_output_files_content(self, sample_input_csv, tmp_path):
        """Test that output files contain correct data."""
        output_dir = tmp_path / "processed"
        
        run_preprocessing(
            input_path=sample_input_csv,
            output_dir=output_dir,
            thresholds=[5, 10, 20]
        )
        
        # Load and check each output file
        for threshold in [5, 10, 20]:
            output_file = output_dir / f"unified_metrics_loc_{threshold}.csv"
            df = pd.read_csv(output_file)
            
            # Check required columns
            required_cols = ['total_lines_changed', 'debt_score', 'avg_loc', 'contributor_count']
            for col in required_cols:
                assert col in df.columns
            
            # Check that avg_loc meets threshold
            assert all(df['avg_loc'] >= threshold)
            
            # Check that all files are source files
            for path in df['file_path']:
                from preprocessing import is_source_file, should_exclude_dir
                assert is_source_file(path)
                assert not should_exclude_dir(Path(path).parent.name)
    
    def test_sensitivity_analysis_varies(self, sample_input_csv, tmp_path):
        """Test that different thresholds produce different dataset sizes."""
        output_dir = tmp_path / "processed"
        
        run_preprocessing(
            input_path=sample_input_csv,
            output_dir=output_dir,
            thresholds=[5, 10, 20]
        )
        
        sizes = {}
        for threshold in [5, 10, 20]:
            output_file = output_dir / f"unified_metrics_loc_{threshold}.csv"
            df = pd.read_csv(output_file)
            sizes[threshold] = len(df)
        
        # Higher thresholds should result in fewer or equal rows
        assert sizes[5] >= sizes[10] >= sizes[20]
        
        # At least one threshold should have different size (if data varies)
        if sizes[5] > 0:
            assert sizes[5] != sizes[20] or sizes[5] == 0

class TestPreprocessingEdgeCases:
    def test_empty_input(self, tmp_path):
        """Test preprocessing with empty input file."""
        input_path = tmp_path / "empty_input.csv"
        input_path.write_text("file_path,total_lines_changed,debt_score,avg_loc,contributor_count\n")
        
        output_dir = tmp_path / "processed"
        
        with pytest.raises(ValueError, match="null values"):
            run_preprocessing(
                input_path=input_path,
                output_dir=output_dir,
                thresholds=[5, 10, 20]
            )
    
    def test_missing_input_file(self, tmp_path):
        """Test preprocessing with missing input file."""
        input_path = tmp_path / "nonexistent.csv"
        output_dir = tmp_path / "processed"
        
        with pytest.raises(FileNotFoundError):
            run_preprocessing(
                input_path=input_path,
                output_dir=output_dir,
                thresholds=[5, 10, 20]
            )
    
    def test_all_files_filtered(self, tmp_path):
        """Test preprocessing when all files are filtered out."""
        input_path = tmp_path / "all_filtered.csv"
        data = {
            'file_path': ['node_modules/pkg/index.js', 'tests/test.py'],
            'total_lines_changed': [100, 50],
            'debt_score': [50, 20],
            'avg_loc': [500, 400],
            'contributor_count': [10, 5],
        }
        pd.DataFrame(data).to_csv(input_path, index=False)
        
        output_dir = tmp_path / "processed"
        
        results = run_preprocessing(
            input_path=input_path,
            output_dir=output_dir,
            thresholds=[5, 10, 20]
        )
        
        # All files should be filtered
        assert results['after_filter_rows'] == 0
        
        # Output files should exist but be empty (header only)
        for threshold in [5, 10, 20]:
            output_file = output_dir / f"unified_metrics_loc_{threshold}.csv"
            df = pd.read_csv(output_file)
            assert len(df) == 0