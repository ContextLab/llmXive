"""
Unit tests for the Syntactic Parser (T028/T029).
"""

import json
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from src.conditions.syntactic_parser import (
    extract_patterns,
    parse_failure_description,
    run,
    log_fallback
)

class TestSyntacticParser:

    def test_extract_patterns_object_interaction(self):
        """Test detection of object interaction failures."""
        text = "The agent failed to pick up the apple."
        matches = extract_patterns(text)
        assert len(matches) > 0
        assert any(m['pattern_type'] == 'object_interaction_fail' for m in matches)
        assert any('apple' in m['matched_text'] for m in matches)

    def test_extract_patterns_navigation(self):
        """Test detection of navigation failures."""
        text = "Cannot navigate to the bedroom."
        matches = extract_patterns(text)
        assert len(matches) > 0
        assert any(m['pattern_type'] == 'navigation_fail' for m in matches)

    def test_extract_patterns_no_match(self):
        """Test behavior when no patterns match."""
        text = "The agent just stared at the wall for 10 seconds."
        matches = extract_patterns(text)
        assert len(matches) == 0

    def test_parse_failure_description_success(self):
        """Test successful parsing and abstraction."""
        desc = "Failed to open the drawer."
        result = parse_failure_description(desc, "traj_001")
        assert result["status"] == "PARSED"
        assert "object_interaction_fail" in result["abstracted_signal"]
        assert result["original_text"] == desc

    def test_parse_failure_description_fallback(self):
        """Test fallback behavior when no pattern matches."""
        desc = "The agent got confused and stopped."
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock the fallback log path
            with patch("src.conditions.syntactic_parser.FALLBACK_LOG_PATH", os.path.join(tmpdir, "fallbacks.json")):
                result = parse_failure_description(desc, "traj_002")
                assert result["status"] == "FALLBACK"
                # Must retain raw text per T051
                assert result["abstracted_signal"] == desc
                assert result["original_text"] == desc

    def test_run_integration(self):
        """Test the full run() function with input/output files."""
        input_data = [
            {
                "id": "traj_1",
                "failure_description": "Failed to pick up the key.",
                "original_field": "test"
            },
            {
                "id": "traj_2",
                "failure_description": "Agent got lost.",
                "original_field": "test"
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.json")
            output_path = os.path.join(tmpdir, "output.json")
            fallback_path = os.path.join(tmpdir, "fallbacks.json")

            # Write input
            with open(input_path, "w") as f:
                json.dump(input_data, f)

            # Mock the fallback path
            with patch("src.conditions.syntactic_parser.FALLBACK_LOG_PATH", fallback_path):
                exit_code = run(input_path, output_path)

            assert exit_code == 0
            assert os.path.exists(output_path)

            with open(output_path, "r") as f:
                output_data = json.load(f)

            assert len(output_data) == 2
            assert output_data[0]["abstracted_signal"] != output_data[0]["failure_description"] # Should be abstracted
            assert output_data[1]["abstracted_signal"] == output_data[1]["failure_description"] # Should be fallback (raw)
            assert output_data[1]["parsing_status"] == "FALLBACK"

    def test_log_fallback_creates_file(self):
        """Test that log_fallback creates the file and writes valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "fallbacks.json")
            with patch("src.conditions.syntactic_parser.FALLBACK_LOG_PATH", log_path):
                log_fallback("traj_99", "Some weird error")
            
            assert os.path.exists(log_path)
            with open(log_path, "r") as f:
                content = f.read()
            # Check if it looks like JSON (starts with { or [ or is a line)
            # Since we append, it might be a line.
            assert "traj_99" in content
            assert "Some weird error" in content