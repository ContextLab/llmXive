"""
Unit tests for ClawSweBenchLoader import graph traversal logic.
"""
import pytest
import networkx as nx
from pathlib import Path
from typing import List, Dict, Set, Optional
import sys
import os

# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.loader import ClawSweBenchLoader, ParsedIssue

class TestImportGraphTraversal:
    """Tests for import graph traversal logic in ClawSweBenchLoader."""

    def test_parse_imports_simple(self):
        """Test parsing simple import statements."""
        loader = ClawSweBenchLoader()
        content = """
        import os
        import sys
        from collections import defaultdict
        """
        imports = loader._parse_imports(content)
        assert 'os' in imports
        assert 'sys' in imports
        assert 'collections' in imports

    def test_parse_imports_from(self):
        """Test parsing 'from X import Y' statements."""
        loader = ClawSweBenchLoader()
        content = """
        from numpy import array
        from pandas import DataFrame
        """
        imports = loader._parse_imports(content)
        assert 'numpy' in imports
        assert 'pandas' in imports

    def test_parse_imports_syntax_error(self):
        """Test that syntax errors in file content are handled gracefully."""
        loader = ClawSweBenchLoader()
        content = """
        import os
        from invalid syntax here
        """
        imports = loader._parse_imports(content)
        # Should not raise, just return what it could parse
        assert isinstance(imports, list)

    def test_extract_file_paths(self):
        """Test file path extraction from issue descriptions."""
        loader = ClawSweBenchLoader()
        description = """
        The bug is in src/main.py and utils/helper.py.
        Please check ./config/settings.py as well.
        """
        paths = loader._extract_file_paths(description)
        assert 'src/main.py' in paths
        assert 'utils/helper.py' in paths
        assert 'config/settings.py' in paths

    def test_extract_file_paths_none(self):
        """Test extraction when no file paths are found."""
        loader = ClawSweBenchLoader()
        description = "This is a general bug report with no file references."
        paths = loader._extract_file_paths(description)
        assert len(paths) == 0

    def test_calculate_line_count(self):
        """Test line counting logic."""
        loader = ClawSweBenchLoader()
        content = """
        import os
        
        def hello():
            print("Hello")
        
        # This is a comment
        
        x = 1
        """
        count = loader._calculate_line_count(content)
        # Should count: import, def, print, x = 1 (4 lines)
        assert count == 4

    def test_traverse_import_graph_basic(self):
        """Test basic import graph traversal."""
        loader = ClawSweBenchLoader()
        file_contents = {
            'main.py': 'import utils',
            'utils.py': 'import helpers',
            'helpers.py': ''
        }
        result = loader._traverse_import_graph(['main.py'], file_contents, max_depth=2)
        assert 'main.py' in result
        assert 'utils.py' in result
        assert 'helpers.py' in result

    def test_traverse_import_graph_max_depth(self):
        """Test that traversal respects max_depth."""
        loader = ClawSweBenchLoader()
        file_contents = {
            'a.py': 'import b',
            'b.py': 'import c',
            'c.py': 'import d',
            'd.py': ''
        }
        # With max_depth=1, should only reach b
        result = loader._traverse_import_graph(['a.py'], file_contents, max_depth=1)
        assert 'a.py' in result
        assert 'b.py' in result
        assert 'c.py' not in result
        assert 'd.py' not in result

    def test_load_and_process_instance(self):
        """Test full instance processing pipeline."""
        loader = ClawSweBenchLoader()
        instance = {
            'instance_id': 'test-001',
            'issue_description': 'Bug in src/app.py',
            'file_contents': {
                'src/app.py': 'import utils\n\ndef main(): pass',
                'src/utils.py': 'def helper(): pass'
            }
        }
        task = loader.load_and_process_instance(instance)
        assert task is not None
        assert task.instance_id == 'test-001'
        assert 'src/app.py' in task.relevant_files

    def test_filter_dataset(self):
        """Test dataset filtering logic."""
        from data.loader import filter_dataset
        
        loader = ClawSweBenchLoader()
        instances = [
            {
                'instance_id': 'test-001',
                'issue_description': 'Bug in src/app.py',
                'file_contents': {
                    'src/app.py': 'import utils\n' * 200,  # ~200 lines
                    'src/utils.py': 'def helper(): pass\n' * 400  # ~400 lines
                }
            },
            {
                'instance_id': 'test-002',
                'issue_description': 'Small bug',
                'file_contents': {
                    'src/small.py': 'x = 1'  # 1 line
                }
            }
        ]
        
        filtered = filter_dataset(instances, min_lines=500, loader=loader)
        # First instance: ~600 lines, should pass
        # Second instance: ~1 line, should fail
        assert len(filtered) == 1
        assert filtered[0]['instance_id'] == 'test-001'
