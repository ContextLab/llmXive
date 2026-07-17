import pytest
from src.models.code_snippet import CodeSnippet, create_snippet


class TestCodeSnippetCreation:
    """Tests for basic CodeSnippet instantiation."""

    def test_create_with_required_fields(self):
        """Test creating a snippet with only required fields."""
        snippet = CodeSnippet(
            language="python",
            source_code="x = 1",
            ground_truth_label=0
        )
        assert snippet.language == "python"
        assert snippet.source_code == "x = 1"
        assert snippet.ground_truth_label == 0
        assert snippet.ground_truth_category is None
        assert isinstance(snippet.id, str)
        assert len(snippet.id) == 36  # UUID length

    def test_create_with_all_fields(self):
        """Test creating a snippet with all fields populated."""
        snippet = CodeSnippet(
            id="test-id-123",
            language="c",
            source_code="strcpy(dest, src);",
            ground_truth_label=1,
            ground_truth_category="Buffer Overflow"
        )
        assert snippet.id == "test-id-123"
        assert snippet.language == "c"
        assert snippet.source_code == "strcpy(dest, src);"
        assert snippet.ground_truth_label == 1
        assert snippet.ground_truth_category == "Buffer Overflow"

    def test_empty_language_raises_error(self):
        """Test that empty language raises ValueError."""
        with pytest.raises(ValueError, match="language cannot be empty"):
            CodeSnippet(
                language="",
                source_code="x = 1",
                ground_truth_label=0
            )

    def test_empty_source_code_raises_error(self):
        """Test that empty source_code raises ValueError."""
        with pytest.raises(ValueError, match="source_code cannot be empty"):
            CodeSnippet(
                language="python",
                source_code="",
                ground_truth_label=0
            )

    def test_invalid_label_raises_error(self):
        """Test that invalid ground_truth_label raises ValueError."""
        with pytest.raises(ValueError, match="ground_truth_label must be 0"):
            CodeSnippet(
                language="python",
                source_code="x = 1",
                ground_truth_label=2
            )

        with pytest.raises(ValueError, match="ground_truth_label must be 0"):
            CodeSnippet(
                language="python",
                source_code="x = 1",
                ground_truth_label=-1
            )


class TestCreateSnippetFactory:
    """Tests for the create_snippet factory function."""

    def test_factory_creates_valid_snippet(self):
        """Test that factory creates a valid snippet."""
        snippet = create_snippet(
            language="java",
            source_code="String s = null;",
            ground_truth_label=0
        )
        assert snippet.language == "java"
        assert snippet.source_code == "String s = null;"
        assert snippet.ground_truth_label == 0
        assert isinstance(snippet.id, str)

    def test_factory_with_custom_id(self):
        """Test factory with custom ID."""
        custom_id = "custom-uuid-999"
        snippet = create_snippet(
            language="python",
            source_code="pass",
            ground_truth_label=1,
            snippet_id=custom_id
        )
        assert snippet.id == custom_id

    def test_factory_with_category(self):
        """Test factory with category."""
        snippet = create_snippet(
            language="c",
            source_code="gets(buf);",
            ground_truth_label=1,
            ground_truth_category="Buffer Overflow"
        )
        assert snippet.ground_truth_category == "Buffer Overflow"


class TestCodeSnippetValidation:
    """Tests for CodeSnippet validation logic."""

    def test_to_dict_serialization(self):
        """Test that to_dict returns correct structure."""
        snippet = CodeSnippet(
            id="test-123",
            language="python",
            source_code="def foo(): pass",
            ground_truth_label=0,
            ground_truth_category="None"
        )
        data = snippet.to_dict()
        
        assert data["id"] == "test-123"
        assert data["language"] == "python"
        assert data["source_code"] == "def foo(): pass"
        assert data["ground_truth_label"] == 0
        assert data["ground_truth_category"] == "None"

    def test_to_dict_with_none_category(self):
        """Test serialization when category is None."""
        snippet = CodeSnippet(
            language="java",
            source_code="int x = 0;",
            ground_truth_label=0
        )
        data = snippet.to_dict()
        assert data["ground_truth_category"] is None

    def test_label_boundary_values(self):
        """Test boundary values for labels."""
        # Safe label
        safe_snippet = CodeSnippet(
            language="c",
            source_code="int a;",
            ground_truth_label=0
        )
        assert safe_snippet.ground_truth_label == 0

        # Vulnerable label
        vuln_snippet = CodeSnippet(
            language="c",
            source_code="strcpy(a, b);",
            ground_truth_label=1
        )
        assert vuln_snippet.ground_truth_label == 1