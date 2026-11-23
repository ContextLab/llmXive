import pytest
import pandas as pd
import os
import sys
from pathlib import Path
import tempfile
import shutil

# Add code root to path for imports
code_root = Path(__file__).resolve().parent.parent.parent / 'code'
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from ingestion.generate_outputs import count_valid_observations, generate_exclusion_summary

class TestGenerateOutputs:
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        temp_dir = tempfile.mkdtemp()
        processed_dir = Path(temp_dir) / 'processed'
        logs_dir = Path(temp_dir) / 'logs'
        processed_dir.mkdir()
        logs_dir.mkdir()
        yield processed_dir, logs_dir, temp_dir
        shutil.rmtree(temp_dir)

    def test_count_valid_observations(self, temp_dirs):
        """Test reading species counts."""
        processed_dir, _, _ = temp_dirs
        counts_file = processed_dir / 'species_counts.csv'
        
        # Create mock data
        data = {
            'species_name': ['A', 'B', 'C'],
            'valid_count': [15, 5, 20]
        }
        df = pd.DataFrame(data)
        df.to_csv(counts_file, index=False)
        
        # Test function
        result = count_valid_observations(counts_file)
        assert len(result) == 3
        assert 'valid_count' in result.columns
        assert result.loc[result['species_name'] == 'B', 'valid_count'].values[0] == 5

    def test_generate_exclusion_summary(self, temp_dirs):
        """Test generation of exclusion summary and log."""
        processed_dir, logs_dir, _ = temp_dirs
        counts_file = processed_dir / 'species_counts.csv'
        summary_file = processed_dir / 'excluded_species_summary.csv'
        log_file = logs_dir / 'species_exclusions.log'
        
        # Create mock data with some species below threshold
        data = {
            'species_name': ['A', 'B', 'C', 'D'],
            'valid_count': [15, 5, 20, 8]
        }
        df = pd.DataFrame(data)
        df.to_csv(counts_file, index=False)
        
        # Run function
        summary_df, log_data = generate_exclusion_summary(
            counts_file, summary_file, log_file, min_observations=10
        )
        
        # Assertions
        assert summary_file.exists(), "Summary CSV not created"
        assert log_file.exists(), "Log file not created"
        
        # Check summary content
        assert len(summary_df) == 2, "Expected 2 excluded species"
        assert 'observation_count' in summary_df.columns
        assert 'reason' in summary_df.columns
        
        # Verify specific species were excluded
        excluded_names = set(summary_df['species_name'].tolist())
        assert excluded_names == {'B', 'D'}
        
        # Verify reason string
        assert all(summary_df['reason'] == 'observation_count < 10')

    def test_no_exclusions(self, temp_dirs):
        """Test behavior when no species are excluded."""
        processed_dir, logs_dir, _ = temp_dirs
        counts_file = processed_dir / 'species_counts.csv'
        summary_file = processed_dir / 'excluded_species_summary.csv'
        log_file = logs_dir / 'species_exclusions.log'
        
        # Create mock data all above threshold
        data = {
            'species_name': ['A', 'B'],
            'valid_count': [15, 20]
        }
        df = pd.DataFrame(data)
        df.to_csv(counts_file, index=False)
        
        # Run function
        summary_df, log_data = generate_exclusion_summary(
            counts_file, summary_file, log_file, min_observations=10
        )
        
        # Assertions
        assert len(summary_df) == 0
        assert log_data == []
        assert summary_file.exists()
        assert log_file.exists()
        # Check that the files are empty or have headers only
        assert len(pd.read_csv(summary_file)) == 0
        # Log file might be empty or just headers depending on implementation
        # We just check it exists
        
    def test_missing_input_file(self, temp_dirs):
        """Test error handling for missing input file."""
        processed_dir, logs_dir, _ = temp_dirs
        counts_file = processed_dir / 'nonexistent.csv'
        summary_file = processed_dir / 'summary.csv'
        log_file = logs_dir / 'log.txt'
        
        with pytest.raises(FileNotFoundError):
            generate_exclusion_summary(
                counts_file, summary_file, log_file, min_observations=10
            )

    def test_missing_columns(self, temp_dirs):
        """Test error handling for missing required columns."""
        processed_dir, logs_dir, _ = temp_dirs
        counts_file = processed_dir / 'species_counts.csv'
        summary_file = processed_dir / 'summary.csv'
        log_file = logs_dir / 'log.txt'
        
        # Create data with wrong columns
        data = {
            'name': ['A', 'B'],
            'count': [5, 10]
        }
        df = pd.DataFrame(data)
        df.to_csv(counts_file, index=False)
        
        with pytest.raises(ValueError):
            generate_exclusion_summary(
                counts_file, summary_file, log_file, min_observations=10
            )