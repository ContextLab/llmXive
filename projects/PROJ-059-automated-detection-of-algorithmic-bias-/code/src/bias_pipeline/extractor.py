import ast
import logging
import re
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple, Set

from .error_handler import safe_execute, ExecutionError, handle_pipeline_error
from .lexicon import load_lexicon, match_lexicon
from .utils import setup_logging, PipelineError, streaming_repo_iterator

# Configure logging
logger = setup_logging(__name__)


def normalize_tokens(token_string: str) -> List[str]:
    """
    Normalize a token string by splitting camelCase/snake_case and lowercasing.
    Example: 'userName' -> ['user', 'name']
    """
    if not token_string:
        return []
    
    # Replace underscores and hyphens with spaces for splitting
    normalized = re.sub(r'[_-]', ' ', token_string)
    
    # Split camelCase: insert space before uppercase letters
    normalized = re.sub(r'([a-z])([A-Z])', r'\1 \2', normalized)
    
    # Split on any whitespace
    tokens = normalized.lower().split()
    
    return [t for t in tokens if t.isalnum()]


def extract_tokens_from_node(node: ast.AST) -> List[str]:
    """
    Extract raw token strings from an AST node.
    Handles Name, Attribute, Constant (strings), and Call nodes.
    """
    tokens = []
    
    if isinstance(node, ast.Name):
        tokens.append(node.id)
    elif isinstance(node, ast.Attribute):
        tokens.append(node.attr)
    elif isinstance(node, ast.Constant) and isinstance(node.value, str):
        # Extract words from string literals (comments, docstrings, etc.)
        words = re.findall(r'\b\w+\b', node.value)
        tokens.extend(words)
    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            tokens.append(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            tokens.append(node.func.attr)
    
    return tokens


def parse_ast_tree(source_code: str) -> Optional[ast.AST]:
    """
    Parse source code into an AST. Returns None if syntax error.
    """
    try:
        return ast.parse(source_code)
    except SyntaxError as e:
        logger.warning(f"Syntax error in code: {e}")
        return None


def extract_code_elements(tree: ast.AST) -> Generator[Tuple[str, str, str], None, None]:
    """
    Walk the AST and yield (element_type, name, context) tuples.
    element_type: 'variable', 'function', 'class', 'string'
    context: surrounding code snippet or parent name
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            yield ('function', node.name, 'def')
        elif isinstance(node, ast.ClassDef):
            yield ('class', node.name, 'class')
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    yield ('variable', target.id, 'assignment')
                elif isinstance(target, ast.Attribute):
                    yield ('variable', target.attr, 'attribute_assignment')
        elif isinstance(node, ast.Name) and not isinstance(node, ast.Store):
            # Skip store contexts (definitions) handled above
            if isinstance(node.ctx, ast.Load):
                yield ('variable', node.id, 'usage')
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            # String literals (comments, docstrings, literals)
            yield ('string', node.value, 'literal')


def match_lexicon(tokens: List[str], lexicon: Set[str]) -> int:
    """
    Count how many tokens match the demographic lexicon.
    Returns the count of matches.
    """
    if not tokens or not lexicon:
        return 0
    
    count = 0
    for token in tokens:
        if token in lexicon:
            count += 1
    return count


def analyze_sentiment(text: str) -> float:
    """
    Analyze sentiment of text using VADER.
    Returns the compound score (-1 to 1).
    """
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        analyzer = SentimentIntensityAnalyzer()
        scores = analyzer.polarity_scores(text)
        return scores['compound']
    except ImportError:
        logger.warning("vaderSentiment not installed. Returning 0.0 sentiment.")
        return 0.0
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        return 0.0


def analyze_file(file_path: Path, lexicon: Set[str]) -> Dict[str, Any]:
    """
    Analyze a single Python file.
    Returns a dict with:
      - 'file_path': str
      - 'token_count': int
      - 'bias_score': float (weighted count of lexicon matches)
      - 'sentiment_score': float (average compound sentiment)
      - 'lexicon_matches': int
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            source_code = f.read()
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        return {
            'file_path': str(file_path),
            'token_count': 0,
            'bias_score': 0.0,
            'sentiment_score': 0.0,
            'lexicon_matches': 0
        }

    tree = parse_ast_tree(source_code)
    if tree is None:
        return {
            'file_path': str(file_path),
            'token_count': 0,
            'bias_score': 0.0,
            'sentiment_score': 0.0,
            'lexicon_matches': 0
        }

    all_tokens = []
    sentiment_scores = []
    
    for elem_type, name, context in extract_code_elements(tree):
        if elem_type == 'string':
            # Sentiment analysis on string literals (comments, docstrings)
            sent = analyze_sentiment(name)
            sentiment_scores.append(sent)
            # Also tokenize string content for lexicon matching
            all_tokens.extend(normalize_tokens(name))
        else:
            # Variable, function, class names
            normalized = normalize_tokens(name)
            all_tokens.extend(normalized)

    lexicon_matches = match_lexicon(all_tokens, lexicon)
    
    # Bias score: normalized count of lexicon matches
    # If no tokens, bias score is 0
    if len(all_tokens) == 0:
        bias_score = 0.0
    else:
        bias_score = lexicon_matches / len(all_tokens)

    # Average sentiment
    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0

    return {
        'file_path': str(file_path),
        'token_count': len(all_tokens),
        'bias_score': bias_score,
        'sentiment_score': avg_sentiment,
        'lexicon_matches': lexicon_matches
    }


@handle_pipeline_error
def process_single_repo(repo_path: Path, lexicon: Set[str]) -> Dict[str, Any]:
    """
    Process a single repository: analyze all Python files and return aggregated stats.
    """
    file_results = []
    
    for py_file in repo_path.rglob('*.py'):
        # Skip hidden directories and common non-source dirs
        if any(part.startswith('.') for part in py_file.parts):
            continue
        if any(part in {'__pycache__', 'venv', '.git', 'node_modules'} for part in py_file.parts):
            continue
        
        result = analyze_file(py_file, lexicon)
        if result['token_count'] > 0:
            file_results.append(result)

    return {
        'repo_path': str(repo_path),
        'files_analyzed': len(file_results),
        'file_results': file_results
    }


def aggregate_repo_score(repo_analysis: Dict[str, Any]) -> float:
    """
    Compute the repository-level bias score.
    
    Logic:
      - Extract file-level 'bias_score' for each file that has tokens (token_count > 0).
      - Compute the mean of these non-zero token file scores.
      - If no files have tokens, return 0.0.
    
    Args:
        repo_analysis: Dict returned by process_single_repo containing 'file_results'.
    
    Returns:
        float: The aggregated repository bias score.
    """
    file_results = repo_analysis.get('file_results', [])
    
    # Filter for files with tokens (exclude 0-token files as per FR-009)
    valid_scores = [
        f['bias_score'] for f in file_results 
        if f.get('token_count', 0) > 0
    ]
    
    if not valid_scores:
        return 0.0
    
    return sum(valid_scores) / len(valid_scores)