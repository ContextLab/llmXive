"""
Integration tests for the full pipeline flow.
"""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

class TestPipelineFlow:
    """Integration tests for pipeline components working together."""

    def test_ingest_to_features_flow(self):
        """Test that data flows correctly from ingestion to feature engineering."""
        # This test verifies the directory structure and basic flow
        # Actual data flow testing requires real data execution
        project_root = Path(__file__).parent.parent.parent
        
        # Verify expected output directories exist
        assert (project_root / "data" / "raw").exists()
        assert (project_root / "data" / "processed").exists()
        assert (project_root / "data" / "features").exists()

    def test_logger_integration(self):
        """Test that logging works across components."""
        from utils.logger import setup_logging, get_logger
        
        logger = get_logger("integration_test")
        assert logger is not None
