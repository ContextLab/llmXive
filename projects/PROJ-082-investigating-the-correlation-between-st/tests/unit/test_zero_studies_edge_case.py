"""
Unit tests for the zero-studies edge case handling (T018).
Verifies that the system correctly identifies N=0 and generates the
appropriate 'Data Insufficient' report without attempting narrative synthesis.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the functions to test
from analysis.narrative_edge_case_handler import (
    load_study_count,
    generate_zero_studies_summary,
    run_zero_case_handler
)

class TestZeroStudiesEdgeCase:
    """Tests for T018: Handle zero-studies edge case."""

    def test_generate_zero_studies_summary_structure(self):
        """Verify the structure of the generated zero-studies summary."""
        summary = generate_zero_studies_summary()
        
        assert "metadata" in summary
        assert "content" in summary
        
        # Check metadata
        meta = summary["metadata"]
        assert meta["study_count"] == 0
        assert meta["synthesis_mode"] == "narrative"
        assert "timestamp" in meta
        assert meta["status"] == "data_insufficient"
        
        # Check content
        content = summary["content"]
        assert "No studies found" in content["header"]
        assert "Study Overview" in [s["title"] for s in content["sections"]]
        assert "Qualitative Themes" in [s["title"] for s in content["sections"]]
        assert "Limitations" in [s["title"] for s in content["sections"]]
        
        # Verify the specific disclaimer text required by Constitution Principle VII
        assert "SYSTEMATIC REVIEW FALLBACK" in content["disclaimer"]
        assert "Constitution Principle VII" in content["disclaimer"]

    def test_run_zero_case_handler_with_zero_count(self):
        """Test that the handler triggers and writes files when N=0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create a study_count.json with N=0
            count_file = tmpdir_path / "study_count.json"
            with open(count_file, 'w') as f:
                json.dump({"N": 0}, f)
            
            output_file = tmpdir_path / "output.json"
            
            # Run the handler
            success = run_zero_case_handler(
                study_count_file=count_file,
                output_file=output_file
            )
            
            assert success is True
            assert output_file.exists()
            
            # Verify the content of the output file
            with open(output_file, 'r') as f:
                result = json.load(f)
            
            assert result["metadata"]["study_count"] == 0
            assert result["metadata"]["status"] == "data_insufficient"
            
            # Check for the markdown file as well
            md_file = output_file.with_suffix('.md')
            assert md_file.exists()
            with open(md_file, 'r') as f:
                md_content = f.read()
            assert "# No studies found" in md_content
            assert "SYSTEMATIC REVIEW FALLBACK" in md_content

    def test_run_zero_case_handler_with_positive_count(self):
        """Test that the handler does NOT trigger when N > 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create a study_count.json with N=15
            count_file = tmpdir_path / "study_count.json"
            with open(count_file, 'w') as f:
                json.dump({"N": 15}, f)
            
            output_file = tmpdir_path / "output.json"
            
            # Run the handler
            success = run_zero_case_handler(
                study_count_file=count_file,
                output_file=output_file
            )
            
            assert success is False
            assert not output_file.exists()

    def test_load_study_count_missing_file(self):
        """Test that load_study_count returns N=0 if file is missing."""
        # Use a path that definitely doesn't exist
        missing_path = Path("/nonexistent/path/to/file.json")
        result = load_study_count(missing_path)
        assert result["N"] == 0

    def test_load_study_count_missing_n_key(self):
        """Test that load_study_count defaults to N=0 if 'N' key is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            count_file = tmpdir_path / "study_count.json"
            
            # Write JSON without 'N' key
            with open(count_file, 'w') as f:
                json.dump({"count": 5}, f)
            
            result = load_study_count(count_file)
            assert result["N"] == 0