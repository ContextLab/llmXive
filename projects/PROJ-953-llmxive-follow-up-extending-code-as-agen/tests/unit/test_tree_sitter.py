"""
Unit tests for tree-sitter parsing on valid Python code.
Tests the core parsing functionality required for structural metric extraction.
"""

import pytest
import json
import tempfile
from pathlib import Path

# Import the tree-sitter library directly for testing the parsing logic
try:
    from tree_sitter import Language, Parser
    import tree_sitter_python as tspython
except ImportError:
    pytest.skip("tree-sitter or tree-sitter-python not installed", allow_module_level=True)

# We define a helper function locally to simulate the parsing logic 
# that will be used in code/scripts/extract_features.py (T020)
def parse_python_code(code: str):
    """
    Parses Python code using tree-sitter and returns the root node.
    This mirrors the logic intended for T020.
    """
    # Initialize the language
    # In production, we might cache the language object, but for unit tests
    # we can instantiate it or load from a known path.
    # For this test, we assume the binary is available or we use the module's helper.
    
    # tree-sitter-python provides a pre-compiled language binary or we can build it.
    # Standard approach:
    PY_LANGUAGE = Language(tspython.language())
    
    parser = Parser()
    parser.set_language(PY_LANGUAGE)
    
    tree = parser.parse(bytes(code, "utf8"))
    return tree.root_node

class TestTreeSitterParsing:
    """Tests for valid Python code parsing."""

    def test_parse_simple_function(self):
        """Test parsing a simple function definition."""
        code = """
        def add(a, b):
            return a + b
        """
        root = parse_python_code(code)
        
        # Verify root node type
        assert root.type == "program"
        
        # Verify we have children (statements)
        assert root.child_count > 0
        
        # Find the function definition
        func_node = None
        for child in root.children:
            if child.type == "function_definition":
                func_node = child
                break
        
        assert func_node is not None, "Could not find function_definition node"
        assert func_node.child_by_field_name("name").text.decode() == "add"

    def test_parse_class_definition(self):
        """Test parsing a class definition."""
        code = """
        class MyClass:
            def __init__(self):
                self.x = 1
        """
        root = parse_python_code(code)
        
        assert root.type == "program"
        
        # Find class definition
        class_node = None
        for child in root.children:
            if child.type == "class_definition":
                class_node = child
                break
        
        assert class_node is not None, "Could not find class_definition node"
        assert class_node.child_by_field_name("name").text.decode() == "MyClass"

    def test_parse_complex_expression(self):
        """Test parsing a complex expression with nested structures."""
        code = """
        if x > 0:
            for i in range(10):
                if i % 2 == 0:
                    print(i)
        """
        root = parse_python_code(code)
        
        assert root.type == "program"
        
        # Find the if_statement
        if_node = None
        for child in root.children:
            if child.type == "if_statement":
                if_node = child
                break
        
        assert if_node is not None, "Could not find if_statement node"
        
        # Verify structure: if_statement should contain a for_statement
        # (simplified check: just ensure the tree is not empty and has depth)
        assert root.descendant_for_point_range((0, 0), (5, 0)) is not None

    def test_parse_empty_file(self):
        """Test parsing an empty file."""
        code = ""
        root = parse_python_code(code)
        
        assert root.type == "program"
        assert root.child_count == 0

    def test_parse_syntax_error_handling(self):
        """Test that invalid code raises an error or produces expected parse state."""
        # tree-sitter often produces a parse tree even with errors, marking them as 'ERROR'
        code = "def broken("
        
        root = parse_python_code(code)
        
        # Check if there is an ERROR node
        has_error = False
        def check_for_error(node):
            nonlocal has_error
            if node.type == "ERROR":
                has_error = True
            for child in node.children:
                check_for_error(child)
        
        check_for_error(root)
        
        # The parser usually succeeds but marks the error node
        assert has_error, "Expected an ERROR node in the parse tree for invalid syntax"

    def test_serialization_to_dict(self):
        """Test converting the parse tree to a serializable dictionary structure."""
        code = "x = 1"
        root = parse_python_code(code)
        
        def node_to_dict(node):
            return {
                "type": node.type,
                "start_point": [node.start_point[0], node.start_point[1]],
                "end_point": [node.end_point[0], node.end_point[1]],
                "children": [node_to_dict(child) for child in node.children]
            }
        
        tree_dict = node_to_dict(root)
        
        assert "type" in tree_dict
        assert tree_dict["type"] == "program"
        assert isinstance(tree_dict["start_point"], list)
        assert len(tree_dict["children"]) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
