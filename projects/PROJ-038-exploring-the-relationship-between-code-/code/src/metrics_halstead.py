"""
Halstead Volume Metric Calculation for Java Files.

This module implements the calculation of Halstead complexity metrics,
specifically the Halstead Volume, for Java source code files.
It uses a custom tokenizer to extract operators and operands,
adhering to the definitions in Halstead's original work.
"""
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Set

# Regular expressions for tokenizing Java
# Operators: symbols and keywords that perform operations
# Operands: identifiers, literals (numbers, strings, characters)

# Define Java operators (simplified set covering common ones)
JAVA_OPERATORS = {
    '++', '--', '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '<<=', '>>=', '>>>=',
    '==', '!=', '<=', '>=', '&&', '||', '<<', '>>', '>>>',
    '+', '-', '*', '/', '%', '=', '<', '>', '!', '&', '|', '^', '~', '?', ':',
    ',', ';', '(', ')', '{', '}', '[', ']', '.', '->'
}

# Java keywords that are treated as operands in some interpretations,
# but strictly speaking, Halstead distinguishes operators and operands.
# Here we treat keywords as operands for the purpose of counting distinct operands,
# or we can exclude them. Standard practice often excludes keywords from operands
# or treats them as operators. We will follow a common approach:
# Operators: symbols + specific keywords (if, else, while, for, etc. can be operators)
# Operands: identifiers, literals.
# To be precise, let's use a standard set where keywords are operands if they are not operators.
# However, a simpler and robust way for this metric is:
# Operators: The set of symbols + reserved words that control flow or logic.
# Operands: Variables, constants, literals.

# Let's define a set of keywords that act as operators (control flow, logical)
JAVA_KEYWORD_OPERATORS = {
    'if', 'else', 'while', 'for', 'do', 'switch', 'case', 'break', 'continue',
    'return', 'throw', 'try', 'catch', 'finally', 'new', 'instanceof', 'extends',
    'implements', 'import', 'package', 'public', 'private', 'protected', 'static',
    'final', 'abstract', 'class', 'interface', 'enum', 'void', 'int', 'long',
    'double', 'float', 'char', 'boolean', 'byte', 'short', 'true', 'false', 'null'
}

# Regex patterns
TOKEN_PATTERN = re.compile(
    r'(?P<STRING>"(?:[^"\\]|\\.)*")|'  # Strings
    r'(?P<CHAR>\'(?:[^\'\\]|\\.)*\')|'  # Chars
    r'(?P<NUMBER>\d+(\.\d+)?([eE][+-]?\d+)?[fFlLdD]?)|'  # Numbers
    r'(?P<IDENTIFIER>[a-zA-Z_][a-zA-Z0-9_]*)|'  # Identifiers
    r'(?P<OPERATOR>[+\-*/%=<>!&|^~?:]+|\+\+|--|<<|>>|&&|\|\||==|!=|<=|>=|->)'  # Operators
)

def tokenize_java(source_code: str) -> Tuple[List[str], List[str]]:
    """
    Tokenize Java source code into operators and operands.
    
    Args:
        source_code: The Java source code as a string.
        
    Returns:
        A tuple (operators, operands) where each is a list of tokens.
    """
    operators = []
    operands = []
    
    for match in TOKEN_PATTERN.finditer(source_code):
        token = match.group()
        token_type = match.lastgroup
        
        if token_type == 'STRING' or token_type == 'CHAR':
            operands.append(token)
        elif token_type == 'NUMBER':
            operands.append(token)
        elif token_type == 'IDENTIFIER':
            if token in JAVA_KEYWORD_OPERATORS:
                operators.append(token)
            else:
                operands.append(token)
        elif token_type == 'OPERATOR':
            # Handle multi-character operators that might be matched as single chars
            # The regex already prioritizes longer matches, so this should be fine.
            # However, we need to ensure we don't split things like `>>` into `>` `>`
            # The regex pattern handles `>>` as a single operator.
            operators.append(token)
            
    return operators, operands

def calculate_halstead_volume(operators: List[str], operands: List[str]) -> float:
    """
    Calculate Halstead Volume given lists of operators and operands.
    
    Halstead Metrics:
    n1 = number of distinct operators
    n2 = number of distinct operands
    N1 = total number of operators
    N2 = total number of operands
    
    Volume V = N * log2(n)
    where N = N1 + N2
    and n = n1 + n2
    
    Args:
        operators: List of operator tokens.
        operands: List of operand tokens.
        
    Returns:
        The Halstead Volume as a float.
    """
    if not operators and not operands:
        return 0.0
        
    n1 = len(set(operators))
    n2 = len(set(operands))
    N1 = len(operators)
    N2 = len(operands)
    
    n = n1 + n2
    N = N1 + N2
    
    if n == 0:
        return 0.0
        
    volume = N * (n1 + n2) if n == 0 else N * (n1 + n2) # Correction: V = N * log2(n)
    # Re-calculation:
    # V = N * log2(n)
    import math
    if n == 0:
        return 0.0
    volume = N * math.log2(n)
    
    return volume

def calculate_halstead_for_file(file_path: str) -> Dict[str, Any]:
    """
    Calculate Halstead metrics for a single Java file.
    
    Args:
        file_path: Path to the Java file.
        
    Returns:
        A dictionary containing:
        - 'file_path': The path to the file.
        - 'halstead_volume': The calculated volume.
        - 'n1': Distinct operators.
        - 'n2': Distinct operands.
        - 'N1': Total operators.
        - 'N2': Total operands.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        source_code = f.read()
        
    operators, operands = tokenize_java(source_code)
    volume = calculate_halstead_volume(operators, operands)
    
    return {
        'file_path': file_path,
        'halstead_volume': volume,
        'n1': len(set(operators)),
        'n2': len(set(operands)),
        'N1': len(operators),
        'N2': len(operands)
    }

def calculate_halstead_batch(file_paths: List[str]) -> List[Dict[str, Any]]:
    """
    Calculate Halstead metrics for a batch of Java files.
    
    Args:
        file_paths: List of paths to Java files.
        
    Returns:
        A list of dictionaries, one per file, containing the metrics.
    """
    results = []
    for file_path in file_paths:
        try:
            result = calculate_halstead_for_file(file_path)
            results.append(result)
        except Exception as e:
            # Log error but continue processing other files
            # In a real pipeline, this might be handled by a logger
            print(f"Error processing {file_path}: {e}")
            results.append({
                'file_path': file_path,
                'halstead_volume': None,
                'error': str(e)
            })
    return results

def main():
    """
    Main entry point for running Halstead calculation on a directory.
    This function is intended to be called by a wrapper script or directly.
    It expects a directory path as a command-line argument or environment variable.
    """
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python -m src.metrics_halstead <directory_path>")
        sys.exit(1)
        
    target_dir = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    java_files = []
    for root, _, files in os.walk(target_dir):
        for file in files:
            if file.endswith('.java'):
                java_files.append(os.path.join(root, file))
                
    if not java_files:
        print(f"No Java files found in {target_dir}")
        sys.exit(0)
        
    print(f"Found {len(java_files)} Java files.")
    results = calculate_halstead_batch(java_files)
    
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results written to {output_file}")
    else:
        # Print summary
        total_volume = sum(r['halstead_volume'] for r in results if r['halstead_volume'] is not None)
        print(f"Total Halstead Volume: {total_volume:.2f}")
        print(f"Average Halstead Volume: {total_volume / len(results):.2f}")

if __name__ == "__main__":
    main()
