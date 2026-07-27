import pytest
import pandas as pd
import numpy as np
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add code to path if not already
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.qc import check_replicates, check_metadata_completeness, run_qc_pipeline

class TestQC:
    @pytest.fixture
    def sample_df_replicates(self):
        """DataFrame with replicate counts."""
        return pd.DataFrame({
            'accession_id': ['SRA001', 'SRA002', 'SRA003'],
            'species': ['Arabidopsis', 'Maize', 'Rice'],
            'tissue': ['Leaf', 'Leaf', 'Root'],
            'replicates': [3, 1, 4]  # SRA002 has < 2
        })

    @pytest.fixture
    def sample_df_metadata(self):
        """DataFrame with missing metadata."""
        return pd.DataFrame({
            'accession_id': ['SRA001', 'SRA002', 'SRA003'],
            'species': ['Arabidopsis', 'Maize', 'Rice'],
            'tissue': ['Leaf', None, 'Root'],  # SRA002 missing tissue
            'replicates': [3, 3, 3]
        })

    @pytest.fixture
    def temp_input_json(self, sample_df_replicates):
        """Create a temporary JSON file for input."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            # Convert to list of dicts
            data = sample_df_replicates.to_dict(orient='records')
            json.dump(data, f)
            return Path(f.name)

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_check_replicates_filter(self, sample_df_replicates):
        """Test that check_replicates removes samples with < 2 replicates."""
        result = check_replicates(sample_df_replicates, min_replicates=2)
        assert len(result) == 2
        assert 'SRA002' not in result['accession_id'].values

    def test_check_replicates_pass(self, sample_df_replicates):
        """Test that samples with >= 2 replicates are kept."""
        result = check_replicates(sample_df_replicates, min_replicates=2)
        assert 'SRA001' in result['accession_id'].values
        assert 'SRA003' in result['accession_id'].values

    def test_check_metadata_completeness_filter(self, sample_df_metadata):
        """Test that check_metadata_completeness removes samples with missing tissue."""
        result = check_metadata_completeness(sample_df_metadata, required_metadata=['tissue'])
        assert len(result) == 2
        assert 'SRA002' not in result['accession_id'].values

    def test_check_metadata_completeness_pass(self, sample_df_metadata):
        """Test that samples with complete metadata are kept."""
        result = check_metadata_completeness(sample_df_metadata, required_metadata=['tissue'])
        assert 'SRA001' in result['accession_id'].values
        assert 'SRA003' in result['accession_id'].values

    def test_run_qc_pipeline_integration(self, temp_input_json, temp_output_dir):
        """Test the full pipeline writes the correct output file."""
        output_file = temp_output_dir / "post_qc_species_list.json"
        
        result = run_qc_pipeline(
            input_path=temp_input_json,
            output_path=output_file,
            min_replicates=2,
            required_metadata=['tissue']
        )
        
        assert output_file.exists()
        with open(output_file, 'r') as f:
            saved_data = json.load(f)
        
        assert 'species_list' in saved_data
        assert 'exclusions' in saved_data
        # SRA002 should be excluded for both reasons if it had low reps AND missing tissue,
        # but in this specific test fixture, SRA002 has low reps (1) but valid tissue (None in metadata fixture, 
        # but we are using sample_df_replicates for input here which has tissue='Leaf').
        # Let's re-evaluate: sample_df_replicates has SRA002 with replicates=1.
        # So it should be excluded for replicates.
        assert saved_data['studies_remaining'] == 2
        assert saved_data['studies_excluded'] == 1
        assert saved_data['exclusions'][0]['accession_id'] == 'SRA002'
        
        # Cleanup
        temp_input_json.unlink()

    def test_run_qc_pipeline_missing_input(self):
        """Test that pipeline raises error if input file missing."""
        with pytest.raises(FileNotFoundError):
            run_qc_pipeline(input_path=Path("/nonexistent/path.json"))