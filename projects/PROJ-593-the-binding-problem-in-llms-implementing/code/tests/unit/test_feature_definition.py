"""
Unit tests for the feature definition module.
"""

import json
import pytest
import tempfile
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.models.feature_definition import (
    load_feature_schema,
    save_feature_schema,
    get_feature_group_for_head,
    get_atomic_units_for_group,
    get_all_feature_groups,
    tag_attention_heads_with_features,
    create_feature_definition_schema,
    DEFAULT_FEATURE_SCHEMA,
    FEATURE_GROUP_DEFINITIONS
)


class TestFeatureDefinitionSchema:
    """Tests for feature definition schema loading and saving."""

    def test_load_default_schema(self):
        """Test loading the default schema."""
        schema = load_feature_schema()
        assert isinstance(schema, dict)
        assert len(schema) > 0
        assert "head_0" in schema
        assert schema["head_0"] == "group_A"

    def test_load_custom_schema(self):
        """Test loading a custom schema from file."""
        custom_schema = {
            "head_0": "group_X",
            "head_1": "group_Y",
            "head_2": "group_X"
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(custom_schema, f)
            temp_path = f.name

        try:
            loaded_schema = load_feature_schema(temp_path)
            assert loaded_schema == custom_schema
        finally:
            Path(temp_path).unlink()

    def test_save_and_load_schema(self):
        """Test saving and loading a schema."""
        schema = {
            "head_0": "group_A",
            "head_1": "group_B"
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            save_feature_schema(schema, temp_path)
            loaded_schema = load_feature_schema(temp_path)
            assert loaded_schema == schema
        finally:
            Path(temp_path).unlink()

    def test_save_creates_directories(self):
        """Test that save_feature_schema creates parent directories."""
        schema = {"head_0": "group_A"}
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = Path(tmpdir) / "nested" / "dir" / "schema.json"
            save_feature_schema(schema, nested_path)
            assert nested_path.exists()


class TestFeatureGroupLookup:
    """Tests for feature group lookup functions."""

    def test_get_feature_group_for_head_int(self):
        """Test getting feature group with integer head index."""
        group = get_feature_group_for_head(0)
        assert group == "group_A"

        group = get_feature_group_for_head(2)
        assert group == "group_B"

    def test_get_feature_group_for_head_string(self):
        """Test getting feature group with string head index."""
        group = get_feature_group_for_head("head_0")
        assert group == "group_A"

        group = get_feature_group_for_head("head_2")
        assert group == "group_B"

    def test_get_feature_group_for_head_not_found(self):
        """Test getting feature group for non-existent head."""
        group = get_feature_group_for_head(999)
        assert group is None

    def test_get_atomic_units_for_group(self):
        """Test getting atomic units for a feature group."""
        units = get_atomic_units_for_group("group_A")
        assert isinstance(units, list)
        assert "head_0" in units
        assert "head_1" in units

        units = get_atomic_units_for_group("group_B")
        assert "head_2" in units
        assert "head_3" in units

    def test_get_all_feature_groups(self):
        """Test getting all feature groups."""
        groups = get_all_feature_groups()
        assert isinstance(groups, list)
        assert len(groups) > 0
        assert "group_A" in groups
        assert "group_B" in groups


class TestFeatureTagging:
    """Tests for attention head feature tagging."""

    def test_tag_attention_heads_with_features(self):
        """Test tagging attention heads with feature groups."""
        attention_weights = {
            "layer_0": {
                "head_0": [[0.1, 0.2], [0.3, 0.4]],
                "head_2": [[0.5, 0.6], [0.7, 0.8]]
            }
        }

        tagged = tag_attention_heads_with_features(attention_weights)

        assert "layer_0" in tagged
        assert "head_0" in tagged["layer_0"]
        assert "head_2" in tagged["layer_0"]

        # Check that feature groups are assigned
        assert tagged["layer_0"]["head_0"]["feature_group"] == "group_A"
        assert tagged["layer_0"]["head_2"]["feature_group"] == "group_B"

        # Check that is_bound flag is set
        assert tagged["layer_0"]["head_0"]["is_bound"] is True
        assert tagged["layer_0"]["head_2"]["is_bound"] is True

    def test_tag_attention_heads_with_layer_filter(self):
        """Test tagging with layer filter."""
        attention_weights = {
            "layer_0": {
                "head_0": [[0.1, 0.2]]
            },
            "layer_1": {
                "head_0": [[0.3, 0.4]]
            }
        }

        tagged = tag_attention_heads_with_features(attention_weights, layer_id=0)

        assert "layer_0" in tagged
        assert "layer_1" not in tagged


class TestSchemaCreation:
    """Tests for dynamic schema creation."""

    def test_create_feature_definition_schema(self):
        """Test creating a feature definition schema."""
        schema = create_feature_definition_schema(num_heads=8, num_groups=4)

        assert len(schema) == 8
        assert "head_0" in schema
        assert "head_7" in schema

        # Check that groups are distributed
        groups = set(schema.values())
        assert len(groups) == 4

    def test_create_feature_definition_schema_custom_heads_per_group(self):
        """Test creating schema with custom heads per group."""
        schema = create_feature_definition_schema(num_heads=6, num_groups=2, heads_per_group=3)

        assert len(schema) == 6
        groups = set(schema.values())
        assert len(groups) == 2
        # First 3 heads should be in one group, next 3 in another
        assert schema["head_0"] == schema["head_1"] == schema["head_2"]
        assert schema["head_3"] == schema["head_4"] == schema["head_5"]
        assert schema["head_0"] != schema["head_3"]


class TestFeatureGroupDefinitions:
    """Tests for feature group definitions."""

    def test_group_definitions_exist(self):
        """Test that feature group definitions are available."""
        assert "group_A" in FEATURE_GROUP_DEFINITIONS
        assert "group_B" in FEATURE_GROUP_DEFINITIONS

    def test_group_definition_structure(self):
        """Test that group definitions have required fields."""
        for group_id, definition in FEATURE_GROUP_DEFINITIONS.items():
            assert "name" in definition
            assert "description" in definition
            assert "atomic_units" in definition
            assert "hierarchical_level" in definition
            assert isinstance(definition["atomic_units"], list)
