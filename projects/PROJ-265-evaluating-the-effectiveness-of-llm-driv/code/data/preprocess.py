"""
Preprocessing module for code sanitization.

Sanitizes code by removing I/O and network calls, and mocking stdlib.
Implements FR-011: Remove I/O/network calls, mock stdlib.
"""

import ast
import json
import re
import sys
from pathlib import Path
from typing import Set, List, Optional, Dict, Any

from utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_error


class CodeSanitizer(ast.NodeTransformer):
    """AST transformer to sanitize code by removing dangerous operations and mocking stdlib."""
    
    # Dangerous functions that must be removed or replaced
    DANGEROUS_FUNCTIONS = {
        'eval', 'exec', 'compile', 'open', 'input', 'raw_input',
        'os.system', 'os.popen', 'subprocess.call', 'subprocess.run',
        'requests.get', 'requests.post', 'urllib.request.urlopen',
        'socket.connect', 'socket.socket', 'ftp', 'http.client'
    }
    
    # Stdlib modules that need mocking (I/O, network, system interaction)
    MOCKABLE_MODULES = {
        'os', 'sys', 'subprocess', 'socket', 'requests', 'urllib',
        'ftplib', 'http.client', 'email', 'pickle', 'shelve',
        'dbm', 'sqlite3', 'mysql', 'psycopg2', 'redis', 'pymongo'
    }
    
    def __init__(self):
        self.imports_mocked = set()
        self.replacements_made = []
    
    def visit_Import(self, node):
        """Mock dangerous imports by replacing with a no-op function call."""
        for alias in node.names:
            module_name = alias.name.split('.')[0]
            if module_name in self.MOCKABLE_MODULES:
                self.imports_mocked.add(module_name)
                # Replace import with a mock assignment
                mock_call = ast.Call(
                    func=ast.Name(id='mock_import', ctx=ast.Load()),
                    args=[ast.Constant(value=module_name)],
                    keywords=[]
                )
                self.replacements_made.append(f"Mocked import: {module_name}")
                return ast.Expr(value=mock_call)
        return self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Mock dangerous from-imports."""
        if node.module:
            module_name = node.module.split('.')[0]
            if module_name in self.MOCKABLE_MODULES:
                self.imports_mocked.add(module_name)
                # Replace from-import with a mock assignment
                mock_call = ast.Call(
                    func=ast.Name(id='mock_import', ctx=ast.Load()),
                    args=[ast.Constant(value=module_name)],
                    keywords=[]
                )
                self.replacements_made.append(f"Mocked from-import: {node.module}")
                return ast.Expr(value=mock_call)
        return self.generic_visit(node)
    
    def visit_Call(self, node):
        # Remove dangerous function calls
        func_name = None
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            # Handle method calls like os.system
            if isinstance(node.func.value, ast.Name):
                func_name = f"{node.func.value.id}.{node.func.attr}"
        
        if func_name:
            if func_name in self.DANGEROUS_FUNCTIONS:
                self.replacements_made.append(f"Removed dangerous call: {func_name}")
                return ast.Pass()
            
            # Check for partial matches (e.g., 'requests.get' in 'requests.get(url)')
            for danger in self.DANGEROUS_FUNCTIONS:
                if danger in func_name:
                    self.replacements_made.append(f"Removed dangerous call: {func_name}")
                    return ast.Pass()
        
        return self.generic_visit(node)
    
    def visit_Expr(self, node):
        """Remove print statements and other expression statements that cause I/O."""
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name):
                if node.value.func.id == 'print':
                    self.replacements_made.append("Removed print statement")
                    return ast.Pass()
        return self.generic_visit(node)

def sanitize_code(code: str) -> Dict[str, Any]:
    """
    Sanitize code by removing dangerous operations and mocking stdlib.
    
    Returns:
        Dict with 'sanitized_code' (str) and 'changes' (list of changes made)
    """
    changes = []
    try:
        tree = ast.parse(code)
        sanitizer = CodeSanitizer()
        sanitized_tree = sanitizer.visit(tree)
        
        # Collect changes
        changes.extend(sanitizer.replacements_made)
        
        # Reconstruct code
        if hasattr(ast, 'unparse'):
            sanitized_code = ast.unparse(sanitized_tree)
        else:
            # Fallback for older Python versions - return original if unparse unavailable
            sanitized_code = code
            changes.append("Warning: ast.unparse not available, code unchanged")
        
        return {
            'sanitized_code': sanitized_code,
            'changes': changes,
            'success': True
        }
    except SyntaxError as e:
        return {
            'sanitized_code': code,
            'changes': [f"SyntaxError: {str(e)}"],
            'success': False
        }
    except Exception as e:
        return {
            'sanitized_code': code,
            'changes': [f"Error: {str(e)}"],
            'success': False
        }

def preprocess_function(func_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Preprocess a single function dictionary.
    
    Args:
        func_dict: Dictionary containing function data with 'code' key
        
    Returns:
        Updated dictionary with 'sanitized_code' and 'preprocessing_log'
    """
    code = func_dict.get('code', '')
    result = sanitize_code(code)
    
    func_dict['sanitized_code'] = result['sanitized_code']
    func_dict['preprocessed'] = result['success']
    func_dict['preprocessing_log'] = result['changes']
    
    return func_dict

def run_preprocessing(input_path: str, output_dir: str) -> Dict[str, Any]:
    """
    Run preprocessing on validated functions.
    
    Args:
        input_path: Path to input JSONL file
        output_dir: Directory to write output files
        
    Returns:
        Dictionary with processing statistics
    """
    logger = get_logger("preprocess")
    log_stage_start(logger, "preprocess", "Starting code preprocessing")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    processed_count = 0
    success_count = 0
    error_count = 0
    changes_log = []
    
    input_file = Path(input_path)
    if not input_file.exists():
        log_stage_error(logger, "preprocess", f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    output_file = output_path / "preprocessed_functions.jsonl"
    
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line_num, line in enumerate(infile, 1):
            try:
                func = json.loads(line.strip())
                processed_func = preprocess_function(func)
                
                if processed_func['preprocessed']:
                    success_count += 1
                else:
                    error_count += 1
                
                # Log first 100 changes for debugging
                if len(changes_log) < 100:
                    changes_log.extend(processed_func.get('preprocessing_log', []))
                
                outfile.write(json.dumps(processed_func) + '\n')
                processed_count += 1
                
            except json.JSONDecodeError as e:
                log_stage_error(logger, "preprocess", f"JSON decode error at line {line_num}: {str(e)}")
                error_count += 1
            except Exception as e:
                log_stage_error(logger, "preprocess", f"Error processing line {line_num}: {str(e)}")
                error_count += 1
    
    log_stage_complete(logger, "preprocess", 
        f"Preprocessed {processed_count} functions (success: {success_count}, errors: {error_count})")
    
    return {
        "functions_processed": processed_count,
        "success_count": success_count,
        "error_count": error_count,
        "output_file": str(output_file),
        "sample_changes": changes_log[:20]  # First 20 changes for inspection
    }

def main():
    """Entry point for command-line execution."""
    if len(sys.argv) < 3:
        print("Usage: python -m data.preprocess <input_path> <output_dir>")
        print("  input_path: Path to JSONL file with functions to preprocess")
        print("  output_dir: Directory to write preprocessed output")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_dir = sys.argv[2]
    
    try:
        result = run_preprocessing(input_path, output_dir)
        print(f"Preprocessing complete:")
        print(f"  Functions processed: {result['functions_processed']}")
        print(f"  Success: {result['success_count']}")
        print(f"  Errors: {result['error_count']}")
        print(f"  Output file: {result['output_file']}")
        if result['sample_changes']:
            print(f"  Sample changes: {result['sample_changes'][:5]}")
        sys.exit(0)
    except Exception as e:
        print(f"Preprocessing failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
