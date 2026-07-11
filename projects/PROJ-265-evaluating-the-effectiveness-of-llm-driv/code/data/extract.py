"""
Code extraction module for parsing Python files from CodeSearchNet.

Extracts top-level function definitions from raw code.
"""

import ast
import json
import os
import sys
from pathlib import Path
from typing import Dict, Generator, Optional

from utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_error


def parse_python_code(code: str) -> Optional[ast.AST]:
    """Parse Python code string into AST."""
    try:
        return ast.parse(code)
    except SyntaxError:
        return None


def extract_top_level_functions(tree: ast.AST) -> Generator[Dict, None, None]:
    """Extract top-level function definitions from AST."""
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef):
            func_code = ast.unparse(node) if hasattr(ast, 'unparse') else "<unparseable>"
            yield {
                "name": node.name,
                "code": func_code,
                "lineno": node.lineno,
                "col_offset": node.col_offset
            }
        elif isinstance(node, ast.AsyncFunctionDef):
            func_code = ast.unparse(node) if hasattr(ast, 'unparse') else "<unparseable>"
            yield {
                "name": node.name,
                "code": func_code,
                "lineno": node.lineno,
                "col_offset": node.col_offset
            }


def process_parquet_file(parquet_path: str, output_file: str) -> int:
    """Process a single parquet file and extract functions."""
    logger = get_logger("extract")
    count = 0
    
    try:
        import pandas as pd
        df = pd.read_parquet(parquet_path)
        
        with open(output_file, 'w') as out_f:
            for idx, row in df.iterrows():
                code = row.get('code', '')
                if not code:
                    continue
                
                tree = parse_python_code(code)
                if tree is None:
                    continue
                
                for func in extract_top_level_functions(tree):
                    func['source_file'] = str(parquet_path)
                    func['row_idx'] = idx
                    out_f.write(json.dumps(func) + '\n')
                    count += 1
                        
    except Exception as e:
        logger.error(f"Error processing {parquet_path}: {str(e)}")
        raise
    
    return count


def run_extraction(input_dir: str, output_dir: str) -> Dict[str, int]:
    """
    Run extraction on all parquet files in input directory.
    
    Args:
        input_dir: Directory containing parquet files
        output_dir: Directory for output JSONL file
        
    Returns:
        Dictionary with extraction statistics
    """
    logger = get_logger("extract")
    log_stage_start(logger, "extract", "Starting function extraction")
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    total_functions = 0
    files_processed = 0
    
    output_file = output_path / "extracted_functions.jsonl"
    
    for parquet_file in input_path.glob("*.parquet"):
        count = process_parquet_file(str(parquet_file), str(output_file))
        total_functions += count
        files_processed += 1
        logger.info(f"Processed {parquet_file.name}: {count} functions")
    
    log_stage_complete(logger, "extract", f"Extracted {total_functions} functions from {files_processed} files")
    
    return {
        "functions_extracted": total_functions,
        "files_processed": files_processed,
        "output_file": str(output_file)
    }

def main():
    """Entry point for command-line execution."""
    if len(sys.argv) < 3:
        print("Usage: python -m data.extract <input_dir> <output_dir>")
        sys.exit(1)
    
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    
    try:
        result = run_extraction(input_dir, output_dir)
        print(f"Extraction complete: {result}")
        sys.exit(0)
    except Exception as e:
        print(f"Extraction failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()