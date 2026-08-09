"""
AST-based feature extraction for code repositories.

Implements FR-007: Skip malformed files, log warnings, and continue processing.
"""
import ast
import tokenize
import io
import collections
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging

# Import the warning handler from T006 (utils.logging)
from utils.logging import get_logger

# Initialize logger for this module
logger = get_logger(__name__)


class CyclomaticComplexityVisitor(ast.NodeVisitor):
    """Visitor to calculate cyclomatic complexity of a function."""

    def __init__(self):
        self.complexity = 1  # Base complexity

    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_With(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        # Each 'and'/'or' adds to complexity
        self.complexity += len(node.values) - 1
        self.generic_visit(node)

    def visit_comprehension(self, node):
        self.complexity += 1
        self.generic_visit(node)


def calculate_cyclomatic_complexity(tree: ast.AST) -> int:
    """Calculate cyclomatic complexity of an AST."""
    visitor = CyclomaticComplexityVisitor()
    visitor.visit(tree)
    return visitor.complexity


class InheritanceDepthVisitor(ast.NodeVisitor):
    """Visitor to calculate maximum inheritance depth."""

    def __init__(self):
        self.max_depth = 0
        self.class_depths = {}

    def visit_ClassDef(self, node):
        # Calculate depth based on bases
        if node.bases:
            max_base_depth = 0
            for base in node.bases:
                if isinstance(base, ast.Name):
                    base_name = base.id
                    # If we've seen this base class before, use its depth
                    if base_name in self.class_depths:
                        max_base_depth = max(max_base_depth, self.class_depths[base_name])
                    # Otherwise, assume depth 1 (direct inheritance from object)
                elif isinstance(base, ast.Attribute):
                    # Handle module.ClassName
                    base_name = base.attr
                    if base_name in self.class_depths:
                        max_base_depth = max(max_base_depth, self.class_depths[base_name])
                elif isinstance(base, ast.Call):
                    # Handle Class() calls (less common in inheritance)
                    if isinstance(base.func, ast.Name):
                        base_name = base.func.id
                        if base_name in self.class_depths:
                            max_base_depth = max(max_base_depth, self.class_depths[base_name])

            depth = max_base_depth + 1
        else:
            depth = 1  # Direct inheritance from object

        self.class_depths[node.name] = depth
        self.max_depth = max(self.max_depth, depth)
        self.generic_visit(node)


def calculate_inheritance_depth(tree: ast.AST) -> int:
    """Calculate maximum inheritance depth of an AST."""
    visitor = InheritanceDepthVisitor()
    visitor.visit(tree)
    return visitor.max_depth


def extract_token_histogram(source_code: str) -> Dict[str, int]:
    """Extract token histogram from source code."""
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source_code).readline))
        token_counts = collections.Counter()
        for tok in tokens:
            if tok.type != tokenize.ENCODING:  # Skip encoding token
                token_counts[tokenize.tok_name[tok.type]] += 1
        return dict(token_counts)
    except (tokenize.TokenError, IndentationError) as e:
        # This should be caught before calling this function, but handle gracefully
        logger.warning(f"Tokenization error: {e}")
        return {}


def extract_ast_features(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Extract AST features from a single Python file.

    Implements FR-007: If the file is malformed, log a warning and return None
    to skip processing this file without stopping the entire pipeline.

    Args:
        file_path: Path to the Python file

    Returns:
        Dictionary of features if successful, None if the file is malformed
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()

        # Try to parse the AST
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            # FR-007: Log warning and skip malformed file
            logger.warning(f"Syntax error in {file_path}: {e}. Skipping file.")
            return None
        except Exception as e:
            # FR-007: Log unexpected errors and skip
            logger.warning(f"Unexpected error parsing {file_path}: {e}. Skipping file.")
            return None

        # Extract features
        features = {
            'file_path': str(file_path),
            'cyclomatic_complexity': calculate_cyclomatic_complexity(tree),
            'inheritance_depth': calculate_inheritance_depth(tree),
            'token_histogram': extract_token_histogram(source_code),
            'num_functions': sum(1 for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))),
            'num_classes': sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef)),
            'num_lines': len(source_code.splitlines()),
        }

        return features

    except FileNotFoundError:
        logger.warning(f"File not found: {file_path}. Skipping.")
        return None
    except PermissionError:
        logger.warning(f"Permission denied: {file_path}. Skipping.")
        return None
    except Exception as e:
        # FR-007: Log unexpected errors and skip
        logger.warning(f"Unexpected error processing {file_path}: {e}. Skipping file.")
        return None


def extract_features_from_directory(repo_path: Path) -> List[Dict[str, Any]]:
    """
    Extract AST features from all Python files in a directory.

    Implements FR-007: Skip malformed files, log warnings, and continue processing.

    Args:
        repo_path: Path to the repository directory

    Returns:
        List of feature dictionaries for successfully parsed files
    """
    if not repo_path.exists():
        logger.error(f"Repository path does not exist: {repo_path}")
        return []

    if not repo_path.is_dir():
        logger.error(f"Path is not a directory: {repo_path}")
        return []

    all_features = []
    python_files = list(repo_path.rglob("*.py"))

    logger.info(f"Found {len(python_files)} Python files in {repo_path}")

    processed = 0
    skipped = 0

    for file_path in python_files:
        features = extract_ast_features(file_path)
        if features is not None:
            all_features.append(features)
            processed += 1
        else:
            # File was skipped due to FR-007 logic
            skipped += 1

    logger.info(f"Processed {processed} files, skipped {skipped} malformed files")

    return all_features


def get_feature_vector_size() -> int:
    """
    Calculate the size of the feature vector for the MLP projection.

    This includes:
    - cyclomatic_complexity (1)
    - inheritance_depth (1)
    - num_functions (1)
    - num_classes (1)
    - num_lines (1)
    - token_histogram (variable, but we'll fix it to a reasonable size)

    Returns:
        Total feature vector size
    """
    # Fixed token types we'll track
    token_types = [
        'NAME', 'NUMBER', 'STRING', 'OP', 'NEWLINE', 'NL',
        'INDENT', 'DEDENT', 'ENDMARKER', 'COMMENT', 'ERRORTOKEN'
    ]
    return 5 + len(token_types)  # 5 scalar features + token histogram


def extract_token_histogram_fixed(source_code: str, fixed_size: int = 11) -> List[float]:
    """
    Extract a fixed-size token histogram for consistent feature vector size.

    Args:
        source_code: Source code string
        fixed_size: Fixed size of the output vector

    Returns:
        List of token counts (fixed size)
    """
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source_code).readline))
        token_counts = collections.Counter()
        for tok in tokens:
            if tok.type != tokenize.ENCODING:
                token_counts[tokenize.tok_name[tok.type]] += 1

        # Map to fixed-size vector
        token_types = [
            'NAME', 'NUMBER', 'STRING', 'OP', 'NEWLINE', 'NL',
            'INDENT', 'DEDENT', 'ENDMARKER', 'COMMENT', 'ERRORTOKEN'
        ][:fixed_size]

        return [float(token_counts.get(tt, 0)) for tt in token_types]
    except Exception:
        return [0.0] * fixed_size


def extract_ast_features_fixed(file_path: Path) -> Optional[List[float]]:
    """
    Extract a fixed-size feature vector from a Python file.

    Implements FR-007: Skip malformed files, log warnings, and continue.

    Args:
        file_path: Path to the Python file

    Returns:
        List of features (fixed size) if successful, None if malformed
    """
    features_dict = extract_ast_features(file_path)
    if features_dict is None:
        return None

    # Extract scalar features
    scalar_features = [
        float(features_dict['cyclomatic_complexity']),
        float(features_dict['inheritance_depth']),
        float(features_dict['num_functions']),
        float(features_dict['num_classes']),
        float(features_dict['num_lines']),
    ]

    # Extract token histogram
    token_histogram = extract_token_histogram_fixed(features_dict['file_path'].__class__.__module__ or "", fixed_size=11)
    # Re-extract properly
    with open(file_path, 'r', encoding='utf-8') as f:
        source_code = f.read()
    token_histogram = extract_token_histogram_fixed(source_code, fixed_size=11)

    return scalar_features + token_histogram


def extract_features_from_directory_fixed(repo_path: Path) -> Tuple[List[List[float]], int]:
    """
    Extract fixed-size feature vectors from all Python files in a directory.

    Implements FR-007: Skip malformed files, log warnings, and continue.

    Args:
        repo_path: Path to the repository directory

    Returns:
        Tuple of (list of feature vectors, feature vector size)
    """
    features_list = []
    python_files = list(repo_path.rglob("*.py"))

    logger.info(f"Found {len(python_files)} Python files in {repo_path}")

    processed = 0
    skipped = 0

    for file_path in python_files:
        features = extract_ast_features_fixed(file_path)
        if features is not None:
            features_list.append(features)
            processed += 1
        else:
            skipped += 1

    logger.info(f"Processed {processed} files, skipped {skipped} malformed files")

    feature_vector_size = get_feature_vector_size()
    return features_list, feature_vector_size