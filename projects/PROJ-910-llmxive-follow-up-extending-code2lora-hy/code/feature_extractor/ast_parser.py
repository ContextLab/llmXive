import ast
import tokenize
import io
import collections
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from utils.logging import get_logger

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

    def visit_BoolOp(self, node):
        # Each 'and'/'or' adds to complexity
        self.complexity += len(node.values) - 1
        self.generic_visit(node)

    def visit_comprehension(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_IfExp(self, node):
        self.complexity += 1
        self.generic_visit(node)


def calculate_cyclomatic_complexity(tree: ast.AST) -> int:
    """Calculate the cyclomatic complexity of an AST."""
    visitor = CyclomaticComplexityVisitor()
    visitor.visit(tree)
    return visitor.complexity


class InheritanceDepthVisitor(ast.NodeVisitor):
    """Visitor to calculate maximum depth of inheritance."""
    def __init__(self):
        self.max_depth = 0
        self.current_depth = 0

    def visit_ClassDef(self, node):
        # Calculate inheritance depth for this class
        if node.bases:
            self.current_depth += 1
            self.max_depth = max(self.max_depth, self.current_depth)
            self.generic_visit(node)
            self.current_depth -= 1
        else:
            self.generic_visit(node)


def calculate_inheritance_depth(tree: ast.AST) -> int:
    """Calculate the maximum depth of inheritance in an AST."""
    visitor = InheritanceDepthVisitor()
    visitor.visit(tree)
    return visitor.max_depth


def extract_token_histogram(source_code: str) -> Dict[str, int]:
    """Extract a histogram of tokens from source code."""
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source_code).readline))
        token_counts = collections.Counter()
        for tok in tokens:
            if tok.type in (tokenize.NAME, tokenize.NUMBER, tokenize.STRING):
                token_counts[tok.string] += 1
        return dict(token_counts)
    except tokenize.TokenError:
        # Return empty histogram if tokenization fails
        return {}


def extract_ast_features(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Extract AST features from a single Python file.
    
    This function implements FR-007: Skip malformed files, log warnings, and continue.
    If a file cannot be parsed (syntax error), it logs a warning and returns None,
    allowing the caller to continue processing other files.
    
    Args:
        file_path: Path to the Python file to analyze
        
    Returns:
        Dictionary of features if successful, None if the file is malformed
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        tree = ast.parse(source_code, filename=str(file_path))
        
        features = {
            'cyclomatic_complexity': calculate_cyclomatic_complexity(tree),
            'max_inheritance_depth': calculate_inheritance_depth(tree),
            'token_histogram': extract_token_histogram(source_code),
            'file_path': str(file_path),
            'is_valid': True
        }
        
        return features
        
    except SyntaxError as e:
        # FR-007: Skip malformed files, log warning, continue
        logger.warning(f"Syntax error in {file_path}: {e.msg} at line {e.lineno}")
        # Log to the warning handler as well for consistency
        from utils.logging import warning_handler
        warning_handler(
            message=f"Syntax error in {file_path}",
            filename="ast_parser.py",
            error=f"Invalid syntax: {e.msg} at line {e.lineno}"
        )
        return None
    except Exception as e:
        # Log any other unexpected errors
        logger.error(f"Unexpected error processing {file_path}: {str(e)}")
        from utils.logging import warning_handler
        warning_handler(
            message=f"Error processing {file_path}",
            filename="ast_parser.py",
            error=str(e)
        )
        return None


def extract_features_from_directory(directory_path: Path) -> List[Dict[str, Any]]:
    """
    Extract AST features from all Python files in a directory.
    
    Implements FR-007: Skips malformed files, logs warnings, and continues
    processing remaining files instead of aborting the entire operation.
    
    Args:
        directory_path: Path to the directory containing Python files
        
    Returns:
        List of feature dictionaries for successfully parsed files
    """
    features_list = []
    processed = 0
    skipped = 0
    
    for py_file in directory_path.rglob('*.py'):
        if py_file.is_file():
            processed += 1
            features = extract_ast_features(py_file)
            
            if features is not None:
                features_list.append(features)
            else:
                skipped += 1
                # Continue processing next file (FR-007)
                continue
    
    logger.info(f"Processed {processed} files, skipped {skipped} malformed files")
    return features_list


def get_feature_vector_size() -> int:
    """
    Return the size of the feature vector produced by this extractor.
    
    This includes:
    - cyclomatic_complexity (1)
    - max_inheritance_depth (1)
    - token_histogram (variable, but we need a fixed size for ML)
    
    For the MLP projection, we'll use a fixed-size histogram (e.g., top 100 tokens)
    """
    # cyclomatic_complexity: 1
    # max_inheritance_depth: 1
    # token_histogram (top 100): 100
    return 102


def extract_ast_features_fixed(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Fixed version of extract_ast_features with robust error handling.
    
    This is an alias for extract_ast_features to maintain compatibility
    with any existing code that might reference this name.
    """
    return extract_ast_features(file_path)


def extract_features_from_directory_fixed(directory_path: Path) -> List[Dict[str, Any]]:
    """
    Fixed version of extract_features_from_directory with robust error handling.
    
    This is an alias for extract_features_from_directory to maintain compatibility.
    """
    return extract_features_from_directory(directory_path)