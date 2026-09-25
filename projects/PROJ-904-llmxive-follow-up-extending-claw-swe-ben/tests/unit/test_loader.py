"""
Unit tests for ClawSweBenchLoader.
Scaffolding for import graph traversal logic (T010/T012a).
"""
import pytest
import networkx as nx
from pathlib import Path
from typing import List, Dict, Set, Optional
import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.join(os.dirname(__file__), '..', '..')))

from data.loader import ClawSweBenchLoader, ParsedIssue
from config import set_global_seeds

class TestClawSweBenchLoader:
    """Tests for ClawSweBenchLoader."""

    @pytest.fixture
    def loader(self):
        set_global_seeds(42)
        return ClawSweBenchLoader(seed=42)

    def test_init(self, loader):
        """Test initialization."""
        assert loader.seed == 42
        assert loader.data_dir is not None
        assert loader.output_dir is not None

    def test_parse_issue_description(self, loader):
        """Test parsing issue description for file paths."""
        description = "Fix bug in src/utils.py and update tests/test_utils.py"
        parsed = loader._parse_issue_description(description)
        
        assert "src/utils.py" in parsed.file_paths
        assert "tests/test_utils.py" in parsed.file_paths
        assert len(parsed.file_paths) >= 2

    def test_calculate_relevant_lines(self, loader):
        """Test line counting logic."""
        file_contents = {
            "file1.py": "line1\nline2\nline3",
            "file2.py": "line1\nline2"
        }
        count = loader._calculate_relevant_lines(file_contents)
        assert count == 5

    def test_build_import_graph(self, loader):
        """Test import graph building."""
        file_contents = {
            "main.py": "import utils\nfrom helpers import func",
            "utils.py": "import math"
        }
        G = loader._build_import_graph(file_contents)
        
        assert "main.py" in G.nodes
        assert "utils.py" in G.nodes
        assert ("main.py", "utils") in G.edges or ("main.py", "helpers") in G.edges
        assert G.number_of_nodes() >= 2

    def test_filter_dataset_streaming(self, loader, tmp_path):
        """Test filtering with streaming (mocked)."""
        # This test mocks the fetch to avoid network dependency in unit tests
        # In integration tests, we test the real fetch
        import pandas as pd
        from unittest.mock import patch, MagicMock

        mock_data = [
            {"instance_id": "1", "problem_statement": "Fix bug in a.py", "file_contents": {"a.py": "x\ny\nz\nw\nv\nu\nt\ns\nr\nq\np\no\nn\nm\nl\nk\nj\ni\nh\ng\nf\ne\nd\nc\nb\na"}}, # 27 lines
            {"instance_id": "2", "problem_statement": "Fix bug in b.py", "file_contents": {"b.py": "x"}}, # 1 line
        ]

        with patch.object(loader, '_fetch_streaming', return_value=iter(mock_data)):
            df = loader.filter_dataset(min_lines=10, output_path=str(tmp_path / "test.parquet"))
            
            assert len(df) == 1
            assert df.iloc[0]['instance_id'] == '1'
            assert df.iloc[0]['_filtered_line_count'] == 27

class TestImportGraphTraversal:
    """Scaffolding tests for import graph traversal logic (T010)."""
    
    def test_graph_traversal_placeholder(self):
        """Placeholder test to ensure scaffolding exists."""
        # This test is for T010 scaffolding
        assert True
