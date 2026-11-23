import ast
import tokenize
import io
import collections
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# Import the logging handler defined in T006
from utils.logging import warning_handler

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

    def visit_assert(self, node):
        self.complexity += 1
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
    """Visitor to calculate maximum depth of inheritance."""

    def __init__(self):
        self.max_depth = 0
        self.current_depth = 0

    def visit_ClassDef(self, node):
        # Simple heuristic: count bases as depth + 1
        if node.bases:
            depth = 1
            self.max_depth = max(self.max_depth, depth)
        self.generic_visit(node)

def calculate_inheritance_depth(tree: ast.AST) -> int:
    """Calculate maximum inheritance depth."""
    visitor = InheritanceDepthVisitor()
    visitor.visit(tree)
    return visitor.max_depth

def extract_token_histogram(source_code: str) -> Dict[str, int]:
    """Extract token frequency histogram from source code."""
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source_code).readline))
        histogram = collections.Counter()
        for tok in tokens:
            # Normalize token type to string name for histogram
            type_name = tokenize.tok_name[tok.type]
            histogram[type_name] += 1
        return dict(histogram)
    except tokenize.TokenError:
        return {}

def extract_ast_features(source_code: str) -> Dict[str, Any]:
    """
    Extract AST features from a single Python source file content.
    Returns a dictionary of metrics.
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        # This function is for a single file content.
        # If called from a context where we want to skip, the caller handles it.
        # However, to be robust, we can raise a specific error or return None.
        # Given the task T016 requirement, we assume the caller wraps this.
        raise SyntaxError(f"Syntax error in provided code: {e}")

    cc = calculate_cyclomatic_complexity(tree)
    inh_depth = calculate_inheritance_depth(tree)

    # Flatten token histogram for feature vector (top N tokens)
    token_hist = extract_token_histogram(source_code)
    # Keep top 10 most frequent token types for fixed vector size
    top_tokens = dict(collections.Counter(token_hist).most_common(10))

    return {
        "cyclomatic_complexity": cc,
        "inheritance_depth": inh_depth,
        "token_histogram": top_tokens,
        "num_nodes": len(ast.walk(tree)),
        "num_functions": len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])
    }

def extract_ast_features_fixed(source_code: str) -> Optional[Dict[str, Any]]:
    """
    Robust version of extract_ast_features that handles syntax errors gracefully
    by returning None instead of raising, allowing the caller to skip.
    """
    try:
        tree = ast.parse(source_code)
        cc = calculate_cyclomatic_complexity(tree)
        inh_depth = calculate_inheritance_depth(tree)
        token_hist = extract_token_histogram(source_code)
        top_tokens = dict(collections.Counter(token_hist).most_common(10))

        return {
            "cyclomatic_complexity": cc,
            "inheritance_depth": inh_depth,
            "token_histogram": top_tokens,
            "num_nodes": len(ast.walk(tree)),
            "num_functions": len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])
        }
    except SyntaxError:
        return None

def extract_features_from_directory(directory: Path) -> List[Dict[str, Any]]:
    """
    Extract features from all Python files in a directory.
    Skips malformed files and logs warnings.
    """
    features_list = []
    py_files = list(directory.rglob("*.py"))

    for file_path in py_files:
        try:
            source_code = file_path.read_text(encoding="utf-8")
            features = extract_ast_features_fixed(source_code)
            
            if features is None:
                # T016 Implementation: Skip malformed files
                # Call the log_warning handler defined in T006
                warning_handler(
                    filename=str(file_path),
                    error="SyntaxError: Malformed Python file skipped."
                )
                continue
            
            features["file_path"] = str(file_path)
            features_list.append(features)
        
        except Exception as e:
            # T016 Implementation: Handle other errors (IO, encoding, etc.)
            # Call the log_warning handler defined in T006
            warning_handler(
                filename=str(file_path),
                error=f"{type(e).__name__}: {str(e)}"
            )
            continue

    return features_list

def extract_features_from_directory_fixed(directory: Path) -> List[Dict[str, Any]]:
    """Alias for extract_features_from_directory with robust error handling."""
    return extract_features_from_directory(directory)

def get_feature_vector_size() -> int:
    """
    Returns the size of the feature vector used for the MLP input.
    This is calculated based on the features extracted:
    - cyclomatic_complexity (1)
    - inheritance_depth (1)
    - num_nodes (1)
    - num_functions (1)
    - token_histogram (top 10)
    Total: 1 + 1 + 1 + 1 + 10 = 14
    """
    return 14  # 4 scalar metrics + 10 token types