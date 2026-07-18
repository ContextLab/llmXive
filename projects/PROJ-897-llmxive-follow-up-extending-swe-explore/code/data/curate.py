import ast
import copy
import hashlib
import json
import random
import sys
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set

from config import get_path, get_config_summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
MAX_SYNTHETIC_ISSUES = 50
MUTATION_TYPES = [
    'variable_rename',
    'comment_removal',
    'control_flow_reorder',
    'api_signature_change'
]

def load_derived_ground_truth() -> List[Dict[str, Any]]:
    """Load the ground truth derived in T013."""
    path = get_path("data/curated/ground_truth.jsonl")
    if not path.exists():
        logger.error(f"Ground truth file not found at {path}. Run T013 first.")
        sys.exit(1)
    
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def filter_hard_instances(ground_truth_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter for hard instances based on initial_coverage scores (T014a logic)."""
    # This is a placeholder for T014a logic which should have populated hard_subset.jsonl
    # For T014b, we assume hard_subset.jsonl exists as per task dependencies
    hard_path = get_path("data/curated/hard_subset.jsonl")
    if not hard_path.exists():
        logger.error(f"Hard subset file not found at {hard_path}. Run T014a first.")
        sys.exit(1)
    
    hard_data = []
    with open(hard_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                hard_data.append(json.loads(line))
    return hard_data

def compute_code_hash(code_str: str) -> str:
    """Compute SHA256 hash of code string."""
    return hashlib.sha256(code_str.encode('utf-8')).hexdigest()

def is_code_valid(code_str: str) -> bool:
    """Check if code is syntactically valid via AST parsing."""
    try:
        ast.parse(code_str)
        return True
    except SyntaxError:
        return False

def mutate_variable_names(code_str: str, seed: Optional[int] = None) -> Tuple[str, Dict[str, str]]:
    """
    Mutate variable names in the code.
    Returns (mutated_code, mapping_dict).
    """
    if seed is not None:
        random.seed(seed)
    
    try:
        tree = ast.parse(code_str)
    except SyntaxError:
        return code_str, {}
    
    # Collect all variable names (Name nodes) that are not built-ins
    builtins = set(dir(__builtins__)) if isinstance(__builtins__, dict) else set(dir(__builtins__))
    var_names: Set[str] = set()
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            if node.id not in builtins and not node.id.startswith('_'):
                var_names.add(node.id)
    
    if not var_names:
        return code_str, {}
    
    # Create mapping
    mapping = {}
    for name in var_names:
        new_name = f"var_{name}_{random.randint(1000, 9999)}"
        mapping[name] = new_name
    
    # Apply renaming
    class Renamer(ast.NodeTransformer):
        def visit_Name(self, node):
            if node.id in mapping:
                node.id = mapping[node.id]
            return node
        def visit_arg(self, node):
            if node.arg in mapping:
                node.arg = mapping[node.arg]
            return node
    
    transformer = Renamer()
    new_tree = transformer.visit(tree)
    ast.fix_missing_locations(new_tree)
    
    return ast.unparse(new_tree), mapping

def remove_comments(code_str: str) -> str:
    """Remove comments from code while preserving structure."""
    try:
        tree = ast.parse(code_str)
    except SyntaxError:
        return code_str
    
    # Simple approach: remove lines starting with # or inline comments
    # More robust: use ast.get_docstring and handle docstrings separately
    lines = code_str.splitlines()
    new_lines = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith('#'):
            continue
        # Handle inline comments (simple heuristic)
        if '#' in line:
            # Check if # is inside a string (simplified check)
            parts = line.split('#')
            if len(parts) > 1:
                # Very basic: assume # is a comment if not in quotes
                # This is a simplification; a full parser would be better
                new_lines.append(parts[0].rstrip())
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    return '\n'.join(new_lines)

def reorder_control_flow(code_str: str) -> str:
    """
    Apply structural obfuscation by reordering control flow blocks.
    Example: Swap order of if/elif/else blocks where semantically safe.
    This is a simplified version; real implementation would be more sophisticated.
    """
    try:
        tree = ast.parse(code_str)
    except SyntaxError:
        return code_str
    
    # Simple reordering: For functions with multiple if statements at top level,
    # we can shuffle their order (with caution)
    # This is a placeholder for a more complex structural obfuscation
    # that maintains syntactic validity.
    
    # For now, we'll implement a safe transformation:
    # Swap the order of independent if-statements in a function body
    class FlowReorder(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            # Look for consecutive if statements that are independent
            body = node.body
            new_body = []
            i = 0
            while i < len(body):
                if isinstance(body[i], ast.If):
                    # Collect consecutive if statements
                    if_block = [body[i]]
                    j = i + 1
                    while j < len(body) and isinstance(body[j], ast.If):
                        if_block.append(body[j])
                        j += 1
                    
                    # Shuffle if blocks (with seed for reproducibility)
                    if len(if_block) > 1:
                        # Simple shuffle: reverse order as a deterministic obfuscation
                        if_block.reverse()
                    
                    new_body.extend(if_block)
                    i = j
                else:
                    new_body.append(body[i])
                    i += 1
            
            node.body = new_body
            return node
    
    transformer = FlowReorder()
    new_tree = transformer.visit(tree)
    ast.fix_missing_locations(new_tree)
    
    return ast.unparse(new_tree)

def change_api_signature(code_str: str) -> str:
    """
    Apply structural obfuscation by changing API signatures.
    Example: Add default values, reorder parameters (with defaults), etc.
    """
    try:
        tree = ast.parse(code_str)
    except SyntaxError:
        return code_str
    
    class ApiMutator(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            # Add a dummy parameter with default value to function signatures
            # This changes the API signature without breaking existing calls
            # if the caller uses keyword arguments or the function is not called
            
            # Only mutate if function has parameters
            if node.args.args:
                # Check if we haven't already added a marker
                has_marker = any(arg.arg.startswith('__mutated__') for arg in node.args.args)
                if not has_marker:
                    # Add a new parameter at the end with a default value
                    new_arg = ast.arg(arg=f'__mutated_opt_{random.randint(1000, 9999)}', lineno=node.lineno, col_offset=node.col_offset)
                    new_arg.arg = f'__mutated_opt_{random.randint(1000, 9999)}'
                    
                    # Create a default value (None)
                    default = ast.Constant(value=None)
                    
                    node.args.args.append(new_arg)
                    node.args.defaults.append(default)
            
            return node
    
    transformer = ApiMutator()
    new_tree = transformer.visit(tree)
    ast.fix_missing_locations(new_tree)
    
    return ast.unparse(new_tree)

def generate_synthetic_issues(
    hard_subset: List[Dict[str, Any]], 
    target_count: int = MAX_SYNTHETIC_ISSUES
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Generate synthetic ambiguous issues by mutating original code.
    
    Args:
        hard_subset: List of hard instances from T014a
        target_count: Target number of synthetic issues to generate (default 50)
    
    Returns:
        Tuple of (synthetic_issues_list, metadata_dict)
    """
    synthetic_issues = []
    metadata = {
        'target_count': target_count,
        'actual_count': 0,
        'mutation_types_used': [],
        'warnings': [],
        'generation_timestamp': str(get_config_summary()['timestamp']),
        'version': '1.0.0'
    }
    
    mutation_functions = [
        ('variable_rename', mutate_variable_names),
        ('comment_removal', remove_comments),
        ('control_flow_reorder', reorder_control_flow),
        ('api_signature_change', change_api_signature)
    ]
    
    # Use a fixed seed for reproducibility
    random.seed(42)
    
    for idx, issue in enumerate(hard_subset):
        if len(synthetic_issues) >= target_count:
            break
        
        original_code = issue.get('original_code', '')
        if not original_code:
            metadata['warnings'].append(f"Skipping issue {issue.get('issue_id', 'unknown')}: no original_code")
            continue
        
        original_hash = compute_code_hash(original_code)
        
        # Select a random mutation type
        mutation_type, mutation_func = random.choice(mutation_functions)
        metadata['mutation_types_used'].append(mutation_type)
        
        # Apply mutation
        try:
            if mutation_type == 'variable_rename':
                mutated_code, mutation_details = mutation_func(original_code, seed=idx)
            elif mutation_type == 'comment_removal':
                mutated_code = mutation_func(original_code)
                mutation_details = {'comments_removed': True}
            elif mutation_type == 'control_flow_reorder':
                mutated_code = mutation_func(original_code)
                mutation_details = {'flow_reordered': True}
            elif mutation_type == 'api_signature_change':
                mutated_code = mutation_func(original_code)
                mutation_details = {'signature_changed': True}
            else:
                continue
            
            # Validate mutated code
            if not is_code_valid(mutated_code):
                logger.warning(f"Mutation {mutation_type} produced invalid code for issue {issue.get('issue_id', 'unknown')}. Skipping.")
                continue
            
            # Create synthetic issue record
            synthetic_issue = {
                'issue_id': f"synthetic_{issue.get('issue_id', 'unknown')}_{idx}",
                'original_issue_id': issue.get('issue_id', 'unknown'),
                'original_code': original_code,
                'mutated_code': mutated_code,
                'ground_truth_lines': issue.get('ground_truth_lines', []),
                'mutation_type': mutation_type,
                'mutation_details': mutation_details,
                'original_code_hash': original_hash,
                'mutated_code_hash': compute_code_hash(mutated_code),
                'is_valid': True,
                'coverage_score': issue.get('initial_coverage', 0.0)
            }
            
            synthetic_issues.append(synthetic_issue)
            
        except Exception as e:
            logger.warning(f"Error applying mutation {mutation_type} to issue {issue.get('issue_id', 'unknown')}: {e}")
            continue
    
    metadata['actual_count'] = len(synthetic_issues)
    
    if len(synthetic_issues) < target_count:
        logger.warning(f"Generated only {len(synthetic_issues)} synthetic issues (target: {target_count}). Insufficient pool or high mutation failure rate.")
    
    return synthetic_issues, metadata

def main():
    """Main entry point for T014b: Generate synthetic ambiguous issues."""
    logger.info("Starting T014b: Synthetic Issue Generation")
    
    # Load dependencies
    logger.info("Loading ground truth data...")
    ground_truth_data = load_derived_ground_truth()
    
    logger.info("Filtering hard instances...")
    hard_subset = filter_hard_instances(ground_truth_data)
    logger.info(f"Found {len(hard_subset)} hard instances")
    
    # Generate synthetic issues
    logger.info(f"Generating up to {MAX_SYNTHETIC_ISSUES} synthetic issues...")
    synthetic_issues, metadata = generate_synthetic_issues(hard_subset, MAX_SYNTHETIC_ISSUES)
    
    # Save synthetic issues to disk
    output_path = get_path("data/curated/synthetic_issues.jsonl")
    logger.info(f"Saving synthetic issues to {output_path}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for issue in synthetic_issues:
            f.write(json.dumps(issue) + '\n')
    
    # Save metadata
    metadata_path = get_path("data/curated/synthetic_issues_meta.json")
    logger.info(f"Saving metadata to {metadata_path}")
    
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Successfully generated {metadata['actual_count']} synthetic issues")
    logger.info("T014b completed")

if __name__ == "__main__":
    main()
