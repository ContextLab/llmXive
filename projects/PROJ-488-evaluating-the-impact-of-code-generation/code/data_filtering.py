import ast
import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from logging_config import setup_logger, get_logger
from data_model import CodeSnippet, DatasetGroup

logger = get_logger(__name__)

def parse_snippet_to_ast(code: str) -> Optional[ast.AST]:
    """
    Attempt to parse a code snippet into an AST.
    Returns the AST node if successful, None otherwise.
    """
    try:
        return ast.parse(code)
    except SyntaxError:
        return None

def extract_top_level_functions(code: str) -> List[str]:
    """
    Extract top-level function definitions from a code snippet.
    Returns a list of function definitions (source code strings).
    """
    tree = parse_snippet_to_ast(code)
    if tree is None:
        return []

    functions = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            # Get the source code for this function
            func_source = ast.get_source_segment(code, node)
            if func_source:
                functions.append(func_source)
            else:
                # Fallback: reconstruct from lines if get_source_segment fails
                lines = code.splitlines(keepends=True)
                start_line = node.lineno - 1
                end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 1
                func_source = "".join(lines[start_line:end_line])
                functions.append(func_source)
    
    return functions

def filter_python_snippets(snippets: List[Dict[str, Any]], language_field: str = "language") -> List[Dict[str, Any]]:
    """
    Filter snippets to keep only those where language is "python".
    Additionally, extracts top-level functions and replaces the code with
    the extracted functions (joined by newlines).
    
    Args:
        snippets: List of snippet dictionaries, each expected to have 'code' and 'language' keys.
        language_field: The key in the snippet dict representing the language.
    
    Returns:
        List of filtered and processed snippet dictionaries.
    """
    filtered = []
    invalid_count = 0

    for i, snippet in enumerate(snippets):
        lang = snippet.get(language_field, "").lower()
        
        if lang != "python":
            continue

        code = snippet.get("code", "")
        if not code:
            invalid_count += 1
            continue

        # Extract top-level functions
        top_level_funcs = extract_top_level_functions(code)
        
        if not top_level_funcs:
            # If no functions found, keep the original code or skip?
            # Task says "extract top-level functions". If none, we might keep original or skip.
            # Based on strict filtering, if no functions, it might not be a valid function snippet.
            # However, for robustness, we'll keep the snippet but note it has no top-level functions.
            # Let's assume we keep the original code if no functions found, but log it.
            logger.warning(f"Snippet {snippet.get('id', i)} has no top-level functions.")
            filtered_snippet = snippet.copy()
        else:
            # Join extracted functions with newlines to form the filtered code
            filtered_code = "\n\n".join(top_level_funcs)
            filtered_snippet = snippet.copy()
            filtered_snippet["code"] = filtered_code
            filtered_snippet["extracted_function_count"] = len(top_level_funcs)

        filtered.append(filtered_snippet)

    logger.info(f"Filtered {len(snippets)} snippets to {len(filtered)} Python snippets. Invalid/Empty: {invalid_count}")
    return filtered

def run_filtering_workflow(input_path: str, output_path: str, language_field: str = "language") -> None:
    """
    Main workflow to load snippets from a JSON file, filter for Python,
    extract top-level functions, and save the result.
    
    Args:
        input_path: Path to the input JSON file containing snippets.
        output_path: Path to the output JSON file for filtered snippets.
        language_field: Key in snippet dict representing language.
    """
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading snippets from {input_path}")
    with open(input_file, 'r', encoding='utf-8') as f:
        snippets = json.load(f)
    
    if not isinstance(snippets, list):
        raise ValueError(f"Expected a list of snippets in {input_path}, got {type(snippets)}")

    logger.info(f"Loaded {len(snippets)} snippets. Filtering for Python and extracting functions...")
    filtered_snippets = filter_python_snippets(snippets, language_field)

    logger.info(f"Saving {len(filtered_snippets)} filtered snippets to {output_path}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_snippets, f, indent=2)

    logger.info(f"Filtering workflow completed. Output: {output_path}")

def main():
    """
    Entry point for the data filtering script.
    Expects command line arguments or default paths.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Filter Python snippets and extract top-level functions.")
    parser.add_argument("--input", type=str, required=True, help="Path to input JSON file with snippets.")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON file for filtered snippets.")
    parser.add_argument("--lang-field", type=str, default="language", help="Key in snippet dict for language.")
    
    args = parser.parse_args()
    
    setup_logger(level=logging.INFO)
    
    try:
        run_filtering_workflow(args.input, args.output, args.lang_field)
    except Exception as e:
        logger.error(f"Workflow failed: {e}")
        raise

if __name__ == "__main__":
    main()
