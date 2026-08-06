"""
Feature Extraction Module for Security Vulnerability Analysis.

This module implements structural feature extraction using tree-sitter
to compute AST depth, node count, and cyclomatic complexity for code snippets.
It consumes preprocessed data from T012 (data/processed/raw_snippets.parquet).
"""
import os
import logging
import re
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import json
import gc

import pandas as pd
from tree_sitter import Language, Parser
from tree_sitter_languages import get_language, get_parser

from src.utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_failure
from src.utils.config import get_data_processed_path, get_data_logs_path, get_config
from src.utils.memory_monitor import get_current_memory_usage_gb, check_memory_constraint, force_gc

# Constants
MAX_AST_DEPTH = 100
CYCLOMATIC_COMPLEXITY_THRESHOLD = 50  # Sanity check for runaway recursion
BATCH_SIZE = 50  # Adjust based on memory monitoring

logger = get_logger(__name__)

# Language mapping for tree-sitter
LANGUAGE_MAP = {
    'python': 'python',
    'c': 'c',
    'cpp': 'cpp',
    'javascript': 'javascript',
    'java': 'java',
}

# Global parser cache to avoid re-initialization
_parsers_cache: Dict[str, Parser] = {}
_languages_cache: Dict[str, Language] = {}

def _get_parser(language: str) -> Optional[Parser]:
    """Retrieve or initialize a tree-sitter parser for the given language."""
    if language not in LANGUAGE_MAP:
        logger.warning(f"Unsupported language for tree-sitter: {language}")
        return None

    lang_name = LANGUAGE_MAP[language]

    if lang_name not in _parsers_cache:
        try:
            # tree-sitter-languages handles the loading of shared libraries
            parser = get_parser(lang_name)
            _parsers_cache[lang_name] = parser
            logger.debug(f"Initialized parser for {lang_name}")
        except Exception as e:
            logger.error(f"Failed to initialize parser for {lang_name}: {e}")
            return None

    return _parsers_cache[lang_name]

def _calculate_ast_depth(node, current_depth: int = 0) -> int:
    """Recursively calculate the maximum depth of the AST."""
    if node.child_count == 0:
        return current_depth
    
    max_child_depth = current_depth
    for child in node.children:
        child_depth = _calculate_ast_depth(child, current_depth + 1)
        if child_depth > max_child_depth:
            max_child_depth = child_depth
    
    return max_child_depth

def _count_nodes(node) -> int:
    """Count total nodes in the AST."""
    count = 1
    for child in node.children:
        count += _count_nodes(child)
    return count

def _calculate_cyclomatic_complexity(node) -> int:
    """
    Calculate cyclomatic complexity based on decision nodes.
    This is a heuristic approximation suitable for static analysis.
    """
    complexity = 1  # Base complexity
    
    # Decision nodes that increase complexity
    decision_keywords = {
        'if_statement', 'for_statement', 'while_statement', 
        'switch_statement', 'case_clause', 'catch_clause',
        'ternary_expression', 'logical_and', 'logical_or'
    }

    # Check current node
    if node.type in decision_keywords:
        complexity += 1

    # Recurse
    for child in node.children:
        complexity += _calculate_cyclomatic_complexity(child)

    return complexity

def extract_structural_features(code: str, language: str) -> Dict[str, Any]:
    """
    Extract structural metrics from a code snippet using tree-sitter.
    
    Args:
        code: The source code string.
        language: The programming language identifier.
        
    Returns:
        Dictionary containing:
            - ast_depth: Maximum depth of the AST
            - node_count: Total number of nodes in the AST
            - cyclomatic_complexity: Estimated cyclomatic complexity
            - valid: Boolean indicating if parsing was successful
    """
    parser = _get_parser(language)
    if not parser:
        return {
            'ast_depth': None,
            'node_count': None,
            'cyclomatic_complexity': None,
            'valid': False,
            'error': f"Unsupported language: {language}"
        }

    try:
        # Encode code for tree-sitter
        code_bytes = code.encode('utf8')
        tree = parser.parse(code_bytes)
        root_node = tree.root_node

        if root_node.type == 'ERROR':
            return {
                'ast_depth': None,
                'node_count': None,
                'cyclomatic_complexity': None,
                'valid': False,
                'error': "Parser returned an ERROR root node"
            }

        ast_depth = _calculate_ast_depth(root_node)
        node_count = _count_nodes(root_node)
        cyclomatic_complexity = _calculate_cyclomatic_complexity(root_node)

        # Sanity checks
        if ast_depth > MAX_AST_DEPTH:
            logger.warning(f"AST depth {ast_depth} exceeds threshold for snippet ID")
            ast_depth = MAX_AST_DEPTH
        
        if cyclomatic_complexity > CYCLOMATIC_COMPLEXITY_THRESHOLD:
            logger.warning(f"Cyclomatic complexity {cyclomatic_complexity} exceeds threshold")
            cyclomatic_complexity = CYCLOMATIC_COMPLEXITY_THRESHOLD

        return {
            'ast_depth': ast_depth,
            'node_count': node_count,
            'cyclomatic_complexity': cyclomatic_complexity,
            'valid': True,
            'error': None
        }

    except Exception as e:
        logger.error(f"Error parsing code snippet: {e}", exc_info=True)
        return {
            'ast_depth': None,
            'node_count': None,
            'cyclomatic_complexity': None,
            'valid': False,
            'error': str(e)
        }

def extract_features_for_snippet(snippet: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract features for a single code snippet.
    
    Args:
        snippet: Dictionary containing 'code' and 'language' keys.
        
    Returns:
        Dictionary with original snippet data plus structural features.
    """
    code = snippet.get('code', '')
    language = snippet.get('language', 'python')
    
    # Check memory before processing
    mem_gb = get_current_memory_usage_gb()
    if mem_gb > 6.0:  # Conservative threshold
        logger.warning(f"Memory usage high ({mem_gb:.2f}GB). Forcing GC.")
        force_gc()
    
    features = extract_structural_features(code, language)
    
    result = {
        'snippet_id': snippet.get('snippet_id'),
        'language': language,
        'ast_depth': features['ast_depth'],
        'node_count': features['node_count'],
        'cyclomatic_complexity': features['cyclomatic_complexity'],
        'feature_extraction_valid': features['valid'],
        'feature_extraction_error': features['error']
    }
    
    return result

def batch_extract_features(snippets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract features for a batch of snippets.
    
    Args:
        snippets: List of snippet dictionaries.
        
    Returns:
        List of dictionaries with extracted features.
    """
    results = []
    for i, snippet in enumerate(snippets):
        try:
            result = extract_features_for_snippet(snippet)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to extract features for snippet {i}: {e}")
            results.append({
                'snippet_id': snippet.get('snippet_id'),
                'language': snippet.get('language'),
                'ast_depth': None,
                'node_count': None,
                'cyclomatic_complexity': None,
                'feature_extraction_valid': False,
                'feature_extraction_error': str(e)
            })
    
    return results

def run_feature_extraction_pipeline():
    """
    Main pipeline function to run feature extraction on the processed dataset.
    Reads from data/processed/raw_snippets.parquet and writes to data/processed/features.csv.
    """
    log_stage_start("Feature Extraction Pipeline", task_id="T018a")
    
    input_path = get_data_processed_path("raw_snippets.parquet")
    output_path = get_data_processed_path("features.csv")
    log_path = get_data_logs_path("feature_extractor_errors.json")
    
    if not input_path.exists():
        msg = f"Input file not found: {input_path}"
        logger.error(msg)
        log_stage_failure("Feature Extraction Pipeline", msg)
        raise FileNotFoundError(msg)
    
    logger.info(f"Loading data from {input_path}")
    try:
        df = pd.read_parquet(input_path)
    except Exception as e:
        msg = f"Failed to load parquet file: {e}"
        logger.error(msg)
        log_stage_failure("Feature Extraction Pipeline", msg)
        raise
    
    logger.info(f"Loaded {len(df)} snippets")
    
    # Convert to list of dicts for processing
    snippets = df.to_dict('records')
    processed_results = []
    errors = []
    
    total = len(snippets)
    processed_count = 0
    
    logger.info(f"Starting batch processing of {total} snippets")
    
    for i in range(0, total, BATCH_SIZE):
        batch = snippets[i : i + BATCH_SIZE]
        batch_results = batch_extract_features(batch)
        processed_results.extend(batch_results)
        
        # Collect errors
        for res in batch_results:
            if not res.get('feature_extraction_valid', False):
                errors.append({
                    'snippet_id': res.get('snippet_id'),
                    'language': res.get('language'),
                    'error': res.get('feature_extraction_error')
                })
        
        processed_count += len(batch)
        if processed_count % 500 == 0:
            logger.info(f"Processed {processed_count}/{total} snippets")
            check_memory_constraint()
    
    # Convert results to DataFrame
    result_df = pd.DataFrame(processed_results)
    
    # Save to CSV
    logger.info(f"Saving results to {output_path}")
    result_df.to_csv(output_path, index=False)
    
    # Save errors log
    if errors:
        logger.warning(f"Found {len(errors)} snippets with extraction errors")
        with open(log_path, 'w') as f:
            json.dump(errors, f, indent=2)
    else:
        # Create empty log if no errors
        with open(log_path, 'w') as f:
            json.dump([], f)
    
    log_stage_complete("Feature Extraction Pipeline", {
        "total_processed": total,
        "successful": len([r for r in processed_results if r.get('feature_extraction_valid')]),
        "failed": len(errors),
        "output_file": str(output_path)
    })
    
    return result_df

def main():
    """Entry point for the feature extraction script."""
    try:
        run_feature_extraction_pipeline()
        logger.info("Feature extraction pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
