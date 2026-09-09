"""
Unit tests for topology_labels module.

These tests verify that the topology type labeling logic works correctly
and that invalid inputs are rejected as expected.
"""

import pytest
from code.utils.topology_labels import (
    validate_topology_type,
    assign_topology_label,
    get_topology_label_for_metadata,
    get_valid_topology_types,
    TOPOLOGY_TYPES
)


class TestValidateTopologyType:
    def test_valid_types(self):
        """Test that valid topology types return True."""
        for t_type in TOPOLOGY_TYPES:
            assert validate_topology_type(t_type) is True

    def test_invalid_type(self):
        """Test that invalid topology types return False."""
        assert validate_topology_type("invalid") is False
        assert validate_topology_type("") is False
        assert validate_topology_type("Random") is False  # Case sensitive

    def test_none_input(self):
        """Test that None input returns False."""
        assert validate_topology_type(None) is False


class TestAssignTopologyLabel:
    def test_valid_assignment(self):
        """Test that valid types are assigned correctly."""
        for t_type in TOPOLOGY_TYPES:
            result = assign_topology_label(t_type)
            assert result == t_type

    def test_invalid_assignment_raises(self):
        """Test that invalid types raise ValueError."""
        with pytest.raises(ValueError):
            assign_topology_label("invalid")

    def test_error_message_content(self):
        """Test that the error message contains helpful information."""
        with pytest.raises(ValueError) as exc_info:
            assign_topology_label("bad_type")
        assert "Invalid topology_type" in str(exc_info.value)
        assert "bad_type" in str(exc_info.value)


class TestGetTopologyLabelForMetadata:
    def test_metadata_structure(self):
        """Test that the returned metadata has the correct structure."""
        metadata = get_topology_label_for_metadata("random", seed=42, density=0.3)
        
        assert "topology_type" in metadata
        assert "seed" in metadata
        assert "inclusion_density" in metadata
        assert "is_stratification_key" in metadata

    def test_metadata_values(self):
        """Test that the metadata values are correct."""
        metadata = get_topology_label_for_metadata("aligned", seed=123, density=0.5)
        
        assert metadata["topology_type"] == "aligned"
        assert metadata["seed"] == 123
        assert metadata["inclusion_density"] == 0.5
        assert metadata["is_stratification_key"] is True

    def test_invalid_topology_in_metadata(self):
        """Test that invalid topology types raise ValueError in metadata generation."""
        with pytest.raises(ValueError):
            get_topology_label_for_metadata("invalid", seed=1, density=0.1)


class TestGetValidTopologyTypes:
    def test_returns_list(self):
        """Test that the function returns a list."""
        result = get_valid_topology_types()
        assert isinstance(result, list)

    def test_contains_expected_types(self):
        """Test that the list contains all expected types."""
        result = get_valid_topology_types()
        for t_type in TOPOLOGY_TYPES:
            assert t_type in result

    def test_no_extra_types(self):
        """Test that the list doesn't contain unexpected types."""
        result = get_valid_topology_types()
        assert len(result) == len(TOPOLOGY_TYPES)

    def test_returns_copy(self):
        """Test that the function returns a copy, not the original list."""
        result = get_valid_topology_types()
        result.append("fake_type")
        assert "fake_type" not in TOPOLOGY_TYPES