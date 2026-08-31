"""
Halstead Complexity Metrics Calculator using javaparser-python.

This module parses Java source files using the javaparser-python library (v3.x)
to compute Halstead Volume. It counts operators and operands, calculates unique
counts, and derives the Halstead Volume metric.

Algorithm:
1. Parse Java AST using javaparser.
2. Traverse AST to count:
   - N1: Total number of operators
   - N2: Total number of operands
   - n1: Number of unique operators
   - n2: Number of unique operands
3. Calculate Halstead Volume: V = N * log2(n)
   where N = N1 + N2 and n = n1 + n2.

Error Handling:
- If parsing fails (syntax error), logs a warning and returns None.
- Does not halt the pipeline on individual file failures.
"""

import logging
import os
from pathlib import Path
from typing import Optional, Tuple, Set, Dict, Any

try:
    from javaparser import JavaParser
    from javaparser.ast import Node
    from javaparser.ast.visitor import Visitor
except ImportError:
    raise ImportError(
        "The 'javaparser-python' package is required. "
        "Please install it with: pip install javaparser-python"
    )

# Configure logging
logger = logging.getLogger(__name__)

# Define operators and operands based on Java grammar
# This is a simplified set; in a production system, one might traverse the AST
# to identify specific node types as operators or operands.
# For this implementation, we will traverse the AST and categorize nodes.

# Operators: Keywords that perform operations, symbols, and specific method calls
# In AST terms: BinaryExpr, UnaryExpr, AssignExpr, MethodCallExpr, etc.
OPERATOR_NODE_TYPES = {
    'BinaryExpr', 'UnaryExpr', 'AssignExpr', 'MethodCallExpr',
    'ConstructorCallExpr', 'LambdaExpr', 'SwitchExpr', 'ForStmt',
    'ForEachStmt', 'WhileStmt', 'DoStmt', 'IfStmt', 'TryStmt',
    'CatchClause', 'ThrowStmt', 'ReturnStmt', 'BreakStmt',
    'ContinueStmt', 'SynchronizedStmt', 'AssertStmt', 'ExpressionStmt'
}

# Operands: Variables, literals, types, and identifiers that hold values
# In AST terms: NameExpr, IntegerLiteralExpr, DoubleLiteralExpr, BooleanLiteralExpr,
# CharLiteralExpr, StringLiteralExpr, ClassOrInterfaceType, FieldAccessExpr
OPERAND_NODE_TYPES = {
    'NameExpr', 'IntegerLiteralExpr', 'DoubleLiteralExpr', 'BooleanLiteralExpr',
    'CharLiteralExpr', 'StringLiteralExpr', 'ClassOrInterfaceType',
    'FieldAccessExpr', 'ArrayCreationExpr', 'ArrayAccessExpr', 'CastExpr',
    'EnclosedExpr', 'VariableDeclarator', 'Parameter', 'ThisExpr',
    'SuperExpr', 'NullLiteralExpr', 'ArrayType'
}

class HalsteadVisitor(Visitor):
    """Visitor to count operators and operands in a Java AST."""

    def __init__(self):
        super().__init__()
        self.operators: Set[str] = set()
        self.operands: Set[str] = set()
        self.total_operators: int = 0
        self.total_operands: int = 0

    def visit(self, node: Node, arg: Any = None):
        """Visit a node and categorize it as operator or operand."""
        node_type = node.__class__.__name__

        if node_type in OPERATOR_NODE_TYPES:
            self.operators.add(node_type)
            self.total_operators += 1
        elif node_type in OPERAND_NODE_TYPES:
            self.operands.add(node_type)
            self.total_operands += 1

        # Continue visiting children
        super().visit(node, arg)

def calculate_halstead_volume(n1: int, n2: int, N1: int, N2: int) -> float:
    """
    Calculate Halstead Volume.

    Args:
        n1: Number of unique operators
        n2: Number of unique operands
        N1: Total number of operators
        N2: Total number of operands

    Returns:
        Halstead Volume (V)
    """
    if n1 == 0 and n2 == 0:
        return 0.0

    N = N1 + N2
    n = n1 + n2

    # V = N * log2(n)
    import math
    return N * math.log2(n)

def tokenize_java(file_path: Path) -> Optional[Tuple[int, int, int, int]]:
    """
    Parse a Java file and return Halstead counts.

    Args:
        file_path: Path to the Java file.

    Returns:
        Tuple of (N1, N2, n1, n2) or None if parsing fails.
    """
    try:
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return None

        if not file_path.suffix == '.java':
            logger.warning(f"Not a Java file: {file_path}")
            return None

        parser = JavaParser()
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        ast = parser.parse(content)

        visitor = HalsteadVisitor()
        visitor.visit(ast, None)

        return (
            visitor.total_operators,
            visitor.total_operands,
            len(visitor.operators),
            len(visitor.operands)
        )

    except Exception as e:
        logger.warning(f"Failed to parse {file_path}: {str(e)}")
        return None

def calculate_halstead_for_file(file_path: Path) -> Optional[float]:
    """
    Calculate Halstead Volume for a single Java file.

    Args:
        file_path: Path to the Java file.

    Returns:
        Halstead Volume or None if parsing fails.
    """
    counts = tokenize_java(file_path)
    if counts is None:
        return None

    N1, N2, n1, n2 = counts
    return calculate_halstead_volume(n1, n2, N1, N2)

def calculate_halstead_batch(file_paths: list) -> Dict[str, float]:
    """
    Calculate Halstead Volume for multiple Java files.

    Args:
        file_paths: List of paths to Java files.

    Returns:
        Dictionary mapping file paths to Halstead Volume.
    """
    results = {}
    for file_path in file_paths:
        vol = calculate_halstead_for_file(file_path)
        if vol is not None:
            results[str(file_path)] = vol
        else:
            logger.warning(f"Skipping file due to parsing error: {file_path}")

    return results

def main():
    """Main entry point for command-line execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Calculate Halstead Volume for Java files.'
    )
    parser.add_argument(
        'input',
        help='Path to a Java file or directory containing Java files.'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output file path for results (JSON). If not provided, prints to stdout.'
    )

    args = parser.parse_args()
    input_path = Path(args.input)

    if input_path.is_file():
        if input_path.suffix == '.java':
            result = calculate_halstead_for_file(input_path)
            if result is not None:
                output_data = {str(input_path): result}
            else:
                output_data = {}
        else:
            logger.error("Input is a file but not a Java file.")
            output_data = {}
    elif input_path.is_dir():
        java_files = list(input_path.rglob('*.java'))
        if not java_files:
            logger.warning("No Java files found in directory.")
            output_data = {}
        else:
            output_data = calculate_halstead_batch(java_files)
    else:
        logger.error(f"Input path does not exist: {input_path}")
        output_data = {}

    import json
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        logger.info(f"Results saved to {args.output}")
    else:
        print(json.dumps(output_data, indent=2))

if __name__ == '__main__':
    main()
