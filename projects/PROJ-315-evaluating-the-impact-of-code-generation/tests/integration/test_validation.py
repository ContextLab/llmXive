import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import os

from code.data.preprocess import (
    check_completeness,
    check_power_insufficiency,
    run_validation_pipeline,
    write_error_report
)

class TestValidationPipeline:
    
    @pytest.fixture
    def mock_completeness_data(self):
        """Create a DataFrame with high completeness."""
        return pd.DataFrame({
            'code_diff': ['diff1', 'diff2', 'diff3'],
            'review_comments': ['comment1', 'comment2', 'comment3'],
            'project_id': ['p1', 'p2', 'p3'],
            'commit_id': ['c1', 'c2', 'c3'],
            'classification': ['llm', 'human', 'llm']
        })

    @pytest.fixture
    def mock_low_completeness_data(self):
        """Create a DataFrame with low completeness (missing required fields)."""
        return pd.DataFrame({
            'code_diff': ['diff1', None, 'diff3'],
            'review_comments': ['comment1', 'comment2', None],
            'project_id': ['p1', 'p2', 'p3'],
            'commit_id': ['c1', 'c2', 'c3'],
            'classification': ['llm', 'human', 'llm']
        })

    @pytest.fixture
    def mock_low_power_data(self):
        """Create a DataFrame with low power in one group."""
        # Create 600 'human' and 100 'llm' (below 500 threshold)
        data = {
            'code_diff': ['d'] * 700,
            'review_comments': ['c'] * 700,
            'project_id': ['p'] * 700,
            'commit_id': ['i'] * 700,
            'classification': ['human'] * 600 + ['llm'] * 100
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_check_completeness_high(self, mock_completeness_data):
        """Test that high completeness returns correct rate."""
        rate = check_completeness(mock_completeness_data)
        assert rate == 1.0

    def test_check_completeness_low(self, mock_low_completeness_data):
        """Test that low completeness raises ValueError."""
        with pytest.raises(ValueError) as excinfo:
            run_validation_pipeline(
                mock_low_completeness_data,
                completeness_threshold=0.95,
                error_report_path=Path(tempfile.gettempdir()) / "test_error.json"
            )
        assert "completeness" in str(excinfo.value).lower()

    def test_check_power_insufficiency(self, mock_low_power_data, temp_dir):
        """Test that insufficient group size raises ValueError."""
        error_path = temp_dir / "power_error.json"
        
        with pytest.raises(ValueError) as excinfo:
            run_validation_pipeline(
                mock_low_power_data,
                power_threshold=500,
                error_report_path=error_path
            )
        
        assert "power insufficiency" in str(excinfo.value).lower()
        
        # Verify error report was written
        assert error_path.exists()
        with open(error_path, 'r') as f:
            report = json.load(f)
        
        assert report['status'] == 'failed'
        assert 'insufficient_groups' in report['details']
        assert report['details']['insufficient_groups']['llm'] < 500

    def test_validation_passes(self, mock_completeness_data, temp_dir):
        """Test that valid data passes validation."""
        error_path = temp_dir / "error.json"
        stats_path = temp_dir / "stats.json"
        
        # Ensure we have enough samples to pass power check (add more data)
        mock_valid = pd.concat([mock_completeness_data] * 200, ignore_index=True)
        
        success, stats = run_validation_pipeline(
            mock_valid,
            completeness_threshold=0.95,
            power_threshold=500,
            error_report_path=error_path,
            stats_report_path=stats_path
        )
        
        assert success is True
        assert stats['validation_status'] == 'passed'
        
        # Verify no error report was created
        assert not error_path.exists()
        assert stats_path.exists()
