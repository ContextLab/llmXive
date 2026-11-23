"""
Code extraction module for parsing Python files from CodeSearchNet.

Extracts top-level function definitions from raw code using AST.
"""

import ast
import json
import os
import sys
from pathlib import Path
from typing import Dict, Generator, Optional

from utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_error


def parse_python_code(code: str) -> Optional[ast.AST]:
    """Parse Python code string into AST.

    Args:
        code: Python source code string

    Returns:
        Parsed AST node if successful, None if syntax error
    """
    try:
        return ast.parse(code)
    except SyntaxError:
        return None


def extract_top_level_functions(tree: ast.AST) -> Generator[Dict, None, None]:
    """Extract top-level function definitions from AST.

    Args:
        tree: Parsed AST tree

    Yields:
        Dictionary containing function metadata and code
    """
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Use ast.unparse if available (Python 3.9+), otherwise fallback
            if hasattr(ast, 'unparse'):
                func_code = ast.unparse(node)
            else:
                # Fallback for older Python versions - reconstruct from source lines
                # This is a basic fallback; ideally requires source lines context
                func_code = f"# unparseable AST node: {node.name}"

            yield {
                "name": node.name,
                "code": func_code,
                "lineno": node.lineno,
                "col_offset": node.col_offset,
                "is_async": isinstance(node, ast.AsyncFunctionDef)
            }


def process_parquet_file(parquet_path: str, output_file: str) -> int:
    """Process a single parquet file and extract top-level functions.

    Args:
        parquet_path: Path to the parquet file
        output_file: Path to the output JSONL file

    Returns:
        Number of functions extracted from this file
    """
    logger = get_logger("extract")
    count = 0

    try:
        import pandas as pd
        df = pd.read_parquet(parquet_path)

        # Open output file in append mode to handle multiple parquet files
        with open(output_file, 'a') as out_f:
            for idx, row in df.iterrows():
                code = row.get('code', '')
                if not code or not isinstance(code, str):
                    continue

                tree = parse_python_code(code)
                if tree is None:
                    continue

                for func in extract_top_level_functions(tree):
                    func['source_file'] = str(parquet_path)
                    func['row_idx'] = int(idx)
                    func['repo_name'] = row.get('repo_name', 'unknown')
                    func['language'] = row.get('language', 'python')
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
        input_dir: Directory containing parquet files (e.g., data/raw)
        output_dir: Directory for output JSONL file (e.g., data/processed)

    Returns:
        Dictionary with extraction statistics
    """
    logger = get_logger("extract")
    log_stage_start(logger, "extract", "Starting function extraction from raw parquet files")

    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    total_functions = 0
    files_processed = 0
    files_failed = 0

    # Output file path
    output_file = output_path / "extracted_functions.jsonl"

    # Clear existing output file if it exists to start fresh
    if output_file.exists():
        output_file.unlink()

    parquet_files = list(input_path.glob("*.parquet"))
    
    if not parquet_files:
        log_stage_error(logger, "extract", f"No parquet files found in {input_dir}")
        raise FileNotFoundError(f"No parquet files found in {input_dir}")

    for parquet_file in parquet_files:
        try:
            count = process_parquet_file(str(parquet_file), str(output_file))
            total_functions += count
            files_processed += 1
            logger.info(f"Processed {parquet_file.name}: {count} functions extracted")
        except Exception as e:
            files_failed += 1
            logger.error(f"Failed to process {parquet_file.name}: {str(e)}")
            # Continue processing other files

    log_stage_complete(
        logger, 
        "extract", 
        f"Extracted {total_functions} functions from {files_processed} files (failed: {files_failed})"
    )

    return {
        "functions_extracted": total_functions,
        "files_processed": files_processed,
        "files_failed": files_failed,
        "output_file": str(output_file)
    }


def main():
    """Entry point for command-line execution."""
    if len(sys.argv) < 3:
        print("Usage: python -m data.extract <input_dir> <output_dir>")
        print("  input_dir: Directory containing parquet files (e.g., data/raw)")
        print("  output_dir: Directory for output JSONL file (e.g., data/processed)")
        sys.exit(1)

    input_dir = sys.argv[1]
    output_dir = sys.argv[2]

    if not os.path.isdir(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist")
        sys.exit(1)

    try:
        result = run_extraction(input_dir, output_dir)
        print(f"Extraction complete: {json.dumps(result, indent=2)}")
        sys.exit(0)
    except Exception as e:
        print(f"Extraction failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()