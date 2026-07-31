import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.data.feature_extractor import (
    extract_semantic_features,
    extract_features_for_snippet,
    _count_api_occurrences,
    _detect_sanitization_present,
    TAINT_APIS_PY,
    SANITIZERS_PY,
    TAINT_APIS_C,
    SANITIZERS_C
)

class TestSemanticFeatures:
    """Tests for T018b: Semantic Metrics (Taint Count & Sanitization)"""

    def test_count_taint_apis_python(self):
        """Verify taint API counting in Python code."""
        code = "user = input()\nexec(user)\nopen('file')"
        count = _count_api_occurrences(code, TAINT_APIS_PY)
        # input, exec, open -> 3
        assert count == 3

    def test_count_taint_apis_c(self):
        """Verify taint API counting in C code."""
        code = "gets(buf);\nsprintf(buf, str);\nscanf(\"%s\", buf);"
        count = _count_api_occurrences(code, TAINT_APIS_C)
        # gets, sprintf, scanf -> 3
        assert count == 3

    def test_detect_sanitization_python(self):
        """Verify sanitization detection in Python."""
        code = "import html\nsafe = html.escape(user_input)\n"
        assert _detect_sanitization_present(code, "python") is True

    def test_detect_sanitization_c(self):
        """Verify sanitization detection in C."""
        code = "snprintf(buf, sizeof(buf), \"%s\", user);"
        assert _detect_sanitization_present(code, "c") is True

    def test_detect_sanitization_false(self):
        """Verify false negative for sanitization."""
        code = "x = input()\ny = x + 1"
        assert _detect_sanitization_present(code, "python") is False

    def test_extract_semantic_features_vulnerable(self):
        """Full extraction on vulnerable code."""
        code = "data = input()\neval(data)"
        taint_count, sanitized = extract_semantic_features(code, "python")
        assert taint_count >= 2 # input, eval
        assert sanitized is False

    def test_extract_semantic_features_safe(self):
        """Full extraction on safe code."""
        code = "import json\ndata = json.loads(user_input)"
        taint_count, sanitized = extract_semantic_features(code, "python")
        # json.loads is not in taint list, but might be in sanitizer list depending on config
        # Here we just check it returns valid types
        assert isinstance(taint_count, int)
        assert isinstance(sanitized, bool)

    def test_extract_features_for_snippet_integration(self):
        """Integration test for the full feature vector creation."""
        snippet = {
            "id": "test-123",
            "code": "x = input()",
            "language": "python"
        }
        feat = extract_features_for_snippet(
            snippet_id=snippet["id"],
            code=snippet["code"],
            language=snippet["language"]
        )
        assert feat.snippet_id == "test-123"
        assert feat.taint_api_count > 0
        assert feat.sanitization_present is False
        # Check structural defaults
        assert feat.ast_depth == 0
        assert feat.node_count == 0
        assert feat.cyclomatic_complexity == 0

    def test_empty_code(self):
        """Handle empty code gracefully."""
        taint, sanit = extract_semantic_features("", "python")
        assert taint == 0
        assert sanit is False

    def test_unknown_language(self):
        """Handle unknown language."""
        taint, sanit = extract_semantic_features("x = 1", "fortran")
        # Should not crash, should return 0/false for unknown language
        assert taint == 0
        assert sanit is False

class TestFeatureExtractionPipeline:
    """Tests for the batch processing logic."""

    def test_batch_extraction(self):
        """Test batch extraction logic."""
        from src.data.feature_extractor import batch_extract_features

        snippets = [
            {"id": "1", "code": "input()", "language": "python"},
            {"id": "2", "code": "gets(buf)", "language": "c"}
        ]
        results = batch_extract_features(snippets)
        assert len(results) == 2
        assert results[0].taint_api_count > 0
        assert results[1].taint_api_count > 0

class TestIntegration:
    """Integration tests with real-world snippets."""

    def test_sql_injection_pattern(self):
        """Detect SQLi pattern."""
        code = "query = 'SELECT * FROM users WHERE id = ' + request.args['id']"
        taint, sanit = extract_semantic_features(code, "python")
        # request.args is a taint source
        assert taint > 0

    def test_xss_pattern(self):
        """Detect XSS pattern."""
        code = "document.write('<h1>' + req.params['name'] + '</h1>');"
        taint, sanit = extract_semantic_features(code, "javascript")
        # req.params is taint
        assert taint > 0

    def test_buffer_overflow_pattern(self):
        """Detect Buffer Overflow pattern."""
        code = "char buf[10]; gets(buf); strcpy(buf, user);"
        taint, sanit = extract_semantic_features(code, "c")
        # gets, strcpy are taints
        assert taint >= 2
        # No sanitizer present
        assert sanit is False
