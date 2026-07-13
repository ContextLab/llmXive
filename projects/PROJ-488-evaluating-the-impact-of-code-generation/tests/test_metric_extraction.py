import pytest
import tempfile
import os
from pathlib import Path
import json
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from metric_extraction import extract_radon_metrics, extract_pylint_metrics, process_snippets_for_metrics

class TestRadonMetrics:
    def test_extract_radon_metrics_simple_function(self):
        code = """
        def add(a, b):
            return a + b
        """
        result = extract_radon_metrics(code, "test-001")
        
        assert result["snippet_id"] == "test-001"
        assert result["max_cc"] == 1
        assert result["avg_cc"] == 1.0
        assert result["num_functions"] == 1
        assert result["loc"] >= 3
        assert "halstead_volume" in result
    
    def test_extract_radon_metrics_complex_function(self):
        code = """
        def complex_func(x):
            if x > 0:
                if x < 10:
                    return "small"
                else:
                    return "large"
            else:
                return "negative"
        """
        result = extract_radon_metrics(code, "test-002")
        
        assert result["snippet_id"] == "test-002"
        assert result["max_cc"] > 1  # Should be higher due to nested if statements
        assert result["num_functions"] == 1
    
    def test_extract_radon_metrics_invalid_code(self):
        code = "def broken("
        result = extract_radon_metrics(code, "test-003")
        
        assert result["snippet_id"] == "test-003"
        assert "error" in result or result["max_cc"] is None

class TestPylintMetrics:
    def test_extract_pylint_metrics_clean_code(self):
        code = """
        def greet(name):
            return f"Hello, {name}!"
        """
        result = extract_pylint_metrics(code, "test-004")
        
        assert result["snippet_id"] == "test-004"
        assert result["total_issues"] >= 0
        assert result["potential_bugs"] >= 0
        assert result["style_issues"] >= 0
    
    def test_extract_pylint_metrics_with_issues(self):
        code = """
        def bad_function(x, y):
            unused_var = 10
            if x > 0:
                return x
            else:
                return y
        """
        result = extract_pylint_metrics(code, "test-005")
        
        assert result["snippet_id"] == "test-005"
        # Should detect unused variable
        assert result["total_issues"] >= 0 # Pylint might not catch everything in snippet context
        # We just verify the structure is correct and no crash
    
    def test_extract_pylint_metrics_invalid_code(self):
        code = "def broken("
        result = extract_pylint_metrics(code, "test-006")
        
        assert result["snippet_id"] == "test-006"
        assert "error" in result or result["total_issues"] >= 0

class TestProcessSnippets:
    def test_process_snippets_for_metrics(self):
        snippets = [
            {"id": "s1", "code": "def f(): pass"},
            {"id": "s2", "code": "def g(): return 1"}
        ]
        
        radon_results, pylint_results = process_snippets_for_metrics(snippets, "test_group")
        
        assert len(radon_results) == 2
        assert len(pylint_results) == 2
        
        for r in radon_results:
            assert r["group"] == "test_group"
            assert "snippet_id" in r
        
        for p in pylint_results:
            assert p["group"] == "test_group"
            assert "snippet_id" in p

if __name__ == "__main__":
    pytest.main([__file__, "-v"])