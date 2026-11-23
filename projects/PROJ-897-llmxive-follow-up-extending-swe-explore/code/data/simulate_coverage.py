"""
T011b: Implement AST-Based Coverage Simulation (Fallback)

This script computes a proxy coverage score for each issue in the SWE-Explore dataset
using a local AST-based retrieval simulation. It is designed as a fallback when
the primary ground truth coverage column is missing.

The simulation works by:
1. Parsing the repository code and issue description.
2. Identifying relevant code entities (functions, classes, variables) mentioned
   in the issue description.
3. Simulating a retrieval process that traverses the AST to find these entities.
4. Calculating a coverage score based on the ratio of retrieved relevant lines
   to the total lines in the target file.

Output: data/raw/swe_explore_with_coverage.jsonl
"""

import ast
import json
import sys
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from config import get_path, DATA_RAW, COVERAGE_COLUMN_NAME
from data.derive_gt import stream_derive_gt


def extract_entities_from_text(text: str) -> Set[str]:
    """
    Extract potential code entity names (identifiers) from the issue description.
    Uses a simple heuristic: capitalised words, camelCase, or snake_case patterns
    that might correspond to Python identifiers.
    """
    if not text:
        return set()
    
    # Regex to match potential identifiers:
    # - camelCase
    # - snake_case
    # - Capitalized words (common in class names)
    pattern = r'\b[A-Z][a-zA-Z0-9_]*\b|\b[a-z][a-zA-Z0-9_]*\b'
    matches = re.findall(pattern, text)
    return set(matches)


def find_entities_in_ast(tree: ast.AST, entities: Set[str]) -> Set[Tuple[str, int, int]]:
    """
    Traverse the AST to find definitions matching the extracted entities.
    Returns a set of tuples: (entity_name, start_line, end_line)
    """
    found_entities = set()
    
    for node in ast.walk(tree):
        # Check for FunctionDef, AsyncFunctionDef, ClassDef
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name in entities:
                # Lines are 1-indexed in AST
                start_line = node.lineno
                end_line = getattr(node, 'end_lineno', start_line)
                found_entities.add((node.name, start_line, end_line))
        # Check for Assign targets (variables)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in entities:
                    start_line = node.lineno
                    end_line = getattr(node, 'end_lineno', start_line)
                    found_entities.add((target.id, start_line, end_line))
        
    return found_entities


def calculate_proxy_coverage(
    code_text: str, 
    issue_description: str, 
    target_file_path: Optional[str] = None
) -> float:
    """
    Simulate coverage by finding relevant code entities and calculating
    the ratio of lines covered by these entities to the total lines in the file.
    
    Args:
        code_text: The source code of the file.
        issue_description: The text of the issue/bug report.
        target_file_path: Optional path to the target file (used for context).
    
    Returns:
        A float between 0.0 and 1.0 representing the proxy coverage score.
    """
    if not code_text or not issue_description:
        return 0.0
    
    try:
        tree = ast.parse(code_text)
    except SyntaxError:
        # If code is invalid, we cannot simulate coverage accurately
        # Return 0.0 or a neutral value. For safety, return 0.0.
        return 0.0
    
    lines = code_text.splitlines()
    total_lines = len(lines)
    if total_lines == 0:
        return 0.0
    
    entities = extract_entities_from_text(issue_description)
    if not entities:
        return 0.0
    
    found_entities = find_entities_in_ast(tree, entities)
    
    if not found_entities:
        return 0.0
    
    # Calculate covered lines
    covered_lines = set()
    for _, start, end in found_entities:
        for line_num in range(start, end + 1):
            covered_lines.add(line_num)
    
    covered_count = len(covered_lines)
    return min(1.0, covered_count / total_lines)


def stream_simulate_coverage(input_path: Path, output_path: Path) -> None:
    """
    Stream through the input dataset, compute proxy coverage for each issue,
    and write the results to the output file.
    
    This function is designed to handle large datasets without loading everything
    into memory at once.
    """
    print(f"Starting AST-based coverage simulation.")
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    processed_count = 0
    error_count = 0
    
    with open(input_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', encoding='utf-8') as outfile:
        
        for line in infile:
            line = line.strip()
            if not line:
                continue
            
            try:
                record = json.loads(line)
                
                # Extract necessary fields
                code_text = record.get('repo_code', '') or record.get('code', '')
                issue_desc = record.get('problem_statement', '') or record.get('text', '')
                
                if not code_text:
                    # If no code is present, we can't compute coverage
                    # We might need to skip or set a default value
                    # For this implementation, we'll set coverage to 0.0
                    record[COVERAGE_COLUMN_NAME] = 0.0
                else:
                    coverage_score = calculate_proxy_coverage(code_text, issue_desc)
                    record[COVERAGE_COLUMN_NAME] = coverage_score
                
                outfile.write(json.dumps(record) + '\n')
                processed_count += 1
                
                if processed_count % 100 == 0:
                    print(f"Processed {processed_count} records...")
                    
            except Exception as e:
                error_count += 1
                print(f"Error processing record: {e}")
                # Continue processing other records
                continue
    
    print(f"Simulation complete.")
    print(f"Processed: {processed_count} records")
    print(f"Errors: {error_count} records")
    print(f"Output written to: {output_path}")


def main() -> None:
    """
    Main entry point for the coverage simulation script.
    """
    input_path = get_path(DATA_RAW, "swe_explore_with_gt.jsonl")
    output_path = get_path(DATA_RAW, "swe_explore_with_coverage.jsonl")
    
    if not input_path.exists():
        print(f"Warning: Input file {input_path} not found.")
        print("Attempting to derive ground truth first...")
        # In a full pipeline, we might call stream_derive_gt here,
        # but for this task, we assume the input exists or fail loudly.
        # If it doesn't exist, we raise an error as per the "fail loudly" principle.
        raise FileNotFoundError(
            f"Input file {input_path} not found. "
            "Please ensure T011 (derive_gt.py) has been run successfully."
        )
    
    stream_simulate_coverage(input_path, output_path)


if __name__ == "__main__":
    main()