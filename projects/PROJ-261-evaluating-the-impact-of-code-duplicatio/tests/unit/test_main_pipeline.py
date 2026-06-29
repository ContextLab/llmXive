"""Unit tests for main.py pipeline orchestration."""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import csv

# Test fixtures
@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    return [
        {'path': 'test1.py', 'code': 'def hello():\n    pass', 'lang': 'python'},
        {'path': 'test2.py', 'code': 'def world():\n    return 42', 'lang': 'python'},
        {'path': 'test3.py', 'code': 'def test():\n    x = 1\n    return x', 'lang': 'python'},
    ]

@pytest.fixture
def tmp_dir():
    """Create temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def raw_data_csv(sample_data, tmp_dir):
    """Create raw data CSV file."""
    csv_path = tmp_dir / 'raw_data.csv'
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['path', 'code', 'lang'])
        writer.writeheader()
        writer.writerows(sample_data)
    return csv_path

class TestPipelineIntegration:
    """Test pipeline integration scenarios."""

    def test_load_raw_data_exists(self, raw_data_csv):
        """Test that raw data loading succeeds when file exists."""
        from data_loader import load_raw_data
        data = load_raw_data(raw_data_csv)
        assert len(data) == 3
        assert data[0]['path'] == 'test1.py'

    def test_load_raw_data_not_exists(self, tmp_dir):
        """Test that raw data loading fails when file doesn't exist."""
        from data_loader import load_raw_data
        non_existent = tmp_dir / 'nonexistent.csv'
        assert not non_existent.exists()
        with pytest.raises(FileNotFoundError):
            load_raw_data(non_existent)

    def test_join_metrics_basic(self, tmp_dir):
        """Test joining clone and perplexity metrics."""
        from main import join_metrics

        clone_df = pd.DataFrame([
            {'path': 'test1.py', 'clone_density': 0.5, 'sample_id': 0},
            {'path': 'test2.py', 'clone_density': 0.3, 'sample_id': 1},
        ])

        perplexity_df = pd.DataFrame([
            {'path': 'test1.py', 'perplexity': 12.5, 'sample_id': 0},
            {'path': 'test2.py', 'perplexity': 15.2, 'sample_id': 1},
        ])

        merged = join_metrics(clone_df, perplexity_df)

        assert len(merged) == 2
        assert 'clone_density' in merged.columns
        assert 'perplexity' in merged.columns
        assert 'sample_id' in merged.columns

    def test_join_metrics_mismatched_ids(self, tmp_dir):
        """Test joining when sample IDs don't match perfectly."""
        from main import join_metrics

        clone_df = pd.DataFrame([
            {'path': 'test1.py', 'clone_density': 0.5, 'sample_id': 0},
            {'path': 'test2.py', 'clone_density': 0.3, 'sample_id': 1},
            {'path': 'test3.py', 'clone_density': 0.7, 'sample_id': 2},
        ])

        perplexity_df = pd.DataFrame([
            {'path': 'test1.py', 'perplexity': 12.5, 'sample_id': 0},
            {'path': 'test3.py', 'perplexity': 18.9, 'sample_id': 2},
        ])

        merged = join_metrics(clone_df, perplexity_df)

        # Should only have 2 rows (inner join)
        assert len(merged) == 2
        assert 1 not in merged['sample_id'].values

    def test_save_results_creates_file(self, tmp_dir):
        """Test that save_results creates the output file."""
        from main import save_results

        merged_df = pd.DataFrame([
            {'path': 'test.py', 'clone_density': 0.5, 'perplexity': 12.5, 'sample_id': 0},
        ])

        output_path = tmp_dir / 'output.csv'
        save_results(merged_df, output_path)

        assert output_path.exists()

        # Verify file contents
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]['path'] == 'test.py'

    def test_save_results_empty_dataframe(self, tmp_dir):
        """Test saving empty dataframe."""
        from main import save_results

        merged_df = pd.DataFrame(columns=['path', 'clone_density', 'perplexity', 'sample_id'])
        output_path = tmp_dir / 'empty_output.csv'
        save_results(merged_df, output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0  # Should have at least headers

    def test_run_pipeline_missing_raw_data(self, tmp_dir):
        """Test pipeline fails gracefully when raw data is missing."""
        from main import run_pipeline

        raw_data_path = tmp_dir / 'missing.csv'
        clone_path = tmp_dir / 'clone.csv'
        perplexity_path = tmp_dir / 'perplexity.csv'
        merged_path = tmp_dir / 'merged.csv'

        with pytest.raises(FileNotFoundError):
            run_pipeline(raw_data_path, clone_path, perplexity_path, merged_path)

    def test_pipeline_output_paths(self, sample_data, tmp_dir):
        """Test that pipeline writes to correct output paths."""
        from main import run_pipeline

        raw_data_path = tmp_dir / 'raw.csv'
        clone_path = tmp_dir / 'clone.csv'
        perplexity_path = tmp_dir / 'perplexity.csv'
        merged_path = tmp_dir / 'merged.csv'

        # Create raw data CSV
        with open(raw_data_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['path', 'code', 'lang'])
            writer.writeheader()
            writer.writerows(sample_data)

        # Run pipeline (will use mock data since models not available)
        merged_df = run_pipeline(
            raw_data_path, clone_path, perplexity_path, merged_path
        )

        # Check outputs exist
        assert clone_path.exists()
        assert perplexity_path.exists()
        assert merged_path.exists()

        # Verify merged has correct columns
        assert 'clone_density' in merged_df.columns
        assert 'perplexity' in merged_df.columns
        assert 'sample_id' in merged_df.columns
