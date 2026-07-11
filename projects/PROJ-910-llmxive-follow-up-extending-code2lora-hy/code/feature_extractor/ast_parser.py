import ast
import tokenize
import io
import collections
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from utils.logging import get_logger, warning_handler

logger = get_logger(__name__)

# --- Cyclomatic Complexity ---
class CyclomaticComplexityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.complexity = 1

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
        self.complexity += len(node.values) - 1
        self.generic_visit(node)

    def visit_comprehension(self, node):
        self.complexity += 1
        self.generic_visit(node)

def calculate_cyclomatic_complexity(tree: ast.AST) -> int:
    visitor = CyclomaticComplexityVisitor()
    visitor.visit(tree)
    return visitor.complexity

# --- Inheritance Depth ---
class InheritanceDepthVisitor(ast.NodeVisitor):
    def __init__(self):
        self.max_depth = 0
        self.class_depths: Dict[str, int] = {}

    def visit_ClassDef(self, node):
        depth = 0
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_name = base.id
                if base_name in self.class_depths:
                    depth = max(depth, self.class_depths[base_name] + 1)
            elif isinstance(base, ast.Subscript):
                depth = max(depth, 1)
            elif isinstance(base, ast.Attribute):
                depth = max(depth, 1)
        
        self.class_depths[node.name] = depth
        self.max_depth = max(self.max_depth, depth)
        self.generic_visit(node)

def calculate_inheritance_depth(tree: ast.AST) -> int:
    visitor = InheritanceDepthVisitor()
    visitor.visit(tree)
    return visitor.max_depth

# --- Token Histogram ---
def extract_token_histogram(source_code: str) -> Dict[str, int]:
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source_code).readline))
        histogram = collections.Counter()
        for tok in tokens:
            if tok.type not in (tokenize.INDENT, tokenize.DEDENT, tokenize.NEWLINE, tokenize.NL, tokenize.COMMENT):
                histogram[tok.type] += 1
        return dict(histogram)
    except tokenize.TokenError as e:
        logger.warning(f"Tokenization error: {e}")
        return {}

# --- Main Extraction Logic with FR-007 Skip Logic ---
def extract_ast_features(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Extracts AST features from a single Python file.
    Implements FR-007: Skips malformed files, logs warnings, and continues.
    Returns None if the file cannot be parsed.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
    except (IOError, UnicodeDecodeError) as e:
        logger.warning(f"Skipping file {file_path}: Could not read content ({e})")
        return None

    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        # FR-007: Log warning and skip malformed files
        warning_handler(str(e))
        logger.warning(f"Skipping file {file_path}: SyntaxError - {e}")
        return None
    except Exception as e:
        # Catch any other unexpected parsing errors
        logger.warning(f"Skipping file {file_path}: Unexpected error during parsing - {e}")
        return None

    cc = calculate_cyclomatic_complexity(tree)
    inheritance_depth = calculate_inheritance_depth(tree)
    token_hist = extract_token_histogram(source_code)

    return {
        "cyclomatic_complexity": cc,
        "inheritance_depth": inheritance_depth,
        "token_histogram": token_hist,
        "file_path": str(file_path)
    }

def extract_features_from_directory(repo_path: Path) -> List[Dict[str, Any]]:
    """
    Recursively extracts features from all .py files in a directory.
    Implements FR-007: Continues processing even if individual files fail.
    """
    features = []
    py_files = list(repo_path.rglob("*.py"))
    
    logger.info(f"Found {len(py_files)} Python files in {repo_path}")

    for file_path in py_files:
        try:
            feature_data = extract_ast_features(file_path)
            if feature_data is not None:
                features.append(feature_data)
        except Exception as e:
            # Extra safety net for unexpected crashes during iteration
            logger.error(f"Unexpected error processing {file_path}: {e}")
            continue

    logger.info(f"Successfully extracted features from {len(features)} files.")
    return features

def get_feature_vector_size() -> int:
    """
    Returns the expected size of the feature vector.
    This is used by the MLP to determine input_dim.
    It includes CC (1) + Inheritance (1) + Token Histogram Size.
    """
    # Common token types: NAME, NUMBER, STRING, OP, ENCODING, etc.
    # We'll define a standard set of types to count, or use a fixed size.
    # For this implementation, we assume a fixed histogram size of 64 to cover common tokens.
    HISTOGRAM_SIZE = 64 
    return 2 + HISTOGRAM_SIZE # CC + Depth + Histogram

def extract_token_histogram_fixed(source_code: str) -> List[int]:
    """
    Returns a fixed-size list for the token histogram to ensure consistent vector dimensions.
    """
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source_code).readline))
        # Map token types to indices 0..63
        histogram = [0] * 64
        for tok in tokens:
            t_type = tok.type
            if 0 <= t_type < 64:
                histogram[t_type] += 1
        return histogram
    except tokenize.TokenError:
        return [0] * 64

def extract_ast_features_fixed(file_path: Path) -> Optional[Tuple[List[float], str]]:
    """
    Extracts a fixed-size feature vector and the file path.
    Used for batching in the MLP.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
    except (IOError, UnicodeDecodeError) as e:
        logger.warning(f"Skipping file {file_path}: Could not read content ({e})")
        return None

    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        warning_handler(str(e))
        logger.warning(f"Skipping file {file_path}: SyntaxError - {e}")
        return None
    except Exception as e:
        logger.warning(f"Skipping file {file_path}: Unexpected error during parsing - {e}")
        return None

    cc = calculate_cyclomatic_complexity(tree)
    inheritance_depth = calculate_inheritance_depth(tree)
    token_hist = extract_token_histogram_fixed(source_code)

    # Construct vector: [CC, Depth, hist...]
    feature_vector = [float(cc), float(inheritance_depth)] + [float(x) for x in token_hist]

    return feature_vector, str(file_path)

def extract_features_from_directory_fixed(repo_path: Path) -> Tuple[List[List[float]], List[str]]:
    """
    Extracts fixed-size feature vectors for all valid files.
    Returns (vectors, paths).
    """
    vectors = []
    paths = []
    
    py_files = list(repo_path.rglob("*.py"))
    logger.info(f"Found {len(py_files)} Python files in {repo_path}")

    for file_path in py_files:
        try:
            result = extract_ast_features_fixed(file_path)
            if result is not None:
                vec, path = result
                vectors.append(vec)
                paths.append(path)
        except Exception as e:
            logger.error(f"Unexpected error processing {file_path}: {e}")
            continue

    logger.info(f"Successfully extracted features from {len(vectors)} files.")
    return vectors, paths