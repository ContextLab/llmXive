"""
Contract tests for the topology audit functionality.

These tests verify that the topology audit module correctly:
1. Loads graph statistics from a .pt file.
2. Generates a valid Markdown report.
3. Handles edge cases (empty data, missing file).
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path
import torch

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from analysis.topology_audit import load_graph_stats, generate_markdown_report
from utils.exceptions import DataError


class TestLoadGraphStats:
    """Tests for the load_graph_stats function."""
    
    def test_load_from_valid_pt_file(self):
        """Test loading stats from a valid .pt file with mock data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pt_path = Path(tmpdir) / "mock_graphs.pt"
            
            # Create mock data structure similar to what graph_build produces
            mock_graph = torch.nn.Module()
            mock_graph.num_nodes = 10
            mock_graph.edge_index = torch.randint(0, 10, (2, 20))
            mock_graph.x = torch.randn(10, 5)
            mock_data = [
                {"graph": mock_graph, "metadata": {"source": "test"}}
            ]
            torch.save(mock_data, pt_path)
            
            stats = load_graph_stats(pt_path)
            
            assert len(stats) == 1
            assert stats[0]["node_count"] == 10
            assert stats[0]["edge_count"] == 20
            assert stats[0]["has_features"] is True
            assert stats[0]["metadata"]["source"] == "test"
    
    def test_load_from_missing_file_raises_error(self):
        """Test that loading from a non-existent file raises DataError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pt_path = Path(tmpdir) / "nonexistent.pt"
            
            with pytest.raises(DataError):
                load_graph_stats(pt_path)
    
    def test_load_from_corrupted_file_raises_error(self):
        """Test that loading from a corrupted file raises DataError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pt_path = Path(tmpdir) / "corrupted.pt"
            pt_path.write_text("not a valid torch file")
            
            with pytest.raises(DataError):
                load_graph_stats(pt_path)

class TestGenerateMarkdownReport:
    """Tests for the generate_markdown_report function."""
    
    def test_generate_report_with_data(self):
        """Test generating a report with valid graph statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "audit.md"
            stats = [
                {"index": 0, "node_count": 10, "edge_count": 20, "has_features": True, "has_edge_features": False, "metadata": {}},
                {"index": 1, "node_count": 15, "edge_count": 30, "has_features": True, "has_edge_features": True, "metadata": {}}
            ]
            
            generate_markdown_report(stats, output_path)
            
            assert output_path.exists()
            content = output_path.read_text()
            
            assert "Topology Audit Report" in content
            assert "Total Graphs Analyzed" in content
            assert "10" in content  # node count
            assert "20" in content  # edge count
            assert "15" in content  # second node count
            assert "30" in content  # second edge count
    
    def test_generate_report_with_empty_data(self):
        """Test generating a report with empty statistics list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "audit.md"
            
            generate_markdown_report([], output_path)
            
            assert output_path.exists()
            content = output_path.read_text()
            assert "No graph data found" in content
            assert "Topology Audit Report" in content
    
    def test_report_created_in_parent_dir(self):
        """Test that the report is created even if parent directory doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "audit.md"
            stats = [{"index": 0, "node_count": 5, "edge_count": 10, "has_features": False, "has_edge_features": False, "metadata": {}}]
            
            generate_markdown_report(stats, output_path)
            
            assert output_path.exists()