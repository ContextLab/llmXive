"""
Integration tests for the pipeline.
"""
import pytest
import os
from pathlib import Path
from code.ingest.annotate_graph import main as annotate_main
from code.analysis.stratify_accuracy import main as stratify_main
from code.analysis.detect_threshold import main as detect_main

def test_full_pipeline():
    # This test assumes the data files exist
    # It runs the main functions of the pipeline
    try:
        annotate_main()
        stratify_main()
        detect_main()
        assert True
    except Exception as e:
        pytest.fail(f"Pipeline failed: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
