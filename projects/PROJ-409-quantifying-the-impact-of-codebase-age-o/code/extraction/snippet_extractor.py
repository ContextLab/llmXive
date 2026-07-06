"""
Snippet Extractor Module

Extracts function-level Python snippets from source files using AST.
Filters by token length (>= 50 tokens) and calculates complexity using
networkx Control Flow Graph analysis.
"""

import ast
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import tokenize
import io
import networkx as nx

# Import logging from project utils
from utils.logging import get_logger

logger = get_logger(__name__)


class ComplexityCalculator:
    """Calculates cyclomatic complexity using Control Flow Graph (CFG)."""

    def __init__(self):
        self.graph = nx.DiGraph()

    def visit(self, node: ast.AST) -> None:
        """Visit an AST node and build the CFG."""
        node_id = id(node)
        if node_id not in self.graph:
            self.graph.add_node(node_id)

        # Add edges for control flow statements
        if isinstance(node, (ast.If, ast.While, ast.For, ast.With)):
            # Condition -> Body
            self._add_edge(node, node.body)
            # Condition -> Orelse (else/elif)
            if node.orelse:
                self._add_edge(node, node.orelse)
            # Also add edge from body to orelse for linear flow
            if node.body and node.orelse:
                self._add_edge(node.body[-1], node.orelse[0])

        elif isinstance(node, ast.Try):
            # Try body -> handlers
            self._add_edge(node, node.body)
            for handler in node.handlers:
                self._add_edge(node, handler.body)
            if node.orelse:
                self._add_edge(node, node.orelse)
            if node.finalbody:
                self._add_edge(node, node.finalbody)

        elif isinstance(node, ast.ExceptHandler):
            self._add_edge(node, node.body)

        elif isinstance(node, ast.FunctionDef):
            self._add_edge(node, node.body)

        elif isinstance(node, ast.AsyncFunctionDef):
            self._add_edge(node, node.body)

        elif isinstance(node, ast.ClassDef):
            self._add_edge(node, node.body)

        # Recursively visit children
        for child in ast.iter_child_nodes(node):
            self.visit(child)

    def _add_edge(self, from_node: ast.AST, to_nodes: List[ast.AST]) -> None:
        """Add edges from a node to a list of child nodes."""
        if not to_nodes:
            return
        from_id = id(from_node)
        to_id = id(to_nodes[0])
        if from_id not in self.graph:
            self.graph.add_node(from_id)
        if to_id not in self.graph:
            self.graph.add_node(to_id)
        self.graph.add_edge(from_id, to_id)

    def calculate(self, tree: ast.AST) -> int:
        """
        Calculate cyclomatic complexity.
        V(G) = E - N + 2P
        Where E = edges, N = nodes, P = connected components (usually 1)
        For a single function, we count decision points + 1.
        """
        self.graph = nx.DiGraph()
        self.visit(tree)

        if len(self.graph.nodes) == 0:
            return 1

        # Count decision points (if, while, for, except, and, or)
        # Plus 1 for the base path
        complexity = 1

        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                # Each 'and'/'or' adds a decision point
                complexity += len(node.values) - 1
            elif isinstance(node, ast.comprehension):
                # List/dict/set comprehensions with if clauses
                complexity += len(node.ifs)

        return complexity


class TokenCounter:
    """Counts tokens in a code snippet."""

    @staticmethod
    def count(code: str) -> int:
        """Count the number of tokens in the code string."""
        try:
            tokens = list(tokenize.generate_tokens(io.StringIO(code).readline))
            # Filter out whitespace and comment-only tokens for meaningful count
            meaningful_tokens = [t for t in tokens if t.type not in (tokenize.ENDMARKER, tokenize.NL, tokenize.NEWLINE)]
            return len(meaningful_tokens)
        except Exception as e:
            logger.warning(f"Error counting tokens: {e}")
            return 0


def extract_functions(file_path: Path) -> List[Dict[str, Any]]:
    """
    Extract all function definitions from a Python file.

    Args:
        file_path: Path to the Python file

    Returns:
        List of dictionaries containing function info
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            source_code = f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return []

    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        logger.warning(f"Syntax error in {file_path}: {e}")
        return []

    calculator = ComplexityCalculator()
    token_counter = TokenCounter()
    snippets = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Extract source code for this function
            try:
                func_source = ast.get_source_segment(source_code, node)
                if func_source is None:
                    # Fallback: reconstruct from lines
                    start_line = node.lineno
                    end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line
                    lines = source_code.split('\n')
                    func_source = '\n'.join(lines[start_line-1:end_line])

                if not func_source or not func_source.strip():
                    continue

                # Count tokens
                token_count = token_counter.count(func_source)

                # Skip if too short
                if token_count < 50:
                    continue

                # Calculate complexity
                complexity = calculator.calculate(node)

                snippets.append({
                    'function_name': node.name,
                    'start_line': node.lineno,
                    'end_line': node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
                    'snippet_content': func_source,
                    'token_count': token_count,
                    'complexity': complexity
                })

            except Exception as e:
                logger.warning(f"Error extracting function {node.name} in {file_path}: {e}")
                continue

    return snippets


def extract_snippets_from_file(file_path: Path, repo_url: str = "") -> List[Dict[str, Any]]:
    """
    Extract function-level snippets from a single file.

    Args:
        file_path: Path to the Python file
        repo_url: URL of the repository (for metadata)

    Returns:
        List of snippet dictionaries with metadata
    """
    if not file_path.exists():
        logger.warning(f"File does not exist: {file_path}")
        return []

    if not file_path.suffix == '.py':
        return []

    raw_snippets = extract_functions(file_path)

    # Add metadata
    enriched_snippets = []
    for snippet in raw_snippets:
        enriched_snippets.append({
            'repo_url': repo_url,
            'file_path': str(file_path),
            'snippet_id': f"{file_path.stem}_{snippet['function_name']}_{snippet['start_line']}",
            'function_name': snippet['function_name'],
            'start_line': snippet['start_line'],
            'end_line': snippet['end_line'],
            'snippet_content': snippet['snippet_content'],
            'token_count': snippet['token_count'],
            'complexity': snippet['complexity'],
            # These will be filled by the caller
            'median_commit_age': None,
            'token_length': snippet['token_count']
        })

    return enriched_snippets


def extract_snippets_from_directory(dir_path: Path, repo_url: str = "") -> List[Dict[str, Any]]:
    """
    Extract snippets from all Python files in a directory.

    Args:
        dir_path: Path to the directory
        repo_url: URL of the repository

    Returns:
        List of all snippets found
    """
    all_snippets = []

    for py_file in dir_path.rglob("*.py"):
        # Skip common non-source directories
        if any(part.startswith('.') for part in py_file.parts):
            continue
        if any(part in ['__pycache__', 'node_modules', '.git'] for part in py_file.parts):
            continue

        snippets = extract_snippets_from_file(py_file, repo_url)
        all_snippets.extend(snippets)

    logger.info(f"Extracted {len(all_snippets)} snippets from {dir_path}")
    return all_snippets


def main():
    """Main entry point for standalone execution."""
    import sys
    from utils.config import ensure_directories

    if len(sys.argv) < 2:
        print("Usage: python snippet_extractor.py <path_to_python_file_or_dir> [repo_url]")
        sys.exit(1)

    target_path = Path(sys.argv[1])
    repo_url = sys.argv[2] if len(sys.argv) > 2 else "unknown"

    ensure_directories()

    if target_path.is_file():
        snippets = extract_snippets_from_file(target_path, repo_url)
    elif target_path.is_dir():
        snippets = extract_snippets_from_directory(target_path, repo_url)
    else:
        print(f"Error: {target_path} is not a valid file or directory")
        sys.exit(1)

    print(f"Found {len(snippets)} valid snippets (>= 50 tokens)")

    # Print summary
    if snippets:
        total_complexity = sum(s['complexity'] for s in snippets)
        avg_complexity = total_complexity / len(snippets)
        print(f"Average complexity: {avg_complexity:.2f}")
        print(f"Sample snippet IDs:")
        for s in snippets[:5]:
            print(f"  - {s['snippet_id']}")


if __name__ == "__main__":
    main()