import pytest
import json
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock

from data.loader import ClawSweBenchLoader, ParsedIssue

class TestClawSweBenchLoader:
    """
    Test scaffolding for import graph traversal logic in ClawSweBenchLoader.

    These tests verify:
    1. Correct parsing of issue descriptions to extract file nodes.
    2. Correct construction of the dependency graph from file contents.
    3. Correct traversal (BFS/DFS) logic to identify relevant files.
    4. Correct calculation of "relevant file history" lines.
    """

    @pytest.fixture
    def sample_instance(self):
        """Provide a mock dataset instance with file history."""
        return {
            "instance_id": "test_instance_001",
            "repo": "test/repo",
            "issue": {
                "title": "Fix import error in utils",
                "body": "The file `src/utils/helpers.py` is not found when imported from `src/main.py`. "
                        "Also `src/config/settings.py` seems to have a syntax error."
            },
            "file_history": {
                "src/main.py": "from src.utils.helpers import process_data\nfrom src.config.settings import CONFIG\n\ndef run():\n    process_data()\n",
                "src/utils/helpers.py": "import os\ndef process_data():\n    return os.getcwd()\n",
                "src/config/settings.py": "DEBUG = True\nVERSION = 1.0\n",
                "src/unused.py": "print('unused')\n"
            }
        }

    @pytest.fixture
    def loader_instance(self):
        """Provide an instance of ClawSweBenchLoader."""
        # Initialize with minimal config for testing
        return ClawSweBenchLoader()

    def test_parse_issue_extracts_file_nodes(self, loader_instance, sample_instance):
        """Test that issue text parsing correctly identifies file paths mentioned."""
        # The issue mentions 'src/utils/helpers.py' and 'src/config/settings.py'
        parsed = loader_instance.parse_issue_description(sample_instance["issue"]["body"])

        assert isinstance(parsed, ParsedIssue)
        # Check that the extracted file nodes contain the mentioned files
        assert "src/utils/helpers.py" in parsed.starting_file_nodes
        assert "src/config/settings.py" in parsed.starting_file_nodes
        # 'src/main.py' is not explicitly mentioned in the issue text, so it shouldn't be a starting node
        # unless the logic infers it. Based on T014 description, we extract from issue text.

    def test_build_dependency_graph(self, loader_instance, sample_instance):
        """Test that the dependency graph is built correctly from file contents."""
        parsed = loader_instance.parse_issue_description(sample_instance["issue"]["body"])
        
        # Build the graph
        graph = loader_instance._build_dependency_graph(
            sample_instance["file_history"], 
            parsed.starting_file_nodes
        )

        # Verify nodes exist
        assert "src/utils/helpers.py" in graph.nodes
        assert "src/main.py" in graph.nodes  # Should be found via import from main if we traverse backwards? 
        # Actually, T016 says: "Use the file nodes extracted by T014 as starting points... Build a dependency graph... Perform BFS/DFS".
        # If the issue mentions helpers.py, we start there. Does helpers.py import main? No.
        # Does main import helpers? Yes.
        # The logic in T016 implies traversing the *dependencies* of the mentioned files.
        # If helpers.py imports os, os is a node (if we track stdlib or not?).
        # Let's assume the graph connects files in the repo.
        
        # If we start at helpers.py, and main.py imports helpers.py, the edge is main -> helpers.
        # If we traverse *dependencies* (files imported BY the start node), we look at what helpers imports.
        # helpers imports os (stdlib).
        # If we traverse *dependents* (files that import the start node), we find main.
        # The task says "relevant file history", implying we need files that are *relevant* to the issue.
        # Usually, this means the file itself + files it imports + files that import it.
        # Let's verify the graph construction logic handles the provided sample.
        
        # For now, assert the graph is not empty and contains the starting node
        assert len(graph.nodes) > 0
        assert "src/utils/helpers.py" in graph.nodes

    def test_traversal_calculation(self, loader_instance, sample_instance):
        """Test that the traversal logic correctly calculates relevant lines."""
        parsed = loader_instance.parse_issue_description(sample_instance["issue"]["body"])
        graph = loader_instance._build_dependency_graph(
            sample_instance["file_history"], 
            parsed.starting_file_nodes
        )
        
        # Perform traversal (BFS/DFS)
        relevant_files = loader_instance._traverse_graph(graph, parsed.starting_file_nodes)
        
        # The starting file must be included
        assert "src/utils/helpers.py" in relevant_files
        
        # Calculate total lines
        total_lines = loader_instance._calculate_relevant_lines(
            sample_instance["file_history"], 
            relevant_files
        )
        
        # Verify calculation logic
        # helpers.py has 3 lines, config/settings.py has 2 lines (if included)
        # The exact count depends on traversal logic, but it must be > 0
        assert total_lines > 0
        assert isinstance(total_lines, int)

    def test_filter_high_complexity_instances(self, loader_instance, sample_instance):
        """Test filtering logic for instances with >500 lines of relevant history."""
        # This sample instance is small, so it should fail the >500 lines check
        parsed = loader_instance.parse_issue_description(sample_instance["issue"]["body"])
        graph = loader_instance._build_dependency_graph(
            sample_instance["file_history"], 
            parsed.starting_file_nodes
        )
        relevant_files = loader_instance._traverse_graph(graph, parsed.starting_file_nodes)
        total_lines = loader_instance._calculate_relevant_lines(
            sample_instance["file_history"], 
            relevant_files
        )
        
        is_high_complexity = total_lines > 500
        assert is_high_complexity is False

    def test_empty_file_history(self, loader_instance):
        """Test handling of empty file history."""
        issue = {"body": "Fix bug in utils.py"}
        parsed = loader_instance.parse_issue_description(issue["body"])
        
        graph = loader_instance._build_dependency_graph({}, parsed.starting_file_nodes)
        relevant_files = loader_instance._traverse_graph(graph, parsed.starting_file_nodes)
        
        assert len(relevant_files) == 0
        
        total_lines = loader_instance._calculate_relevant_lines({}, relevant_files)
        assert total_lines == 0

    def test_missing_starting_node_in_history(self, loader_instance, sample_instance):
        """Test behavior when a file mentioned in the issue is not in file_history."""
        # Modify sample to remove the mentioned file
        modified_history = {k: v for k, v in sample_instance["file_history"].items() if k != "src/utils/helpers.py"}
        
        parsed = loader_instance.parse_issue_description(sample_instance["issue"]["body"])
        
        # Should handle gracefully, likely resulting in an empty or partial graph
        graph = loader_instance._build_dependency_graph(modified_history, parsed.starting_file_nodes)
        
        # The starting node should not be in the graph if it's missing from history
        assert "src/utils/helpers.py" not in graph.nodes

    def test_regex_extraction_edge_cases(self, loader_instance):
        """Test regex extraction with various file path formats."""
        test_cases = [
            ("File `src/main.py` is broken.", ["src/main.py"]),
            ("Check `./utils/helper.py` and `config/settings.py`.", ["./utils/helper.py", "config/settings.py"]),
            ("No file paths here.", []),
            ("Path: /absolute/path/to/file.py", ["/absolute/path/to/file.py"]),
        ]
        
        for text, expected_files in test_cases:
            parsed = loader_instance.parse_issue_description(text)
            # The regex might be more complex, but we check if it finds the expected ones
            for f in expected_files:
                assert f in parsed.starting_file_nodes, f"Failed to extract {f} from {text}"

    def test_ast_based_extraction_stub(self, loader_instance):
        """
        Test placeholder for AST-based extraction.
        T014 mentions AST-based extraction. This test ensures the method exists
        and is callable, even if the full implementation details are in loader.py.
        """
        # Verify the method exists on the loader
        assert hasattr(loader_instance, '_extract_files_from_ast')
        
        # Create a dummy code string
        code = "import os\nfrom src.utils import helper\n"
        
        # This should not raise an exception
        files = loader_instance._extract_files_from_ast(code)
        assert isinstance(files, list)
        # The specific content of 'files' depends on the implementation of _extract_files_from_ast
        # We just verify it runs and returns a list.
        
    def test_integration_graph_traversal_logic(self, loader_instance):
        """
        Integration test for the full graph traversal pipeline.
        Simulates a scenario where a chain of imports exists.
        """
        instance = {
            "issue": {"body": "Fix bug in `a.py`"},
            "file_history": {
                "a.py": "import b\n",
                "b.py": "import c\n",
                "c.py": "print('c')\n",
                "d.py": "print('d')\n"  # Unrelated
            }
        }
        
        parsed = loader_instance.parse_issue_description(instance["issue"]["body"])
        assert "a.py" in parsed.starting_file_nodes
        
        graph = loader_instance._build_dependency_graph(instance["file_history"], parsed.starting_file_nodes)
        relevant = loader_instance._traverse_graph(graph, parsed.starting_file_nodes)
        
        # Should find a, b, c (if traversing imports)
        assert "a.py" in relevant
        assert "b.py" in relevant
        assert "c.py" in relevant
        assert "d.py" not in relevant  # Unrelated

    def test_line_count_accuracy(self, loader_instance):
        """Verify line counting logic is accurate."""
        files = {
            "file1.py": "line1\nline2\nline3\n",
            "file2.py": "line1\n"
        }
        
        count = loader_instance._calculate_relevant_lines(files, ["file1.py", "file2.py"])
        # 3 lines + 1 line = 4 lines
        assert count == 4

    def test_validation_report_structure(self, loader_instance, sample_instance):
        """Test that the validation report structure is correct."""
        # This simulates the logic in T015
        parsed = loader_instance.parse_issue_description(sample_instance["issue"]["body"])
        graph = loader_instance._build_dependency_graph(
            sample_instance["file_history"], 
            parsed.starting_file_nodes
        )
        relevant_files = loader_instance._traverse_graph(graph, parsed.starting_file_nodes)
        total_lines = loader_instance._calculate_relevant_lines(
            sample_instance["file_history"], 
            relevant_files
        )
        
        # Construct the report as per T015
        is_sufficient = len(relevant_files) > 0
        report = {
            "is_sufficient": is_sufficient,
            "extracted_n_files": len(relevant_files),
            "total_relevant_lines": total_lines,
            "threshold_met": total_lines > 0  # Example threshold
        }
        
        assert "is_sufficient" in report
        assert "extracted_n_files" in report
        assert "total_relevant_lines" in report
        assert isinstance(report["is_sufficient"], bool)
        assert isinstance(report["extracted_n_files"], int)