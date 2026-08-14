"""
AST-based feature extraction for code language models.

Implements FR-007: Skip malformed files, log warnings, and continue processing.
Uses the warning_handler from code/utils/logging.py (T006).
"""

import ast
import tokenize
import io
import collections
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from utils.logging import get_logger, warning_handler

# Initialize logger for this module
logger = get_logger(__name__)


class CyclomaticComplexityVisitor(ast.NodeVisitor):
    """Visitor to calculate cyclomatic complexity of an AST."""

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

    def visit_comprehension(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        # Each 'and'/'or' adds to complexity
        self.complexity += len(node.values) - 1
        self.generic_visit(node)


def calculate_cyclomatic_complexity(tree: ast.AST) -> int:
    """Calculate cyclomatic complexity for a given AST."""
    visitor = CyclomaticComplexityVisitor()
    visitor.visit(tree)
    return visitor.complexity


class InheritanceDepthVisitor(ast.NodeVisitor):
    """Visitor to calculate maximum depth of inheritance."""

    def __init__(self):
        self.max_depth = 0
        self.class_depths: Dict[str, int] = {}

    def visit_ClassDef(self, node):
        # Calculate depth for this class
        depth = 0
        for base in node.bases:
            if isinstance(base, ast.Name):
                # Simple name reference
                base_name = base.id
                if base_name in self.class_depths:
                    depth = max(depth, self.class_depths[base_name] + 1)
                else:
                    depth = max(depth, 1)  # Assume at least 1 level if base exists
            elif isinstance(base, ast.Attribute):
                # Qualified name (e.g., module.Class)
                depth = max(depth, 1)

        self.class_depths[node.name] = depth
        self.max_depth = max(self.max_depth, depth)
        self.generic_visit(node)


def calculate_inheritance_depth(tree: ast.AST) -> int:
    """Calculate maximum inheritance depth for a given AST."""
    visitor = InheritanceDepthVisitor()
    visitor.visit(tree)
    return visitor.max_depth


def extract_token_histogram(source_code: str, num_bins: int = 20) -> List[int]:
    """
    Extract a histogram of token lengths from the source code.

    Args:
        source_code: The Python source code as a string.
        num_bins: Number of bins for the histogram.

    Returns:
        A list of bin counts.
    """
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source_code).readline))
        token_lengths = [len(token.string) for token in tokens if token.type != tokenize.ENCODING]

        if not token_lengths:
            return [0] * num_bins

        min_len = min(token_lengths)
        max_len = max(token_lengths)

        if min_len == max_len:
            # All tokens same length
            histogram = [0] * num_bins
            histogram[0] = len(token_lengths)
            return histogram

        bin_width = (max_len - min_len + 1) / num_bins
        histogram = [0] * num_bins

        for length in token_lengths:
            bin_index = int((length - min_len) / bin_width)
            if bin_index >= num_bins:
                bin_index = num_bins - 1
            histogram[bin_index] += 1

        return histogram
    except tokenize.TokenError:
        # Return empty histogram if tokenization fails
        return [0] * num_bins


def extract_ast_features(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Extract AST features from a single Python file.

    Implements FR-007: Skips malformed files, logs warnings, and returns None.

    Args:
        file_path: Path to the Python file.

    Returns:
        Dictionary of features if successful, None if the file is malformed.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            source_code = f.read()

        # Parse the AST
        try:
            tree = ast.parse(source_code, filename=str(file_path))
        except SyntaxError as e:
            # FR-007: Log warning and skip malformed file
            warning_handler(
                logger,
                "syntax_error",
                f"Syntax error in {file_path}: {e.msg} at line {e.lineno}",
                exc_info=False
            )
            return None
        except Exception as e:
            # FR-007: Log warning for other parsing errors
            warning_handler(
                logger,
                "parse_error",
                f"Failed to parse {file_path}: {str(e)}",
                exc_info=True
            )
            return None

        # Extract features
        features = {
            'file_path': str(file_path),
            'cyclomatic_complexity': calculate_cyclomatic_complexity(tree),
            'inheritance_depth': calculate_inheritance_depth(tree),
            'token_histogram': extract_token_histogram(source_code)
        }

        return features

    except FileNotFoundError:
        warning_handler(
            logger,
            "file_not_found",
            f"File not found: {file_path}",
            exc_info=False
        )
        return None
    except PermissionError:
        warning_handler(
            logger,
            "permission_denied",
            f"Permission denied: {file_path}",
            exc_info=False
        )
        return None
    except Exception as e:
        # FR-007: Log unexpected errors and skip
        warning_handler(
            logger,
            "extraction_error",
            f"Unexpected error extracting features from {file_path}: {str(e)}",
            exc_info=True
        )
        return None


def extract_features_from_directory(
    directory_path: Path,
    recursive: bool = True
) -> Tuple[List[Dict[str, Any]], int, int]:
    """
    Extract AST features from all Python files in a directory.

    Implements FR-007: Skips malformed files, logs warnings, and continues processing.

    Args:
        directory_path: Path to the directory containing Python files.
        recursive: Whether to search recursively in subdirectories.

    Returns:
        Tuple of (list of successful feature dicts, count of processed files, count of skipped files).
    """
    if not directory_path.exists():
        warning_handler(
            logger,
            "directory_not_found",
            f"Directory not found: {directory_path}",
            exc_info=False
        )
        return [], 0, 0

    features_list = []
    processed_count = 0
    skipped_count = 0

    # Find all Python files
    pattern = '**/*.py' if recursive else '*.py'
    python_files = list(directory_path.glob(pattern))

    total_files = len(python_files)
    logger.info(f"Found {total_files} Python files in {directory_path}")

    for file_path in python_files:
        processed_count += 1

        # Extract features (returns None if malformed - FR-007)
        features = extract_ast_features(file_path)

        if features is not None:
            features_list.append(features)
        else:
            # File was skipped due to FR-007 logic
            skipped_count += 1

    logger.info(
        f"Processed {processed_count} files: "
        f"{len(features_list)} successful, {skipped_count} skipped"
    )

    return features_list, processed_count, skipped_count


def get_feature_vector_size() -> int:
    """
    Get the total size of the feature vector.

    Returns:
        Integer representing the total number of features.
    """
    # Cyclomatic complexity: 1
    # Inheritance depth: 1
    # Token histogram: 20 bins
    return 1 + 1 + 20


def extract_ast_features_fixed(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Fixed version of extract_ast_features with improved error handling.

    This is an alias for extract_ast_features to maintain backward compatibility
    while ensuring FR-007 compliance.
    """
    return extract_ast_features(file_path)


def extract_features_from_directory_fixed(
    directory_path: Path,
    recursive: bool = True
) -> Tuple[List[Dict[str, Any]], int, int]:
    """
    Fixed version of extract_features_from_directory with improved error handling.

    This is an alias for extract_features_from_directory to maintain backward
    compatibility while ensuring FR-007 compliance.
    """
    return extract_features_from_directory(directory_path, recursive)