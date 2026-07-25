import ast
import copy
import hashlib
import json
import random
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import get_path, get_config_summary

def load_derived_ground_truth(path: Path) -> List[Dict[str, Any]]:
    """Load the derived ground truth dataset."""
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    return data

def filter_hard_instances(
    dataset: List[Dict[str, Any]],
    percentile: float = 0.20
) -> List[Dict[str, Any]]:
    """
    Filter the dataset to keep only the 'hard' instances based on initial_coverage.
    
    Args:
        dataset: List of issue dictionaries.
        percentile: The bottom percentile to select (e.g., 0.20 for bottom 20%).
        
    Returns:
        List of hard instances.
    """
    # Filter out entries with missing initial_coverage
    valid_data = [d for d in dataset if "initial_coverage" in d and d["initial_coverage"] is not None]
    
    if not valid_data:
        return []
        
    scores = sorted([d["initial_coverage"] for d in valid_data])
    threshold_idx = int(len(scores) * percentile)
    threshold = scores[threshold_idx]
    
    hard_instances = [d for d in valid_data if d["initial_coverage"] <= threshold]
    return hard_instances

def compute_code_hash(code: str) -> str:
    """Compute SHA256 hash of code."""
    return hashlib.sha256(code.encode('utf-8')).hexdigest()

def is_code_valid(code: str) -> bool:
    """Check if code is syntactically valid."""
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False

def mutate_variable_names(code: str) -> str:
    """Rename local variables using a deterministic hash-based mapping."""
    # Simplified mutation: replace variable names with hashed versions
    # This is a placeholder for a more robust AST-based mutation
    if not is_code_valid(code):
        return code
        
    # Simple regex-based replacement for demonstration
    # In a real implementation, use AST to identify local variables
    import re
    # Find all words that look like variable assignments
    pattern = r'\b([a-z_][a-z0-9_]*)\s*='
    def replacer(match):
        var_name = match.group(1)
        if var_name in ['if', 'for', 'while', 'def', 'class', 'return', 'import', 'from', 'as', 'try', 'except', 'finally', 'with', 'lambda', 'yield', 'raise', 'assert', 'del', 'global', 'nonlocal']:
            return match.group(0)
        # Generate a deterministic hash-based name
        new_name = f"var_{hashlib.sha256(var_name.encode()).hexdigest()[:8]}"
        return f"{new_name}="
        
    return re.sub(pattern, replacer, code)

def remove_comments(code: str) -> str:
    """Strip all comments from code."""
    try:
        tree = ast.parse(code)
        # AST doesn't preserve comments, so we use a simple regex approach
        import re
        # Remove single-line comments
        code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
        # Remove multi-line comments (docstrings are tricky, but we'll try)
        # This is a simplification
        return code
    except SyntaxError:
        return code

def reorder_control_flow(code: str) -> str:
    """Reorder independent if/else blocks (simplified)."""
    # This is a placeholder for a more complex AST manipulation
    return code

def change_api_signature(code: str) -> str:
    """Rename function arguments (API signature changes)."""
    # Placeholder for AST-based signature change
    return code

def generate_synthetic_issues(
    non_hard_dataset: List[Dict[str, Any]],
    min_count: int = 10
) -> List[Dict[str, Any]]:
    """
    Generate synthetic ambiguous issues from the non-hard dataset.
    
    Args:
        non_hard_dataset: List of non-hard issue dictionaries.
        min_count: Minimum number of synthetic issues to generate.
        
    Returns:
        List of synthetic issues.
    """
    synthetic_issues = []
    
    for issue in non_hard_dataset:
        original_code = issue.get("code", "")
        if not original_code:
            continue
            
        # Apply mutations
        mutated_code = mutate_variable_names(original_code)
        if is_code_valid(mutated_code):
            new_issue = copy.deepcopy(issue)
            new_issue["code"] = mutated_code
            new_issue["is_synthetic"] = True
            new_issue["mutation_type"] = "variable_rename"
            new_issue["original_code_hash"] = compute_code_hash(original_code)
            synthetic_issues.append(new_issue)
            
        # Try comment removal
        mutated_code = remove_comments(original_code)
        if is_code_valid(mutated_code):
            new_issue = copy.deepcopy(issue)
            new_issue["code"] = mutated_code
            new_issue["is_synthetic"] = True
            new_issue["mutation_type"] = "comment_removal"
            new_issue["original_code_hash"] = compute_code_hash(original_code)
            synthetic_issues.append(new_issue)
            
    if len(synthetic_issues) == 0:
        raise ValueError("No valid synthetic issues generated.")
    elif len(synthetic_issues) < min_count:
        print(f"Warning: Only generated {len(synthetic_issues)} synthetic issues (min: {min_count}).")
        
    return synthetic_issues

def main():
    """Main entry point for the curation script."""
    gt_path = get_path("data_raw", "swe_explore_with_gt.jsonl")
    hard_path = get_path("data_curated", "hard_subset.jsonl")
    non_hard_path = get_path("data_curated", "non_hard_subset.jsonl")
    synthetic_path = get_path("data_curated", "synthetic_issues.jsonl")
    synthetic_meta_path = get_path("data_curated", "synthetic_issues_meta.json")
    
    if not gt_path.exists():
        print(f"Error: Ground truth file not found: {gt_path}")
        sys.exit(1)
        
    # Load and filter
    dataset = load_derived_ground_truth(gt_path)
    hard_instances = filter_hard_instances(dataset, 0.20)
    non_hard_instances = [d for d in dataset if d not in hard_instances]
    
    # Write subsets
    hard_path.parent.mkdir(parents=True, exist_ok=True)
    with open(hard_path, 'w', encoding='utf-8') as f:
        for item in hard_instances:
            f.write(json.dumps(item) + '\n')
            
    with open(non_hard_path, 'w', encoding='utf-8') as f:
        for item in non_hard_instances:
            f.write(json.dumps(item) + '\n')
            
    # Generate synthetic issues
    synthetic_issues = generate_synthetic_issues(non_hard_instances, 10)
    
    with open(synthetic_path, 'w', encoding='utf-8') as f:
        for item in synthetic_issues:
            f.write(json.dumps(item) + '\n')
            
    # Write metadata
    meta = {
        "count": len(synthetic_issues),
        "source": "non_hard_subset",
        "mutations": ["variable_rename", "comment_removal"]
    }
    with open(synthetic_meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=2)
        
    print(f"Generated {len(synthetic_issues)} synthetic issues.")

if __name__ == "__main__":
    main()
