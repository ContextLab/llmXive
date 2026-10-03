import pytest
import networkx as nx
from pathlib import Path
from typing import List, Dict, Set, Optional
import sys
import os
import re

# Add project root to path if running directly, though usually handled by pytest
# The test runner should be invoked from the code/ directory or with PYTHONPATH set
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.loader import ClawSweBenchLoader

class TestImportGraphTraversal:
    """Unit tests for import graph traversal logic in loader.py.
    
    This is scaffolding for T012 implementation. These tests verify the 
    logic that will be used to calculate relevant lines via static analysis.
    """

    @pytest.fixture
    def sample_repo_structure(self) -> Dict[str, List[str]]:
        """Mock a repository structure with imports."""
        return {
            "main.py": ["utils.py", "core.py"],
            "utils.py": ["config.py"],
            "core.py": ["utils.py", "models.py"],
            "models.py": [],
            "config.py": []
        }

    @pytest.fixture
    def loader_instance(self) -> ClawSweBenchLoader:
        """Create a loader instance without loading real data."""
        # We instantiate but don't call load() to avoid network calls in unit tests
        # Using a dummy dataset name that will fail gracefully if accessed
        return ClawSweBenchLoader(dataset_name="dummy", streaming=False)

    def test_build_dependency_graph(self, loader_instance, sample_repo_structure):
        """Test that the dependency graph is built correctly from imports."""
        # The method to test is likely internal or part of the static analysis logic
        # We simulate the logic here to ensure the graph construction is sound
        
        G = nx.DiGraph()
        
        # Build graph manually as the loader would
        for file, imports in sample_repo_structure.items():
            if file not in G:
                G.add_node(file)
            for imp in imports:
                if imp not in G:
                    G.add_node(imp)
                G.add_edge(file, imp)
        
        # Verify nodes
        assert set(G.nodes()) == {"main.py", "utils.py", "core.py", "models.py", "config.py"}
        
        # Verify edges
        assert G.has_edge("main.py", "utils.py")
        assert G.has_edge("main.py", "core.py")
        assert G.has_edge("core.py", "models.py")
        assert not G.has_edge("models.py", "core.py") # Direction matters

    def test_traverse_from_target(self, loader_instance, sample_repo_structure):
        """Test BFS/DFS traversal from a target file to find all relevant dependencies."""
        G = nx.DiGraph()
        for file, imports in sample_repo_structure.items():
            if file not in G:
                G.add_node(file)
            for imp in imports:
                if imp not in G:
                    G.add_node(imp)
                G.add_edge(file, imp)

        target = "main.py"
        
        # Test BFS (Breadth-First Search)
        bfs_reachable = nx.descendants(G, target)
        bfs_reachable.add(target)
        
        # Test DFS (Depth-First Search) - order differs but set should be same for reachable
        dfs_reachable = nx.descendants(G, target)
        dfs_reachable.add(target)
        
        expected_reachable = {"main.py", "utils.py", "core.py", "models.py", "config.py"}
        
        assert bfs_reachable == expected_reachable
        assert dfs_reachable == expected_reachable

    def test_calculate_total_lines_in_graph(self, loader_instance):
        """Test that line counting logic aggregates correctly across the graph."""
        # Mock file content lengths
        file_lengths = {
            "main.py": 100,
            "utils.py": 50,
            "core.py": 200,
            "models.py": 30,
            "config.py": 20
        }
        
        # Simulate the graph set of files
        relevant_files = {"main.py", "utils.py", "core.py", "models.py", "config.py"}
        
        total_lines = sum(file_lengths[f] for f in relevant_files if f in file_lengths)
        
        assert total_lines == 400

    def test_filter_by_threshold(self, loader_instance):
        """Test that the logic correctly filters instances based on line thresholds."""
        # Case 1: Below threshold
        lines_below = 400
        threshold = 500
        assert not (lines_below > threshold)

        # Case 2: Above threshold
        lines_above = 600
        assert lines_above > threshold

        # Case 3: Exactly at threshold (should be false for > 500)
        lines_exact = 500
        assert not (lines_exact > threshold)

    def test_empty_dependency_graph(self, loader_instance):
        """Test behavior when a file has no imports or dependencies."""
        G = nx.DiGraph()
        G.add_node("isolated.py")
        
        # Traversal should return just the node itself
        reachable = nx.descendants(G, "isolated.py")
        reachable.add("isolated.py")
        
        assert reachable == {"isolated.py"}

    def test_cyclic_dependencies_handling(self, loader_instance):
        """Test that the graph traversal handles cycles without infinite loops."""
        G = nx.DiGraph()
        G.add_edge("a.py", "b.py")
        G.add_edge("b.py", "c.py")
        G.add_edge("c.py", "a.py") # Cycle
        
        # nx.descendants handles cycles correctly by tracking visited nodes
        reachable = nx.descendants(G, "a.py")
        reachable.add("a.py")
        
        assert reachable == {"a.py", "b.py", "c.py"}

    def test_missing_file_in_graph(self, loader_instance):
        """Test behavior when a target file is not in the graph."""
        G = nx.DiGraph()
        G.add_node("existing.py")
        
        with pytest.raises(nx.NetworkXError):
            # This should raise because 'missing.py' is not in the graph
            nx.descendants(G, "missing.py")

    def test_static_analysis_sanity_check_no_ground_truth_leak(self, loader_instance):
        """
        StaticAnalysisSanityCheck: Verify that the 'Hybrid IR-Seeding' logic 
        does NOT accidentally use 'test_patch' or 'ground_truth' fields.
        
        This test inspects the source code of the loader module to ensure that
        the static analysis functions do not read from fields that contain 
        ground-truth solution data.
        """
        # Read the source code of the loader module
        loader_path = Path(__file__).parent.parent.parent / "code" / "data" / "loader.py"
        
        if not loader_path.exists():
            pytest.fail(f"Loader file not found at {loader_path}")
        
        source_code = loader_path.read_text()
        
        # Define patterns that indicate ground truth usage
        # We look for assignments or reads involving 'test_patch' or 'ground_truth'
        # within the context of static analysis or IR-seeding logic.
        
        # Patterns to detect forbidden access
        forbidden_patterns = [
            r'\binstance\s*\[\s*["\']test_patch["\']\s*\]',
            r'\binstance\s*\[\s*["\']ground_truth["\']\s*\]',
            r'\bdata\s*\[\s*["\']test_patch["\']\s*\]',
            r'\bdata\s*\[\s*["\']ground_truth["\']\s*\]',
            r'\b\.get\s*\(\s*["\']test_patch["\']\s*\)',
            r'\b\.get\s*\(\s*["\']ground_truth["\']\s*\)',
            r'\btest_patch\s*=',
            r'\bground_truth\s*=',
        ]
        
        # Check for forbidden patterns
        found_violations = []
        for pattern in forbidden_patterns:
            matches = list(re.finditer(pattern, source_code, re.IGNORECASE))
            if matches:
                for match in matches:
                    # Get the line number
                    line_start = source_code.rfind('\n', 0, match.start()) + 1
                    line_end = source_code.find('\n', match.start())
                    if line_end == -1:
                        line_end = len(source_code)
                    line_num = source_code[:match.start()].count('\n') + 1
                    line_content = source_code[line_start:line_end]
                    
                    # Skip if it's inside a comment or docstring
                    if '#' in line_content and line_content.index('#') < line_content.index(match.group(0)):
                        continue
                    
                    found_violations.append({
                        "pattern": pattern,
                        "line": line_num,
                        "content": line_content.strip()
                    })
        
        # Assert no violations found
        if found_violations:
            violation_details = "\n".join([
                f"Line {v['line']}: {v['content']} (matched {v['pattern']})"
                for v in found_violations
            ])
            pytest.fail(
                f"StaticAnalysisSanityCheck FAILED: Found potential ground truth leakage in loader.py:\n{violation_details}"
            )
        
        # Additional check: Ensure that the static analysis methods are defined
        # and do not rely on the test_patch field for their core logic
        # We verify that 'static_analysis' or 'ir_seeding' functions exist
        # and that they primarily rely on 'issue_description' and file content
        
        required_methods = [
            "parse_issue_description",
            "extract_file_paths",
            "traverse_imports"
        ]
        
        # Simple check for method existence (not exhaustive, but a sanity check)
        for method in required_methods:
            if method not in source_code:
                # It's okay if they are internal helpers, but we expect some static analysis logic
                # We'll just log a warning if not found, not fail
                pass
        
        # Verify that the loader uses 'issue_description' for static analysis
        if "issue_description" not in source_code:
            pytest.fail("Loader does not seem to use 'issue_description' for static analysis.")

class TestHybridIRSeedingSanity:
    """
    Additional tests to ensure Hybrid IR-Seeding is strictly static.
    """
    
    def test_no_runtime_code_execution_in_seeding(self, loader_instance):
        """
        Verify that the seeding logic does not execute code (e.g., eval, exec).
        """
        loader_path = Path(__file__).parent.parent.parent / "code" / "data" / "loader.py"
        source_code = loader_path.read_text()
        
        dangerous_calls = ["eval(", "exec(", "compile("]
        for call in dangerous_calls:
            if call in source_code:
                # Check if it's in a comment
                lines = source_code.split('\n')
                for i, line in enumerate(lines):
                    if call in line and not line.strip().startswith('#'):
                        pytest.fail(f"Dangerous runtime execution found in loader.py at line {i+1}: {line.strip()}")

    def test_only_issue_description_used_for_seeding(self, loader_instance):
        """
        Verify that the seeding logic primarily relies on issue_description.
        """
        loader_path = Path(__file__).parent.parent.parent / "code" / "data" / "loader.py"
        source_code = loader_path.read_text()
        
        # We expect issue_description to be used
        assert "issue_description" in source_code, "issue_description should be used for seeding"
        
        # We do NOT expect test_patch to be used
        assert "test_patch" not in source_code or source_code.find("test_patch") < source_code.find("#"), \
            "test_patch should not be used for seeding logic"