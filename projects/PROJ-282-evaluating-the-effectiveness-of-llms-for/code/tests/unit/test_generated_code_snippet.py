import pytest
from src.models.code_snippet import CodeSnippet, create_codesnippet, CodeSnippetSchema, CodeSnippetLanguageEnum

class TestGeneratedCodeSnippet:
    def test_create_valid_snippet(self):
        """Test creation of a valid CodeSnippet."""
        data = {
            "id": "test-123",
            "language": "C",
            "source_code": "int main() { return 0; }",
            "ground_truth_label": "vulnerable",
            "ground_truth_category": "Buffer Overflow"
        }
        snippet = create_codesnippet(**data)
        assert snippet.id == "test-123"
        assert snippet.language == CodeSnippetLanguageEnum.C
        assert snippet.source_code == "int main() { return 0; }"
        assert snippet.ground_truth_label == "vulnerable"
        assert snippet.ground_truth_category == "Buffer Overflow"

    def test_invalid_language(self):
        """Test that invalid language raises validation error."""
        with pytest.raises(Exception):
            create_codesnippet(
                id="test-456",
                language="Java",
                source_code="public class Test {}",
                ground_truth_label="safe",
                ground_truth_category="None"
            )

    def test_missing_required_field(self):
        """Test that missing required field raises validation error."""
        with pytest.raises(Exception):
            create_codesnippet(
                id="test-789",
                # Missing language
                source_code="void func() {}",
                ground_truth_label="vulnerable",
                ground_truth_category="SQLi"
            )

    def test_schema_validation(self):
        """Test that the schema class validates correctly."""
        schema_data = {
            "id": "schema-test",
            "language": "Python",
            "source_code": "print('hello')",
            "ground_truth_label": "safe",
            "ground_truth_category": "None"
        }
        snippet = CodeSnippetSchema(**schema_data)
        assert snippet.id == "schema-test"
        assert snippet.language == CodeSnippetLanguageEnum.PYTHON

    def test_serialization(self):
        """Test JSON serialization."""
        snippet = create_codesnippet(
            id="ser-test",
            language="JavaScript",
            source_code="console.log('hi');",
            ground_truth_label="vulnerable",
            ground_truth_category="XSS"
        )
        data = snippet.model_dump()
        assert data["id"] == "ser-test"
        assert data["language"] == "JavaScript"
        assert data["source_code"] == "console.log('hi');"
        assert data["ground_truth_label"] == "vulnerable"
        assert data["ground_truth_category"] == "XSS"