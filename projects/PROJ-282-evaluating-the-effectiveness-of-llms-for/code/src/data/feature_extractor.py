"""
Feature extraction module using tree-sitter for structural metrics.
Computes AST depth, node count, and cyclomatic complexity for code snippets.
"""
import os
import logging
import re
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import json

# Tree-sitter imports
try:
    from tree_sitter import Language, Parser
    import tree_sitter_c as tsc
    import tree_sitter_cpp as tscpp
    import tree_sitter_javascript as tsjs
    import tree_sitter_python as tspython
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    logging.warning("tree-sitter libraries not installed. Structural features will be unavailable.")

import pandas as pd
import numpy as np

from src.utils.logger import get_logger
from src.utils.config import get_data_processed_path, get_data_logs_path
from src.models.feature_vector import FeatureVector, create_feature_vector

logger = get_logger(__name__)

# Language mappings for tree-sitter
LANGUAGE_MAP = {
    'c': (tsc, 'c'),
    'cpp': (tscpp, 'cpp'),
    'javascript': (tsjs, 'javascript'),
    'python': (tspython, 'python')
}

# Initialize parsers (lazy loading to avoid memory bloat)
_parsers: Dict[str, Parser] = {}
_languages: Dict[str, Language] = {}

def _get_parser(lang: str) -> Optional[Parser]:
    """Get or create a tree-sitter parser for the specified language."""
    if not TREE_SITTER_AVAILABLE:
        return None
    
    if lang in _parsers:
        return _parsers[lang]
    
    if lang not in LANGUAGE_MAP:
        logger.warning(f"Unsupported language for tree-sitter: {lang}")
        return None
    
    try:
        module, lang_name = LANGUAGE_MAP[lang]
        # Create language instance
        lang_instance = Language(module.language())
        _languages[lang] = lang_instance
        
        # Create parser
        parser = Parser()
        parser.set_language(lang_instance)
        _parsers[lang] = parser
        
        return parser
    except Exception as e:
        logger.error(f"Failed to initialize parser for {lang}: {e}")
        return None

def _calculate_ast_depth(node, current_depth=0) -> int:
    """Recursively calculate the maximum depth of the AST."""
    if not node.children:
        return current_depth
    
    max_depth = current_depth
    for child in node.children:
        child_depth = _calculate_ast_depth(child, current_depth + 1)
        max_depth = max(max_depth, child_depth)
    
    return max_depth

def _count_nodes(node) -> int:
    """Count total number of nodes in the AST."""
    count = 1  # Count current node
    for child in node.children:
        count += _count_nodes(child)
    return count

def _calculate_cyclomatic_complexity(node) -> int:
    """
    Calculate cyclomatic complexity based on decision points.
    Counts: if, elif, for, while, case, catch, logical operators (and, or).
    """
    complexity = 1  # Base complexity
    
    # Decision point keywords for various languages
    decision_keywords = {
        'if', 'elif', 'else_if', 'for', 'while', 'case', 'catch', 
        'except', 'match', '&&', '||', 'and', 'or', '?:'
    }
    
    # Traverse the tree
    stack = [node]
    while stack:
        current = stack.pop()
        if current.type in decision_keywords:
            complexity += 1
        stack.extend(current.children)
    
    return complexity

def extract_structural_features(code: str, language: str) -> Dict[str, Any]:
    """
    Extract structural features from code using tree-sitter.
    
    Args:
        code: The source code string
        language: Language identifier (c, cpp, javascript, python)
        
    Returns:
        Dictionary with structural metrics
    """
    if not TREE_SITTER_AVAILABLE:
        return {
            'ast_depth': None,
            'node_count': None,
            'cyclomatic_complexity': None,
            'parse_error': 'tree-sitter not available'
        }
    
    parser = _get_parser(language)
    if not parser:
        return {
            'ast_depth': None,
            'node_count': None,
            'cyclomatic_complexity': None,
            'parse_error': f'parser not available for {language}'
        }
    
    try:
        # Encode code to bytes
        code_bytes = code.encode('utf-8')
        
        # Parse the code
        tree = parser.parse(code_bytes)
        root_node = tree.root_node
        
        # Calculate metrics
        ast_depth = _calculate_ast_depth(root_node)
        node_count = _count_nodes(root_node)
        cyclomatic_complexity = _calculate_cyclomatic_complexity(root_node)
        
        return {
            'ast_depth': ast_depth,
            'node_count': node_count,
            'cyclomatic_complexity': cyclomatic_complexity,
            'parse_error': None
        }
        
    except Exception as e:
        logger.error(f"Parse error for language {language}: {e}")
        return {
            'ast_depth': None,
            'node_count': None,
            'cyclomatic_complexity': None,
            'parse_error': str(e)
        }

def extract_semantic_features(code: str, language: str) -> Dict[str, Any]:
    """
    Extract semantic features (placeholder for T018b).
    Currently returns None values as this is implemented in T018b.
    """
    return {
        'taint_api_count': None,
        'sanitization_present': None
    }

def extract_features_for_snippet(snippet: Dict[str, Any]) -> Optional[FeatureVector]:
    """
    Extract all features for a single code snippet.
    
    Args:
        snippet: Dictionary containing 'code', 'language', and 'snippet_id'
        
    Returns:
        FeatureVector object or None if extraction fails
    """
    code = snippet.get('code', '')
    language = snippet.get('language', '').lower()
    snippet_id = snippet.get('snippet_id', 'unknown')
    
    if not code:
        logger.warning(f"Empty code for snippet {snippet_id}")
        return None
    
    # Extract structural features
    structural = extract_structural_features(code, language)
    
    # Extract semantic features (placeholder)
    semantic = extract_semantic_features(code, language)
    
    # Create FeatureVector
    try:
        feature_vector = create_feature_vector(
            snippet_id=snippet_id,
            language=language,
            ast_depth=structural.get('ast_depth'),
            node_count=structural.get('node_count'),
            cyclomatic_complexity=structural.get('cyclomatic_complexity'),
            taint_api_count=semantic.get('taint_api_count'),
            sanitization_present=semantic.get('sanitization_present')
        )
        
        return feature_vector
        
    except Exception as e:
        logger.error(f"Failed to create FeatureVector for {snippet_id}: {e}")
        return None

def batch_extract_features(snippets: List[Dict[str, Any]], batch_size: int = 100) -> List[FeatureVector]:
    """
    Extract features for a batch of snippets.
    
    Args:
        snippets: List of snippet dictionaries
        batch_size: Number of snippets to process at once
        
    Returns:
        List of FeatureVector objects
    """
    results = []
    total = len(snippets)
    
    logger.info(f"Starting batch extraction for {total} snippets")
    
    for i in range(0, total, batch_size):
        batch = snippets[i:i + batch_size]
        batch_results = []
        
        for j, snippet in enumerate(batch):
            try:
                feature_vector = extract_features_for_snippet(snippet)
                if feature_vector:
                    batch_results.append(feature_vector)
            except Exception as e:
                logger.error(f"Error processing snippet {i+j}: {e}")
                continue
        
        results.extend(batch_results)
        
        # Log progress
        if (i + batch_size) % 500 == 0 or (i + batch_size) >= total:
            logger.info(f"Processed {min(i + batch_size, total)}/{total} snippets")
    
    logger.info(f"Completed extraction: {len(results)}/{total} successful")
    return results

def main():
    """Main entry point for feature extraction pipeline."""
    logger.info("Starting feature extraction pipeline (T018a)")
    
    # Check for tree-sitter
    if not TREE_SITTER_AVAILABLE:
        logger.error("tree-sitter libraries not installed. Cannot proceed.")
        logger.error("Install with: pip install tree-sitter tree-sitter-c tree-sitter-cpp tree-sitter-javascript tree-sitter-python")
        return 1
    
    # Load processed snippets from T012
    processed_path = get_data_processed_path()
    input_file = processed_path / "raw_snippets.parquet"
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please run T012 (preprocess) first to generate raw_snippets.parquet")
        return 1
    
    logger.info(f"Loading snippets from {input_file}")
    df = pd.read_parquet(input_file)
    
    # Convert to list of dicts
    snippets = df.to_dict('records')
    logger.info(f"Loaded {len(snippets)} snippets")
    
    # Extract features
    feature_vectors = batch_extract_features(snippets, batch_size=100)
    
    if not feature_vectors:
        logger.error("No features extracted. Check logs for errors.")
        return 1
    
    # Convert to DataFrame for saving
    feature_data = []
    for fv in feature_vectors:
        feature_data.append({
            'snippet_id': fv.snippet_id,
            'language': fv.language,
            'ast_depth': fv.ast_depth,
            'node_count': fv.node_count,
            'cyclomatic_complexity': fv.cyclomatic_complexity,
            'taint_api_count': fv.taint_api_count,
            'sanitization_present': fv.sanitization_present,
            'embedding_similarity_score': None,  # Placeholder for T019c
        })
    
    features_df = pd.DataFrame(feature_data)
    
    # Save to CSV
    output_file = processed_path / "features.csv"
    features_df.to_csv(output_file, index=False)
    
    logger.info(f"Saved features to {output_file}")
    logger.info(f"Total features extracted: {len(features_df)}")
    
    # Log summary statistics
    logger.info(f"Ast depth stats: min={features_df['ast_depth'].min()}, max={features_df['ast_depth'].max()}, mean={features_df['ast_depth'].mean():.2f}")
    logger.info(f"Node count stats: min={features_df['node_count'].min()}, max={features_df['node_count'].max()}, mean={features_df['node_count'].mean():.2f}")
    logger.info(f"Cyclomatic complexity stats: min={features_df['cyclomatic_complexity'].min()}, max={features_df['cyclomatic_complexity'].max()}, mean={features_df['cyclomatic_complexity'].mean():.2f}")
    
    return 0

if __name__ == "__main__":
    exit(main())
