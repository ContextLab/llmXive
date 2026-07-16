"""
Unit tests for the elements configuration module.
"""

import pytest
from pathlib import Path
import sys

# Add the project root to the path for imports
# Assuming tests are at tests/unit/ and code is at code/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.config.elements import (
    get_abundant_elements,
    get_abundant_elements_set,
    is_abundant_element,
    _load_elements,
    _ELEMENTS_YAML_PATH
)

class TestElementsConfig:
    """Tests for the elements configuration module."""
    
    def test_yaml_file_exists(self):
        """Verify that the elements.yaml configuration file exists."""
        assert _ELEMENTS_YAML_PATH.exists(), "elements.yaml file not found"
    
    def test_load_elements_success(self):
        """Test that elements can be loaded successfully."""
        # Reset state if necessary (though _load_elements doesn't reset globals on re-call in current impl)
        # For this test, we assume the module is fresh or the list is already loaded correctly
        elements = get_abundant_elements()
        assert len(elements) == 30, f"Expected 30 elements, got {len(elements)}"
        assert isinstance(elements, list)
    
    def test_load_elements_set(self):
        """Test that elements set is correctly populated."""
        elements_set = get_abundant_elements_set()
        assert len(elements_set) == 30
        assert isinstance(elements_set, set)
    
    def test_expected_elements_present(self):
        """Verify that specific expected elements are in the list."""
        expected_elements = ["Al", "Ca", "Fe", "Mg", "Ti", "Cu", "Ni", "Zr"]
        elements = get_abundant_elements()
        
        for el in expected_elements:
            assert el in elements, f"Expected element {el} not found in list"
    
    def test_is_abundant_element_true(self):
        """Test is_abundant_element returns True for valid elements."""
        assert is_abundant_element("Al") is True
        assert is_abundant_element("Fe") is True
        assert is_abundant_element("Zr") is True
    
    def test_is_abundant_element_false(self):
        """Test is_abundant_element returns False for invalid elements."""
        assert is_abundant_element("Uut") is False
        assert is_abundant_element("FakeElement") is False
        assert is_abundant_element("") is False
    
    def test_list_and_set_consistency(self):
        """Verify that the list and set contain the same elements."""
        elements_list = get_abundant_elements()
        elements_set = get_abundant_elements_set()
        
        assert set(elements_list) == elements_set
    
    def test_unique_elements(self):
        """Verify that all elements in the list are unique."""
        elements = get_abundant_elements()
        assert len(elements) == len(set(elements)), "Duplicate elements found in the list"