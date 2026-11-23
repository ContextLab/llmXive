"""
Unit tests for src/data/descriptors.py
"""
import pytest
import json
import tempfile
from pathlib import Path
import csv

from src.data.models import CodeSnippet
from src.data.descriptors import (
    _calculate_api_density,
    _calculate_doc_density,
    _calculate_naming_consistency,
    compute_descriptors_for_query,
    compute_all_descriptors,
    load_snippets
)


class TestAPIDensity:
    """Tests for API density calculation."""

    def test_function_calls(self):
        """Test detection of function calls."""
        code = "print('hello')\nlen(arr)\nmy_func(x)"
        density = _calculate_api_density(code)
        assert density > 0, "Should detect function calls"

    def test_imports(self):
        """Test detection of import statements."""
        code = "import os\nfrom sys import path"
        density = _calculate_api_density(code)
        assert density > 0, "Should detect imports"

    def test_empty_code(self):
        """Test handling of empty code."""
        density = _calculate_api_density("")
        assert density == 0.0, "Empty code should have 0 density"

    def test_no_api_patterns(self):
        """Test code with no API patterns."""
        code = "x = 1\ny = 2"
        density = _calculate_api_density(code)
        # Should be low but not necessarily zero due to variable access patterns
        assert 0 <= density <= 1, "Density should be between 0 and 1"


class TestDocDensity:
    """Tests for documentation density calculation."""

    def test_docstrings(self):
        """Test detection of docstrings."""
        code = '"""This is a docstring."""\ndef foo():\n    """Another docstring."""'
        density = _calculate_doc_density(code)
        assert density > 0, "Should detect docstrings"

    def test_comments(self):
        """Test detection of descriptive comments."""
        code = "# This is a comment\n# Another comment"
        density = _calculate_doc_density(code)
        assert density > 0, "Should detect comments"

    def test_empty_code(self):
        """Test handling of empty code."""
        density = _calculate_doc_density("")
        assert density == 0.0, "Empty code should have 0 density"


class TestNamingConsistency:
    """Tests for naming consistency calculation."""

    def test_consistent_snake_case(self):
        """Test code with consistent snake_case naming."""
        code = "my_variable = 1\nanother_variable = 2\ndef my_function():\n    pass"
        consistency = _calculate_naming_consistency(code)
        assert 0 <= consistency <= 1, "Consistency should be between 0 and 1"

    def test_empty_code(self):
        """Test handling of empty code."""
        consistency = _calculate_naming_consistency("")
        assert consistency == 0.0, "Empty code should have 0 consistency"

    def test_single_identifier(self):
        """Test code with only one identifier."""
        code = "x = 1"
        consistency = _calculate_naming_consistency(code)
        assert consistency == 1.0, "Single identifier should be perfectly consistent"


class TestComputeDescriptorsForQuery:
    """Tests for query-level descriptor computation."""

    def test_basic_computation(self):
        """Test basic descriptor computation."""
        gt_snippets = [
            CodeSnippet(
                query_id="q1",
                code="def my_function():\n    '''A function.'''\n    pass",
                docstring="A function",
                language="python",
                is_ground_truth=True
            )
        ]
        retrieved_snippets = [
            CodeSnippet(
                query_id="q1",
                code="def another_function():\n    '''Another function.'''\n    pass",
                docstring="Another function",
                language="python",
                is_ground_truth=False
            )
        ]

        result = compute_descriptors_for_query("q1", gt_snippets, retrieved_snippets)

        assert result['query_id'] == "q1"
        assert result['snippet_count'] == 2
        assert 0 <= result['api_density'] <= 1
        assert 0 <= result['doc_density'] <= 1
        assert 0 <= result['naming_consistency'] <= 1

    def test_empty_snippets(self):
        """Test computation with empty snippet lists."""
        result = compute_descriptors_for_query("q1", [], [])
        assert result['snippet_count'] == 0
        assert result['api_density'] == 0.0
        assert result['doc_density'] == 0.0
        assert result['naming_consistency'] == 0.0

    def test_duplicate_snippets(self):
        """Test that duplicate snippets are handled correctly."""
        snippet = CodeSnippet(
            query_id="q1",
            code="def foo():\n    pass",
            docstring="",
            language="python",
            is_ground_truth=True
        )
        result = compute_descriptors_for_query("q1", [snippet, snippet], [])
        # Should count as 1 unique snippet
        assert result['snippet_count'] == 1


class TestComputeAllDescriptors:
    """Tests for batch descriptor computation."""

    def test_full_pipeline(self):
        """Test the full descriptor computation pipeline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create processed data directory with snippets
            processed_dir = tmpdir / "processed"
            processed_dir.mkdir()

            snippets_file = processed_dir / "snippets.jsonl"
            with open(snippets_file, 'w') as f:
                f.write(json.dumps({
                    'query_id': 'q1',
                    'code': 'def foo():\n    pass',
                    'docstring': 'A function',
                    'language': 'python',
                    'is_ground_truth': True
                }) + '\n')
                f.write(json.dumps({
                    'query_id': 'q1',
                    'code': 'def bar():\n    pass',
                    'docstring': 'Another function',
                    'language': 'python',
                    'is_ground_truth': False
                }) + '\n')

            # Create retrieval results
            results_file = tmpdir / "results.csv"
            with open(results_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['query_id', 'method', 'retrieved_codes'])
                writer.writerow(['q1', 'rag', json.dumps(['def bar():\n    pass'])])

            # Output path
            output_file = tmpdir / "descriptors.json"

            # Run computation
            compute_all_descriptors(processed_dir, results_file, output_file)

            # Verify output
            assert output_file.exists(), "Output file should be created"
            with open(output_file, 'r') as f:
                descriptors = json.load(f)

            assert len(descriptors) >= 1, "Should have at least one descriptor"
            assert descriptors[0]['query_id'] == 'q1'
            assert descriptors[0]['snippet_count'] >= 1

    def test_missing_retrieval_results(self):
        """Test handling of missing retrieval results file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            processed_dir = tmpdir / "processed"
            processed_dir.mkdir()

            # Create snippets file
            snippets_file = processed_dir / "snippets.jsonl"
            with open(snippets_file, 'w') as f:
                f.write(json.dumps({
                    'query_id': 'q1',
                    'code': 'def foo():\n    pass',
                    'docstring': '',
                    'language': 'python',
                    'is_ground_truth': True
                }) + '\n')

            results_file = tmpdir / "nonexistent.csv"
            output_file = tmpdir / "descriptors.json"

            # Should not raise, just process what's available
            compute_all_descriptors(processed_dir, results_file, output_file)
            assert output_file.exists()

    def test_missing_processed_data(self):
        """Test handling of missing processed data directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            processed_dir = tmpdir / "nonexistent"
            results_file = tmpdir / "results.csv"
            output_file = tmpdir / "descriptors.json"

            # Create empty results file
            results_file.touch()

            # Should not raise
            compute_all_descriptors(processed_dir, results_file, output_file)
            assert output_file.exists()
            with open(output_file, 'r') as f:
                descriptors = json.load(f)
            assert len(descriptors) == 0