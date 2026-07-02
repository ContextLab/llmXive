"""
Extract comments from Python source code using tree-sitter.
Handles empty files and syntax errors gracefully.
"""
import logging
from typing import List, Optional, Dict, Any
import os
import json
from pathlib import Path

try:
    from tree_sitter import Language, Parser
    import tree_sitter_python as tspython
except ImportError:
    # Fallback if packages are not installed yet (for validation)
    Language = None
    Parser = None
    tspython = None

# Configure logger
logger = logging.getLogger(__name__)

# Initialize tree-sitter language and parser
# We use a singleton approach to avoid re-initializing the parser for every file
_parser: Optional[Parser] = None
_language: Optional[Language] = None

def _get_parser() -> Parser:
    """Lazy initialization of the tree-sitter parser."""
    global _parser, _language
    if _parser is None:
        if Language is None or tspython is None:
            raise ImportError(
                "tree-sitter or tree-sitter-python not installed. "
                "Please run: pip install tree-sitter tree-sitter-python"
            )
        # Initialize the language
        # We create a new Language instance using the tree_sitter_python module
        _language = Language(tspython.language())
        _parser = Parser(_language)
    return _parser

def extract_comments_ast(source_code: str, file_path: str = "<string>") -> List[Dict[str, Any]]:
    """
    Extract comments from Python source code using tree-sitter AST.
    
    This function isolates comments while ensuring they are not part of string literals.
    Tree-sitter's Python grammar naturally distinguishes between comments and string tokens,
    so we simply traverse the AST and collect nodes of type 'comment'.
    
    Args:
        source_code: The Python source code as a string.
        file_path: The path to the file (used for logging errors).
        
    Returns:
        A list of dictionaries, each containing:
            - 'text': The comment text (including the '#' symbol).
            - 'start_row': The starting line number (0-indexed).
            - 'start_col': The starting column number.
            - 'end_row': The ending line number.
            - 'end_col': The ending column.
        
    Raises:
        None: Errors are handled gracefully; empty list is returned on failure.
    """
    if not source_code or not source_code.strip():
        logger.debug(f"Empty source code in {file_path}, returning empty list.")
        return []

    try:
        parser = _get_parser()
        tree = parser.parse(source_code.encode('utf-8'))
    except Exception as e:
        logger.warning(f"Syntax error or parsing failed in {file_path}: {e}")
        return []

    comments = []
    root_node = tree.root_node

    def traverse(node):
        if node.type == 'comment':
            start_row, start_col = node.start_point
            end_row, end_col = node.end_point
            
            # Extract text directly from source code to ensure accuracy
            # tree-sitter points are 0-indexed
            lines = source_code.split('\n')
            
            # Handle multiline comments (though Python comments are usually single line)
            if start_row == end_row:
                text = lines[start_row][start_col:end_col]
            else:
                # Fallback for edge cases: reconstruct from lines
                text_lines = []
                for i in range(start_row, end_row + 1):
                    if i == start_row:
                        text_lines.append(lines[i][start_col:])
                    elif i == end_row:
                        text_lines.append(lines[i][:end_col])
                    else:
                        text_lines.append(lines[i])
                text = '\n'.join(text_lines)
            
            comments.append({
                'text': text,
                'start_row': start_row,
                'start_col': start_col,
                'end_row': end_row,
                'end_col': end_col
            })
        
        for child in node.children:
            traverse(child)

    traverse(root_node)
    return comments

def extract_comments_from_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Extract comments from a Python file on disk.
    
    Args:
        file_path: Path to the Python file.
        
    Returns:
        List of comment dictionaries.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            source_code = f.read()
        return extract_comments_ast(source_code, file_path)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return []
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return []

def extract_comments_batch(file_paths: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extract comments from multiple files.
    
    Args:
        file_paths: List of paths to Python files.
        
    Returns:
        Dictionary mapping file_path to list of comments.
    """
    results = {}
    for fp in file_paths:
        results[fp] = extract_comments_from_file(fp)
    return results

def run_extraction_pipeline(raw_data_dir: str = "data/raw", output_path: str = "data/processed/comments.json"):
    """
    Main entry point for T021: Parse Python files with tree-sitter, extract comments,
    handle empty files, and save to data/processed/comments.json.
    
    This function scans the raw data directory for Python files, extracts comments,
    and writes the aggregated results to a JSON file.
    
    Args:
        raw_data_dir: Path to the directory containing cloned repositories.
        output_path: Path where the output JSON file will be saved.
    """
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all Python files in the raw data directory
    python_files = []
    for root, _, files in os.walk(raw_data_dir):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    logger.info(f"Found {len(python_files)} Python files to process.")
    
    if not python_files:
        logger.warning("No Python files found in the specified directory.")
        # Write empty result if no files found
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({"files_processed": 0, "total_comments": 0, "data": {}}, f, indent=2)
        return
    
    # Process files in batches to manage memory
    all_comments = {}
    total_comments = 0
    files_with_comments = 0
    
    # Process files one by one (could be batched if needed)
    for i, file_path in enumerate(python_files):
        comments = extract_comments_from_file(file_path)
        if comments:
            all_comments[file_path] = comments
            total_comments += len(comments)
            files_with_comments += 1
        
        if (i + 1) % 100 == 0:
            logger.info(f"Processed {i + 1}/{len(python_files)} files.")
    
    # Prepare output data
    output_data = {
        "files_processed": len(python_files),
        "files_with_comments": files_with_comments,
        "total_comments": total_comments,
        "data": all_comments
    }
    
    # Write to JSON file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Successfully extracted comments from {files_with_comments} files.")
    logger.info(f"Total comments extracted: {total_comments}")
    logger.info(f"Output saved to: {output_path}")

if __name__ == "__main__":
    # Configure logging for script execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the extraction pipeline
    run_extraction_pipeline()