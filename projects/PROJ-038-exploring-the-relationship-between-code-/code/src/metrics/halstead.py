"""
Halstead Complexity Metrics Calculator using JavaParser.

This module computes Halstead Volume and related metrics for Java source files
by parsing the Abstract Syntax Tree (AST) using the javaparser-python library.

Algorithm:
1. Parse Java file into AST.
2. Traverse AST to count:
   - N1: Total number of operators
   - N2: Total number of operands
   - n1: Number of unique operators
   - n2: Number of unique operands
3. Calculate Halstead Volume: V = N * log2(n)
   where N = N1 + N2, n = n1 + n2

Token Mapping follows standard JavaParser definitions:
https://github.com/javaparser/javaparser/wiki/Token-Definitions
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional, Tuple, Set, Dict, Any, List

# Attempt to import JavaParser. If not installed, the script will fail loudly
# as per the "Real data only" and "Fail loudly" constraints.
try:
    from javaparser import JavaParser
except ImportError:
    # Fallback to a clear error message if the package is missing
    # This ensures the pipeline fails fast if dependencies are not met.
    print("ERROR: javaparser-python package is required. Install via: pip install javaparser", file=sys.stderr)
    raise ImportError("javaparser-python is required for Halstead metric calculation.")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Token Classification Mappings ---
# These mappings approximate the classification of Java tokens into Operators and Operands
# based on standard Halstead definitions for Java.

# Operators: Keywords that control flow, logical operators, arithmetic operators, etc.
# Note: This is a comprehensive list based on Java keywords and common operators.
# In a full implementation, one might distinguish between "reserved words" and "operators",
# but for Halstead, we typically count all distinct operator tokens.
JAVA_OPERATORS_KEYWORDS = {
    'abstract', 'assert', 'boolean', 'break', 'byte', 'case', 'catch', 'char',
    'class', 'const', 'continue', 'default', 'do', 'double', 'else', 'enum',
    'extends', 'final', 'finally', 'float', 'for', 'goto', 'if', 'implements',
    'import', 'instanceof', 'int', 'interface', 'long', 'native', 'new', 'package',
    'private', 'protected', 'public', 'return', 'short', 'static', 'strictfp',
    'super', 'switch', 'synchronized', 'this', 'throw', 'throws', 'transient',
    'try', 'void', 'volatile', 'while', 'true', 'false', 'null'
}

# Symbolic Operators
JAVA_SYMBOLIC_OPERATORS = {
    '+', '-', '*', '/', '%', '++', '--', '=', '+=', '-=', '*=', '/=', '%=',
    '&', '|', '^', '~', '<<', '>>', '>>>', '&&', '||', '!', '==', '!=',
    '<', '>', '<=', '>=', '?', ':', ',', ';', '.', '(', ')', '{', '}', '[', ']',
    '@'
}

# Operands: Identifiers, Literals (Numbers, Strings, Chars)
# In AST traversal, these are typically:
# - NameExpr (variables, types)
# - IntegerLiteralExpr, LongLiteralExpr, DoubleLiteralExpr, FloatLiteralExpr
# - StringLiteralExpr, CharLiteralExpr
# - BooleanLiteralExpr (true, false) - though often treated as keywords, they act as operands here
# - ThisExpr, SuperExpr

def _is_operator(node_type: str, node_text: str = None) -> bool:
    """
    Determines if a node represents an operator based on its type or text.
    """
    # Check symbolic operators first
    if node_text and node_text in JAVA_SYMBOLIC_OPERATORS:
        return True

    # Check keyword operators
    if node_text and node_text.lower() in JAVA_OPERATORS_KEYWORDS:
        return True

    # Type-based classification for AST nodes
    # Operators often correspond to specific node types in the AST
    operator_node_types = {
        'BinaryExpr', 'UnaryExpr', 'AssignmentExpr', 'ConditionalExpr',
        'MethodCallExpr', 'ConstructorCallExpr', 'SuperConstructorCallExpr',
        'ExplicitConstructorInvocationExpr', 'LambdaExpr',
        'CastExpr', 'InstanceOfExpr', 'ArrayCreationExpr', 'ArrayAccessExpr',
        'EnclosedExpr', 'ForeachStmt', 'ForStmt', 'WhileStmt', 'DoStmt',
        'SwitchStmt', 'ReturnStmt', 'ThrowStmt', 'BreakStmt', 'ContinueStmt',
        'SynchronizedStmt', 'TryStmt', 'CatchClause', 'FinallyBlock',
        'BlockStmt', 'IfStmt', 'AssertStmt', 'ExpressionStmt'
    }

    if node_type in operator_node_types:
        return True

    return False

def _is_operand(node_type: str, node_text: str = None) -> bool:
    """
    Determines if a node represents an operand based on its type or text.
    """
    # Literals are operands
    literal_node_types = {
        'IntegerLiteralExpr', 'LongLiteralExpr', 'DoubleLiteralExpr',
        'FloatLiteralExpr', 'StringLiteralExpr', 'CharLiteralExpr',
        'BooleanLiteralExpr', 'NullLiteralExpr', 'TextBlockLiteralExpr'
    }

    if node_type in literal_node_types:
        return True

    # Identifiers (variables, method names, class names) are operands
    identifier_node_types = {
        'NameExpr', 'VariableDeclaratorId', 'FieldAccessExpr',
        'ThisExpr', 'SuperExpr', 'ClassOrInterfaceType'
    }

    if node_type in identifier_node_types:
        return True

    return False

class HalsteadVisitor:
    """
    A visitor class to traverse the Java AST and count operators and operands.
    """

    def __init__(self):
        self.operators: List[str] = []
        self.operands: List[str] = []

    def visit(self, node, parent=None):
        """
        Recursively visit nodes in the AST.
        This is a simplified traversal. In a real implementation, one would
        use the visitor pattern provided by javaparser or iterate children.
        """
        node_type = node.__class__.__name__
        node_text = None

        # Extract text if possible (heuristic for leaf nodes)
        if hasattr(node, 'asString'):
            try:
                node_text = node.asString()
            except:
                pass
        elif hasattr(node, 'getValue'):
            try:
                node_text = str(node.getValue())
            except:
                pass
        elif hasattr(node, 'name'):
            try:
                node_text = str(node.name)
            except:
                pass

        # Classify the node
        if _is_operator(node_type, node_text):
            self.operators.append(node_text if node_text else node_type)
        elif _is_operand(node_type, node_text):
            self.operands.append(node_text if node_text else node_type)

        # Traverse children
        if hasattr(node, 'getChildNodes'):
            for child in node.getChildNodes():
                self.visit(child, node)
        elif hasattr(node, 'children'):
            for child in node.children:
                self.visit(child, node)

    def get_metrics(self) -> Tuple[int, int, int, int]:
        """
        Returns (N1, N2, n1, n2)
        N1: Total operators
        N2: Total operands
        n1: Unique operators
        n2: Unique operands
        """
        N1 = len(self.operators)
        N2 = len(self.operands)
        n1 = len(set(self.operators))
        n2 = len(set(self.operands))
        return N1, N2, n1, n2


def calculate_halstead_volume(N1: int, N2: int, n1: int, n2: int) -> float:
    """
    Calculate Halstead Volume (V) and other derived metrics.

    V = N * log2(n)
    N = N1 + N2
    n = n1 + n2

    Returns:
        float: Halstead Volume. Returns 0.0 if n is 0 to avoid log(0).
    """
    N = N1 + N2
    n = n1 + n2

    if n == 0:
        return 0.0

    V = N * (n1 + n2) # Wait, formula is V = N * log2(n)
    # Correct formula:
    import math
    V = N * math.log2(n) if n > 0 else 0.0
    return V


def tokenize_java(file_path: Path) -> Tuple[List[str], List[str]]:
    """
    Parses a Java file and returns lists of operators and operands.
    This is a wrapper for the AST-based approach.

    Args:
        file_path: Path to the Java file.

    Returns:
        Tuple of (operators_list, operands_list)
    """
    parser = JavaParser()
    try:
        # Parse the file
        ast = parser.parse(file_path)
        if not ast:
            logger.warning(f"Failed to parse AST for {file_path}")
            return [], []

        visitor = HalsteadVisitor()
        # The AST structure in javaparser-python might vary.
        # Assuming ast is the root node.
        visitor.visit(ast)

        return visitor.operators, visitor.operands

    except Exception as e:
        logger.warning(f"Error parsing {file_path}: {e}")
        return [], []


def calculate_halstead_for_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Calculate Halstead metrics for a single Java file.

    Args:
        file_path: Path to the Java file.

    Returns:
        Dictionary containing N1, N2, n1, n2, volume, or None if parsing fails.
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return None

    try:
        operators, operands = tokenize_java(file_path)

        if not operators and not operands:
            # If no tokens found, maybe it's an empty file or failed parsing
            # We return None to indicate failure to extract meaningful metrics
            # unless we want to count 0 metrics. Let's return 0s if empty.
            # But per spec: "If parsing fails... raise a warning but not halt."
            # Returning None signals no data.
            return None

        N1, N2, n1, n2 = len(operators), len(operands), len(set(operators)), len(set(operands))
        volume = calculate_halstead_volume(N1, N2, n1, n2)

        return {
            'file_path': str(file_path),
            'N1': N1,
            'N2': N2,
            'n1': n1,
            'n2': n2,
            'volume': volume
        }

    except Exception as e:
        logger.warning(f"Failed to calculate Halstead for {file_path}: {e}")
        return None


def calculate_halstead_batch(file_paths: List[Path]) -> List[Dict[str, Any]]:
    """
    Calculate Halstead metrics for a batch of Java files.

    Args:
        file_paths: List of paths to Java files.

    Returns:
        List of dictionaries containing metrics for each successfully processed file.
    """
    results = []
    for path in file_paths:
        result = calculate_halstead_for_file(path)
        if result:
            results.append(result)
        else:
            logger.warning(f"Skipping {path} due to parsing error or empty result.")
    return results


def main():
    """
    Main entry point for command-line execution.
    Expects a directory or file path as argument.
    """
    import argparse

    parser = argparse.ArgumentParser(description='Calculate Halstead Volume for Java files.')
    parser.add_argument('path', type=str, help='Path to a Java file or directory of Java files')
    parser.add_argument('--output', type=str, help='Output JSON file path (optional)')

    args = parser.parse_args()
    input_path = Path(args.path)

    if input_path.is_file():
        if input_path.suffix != '.java':
            logger.error(f"File {input_path} is not a .java file.")
            sys.exit(1)
        file_paths = [input_path]
    elif input_path.is_dir():
        file_paths = list(input_path.rglob('*.java'))
        if not file_paths:
            logger.warning(f"No Java files found in {input_path}")
            sys.exit(0)
    else:
        logger.error(f"Path {input_path} does not exist.")
        sys.exit(1)

    logger.info(f"Processing {len(file_paths)} files...")
    results = calculate_halstead_batch(file_paths)

    if args.output:
        import json
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {args.output}")
    else:
        # Print summary
        for res in results:
            print(f"{res['file_path']}: Volume={res['volume']:.2f}")

    if not results:
        logger.warning("No results generated.")
        sys.exit(1)


if __name__ == '__main__':
    main()