import os
import sys
import json
import tempfile
import shutil
import pytest
from pathlib import Path


class TestQuickstartValidation:
    """Tests for quickstart validation."""
    
    def test_synthetic_mode(self):
        """Test running in synthetic mode."""
        # Verify synthetic mode runs without error
        from src.cli import run_synthetic_generation
        output_path = os.path.join(tempfile.gettempdir(), "test_results.json")
        run_synthetic_generation(output_path, None, [0.05])
        assert os.path.exists(output_path)
        
    def test_data_sources(self):
        """Test data source handling."""
        # Verify that missing instruction_type triggers synthetic
        from src.data_loader import load_public_dataset
        import csv
        import tempfile
        
        fd, path = tempfile.mkstemp(suffix='.csv')
        try:
            with os.fdopen(fd, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["pre_test_score", "post_test_score"])
                writer.writerow([50, 60])
                
            records = load_public_dataset(path)
            assert len(records) > 0 # Should fallback to synthetic
        finally:
            os.remove(path)
