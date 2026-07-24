"""
Metrics for Halstead Complexity Measures.
Implements extraction of operators and operands from Java code to calculate Halstead Volume.
"""
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Set

# Simple regex-based tokenizer for Java (sufficient for volume calculation)
# In a production setting, use a proper parser like tree-sitter-java, 
# but for this research task, a robust regex is acceptable for volume estimation.

# Java Operators (simplified set)
JAVA_OPERATORS = [
    '>>>', '<<=', '>>=', '<<', '>>', '==', '!=', '<=', '>=', '&&', '||',
    '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '++', '--', '+', '-',
    '*', '/', '%', '<', '>', '=', '!', '&', '|', '^', '~', '?', ':'
]

# Java Keywords and Literals (to identify operands)
JAVA_KEYWORDS = {
    'abstract', 'assert', 'boolean', 'break', 'byte', 'case', 'catch', 
    'char', 'class', 'const', 'continue', 'default', 'do', 'double', 
    'else', 'enum', 'extends', 'final', 'finally', 'float', 'for', 
    'goto', 'if', 'implements', 'import', 'instanceof', 'int', 'interface', 
    'long', 'native', 'new', 'package', 'private', 'protected', 'public', 
    'return', 'short', 'static', 'strictfp', 'super', 'switch', 'synchronized', 
    'this', 'throw', 'throws', 'transient', 'try', 'void', 'volatile', 'while'
}

def tokenize_java(code: str) -> Tuple[List[str], List[str]]:
    """
    Tokenize Java code into operators and operands.
    Returns (operators_list, operands_list).
    """
    # Remove comments
    code = re.sub(r'//.*', '', code)
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    
    # Replace operators with space-delimited versions to separate them
    # Sort by length descending to match multi-char operators first
    sorted_operators = sorted(JAVA_OPERATORS, key=len, reverse=True)
    for op in sorted_operators:
        code = code.replace(op, f' {op} ')
    
    # Split by whitespace and punctuation (except dots inside identifiers)
    # This is a simplified split; a real parser is better but this works for volume.
    tokens = re.split(r'[\s\(\)\{\}\[\],;]+', code)
    tokens = [t for t in tokens if t]
    
    operators = []
    operands = []
    
    for token in tokens:
        if token in JAVA_OPERATORS:
            operators.append(token)
        elif token not in JAVA_KEYWORDS and not token.isdigit():
            # Identify as operand (variables, literals, method names)
            # Simple heuristic: if it's not a keyword and not a pure operator
            operands.append(token)
    
    return operators, operands

def calculate_halstead_volume(operators: List[str], operands: List[str]) -> float:
    """
    Calculate Halstead Volume.
    N = total number of operators + total number of operands
    n1 = number of unique operators
    n2 = number of unique operands
    V = N * log2(n1 + n2)
    """
    n1 = len(set(operators))
    n2 = len(set(operands))
    N = len(operators) + len(operands)
    
    if (n1 + n2) == 0:
        return 0.0
    
    volume = N * (n1 + n2).bit_length() # Approximation of log2, but we need exact log2
    import math
    volume = N * math.log2(n1 + n2) if (n1 + n2) > 0 else 0.0
    
    return volume

def calculate_halstead_for_file(file_path: Path) -> float:
    """Calculate Halstead Volume for a single Java file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        
        operators, operands = tokenize_java(code)
        return calculate_halstead_volume(operators, operands)
    except Exception as e:
        # Log error and return 0 or raise
        print(f"Error processing {file_path}: {e}")
        return 0.0

def calculate_halstead_batch(file_paths: List[Path]) -> Dict[str, float]:
    """
    Calculate Halstead Volume for a batch of files.
    Returns a dictionary mapping absolute file path string to volume.
    """
    results = {}
    for fp in file_paths:
        vol = calculate_halstead_for_file(fp)
        results[str(fp.resolve())] = vol
    return results

def main():
    """Simple CLI entry point for testing."""
    # This would be called by the pipeline
    print("Halstead Metrics Module")

if __name__ == "__main__":
    main()
