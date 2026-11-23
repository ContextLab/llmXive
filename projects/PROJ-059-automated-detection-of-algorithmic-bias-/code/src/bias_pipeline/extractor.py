"""
Extractor module for Automated Detection of Algorithmic Bias.

This module handles the static analysis of Python repositories to extract
code artifacts (AST nodes, tokens) and compute "Textual Bias Scores" based on
demographic lexicon matching and sentiment analysis of comments.

Implements User Story 1 (US1) and integrates with error_handler (T009, T043a).
"""

import ast
import logging
import re
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple, Set

from .error_handler import safe_execute, ExecutionError, handle_pipeline_error
from .utils import is_valid_python_syntax, streaming_repo_iterator
from .lexicon import load_lexicon, match_lexicon as lexicon_matcher

logger = logging.getLogger(__name__)

# --- Core Extraction Functions ---

@handle_pipeline_error(task_name="parse_ast_tree")
def parse_ast_tree(file_path: Path) -> Optional[ast.AST]:
    """
    Parse a Python file into an AST.

    Args:
        file_path: Path to the Python source file.

    Returns:
        The parsed AST object, or None if parsing fails (handled by decorator).
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            source_code = f.read()
        return ast.parse(source_code, filename=str(file_path))
    except SyntaxError:
        # Re-raise specific syntax error for the error handler to catch
        raise ExecutionError(f"SyntaxError in {file_path}") from None
    except Exception as e:
        raise ExecutionError(f"Failed to parse {file_path}: {e}") from e

@handle_pipeline_error(task_name="extract_code_elements")
def extract_code_elements(tree: ast.AST) -> Dict[str, List[str]]:
    """
    Traverse AST and extract variable names, function names, and string literals.

    Args:
        tree: The AST object.

    Returns:
        Dictionary with keys 'variables', 'functions', 'strings'.
    """
    elements = {
        'variables': [],
        'functions': [],
        'strings': [],
        'comments': [] # Comments are not in AST directly, handled in analyze_file via source
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    elements['variables'].append(target.id)
                elif isinstance(target, ast.Attribute):
                    elements['variables'].append(target.attr)
        elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            elements['functions'].append(node.name)
        elif isinstance(node, ast.Str) or isinstance(node, ast.Constant) and isinstance(node.value, str):
            elements['strings'].append(node.value)
        elif isinstance(node, ast.arguments):
            for arg in node.args:
                elements['variables'].append(arg.arg)

    return elements

@handle_pipeline_error(task_name="normalize_tokens")
def normalize_tokens(tokens: List[str]) -> List[str]:
    """
    Normalize tokens from camelCase to snake_case and lowercasing.

    Args:
        tokens: List of raw token strings.

    Returns:
        List of normalized tokens.
    """
    normalized = []
    for token in tokens:
        # Handle camelCase to snake_case
        # Insert underscore before uppercase letters that are followed by lowercase
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', token)
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
        # Lowercase
        normalized.append(s2.lower())
    return normalized

@handle_pipeline_error(task_name="match_lexicon")
def match_lexicon(tokens: List[str], lexicon: Dict[str, float]) -> Dict[str, Any]:
    """
    Match normalized tokens against the demographic lexicon.

    Args:
        tokens: List of normalized tokens.
        lexicon: The loaded lexicon dictionary {term: bias_score}.

    Returns:
        Dictionary containing matches and aggregated score.
    """
    matches = []
    total_score = 0.0
    count = 0

    for token in tokens:
        if token in lexicon:
            score = lexicon[token]
            matches.append({'token': token, 'score': score})
            total_score += score
            count += 1

    return {
        'matches': matches,
        'total_score': total_score,
        'count': count,
        'avg_score': total_score / count if count > 0 else 0.0
    }

@handle_pipeline_error(task_name="analyze_sentiment")
def analyze_sentiment(text: str) -> Dict[str, float]:
    """
    Analyze sentiment of a text string using VADER.

    Args:
        text: The text to analyze.

    Returns:
        Dictionary with compound, pos, neu, neg scores.
    """
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    except ImportError:
        raise ExecutionError("vaderSentiment not installed") from None

    analyzer = SentimentIntensityAnalyzer()
    scores = analyzer.polarity_scores(text)
    return scores

# --- File and Repository Level Processing ---

@handle_pipeline_error(task_name="analyze_file")
def analyze_file(file_path: Path, lexicon: Dict[str, float]) -> Dict[str, Any]:
    """
    Perform full analysis on a single Python file.

    1. Parse AST.
    2. Extract elements.
    3. Normalize tokens.
    4. Match lexicon.
    5. Analyze sentiment of comments (extracted via regex from source).

    Args:
        file_path: Path to the file.
        lexicon: Loaded lexicon.

    Returns:
        Aggregated analysis result for the file.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Extract comments using regex from source
    source = file_path.read_text(encoding='utf-8', errors='ignore')
    comment_pattern = re.compile(r'#.*$|\"\"\"[\s\S]*?\"\"\"|\'\'\'[\s\S]*?\'\'\'', re.MULTILINE)
    comments = comment_pattern.findall(source)
    comment_text = " ".join(comments)

    tree = parse_ast_tree(file_path)
    if tree is None:
        return {'status': 'error', 'message': 'Failed to parse AST'}

    elements = extract_code_elements(tree)
    all_tokens = (
        elements.get('variables', []) +
        elements.get('functions', []) +
        elements.get('strings', [])
    )

    normalized = normalize_tokens(all_tokens)
    lexicon_result = match_lexicon(normalized, lexicon)

    sentiment_result = analyze_sentiment(comment_text)

    return {
        'file': str(file_path),
        'lexicon': lexicon_result,
        'sentiment': sentiment_result,
        'token_count': len(normalized),
        'comment_count': len(comments)
    }

@handle_pipeline_error(task_name="process_single_repo")
def process_single_repo(repo_path: Path, lexicon: Dict[str, float]) -> Generator[Dict[str, Any], None, None]:
    """
    Iterate over Python files in a repository and yield analysis results.

    Args:
        repo_path: Path to the repository root.
        lexicon: Loaded lexicon.

    Yields:
        Analysis result for each valid Python file.
    """
    if not repo_path.is_dir():
        raise ExecutionError(f"Path is not a directory: {repo_path}")

    # Use streaming iterator if available, else fallback to walk
    try:
        files = streaming_repo_iterator(repo_path, language="python")
    except Exception:
        files = (p for p in repo_path.rglob("*.py") if ".git" not in str(p))

    for file_path in files:
        try:
            result = analyze_file(file_path, lexicon)
            yield result
        except Exception as e:
            logger.warning(f"Skipping {file_path} due to error: {e}")
            continue

@handle_pipeline_error(task_name="aggregate_repo_score")
def aggregate_repo_score(file_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate file-level results into a single repository-level score.

    Logic: Mean of file scores, excluding files with 0 tokens.

    Args:
        file_results: List of dictionaries returned by analyze_file.

    Returns:
        Aggregated repository score dictionary.
    """
    valid_scores = []
    valid_sentiments = []

    for res in file_results:
        if res.get('token_count', 0) > 0:
            valid_scores.append(res['lexicon']['avg_score'])
            valid_sentiments.append(res['sentiment']['compound'])

    if not valid_scores:
        return {
            'repo_bias_score': 0.0,
            'repo_sentiment_score': 0.0,
            'files_analyzed': 0,
            'files_with_tokens': 0
        }

    avg_bias = sum(valid_scores) / len(valid_scores)
    avg_sentiment = sum(valid_sentiments) / len(valid_sentiments) if valid_sentiments else 0.0

    return {
        'repo_bias_score': avg_bias,
        'repo_sentiment_score': avg_sentiment,
        'files_analyzed': len(file_results),
        'files_with_tokens': len(valid_scores)
    }