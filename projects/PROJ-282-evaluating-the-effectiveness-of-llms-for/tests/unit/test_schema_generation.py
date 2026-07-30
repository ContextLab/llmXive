"""
Tests for schema generation and model integrity.
"""
import pytest
import yaml
import json
import tempfile
from pathlib import Path
from src.models.code_snippet import CodeSnippet, create_snippet
from src.utils.schema_generator import load_schema, generate_dataclass_code

class TestSchemaGeneration:
    """Test that models are correctly generated from schemas."""

    def test_schema_loads_correctly(self, tmp_path):
        """Verify the schema file can be loaded."""
        schema_content = """
        title: TestModel
        type: object
        required:
          - id
        properties:
          id:
            type: string
          name:
            type: string
        """
        schema_file = tmp_path / "test.schema.yaml"
        schema_file.write_text(schema_content)
        
        schema = load_schema(str(schema_file))
        assert schema["title"] == "TestModel"
        assert "id" in schema["required"]

    def test_generated_code_is_valid_python(self, tmp_path):
        """Verify generated code is syntactically valid."""
        schema_content = """
        title: GeneratedModel
        type: object
        required:
          - field1
        properties:
          field1:
            type: string
          field2:
            type: integer
            nullable: true
        """
        schema_file = tmp_path / "gen.schema.yaml"
        schema_file.write_text(schema_content)
        
        schema = load_schema(str(schema_file))
        code = generate_dataclass_code(schema, "GeneratedModel", str(schema_file))
        
        # Check that the code compiles
        compile(code, "generated.py", "exec")
        assert "class GeneratedModel:" in code
        assert "field1: str" in code

class TestCodeSnippetModel:
    """Test the CodeSnippet model generated from dataset.schema.yaml."""

    def test_create_snippet_required_fields(self):
        """Test creation with required fields."""
        snippet = create_snippet(
            language="python",
            source_code="x = 1"
        )
        assert snippet.id is not None
        assert snippet.language == "python"
        assert snippet.source_code == "x = 1"
        assert snippet.ground_truth_label is None
        assert snippet.ground_truth_category is None

    def test_create_snippet_all_fields(self):
        """Test creation with all fields."""
        snippet = create_snippet(
            language="c",
            source_code="int *p = NULL;",
            ground_truth_label="vulnerable",
            ground_truth_category="Buffer Overflow"
        )
        assert snippet.language == "c"
        assert snippet.source_code == "int *p = NULL;"
        assert snippet.ground_truth_label == "vulnerable"
        assert snippet.ground_truth_category == "Buffer Overflow"

    def test_to_dict_round_trip(self):
        """Test serialization and deserialization."""
        original = create_snippet(
            language="java",
            source_code="System.out.println(\"Hello\");",
            ground_truth_label="safe",
            ground_truth_category=None
        )
        
        data = original.to_dict()
        restored = CodeSnippet.from_dict(data)
        
        assert restored.id == original.id
        assert restored.language == original.language
        assert restored.source_code == original.source_code
        assert restored.ground_truth_label == original.ground_truth_label
        assert restored.ground_truth_category == original.ground_truth_category

    def test_json_serialization(self):
        """Test JSON string serialization."""
        snippet = create_snippet(
            language="python",
            source_code="print('test')",
            ground_truth_label="safe"
        )
        
        json_str = snippet.to_json()
        data = json.loads(json_str)
        
        assert data["language"] == "python"
        assert data["ground_truth_label"] == "safe"

    def test_validation_empty_id(self):
        """Test that empty ID raises error."""
        with pytest.raises(ValueError):
            CodeSnippet(
                id="",
                language="python",
                source_code="x=1",
                ground_truth_label=None,
                ground_truth_category=None
            )

    def test_validation_invalid_label(self):
        """Test that invalid label raises error."""
        with pytest.raises(ValueError):
            CodeSnippet(
                id="123",
                language="python",
                source_code="x=1",
                ground_truth_label="invalid_label",
                ground_truth_category=None
            )
