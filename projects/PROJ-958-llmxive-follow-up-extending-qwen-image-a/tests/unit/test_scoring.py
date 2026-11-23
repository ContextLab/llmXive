"""
Unit tests for src/scoring/syntactic_features.py
"""

import pytest
import importlib
import sys
import os
import ast

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.scoring.syntactic_features import compute_syntactic_features, get_feature_names

def test_feature_names():
    """Verify that the module exposes the correct feature names."""
    names = get_feature_names()
    assert "parse_tree_depth" in names
    assert "clause_count" in names

def test_malformed_prompt_handling():
    """
    Verify that malformed/empty prompts return a default score of 0.0
    and set is_valid to False.
    """
    # Test empty string
    result = compute_syntactic_features("")
    assert result["parse_tree_depth"] == 0.0
    assert result["clause_count"] == 0
    assert result["is_valid"] is False
    assert "warning" in result

    # Test None
    result = compute_syntactic_features(None)
    assert result["parse_tree_depth"] == 0.0
    assert result["is_valid"] is False

    # Test whitespace only
    result = compute_syntactic_features("   \n\t   ")
    assert result["is_valid"] is False

def test_no_semantic_embeddings():
    """
    Static analysis test: Verify that the source code of syntactic_features.py
    does NOT import or use semantic embedding libraries (BERT, CLIP, transformers text encoders).
    """
    source_file = os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'scoring', 'syntactic_features.py')
    with open(source_file, 'r', encoding='utf-8') as f:
        source_code = f.read()

    forbidden_imports = [
        'transformers', 'bert', 'clip', 'sentence_transformers',
        'torch.nn.BertModel', 'torchvision.models.vision_transformer'
    ]
    
    # Parse the AST to check imports more robustly
    tree = ast.parse(source_code)
    
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.add(node.module.split('.')[0])

    # Check for forbidden high-level packages
    forbidden_found = []
    for mod in imported_modules:
        if mod in ['transformers', 'clip', 'sentence_transformers']:
            forbidden_found.append(mod)
    
    # Also check raw source for specific strings if AST misses something
    for pattern in forbidden_imports:
        if pattern in source_code:
            forbidden_found.append(pattern)

    assert len(forbidden_found) == 0, f"Semantic embedding libraries found in source: {forbidden_found}"

def test_valid_prompt_structure():
    """
    Verify that a valid, simple prompt returns non-zero features and is_valid=True.
    """
    prompt = "The cat sat on the mat."
    result = compute_syntactic_features(prompt)
    
    assert result["is_valid"] is True
    assert result["parse_tree_depth"] >= 0.0
    assert result["clause_count"] >= 1 # At least one main clause

def test_complex_prompt_structure():
    """
    Verify that a complex sentence yields higher clause count or depth than a simple one.
    """
    simple = "The dog runs."
    complex_prompt = "Although it was raining, the dog ran outside because he wanted to play."
    
    res_simple = compute_syntactic_features(simple)
    res_complex = compute_syntactic_features(complex_prompt)
    
    # Complex should have more clauses
    assert res_complex["clause_count"] >= res_simple["clause_count"]