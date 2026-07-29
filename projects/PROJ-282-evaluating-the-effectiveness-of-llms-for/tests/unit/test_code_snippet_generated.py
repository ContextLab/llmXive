"""
Tests for CodeSnippet generated from contract.
Verifies that the generated model matches the schema specification.
"""
import pytest
import json
import uuid
from src.models.code_snippet import CodeSnippet, create_snippet

class TestCodeSnippetFromContract:
    """Tests ensuring CodeSnippet matches contracts/dataset.schema.yaml."""

    def test_valid_snippet_creation(self):
        """Test creation of a valid snippet."""
        snippet = create_snippet(
            source_dataset="VulDeePecker",
            file_path="data/raw/test.py",
            language="Python",
            code="def x(): pass",
            line_start=1,
            line_end=1,
            label="vulnerable"
        )
        assert snippet.snippet_id is not None
        assert snippet.source_dataset == "VulDeePecker"
        assert snippet.language == "Python"
        assert snippet.label == "vulnerable"

    def test_uuid_format_validation(self):
        """Test that invalid UUID format raises error."""
        with pytest.raises(ValueError, match="Invalid snippet_id format"):
            CodeSnippet(
                snippet_id="invalid-uuid",
                source_dataset="VulDeePecker",
                file_path="test.py",
                language="Python",
                code="x=1",
                line_start=1,
                line_end=1,
                label="safe"
            )

    def test_valid_datasets(self):
        """Test all valid dataset values."""
        valid_datasets = ["VulDeePecker", "BigVul", "Juliet_C", "Juliet_Java"]
        for ds in valid_datasets:
            snippet = create_snippet(
                source_dataset=ds,
                file_path="test.py",
                language="Python",
                code="x=1",
                line_start=1,
                line_end=1,
                label="safe"
            )
            assert snippet.source_dataset == ds

    def test_invalid_dataset_raises(self):
        """Test that invalid dataset raises error."""
        with pytest.raises(ValueError, match="Invalid source_dataset"):
            create_snippet(
                source_dataset="InvalidDataset",
                file_path="test.py",
                language="Python",
                code="x=1",
                line_start=1,
                line_end=1,
                label="safe"
            )

    def test_valid_languages(self):
        """Test all valid language values."""
        valid_languages = ["Python", "C", "JavaScript", "Java"]
        for lang in valid_languages:
            snippet = create_snippet(
                source_dataset="VulDeePecker",
                file_path="test.py",
                language=lang,
                code="x=1",
                line_start=1,
                line_end=1,
                label="safe"
            )
            assert snippet.language == lang

    def test_invalid_language_raises(self):
        """Test that invalid language raises error."""
        with pytest.raises(ValueError, match="Invalid language"):
            create_snippet(
                source_dataset="VulDeePecker",
                file_path="test.py",
                language="Go",
                code="x=1",
                line_start=1,
                line_end=1,
                label="safe"
            )

    def test_valid_labels(self):
        """Test all valid label values."""
        valid_labels = ["vulnerable", "safe", "unknown"]
        for lbl in valid_labels:
            snippet = create_snippet(
                source_dataset="VulDeePecker",
                file_path="test.py",
                language="Python",
                code="x=1",
                line_start=1,
                line_end=1,
                label=lbl
            )
            assert snippet.label == lbl

    def test_invalid_label_raises(self):
        """Test that invalid label raises error."""
        with pytest.raises(ValueError, match="Invalid label"):
            create_snippet(
                source_dataset="VulDeePecker",
                file_path="test.py",
                language="Python",
                code="x=1",
                line_start=1,
                line_end=1,
                label="buggy"
            )

    def test_line_number_validation(self):
        """Test line number constraints."""
        # line_start must be >= 1
        with pytest.raises(ValueError, match="line_start must be >= 1"):
            create_snippet(
                source_dataset="VulDeePecker",
                file_path="test.py",
                language="Python",
                code="x=1",
                line_start=0,
                line_end=1,
                label="safe"
            )

        # line_end must be >= line_start
        with pytest.raises(ValueError, match="line_end .* must be >= line_start"):
            create_snippet(
                source_dataset="VulDeePecker",
                file_path="test.py",
                language="Python",
                code="x=1",
                line_start=5,
                line_end=3,
                label="safe"
            )

    def test_optional_fields(self):
        """Test optional fields can be None or set."""
        snippet_min = create_snippet(
            source_dataset="VulDeePecker",
            file_path="test.py",
            language="Python",
            code="x=1",
            line_start=1,
            line_end=1,
            label="safe"
        )
        assert snippet_min.category is None
        assert snippet_min.context is None
        assert snippet_min.raw_metadata is None

        snippet_full = create_snippet(
            source_dataset="VulDeePecker",
            file_path="test.py",
            language="Python",
            code="x=1",
            line_start=1,
            line_end=1,
            label="safe",
            category="SQLi",
            context="def func():",
            raw_metadata={"key": "value"}
        )
        assert snippet_full.category == "SQLi"
        assert snippet_full.context == "def func():"
        assert snippet_full.raw_metadata == {"key": "value"}

    def test_serialization_roundtrip(self):
        """Test JSON serialization and deserialization."""
        original = create_snippet(
            source_dataset="BigVul",
            file_path="data/raw/test.c",
            language="C",
            code="int x = 0;",
            line_start=10,
            line_end=12,
            label="vulnerable",
            category="Buffer Overflow"
        )
        
        json_str = original.to_json()
        restored = CodeSnippet.from_json(json_str)
        
        assert restored.snippet_id == original.snippet_id
        assert restored.source_dataset == original.source_dataset
        assert restored.language == original.language
        assert restored.code == original.code
        assert restored.label == original.label
        assert restored.category == original.category

    def test_dict_roundtrip(self):
        """Test dictionary conversion roundtrip."""
        original = create_snippet(
            source_dataset="VulDeePecker",
            file_path="test.py",
            language="Python",
            code="x=1",
            line_start=1,
            line_end=1,
            label="safe"
        )
        
        d = original.to_dict()
        restored = CodeSnippet.from_dict(d)
        
        assert restored.snippet_id == original.snippet_id
        assert restored.source_dataset == original.source_dataset
        assert restored.language == original.language
        assert restored.code == original.code

    def test_factory_generates_uuid(self):
        """Test that factory function generates a unique UUID."""
        s1 = create_snippet(
            source_dataset="VulDeePecker",
            file_path="test.py",
            language="Python",
            code="x=1",
            line_start=1,
            line_end=1,
            label="safe"
        )
        s2 = create_snippet(
            source_dataset="VulDeePecker",
            file_path="test.py",
            language="Python",
            code="y=2",
            line_start=1,
            line_end=1,
            label="safe"
        )
        assert s1.snippet_id != s2.snippet_id
        assert uuid.UUID(s1.snippet_id)  # Valid UUID
        assert uuid.UUID(s2.snippet_id)  # Valid UUID

    def test_custom_snippet_id(self):
        """Test that custom snippet_id is accepted."""
        custom_id = "12345678-1234-1234-1234-123456789abc"
        snippet = create_snippet(
            source_dataset="VulDeePecker",
            file_path="test.py",
            language="Python",
            code="x=1",
            line_start=1,
            line_end=1,
            label="safe",
            snippet_id=custom_id
        )
        assert snippet.snippet_id == custom_id

    def test_invalid_custom_snippet_id(self):
        """Test that invalid custom snippet_id raises error."""
        with pytest.raises(ValueError, match="Invalid snippet_id format"):
            create_snippet(
                source_dataset="VulDeePecker",
                file_path="test.py",
                language="Python",
                code="x=1",
                line_start=1,
                line_end=1,
                label="safe",
                snippet_id="not-a-valid-uuid"
            )