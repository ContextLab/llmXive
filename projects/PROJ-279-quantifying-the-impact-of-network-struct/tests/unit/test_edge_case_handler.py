"""
Unit tests for edge case handling in edge_case_handler.py.
Tests for:
1. Corrupted file detection and abortion.
2. Unexpected coordination number detection and flagging/dropping.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from code.edge_case_handler import (
    detect_corrupted_file,
    handle_corrupted_file,
    handle_unexpected_coordination,
    analyze_coordination_numbers,
    process_with_edge_case_handling,
    CorruptedFileError,
    UnexpectedCoordinationError,
    save_edge_case_report
)


class TestCorruptedFileDetection:
    def test_detect_nonexistent_file(self, tmp_path):
        """Test that a non-existent file is detected as corrupted."""
        fake_path = tmp_path / "does_not_exist.xyz"
        assert detect_corrupted_file(fake_path) is True

    def test_detect_empty_file(self, tmp_path):
        """Test that an empty file is detected as corrupted."""
        empty_file = tmp_path / "empty.xyz"
        empty_file.write_text("")
        assert detect_corrupted_file(empty_file) is True

    def test_detect_invalid_xyz_header(self, tmp_path):
        """Test that a file with invalid XYZ header (non-integer) is corrupted."""
        invalid_file = tmp_path / "invalid_header.xyz"
        invalid_file.write_text("NotANumber\nComment line\n")
        assert detect_corrupted_file(invalid_file) is True

    def test_detect_truncated_xyz(self, tmp_path):
        """Test that a file with fewer atoms than declared is corrupted."""
        truncated_file = tmp_path / "truncated.xyz"
        # Declares 10 atoms but only provides 2 lines of data
        content = "10\nComment\nSi 0 0 0\nSi 1 1 1\n"
        truncated_file.write_text(content)
        assert detect_corrupted_file(truncated_file) is True

    def test_detect_valid_xyz(self, tmp_path):
        """Test that a valid XYZ file passes detection."""
        valid_file = tmp_path / "valid.xyz"
        # 2 atoms, 2 lines of coords
        content = "2\nComment\nSi 0.0 0.0 0.0\nSi 1.0 1.0 1.0\n"
        valid_file.write_text(content)
        assert detect_corrupted_file(valid_file) is False


class TestCoordinationAnalysis:
    def test_analyze_normal_coordination(self):
        """Test analysis of a graph with normal coordination numbers (4)."""
        # 4 atoms, each connected to 2 others (ring), but let's make a simple chain or star
        # Let's make a central atom connected to 3 others (coord 3, 1, 1, 1) - all within range
        graph_data = {
            "nodes": [{"id": 0}, {"id": 1}, {"id": 2}, {"id": 3}],
            "edges": [
                {"u": 0, "v": 1},
                {"u": 0, "v": 2},
                {"u": 0, "v": 3}
            ]
        }
        has_unexpected, counts = analyze_coordination_numbers(graph_data, "test_config")
        assert has_unexpected is False
        assert counts[3] == 1
        assert counts[1] == 3

    def test_analyze_unexpected_low_coordination(self):
        """Test detection of atoms with coordination < 2."""
        # Atom 0 connected to nothing (coord 0)
        graph_data = {
            "nodes": [{"id": 0}, {"id": 1}],
            "edges": []
        }
        has_unexpected, counts = analyze_coordination_numbers(graph_data, "test_config")
        assert has_unexpected is True
        assert counts[0] == 2

    def test_analyze_unexpected_high_coordination(self):
        """Test detection of atoms with coordination > 6."""
        # Create a star graph where center has degree 10
        nodes = [{"id": i} for i in range(11)]
        edges = [{"u": 0, "v": i} for i in range(1, 11)]
        graph_data = {"nodes": nodes, "edges": edges}
        
        has_unexpected, counts = analyze_coordination_numbers(graph_data, "test_config")
        assert has_unexpected is True
        assert counts[10] == 1


class TestEdgeCaseHandling:
    def test_handle_corrupted_file_raises(self, tmp_path, caplog):
        """Test that handle_corrupted_file raises CorruptedFileError."""
        fake_file = tmp_path / "bad.xyz"
        with pytest.raises(CorruptedFileError):
            handle_corrupted_file(fake_file)

    def test_handle_unexpected_coordination_raises(self, caplog):
        """Test that handle_unexpected_coordination raises UnexpectedCoordinationError."""
        invalid_coords = {0: 1, 10: 1}
        with pytest.raises(UnexpectedCoordinationError) as exc_info:
            handle_unexpected_coordination("config_123", invalid_coords)
        
        assert "config_123" in str(exc_info.value)
        assert "0" in str(exc_info.value)

    def test_process_with_edge_case_handling_corrupted(self, tmp_path):
        """Test that process_with_edge_case_handling aborts on corrupted file."""
        bad_file = tmp_path / "bad.xyz"
        bad_file.write_text("BadHeader\n")
        
        with pytest.raises(CorruptedFileError):
            process_with_edge_case_handling(bad_file)

    def test_process_with_edge_case_handling_unexpected_coords(self, tmp_path):
        """Test that process_with_edge_case_handling drops on unexpected coords."""
        good_file = tmp_path / "good.xyz"
        good_file.write_text("2\nComment\nSi 0 0 0\nSi 1 1 1\n")
        
        bad_graph = {
            "nodes": [{"id": 0}],
            "edges": [] # Coord 0
        }
        
        with pytest.raises(UnexpectedCoordinationError):
            process_with_edge_case_handling(good_file, bad_graph, "test_id")


class TestReportSaving:
    def test_save_edge_case_report(self, tmp_path):
        """Test saving the edge case report JSON."""
        report_path = tmp_path / "edge_cases.json"
        dropped = ["config_A", "config_B"]
        corrupted = ["/path/to/bad.xyz"]
        
        save_edge_case_report(report_path, dropped, corrupted)
        
        assert report_path.exists()
        with open(report_path, 'r') as f:
            data = json.load(f)
        
        assert data["summary"]["total_dropped"] == 2
        assert data["summary"]["total_corrupted"] == 1
        assert data["dropped_due_to_coordination"] == dropped
        assert data["corrupted_files"] == corrupted
