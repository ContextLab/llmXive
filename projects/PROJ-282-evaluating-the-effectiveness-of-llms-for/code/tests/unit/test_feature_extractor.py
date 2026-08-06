"""
Unit tests for the feature extraction module (T018a).
"""
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code to path if running standalone
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.feature_extractor import (
    extract_structural_features,
    _calculate_ast_depth,
    _count_nodes,
    _calculate_cyclomatic_complexity,
    extract_features_for_snippet,
    batch_extract_features
)

# Mock tree-sitter parser for testing without real parsing
class MockNode:
    def __init__(self, node_type, children=None):
        self.type = node_type
        self.children = children or []
        self.child_count = len(self.children)

class MockTree:
    def __init__(self, root):
        self.root_node = root

class MockParser:
    def parse(self, code):
        # Return a simple mock tree for valid code
        if "error" in code.lower():
            root = MockNode("ERROR")
        else:
            # Create a simple AST: function -> block -> if_statement
            if_node = MockNode("if_statement")
            block_node = MockNode("compound_statement", [if_node])
            func_node = MockNode("function_definition", [block_node])
            root = MockNode("translation_unit", [func_node])
        return MockTree(root)

@pytest.fixture
def mock_get_parser():
    with patch('src.data.feature_extractor._get_parser') as mock:
        mock.return_value = MockParser()
        yield mock

@pytest.fixture
def mock_get_parser_error():
    with patch('src.data.feature_extractor._get_parser') as mock:
        mock.return_value = None
        yield mock

def test_extract_structural_features_success(mock_get_parser):
    """Test successful extraction of structural features."""
    code = "def foo():\n    if True:\n        pass"
    result = extract_structural_features(code, "python")
    
    assert result['valid'] is True
    assert result['ast_depth'] is not None
    assert result['node_count'] is not None
    assert result['cyclomatic_complexity'] is not None
    assert result['error'] is None

def test_extract_structural_features_unsupported_language(mock_get_parser_error):
    """Test handling of unsupported language."""
    code = "some code"
    result = extract_structural_features(code, "unknown_lang")
    
    assert result['valid'] is False
    assert result['ast_depth'] is None
    assert "Unsupported language" in result['error']

def test_extract_structural_features_parse_error(mock_get_parser):
    """Test handling of parse errors."""
    code = "this is invalid code with error keyword"
    # We need to mock the parser to return an ERROR node
    with patch('src.data.feature_extractor._get_parser') as mock_parser:
        error_parser = MagicMock()
        error_tree = MockTree(MockNode("ERROR"))
        error_parser.parse.return_value = error_tree
        mock_parser.return_value = error_parser
        
        result = extract_structural_features(code, "python")
        
        assert result['valid'] is False
        assert "ERROR root node" in result['error']

def test_calculate_ast_depth():
    """Test AST depth calculation logic."""
    # Create a tree: root -> child1 -> grandchild
    grandchild = MockNode("leaf")
    child1 = MockNode("node", [grandchild])
    root = MockNode("root", [child1])
    
    depth = _calculate_ast_depth(root)
    assert depth == 2  # root(0) -> child(1) -> grandchild(2)

def test_count_nodes():
    """Test node counting logic."""
    # Create a tree: root -> [child1, child2]
    child1 = MockNode("c1")
    child2 = MockNode("c2")
    root = MockNode("root", [child1, child2])
    
    count = _count_nodes(root)
    assert count == 3  # root + 2 children

def test_cyclomatic_complexity_basic():
    """Test basic cyclomatic complexity calculation."""
    # Create a tree with an if statement
    if_node = MockNode("if_statement")
    root = MockNode("root", [if_node])
    
    complexity = _calculate_cyclomatic_complexity(root)
    # Base (1) + if (1) = 2
    assert complexity == 2

def test_extract_features_for_snippet(mock_get_parser):
    """Test feature extraction for a single snippet."""
    snippet = {
        'snippet_id': 'test-123',
        'language': 'python',
        'code': 'def x(): pass'
    }
    
    result = extract_features_for_snippet(snippet)
    
    assert result['snippet_id'] == 'test-123'
    assert result['language'] == 'python'
    assert result['feature_extraction_valid'] is True
    assert 'ast_depth' in result
    assert 'node_count' in result
    assert 'cyclomatic_complexity' in result

def test_batch_extract_features(mock_get_parser):
    """Test batch extraction logic."""
    snippets = [
        {'snippet_id': '1', 'language': 'python', 'code': 'x=1'},
        {'snippet_id': '2', 'language': 'python', 'code': 'y=2'}
    ]
    
    results = batch_extract_features(snippets)
    
    assert len(results) == 2
    assert results[0]['snippet_id'] == '1'
    assert results[1]['snippet_id'] == '2'
    assert all(r['feature_extraction_valid'] for r in results)

def test_batch_extract_features_partial_failure(mock_get_parser):
    """Test batch extraction with some failures."""
    snippets = [
        {'snippet_id': '1', 'language': 'python', 'code': 'x=1'},
        {'snippet_id': '2', 'language': 'unknown', 'code': 'y=2'}
    ]
    
    # Mock second parser to fail
    with patch('src.data.feature_extractor._get_parser') as mock_parser:
        mock_parser.side_effect = [MockParser(), None]
        
        results = batch_extract_features(snippets)
        
        assert len(results) == 2
        assert results[0]['feature_extraction_valid'] is True
        assert results[1]['feature_extraction_valid'] is False

@pytest.mark.integration
def test_integration_real_parsing():
    """
    Integration test with real tree-sitter if available.
    Skipped if tree-sitter-languages is not installed.
    """
    try:
        from tree_sitter_languages import get_parser
        parser = get_parser('python')
        code = "def hello():\n    if True:\n        return 1"
        tree = parser.parse(code.encode('utf8'))
        
        # Basic sanity check
        assert tree.root_node.type == 'module' or tree.root_node.type == 'program'
    except ImportError:
        pytest.skip("tree-sitter-languages not installed")
    except Exception as e:
        pytest.fail(f"Integration test failed: {e}")
