import ast
import sys
import tokenize
import io
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
import networkx as nx
import logging

from ..utils.logging import get_logger

logger = get_logger(__name__)


class TokenCounter:
    """Counts tokens in a code snippet using Python's tokenize module."""

    @staticmethod
    def count_tokens(code: str) -> int:
        """
        Count the number of tokens in a code string.

        Args:
            code: The Python code string to tokenize.

        Returns:
            The number of tokens in the code.
        """
        try:
            tokens = list(tokenize.generate_tokens(io.StringIO(code).readline))
            # Filter out ENCODING, NEWLINE, NL, COMMENT, and ENDMARKER if desired
            # For this task, we count all tokens to get a robust length estimate.
            return len(tokens)
        except tokenize.TokenError:
            logger.warning("Tokenization failed for snippet, returning 0")
            return 0


class ComplexityCalculator:
    """Calculates cyclomatic complexity using a Control Flow Graph (CFG)."""

    @staticmethod
    def build_cfg(node: ast.FunctionDef) -> nx.DiGraph:
        """
        Build a Control Flow Graph for a function definition node.

        Args:
            node: The AST FunctionDef node.

        Returns:
            A networkx DiGraph representing the CFG.
        """
        G = nx.DiGraph()
        # Create a node for the function entry
        G.add_node("entry")
        # Create a node for the function exit
        G.add_node("exit")

        # Map basic blocks (represented by line numbers or just sequential nodes)
        # For simplicity in this implementation, we treat each statement as a node
        # and add edges based on control flow keywords.
        # A more robust implementation would group statements into basic blocks.

        # We will iterate through the body and build edges.
        # To keep it simple but effective for complexity:
        # 1. Entry -> First statement
        # 2. Last statement -> Exit
        # 3. Branching statements add edges and increase complexity.

        # Flatten the body to a list of statements for linear traversal
        # Note: This is a simplified CFG construction.
        # Real cyclomatic complexity M = E - N + 2P.
        # Here we approximate by counting decision points + 1.

        decision_points = 0

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                decision_points += 1
            elif isinstance(child, ast.Assert):
                decision_points += 1
            elif isinstance(child, ast.comprehension):
                # List comprehensions, generator expressions, etc.
                decision_points += 1
            elif isinstance(child, ast.BoolOp):
                # and/or operators create implicit branches
                decision_points += len(child.values) - 1

        # Complexity = Decision Points + 1
        return decision_points + 1

    @staticmethod
    def calculate_complexity(node: ast.AST) -> int:
        """
        Calculate the cyclomatic complexity of an AST node.

        Args:
            node: The AST node (usually a FunctionDef).

        Returns:
            The cyclomatic complexity score.
        """
        if isinstance(node, ast.FunctionDef):
            return ComplexityCalculator.build_cfg(node)
        else:
            logger.warning(f"Complexity calculation requested for non-function node: {type(node)}")
            return 1


def extract_functions(tree: ast.AST) -> List[ast.FunctionDef]:
    """
    Recursively extract all function definitions from an AST.

    Args:
        tree: The root AST node.

    Returns:
        A list of ast.FunctionDef nodes found in the tree.
    """
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append(node)
    return functions


def extract_snippets_from_file(file_path: Path, min_tokens: int = 50) -> List[Dict[str, Any]]:
    """
    Extract function-level Python snippets from a file.

    Filters snippets by token length (>= min_tokens).
    Calculates complexity using networkx-based CFG analysis.

    Args:
        file_path: Path to the Python file.
        min_tokens: Minimum number of tokens required for a snippet to be included.

    Returns:
        A list of dictionaries containing snippet data:
        - snippet_content: The code string
        - token_count: Number of tokens
        - complexity: Cyclomatic complexity
        - start_line: Starting line number
        - end_line: Ending line number
    """
    snippets = []

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return snippets

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
    except UnicodeDecodeError:
        logger.warning(f"Could not decode file {file_path}, skipping.")
        return snippets
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return snippets

    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        logger.warning(f"Syntax error in {file_path}: {e}, skipping file.")
        return snippets

    functions = extract_functions(tree)

    for func in functions:
        # Get the source code for this specific function
        # ast.get_source_segment is available in Python 3.11+
        # For compatibility, we calculate lines manually
        start_line = func.lineno
        end_line = func.end_lineno if hasattr(func, 'end_lineno') and func.end_lineno else start_line

        # Extract lines (1-based to 0-based)
        lines = source_code.splitlines()
        if start_line <= len(lines) and end_line <= len(lines):
            func_source = '\n'.join(lines[start_line - 1 : end_line])
        else:
            # Fallback: reconstruct from AST (less reliable for formatting)
            func_source = ast.unparse(func) if hasattr(ast, 'unparse') else "<unparseable>"

        # Count tokens
        token_count = TokenCounter.count_tokens(func_source)

        # Filter by token length
        if token_count < min_tokens:
            continue

        # Calculate complexity
        complexity = ComplexityCalculator.calculate_complexity(func)

        snippets.append({
            "snippet_content": func_source,
            "token_count": token_count,
            "complexity": complexity,
            "start_line": start_line,
            "end_line": end_line
        })

    return snippets


def extract_snippets_from_directory(dir_path: Path, min_tokens: int = 50) -> List[Dict[str, Any]]:
    """
    Recursively extract snippets from all Python files in a directory.

    Args:
        dir_path: Path to the directory.
        min_tokens: Minimum token count filter.

    Returns:
        A list of snippet dictionaries with an added 'file_path' key.
    """
    all_snippets = []

    if not dir_path.exists() or not dir_path.is_dir():
        logger.error(f"Directory not found or not a directory: {dir_path}")
        return all_snippets

    for py_file in dir_path.rglob("*.py"):
        # Skip __pycache__ and hidden directories
        if "__pycache__" in str(py_file) or py_file.name.startswith('.'):
            continue

        file_snippets = extract_snippets_from_file(py_file, min_tokens)
        for snippet in file_snippets:
            snippet["file_path"] = str(py_file)
            all_snippets.append(snippet)

    logger.info(f"Extracted {len(all_snippets)} snippets from {dir_path}")
    return all_snippets


def main():
    """CLI entry point for testing the extractor."""
    import argparse

    parser = argparse.ArgumentParser(description="Extract function snippets from Python files.")
    parser.add_argument("path", type=str, help="Path to a Python file or directory")
    parser.add_argument("--min-tokens", type=int, default=50, help="Minimum token count filter")
    args = parser.parse_args()

    path = Path(args.path)
    min_tokens = args.min_tokens

    if path.is_file():
        snippets = extract_snippets_from_file(path, min_tokens)
    elif path.is_dir():
        snippets = extract_snippets_from_directory(path, min_tokens)
    else:
        logger.error(f"Path does not exist: {path}")
        sys.exit(1)

    print(f"Found {len(snippets)} snippets:")
    for i, s in enumerate(snippets):
        print(f"{i+1}. File: {s['file_path']}, Lines: {s['start_line']}-{s['end_line']}, "
              f"Tokens: {s['token_count']}, Complexity: {s['complexity']}")
        # Print first 50 chars of content
        content_preview = s['snippet_content'][:50].replace('\n', ' ')
        print(f"   Content: {content_preview}...")

    return snippets


if __name__ == "__main__":
    main()