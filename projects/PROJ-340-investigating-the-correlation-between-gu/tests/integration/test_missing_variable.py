"""
Integration Test for Missing Variable Error Handling (Task T011).

Verifies that the system halts with a specific error when a required
variable is missing from the dataset.
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ingest import load_data, RealDataFetchError
from generate_synthetic_data import generate_synthetic_dataset

class TestMissingVariableHandling:
    """Test cases for missing variable error handling."""

    def test_halt_on_missing_sws_duration(self):
        """Test that the system halts when SWS duration is missing."""
        # Create a temporary directory for test data
        temp_dir = tempfile.mkdtemp()
        try:
            # Generate synthetic data with missing SWS duration
            df = generate_synthetic_dataset(
                n_samples=50,
                n_taxa=20,
                missing_var='sws_duration',
                seed=42
            )
            
            # Save to temp file
            input_path = os.path.join(temp_dir, 'test_data.csv')
            df.to_csv(input_path, index=False)
            
            # Try to load and validate - should raise ValueError
            from ingest import load_required_variables, validate_variables
            
            required = load_required_variables()
            
            with pytest.raises(ValueError) as exc_info:
                validate_variables(df, required)
            
            # Verify error message contains the missing variable
            assert "sws_duration" in str(exc_info.value).lower()
            
        finally:
            # Cleanup
            shutil.rmtree(temp_dir)

    def test_pipeline_halt_on_missing_variable(self):
        """Test that the full pipeline halts on missing variable."""
        # Generate data with missing variable
        df = generate_synthetic_dataset(
            n_samples=50,
            n_taxa=20,
            missing_var='total_sleep_time',
            seed=42
        )
        
        from ingest import load_required_variables, validate_variables
        
        required = load_required_variables()
        
        with pytest.raises(ValueError) as exc_info:
            validate_variables(df, required)
        
        assert "total_sleep_time" in str(exc_info.value).lower()

if __name__ == '__main__':
    pytest.main([__file__, '-v'])