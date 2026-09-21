"""
US1: Static Code Artifact Extraction.
Parses Python ASTs, normalizes tokens, matches lexicon, and computes sentiment scores.
"""
import ast
import logging
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

from .error_handler import safe_execute, ExecutionError, handle_pipeline_error
from .utils import setup_logging, streaming_repo_iterator, is_valid_python_syntax
from .lexicon import load_lexicon, match_lexicon

logger = setup_logging(__name__)

def parse_ast_tree(file_path: Path) -> Optional[ast.AST]:
    """
    Parse a Python file into an AST.
    Uses safe_execute to handle syntax errors gracefully.
    """
    @safe_execute(
        expected_exception=SyntaxError,
        error_msg="SyntaxError in file",
        fallback_return=None
    )
    def _parse(path: Path) -> ast.AST:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return ast.parse(f.read(), filename=str(path))

    return _parse(file_path)

def normalize_tokens(tokens: List[str]) -> List[str]:
    """
    Normalize tokens: convert camelCase to snake_case, lowercase.
    """
    normalized = []
    for token in tokens:
        # Simple camelCase to snake_case conversion
        result = []
        for i, char in enumerate(token):
            if char.isupper() and i > 0:
                result.append('_')
            result.append(char.lower())
        normalized.append("".join(result))
    return normalized

def analyze_sentiment(text: str) -> Dict[str, float]:
    """
    Analyze sentiment of a text string using VADER.
    Returns a dict with 'compound', 'pos', 'neu', 'neg'.
    """
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        analyzer = SentimentIntensityAnalyzer()
        scores = analyzer.polarity_scores(text)
        return scores
    except ImportError:
        logger.warning("vaderSentiment not installed. Returning neutral scores.")
        return {'compound': 0.0, 'pos': 0.0, 'neu': 1.0, 'neg': 0.0}

def extract_code_elements(tree: ast.AST) -> Tuple[List[str], List[str]]:
    """
    Extract variable names, function names, and comments from AST.
    Returns (identifiers, comments).
    """
    identifiers = []
    comments = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            identifiers.append(node.id)
        elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            identifiers.append(node.name)
            # Check for docstrings (comments)
            if (node.body and isinstance(node.body[0], ast.Expr) and
                isinstance(node.body[0].value, (ast.Str, ast.Constant))):
                val = node.body[0].value
                if isinstance(val, ast.Str):
                    comments.append(val.s)
                elif isinstance(val, ast.Constant) and isinstance(val.value, str):
                    comments.append(val.value)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    identifiers.append(target.id)
        # Extract comments from the AST's lineno mapping if available
        # Note: Standard ast module doesn't preserve comments well without `ast.get_docstring`
        # or specialized libraries, but we rely on docstrings above.
        # For line comments, we would need to read the file and map lines,
        # which is out of scope for pure AST extraction unless using `ast.get_source_segment`.
    
    return identifiers, comments

def aggregate_repo_score(file_scores: List[Dict[str, Any]]) -> float:
    """
    Compute repository-level score (mean of file scores, excluding 0-token files).
    """
    if not file_scores:
        return 0.0
    
    valid_scores = [f['bias_score'] for f in file_scores if f['token_count'] > 0]
    if not valid_scores:
        return 0.0
    
    return sum(valid_scores) / len(valid_scores)

@handle_pipeline_error(task_name="Repo Extraction")
def process_single_repo(repo_path: Path) -> Dict[str, Any]:
    """
    Process a single repository: iterate files, extract, analyze, aggregate.
    """
    lexicon = load_lexicon()
    file_scores = []
    
    # Use streaming iterator for memory efficiency
    for file_path, content in streaming_repo_iterator(repo_path):
        if not file_path.suffix == '.py':
            continue
        
        tree = parse_ast_tree(file_path)
        if tree is None:
            # Syntax error handled by safe_execute returning None
            logger.warning(f"Skipping {file_path} due to syntax error.")
            continue

        identifiers, comments = extract_code_elements(tree)
        
        # Normalize
        norm_ids = normalize_tokens(identifiers)
        
        # Match Lexicon
        lexicon_matches = match_lexicon(norm_ids, lexicon)
        
        # Sentiment on comments
        comment_scores = [analyze_sentiment(c) for c in comments]
        avg_sentiment = sum(s['compound'] for s in comment_scores) / len(comment_scores) if comment_scores else 0.0
        
        # Calculate file score (simple weighted sum for now)
        # Bias score = (lexicon_match_count * 1.0) + (negative_sentiment * 0.5)
        bias_score = len(lexicon_matches) + (max(0, -avg_sentiment) * 0.5)
        
        file_scores.append({
            'file': str(file_path),
            'bias_score': bias_score,
            'token_count': len(norm_ids),
            'lexicon_matches': lexicon_matches,
            'sentiment': avg_sentiment
        })
    
    repo_score = aggregate_repo_score(file_scores)
    
    return {
        'repo_path': str(repo_path),
        'repo_score': repo_score,
        'files_processed': len(file_scores),
        'details': file_scores
    }

def run_extraction_pipeline(repos: List[Path], output_path: Path) -> None:
    """
    Main entry point for US1. Runs extraction on a list of repos.
    """
    results = []
    for repo in repos:
        if not repo.exists():
            logger.error(f"Repo not found: {repo}")
            continue
        try:
            result = process_single_repo(repo)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to process {repo}: {e}")
            results.append({'repo_path': str(repo), 'error': str(e)})
    
    # Write output
    import json
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Extraction complete. Results written to {output_path}")
