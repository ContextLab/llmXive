"""
Preprocessing module for code sanitization.

Sanitizes code by removing I/O and network calls, and mocking stdlib.
"""

import ast
import re
import sys
from pathlib import Path
from typing import Set, List, Optional, Dict, Any

from utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_error


class CodeSanitizer(ast.NodeTransformer):
    """AST transformer to sanitize code by removing dangerous operations."""
    
    DANGEROUS_FUNCTIONS = {
        'eval', 'exec', 'compile', 'open', 'input', 'raw_input',
        'os.system', 'os.popen', 'subprocess.call', 'subprocess.run',
        'requests.get', 'requests.post', 'urllib.request.urlopen',
        'socket.connect', 'socket.socket', 'ftp', 'http.client'
    }
    
    def visit_Call(self, node):
        # Remove dangerous function calls
        if isinstance(node.func, ast.Name):
            if node.func.id in self.DANGEROUS_FUNCTIONS:
                # Replace with pass statement
                return ast.Pass()
        elif isinstance(node.func, ast.Attribute):
            full_name = ast.unparse(node.func) if hasattr(ast, 'unparse') else ""
            if any(danger in full_name for danger in self.DANGEROUS_FUNCTIONS):
                return ast.Pass()
        
        return self.generic_visit(node)

def sanitize_code(code: str) -> str:
    """Sanitize code by removing dangerous operations."""
    try:
        tree = ast.parse(code)
        sanitizer = CodeSanitizer()
        sanitized_tree = sanitizer.visit(tree)
        
        # Reconstruct code
        if hasattr(ast, 'unparse'):
            return ast.unparse(sanitized_tree)
        else:
            # Fallback for older Python versions
            return code
    except SyntaxError:
        return code

def preprocess_function(func_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Preprocess a single function dictionary."""
    code = func_dict.get('code', '')
    sanitized_code = sanitize_code(code)
    
    func_dict['sanitized_code'] = sanitized_code
    func_dict['preprocessed'] = True
    
    return func_dict

def run_preprocessing(input_path: str, output_dir: str) -> Dict[str, int]:
    """Run preprocessing on validated functions."""
    logger = get_logger("preprocess")
    log_stage_start(logger, "preprocess", "Starting code preprocessing")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    processed_count = 0
    
    with open(input_path, 'r') as infile, open(output_path / "preprocessed_functions.jsonl", 'w') as outfile:
        for line in infile:
            func = json.loads(line)
            processed_func = preprocess_function(func)
            outfile.write(json.dumps(processed_func) + '\n')
            processed_count += 1
    
    log_stage_complete(logger, "preprocess", f"Preprocessed {processed_count} functions")
    
    return {
        "functions_processed": processed_count,
        "output_file": str(output_path / "preprocessed_functions.jsonl")
    }

def main():
    """Entry point for command-line execution."""
    if len(sys.argv) < 3:
        print("Usage: python -m data.preprocess <input_path> <output_dir>")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_dir = sys.argv[2]
    
    try:
        result = run_preprocessing(input_path, output_dir)
        print(f"Preprocessing complete: {result}")
        sys.exit(0)
    except Exception as e:
        print(f"Preprocessing failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    import json  # Import here for main function
    main()