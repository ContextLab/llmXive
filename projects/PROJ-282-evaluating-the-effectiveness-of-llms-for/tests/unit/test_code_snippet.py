import pytest
import json
from src.models.code_snippet import CodeSnippet, create_snippet


class TestCodeSnippetCreation:
    def test_create_snippet_minimal(self):
        snippet = create_snippet(
            code="int x = 0;",
            language="C",
            source="test"
        )
        assert snippet.code == "int x = 0;"
        assert snippet.language == "C"
        assert snippet.source == "test"
        assert snippet.snippet_id is not None

    def test_create_snippet_full(self):
        snippet = create_snippet(
            code="SELECT * FROM users;",
            language="SQL",
            source="vuldeepecker",
            ground_truth_label="SQLi",
            context="User query function"
        )
        assert snippet.ground_truth_label == "SQLi"
        assert snippet.context == "User query function"

class TestCreateSnippetFactory:
    def test_snippet_id_uniqueness(self):
        s1 = create_snippet("code1", "py", "src")
        s2 = create_snippet("code2", "py", "src")
        assert s1.snippet_id != s2.snippet_id

    def test_language_detection(self):
        # If language is not provided, it should be detected or set to 'unknown'
        snippet = create_snippet("print('hello')", language="")
        # The factory logic should handle empty string
        # Depending on implementation, it might be 'unknown' or derived
        assert snippet.language is not None

class TestCodeSnippetValidation:
    def test_invalid_code_type(self):
        with pytest.raises(ValueError):
            create_snippet(code=123, language="py", source="test")

    def test_missing_required_fields(self):
        # create_snippet requires code, language, source
        with pytest.raises(TypeError):
            create_snippet(code="x")
