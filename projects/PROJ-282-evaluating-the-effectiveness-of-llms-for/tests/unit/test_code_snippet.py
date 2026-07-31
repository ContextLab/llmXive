"""
Tests for CodeSnippet model generated from contracts/dataset.schema.yaml.
"""
import pytest
import json
from src.models.code_snippet import CodeSnippet, create_snippet

class TestCodeSnippetCreation:
    def test_create_valid_snippet(self):
        """Test creation of a valid CodeSnippet."""
        snippet = create_snippet(
            snippet_id="test_001",
            language="Python",
            source_code="print('hello')",
            ground_truth_label="vulnerable",
            ground_truth_category="SQLi"
        )
        assert snippet.id == "test_001"
        assert snippet.language == "Python"
        assert snippet.source_code == "print('hello')"
        assert snippet.ground_truth_label == "vulnerable"
        assert snippet.ground_truth_category == "SQLi"

    def test_create_snippet_with_auto_id(self):
        """Test that create_snippet generates a UUID if none provided."""
        snippet = create_snippet(
            language="C",
            source_code="int main() { return 0; }",
            ground_truth_label="safe",
            ground_truth_category="none"
        )
        assert snippet.id is not None
        assert len(snippet.id) > 0

    def test_language_enum_validation(self):
        """Test that only valid languages are accepted."""
        valid_languages = ["C", "Python", "JavaScript"]
        for lang in valid_languages:
            snippet = create_snippet(language=lang, source_code="x", ground_truth_label="safe", ground_truth_category="none")
            assert snippet.language == lang

        with pytest.raises(Exception):
            create_snippet(language="Java", source_code="x", ground_truth_label="safe", ground_truth_category="none")

class TestCreateSnippetFactory:
    def test_factory_default_values(self):
        """Test factory defaults."""
        snippet = create_snippet(source_code="test")
        assert snippet.language == "Python"
        assert snippet.ground_truth_label == "vulnerable"
        assert snippet.ground_truth_category == "SQLi"

class TestCodeSnippetValidation:
    def test_empty_id_rejected(self):
        """Test that empty ID is rejected."""
        with pytest.raises(Exception):
            CodeSnippet(
                id="",
                language="Python",
                source_code="x",
                ground_truth_label="safe",
                ground_truth_category="none"
            )

    def test_empty_source_code_rejected(self):
        """Test that empty source_code is rejected."""
        with pytest.raises(Exception):
            CodeSnippet(
                id="test",
                language="Python",
                source_code="",
                ground_truth_label="safe",
                ground_truth_category="none"
            )

    def test_empty_label_rejected(self):
        """Test that empty ground_truth_label is rejected."""
        with pytest.raises(Exception):
            CodeSnippet(
                id="test",
                language="Python",
                source_code="x",
                ground_truth_label="",
                ground_truth_category="none"
            )

    def test_empty_category_rejected(self):
        """Test that empty ground_truth_category is rejected."""
        with pytest.raises(Exception):
            CodeSnippet(
                id="test",
                language="Python",
                source_code="x",
                ground_truth_label="safe",
                ground_truth_category=""
            )

    def test_serialization(self):
        """Test JSON serialization and deserialization."""
        original = create_snippet(
            snippet_id="ser_test",
            language="JavaScript",
            source_code="console.log('hi');",
            ground_truth_label="vulnerable",
            ground_truth_category="XSS"
        )
        json_str = original.model_dump_json()
        restored = CodeSnippet.model_validate_json(json_str)
        
        assert restored.id == original.id
        assert restored.language == original.language
        assert restored.source_code == original.source_code
        assert restored.ground_truth_label == original.ground_truth_label
        assert restored.ground_truth_category == original.ground_truth_category

    def test_schema_drift_prevention(self):
        """
        Verify that the model fields match the contract in contracts/dataset.schema.yaml.
        The contract requires: id, language, source_code, ground_truth_label, ground_truth_category.
        """
        expected_fields = {"id", "language", "source_code", "ground_truth_label", "ground_truth_category"}
        actual_fields = set(CodeSnippet.model_fields.keys())
        
        assert actual_fields == expected_fields, f"Schema drift detected: expected {expected_fields}, got {actual_fields}"