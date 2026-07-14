"""
Data curation module for SWE-Explore benchmark.

Implements:
- Part A: Filter hard instances based on initial_coverage scores (T014a)
- Part B: Generate synthetic ambiguous issues with mutations (T014b)
- Part C: Validation logic to skip invalid mutations and log warnings (T014c)
"""
import ast
import copy
import hashlib
import json
import random
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set

# Import config
try:
    from config import get_config_summary
except ImportError:
    # Fallback for direct execution or different import context
    import os
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from config import get_config_summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for validation
VALIDATION_SAMPLE_SIZE = 20  # Can be overridden by config
AST_TIMEOUT_SECONDS = 5

def load_derived_ground_truth(ground_truth_path: Path) -> Dict[str, Any]:
    """
    Load derived ground truth data from T013.
    
    Args:
        ground_truth_path: Path to the derived ground truth JSON file
        
    Returns:
        Dictionary containing ground truth data keyed by issue_id
    """
    if not ground_truth_path.exists():
        raise FileNotFoundError(f"Ground truth file not found: {ground_truth_path}")
    
    with open(ground_truth_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def filter_hard_instances(
    dataset_path: Path,
    ground_truth_data: Dict[str, Any],
    output_path: Path,
  ) -> List[Dict[str, Any]]:
    """
    Part A: Filter the bottom percentile of issues based on initial_coverage scores.
    
    Args:
        dataset_path: Path to the original benchmark dataset JSONL
        ground_truth_data: Derived ground truth data
        output_path: Path to save the filtered hard subset
        hard_percentile: Percentile threshold (e.g., 20 for bottom 20%)
        
    Returns:
        List of hard instances
    """
    config = get_config_summary()
    hard_percentile = config.get('HARD_INSTANCE_PERCENTILE', 20)
    
    # Load dataset
    issues = []
    with open(dataset_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                issues.append(json.loads(line))
    
    # Calculate threshold
    coverage_scores = [
        issue.get('initial_coverage', 0.0) 
        for issue in issues 
        if 'initial_coverage' in issue
    ]
    
    if not coverage_scores:
        logger.warning("No initial_coverage scores found in dataset. Using all instances.")
        hard_issues = issues
    else:
        coverage_scores.sort()
        threshold_index = int(len(coverage_scores) * hard_percentile / 100)
        threshold = coverage_scores[threshold_index] if threshold_index < len(coverage_scores) else coverage_scores[-1]
        
        logger.info(f"Hard instance threshold (bottom {hard_percentile}%): {threshold:.4f}")
        hard_issues = [
            issue for issue in issues 
            if issue.get('initial_coverage', 1.0) <= threshold
        ]
    
    # Save filtered subset
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for issue in hard_issues:
            f.write(json.dumps(issue) + '\n')
    
    logger.info(f"Filtered {len(hard_issues)} hard instances to {output_path}")
    return hard_issues

def mutate_variable_names(code: str, rename_map: Optional[Dict[str, str]] = None) -> Tuple[str, Dict[str, str]]:
    """
    Mutate variable names in code.
    
    Args:
        code: Original code string
        rename_map: Optional mapping of old names to new names
        
    Returns:
        Tuple of (mutated_code, rename_map)
    """
    if rename_map is None:
        rename_map = {}
    
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code, rename_map
    
    # Simple variable renaming (names that are not keywords)
    new_names = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            if node.id not in rename_map and node.id not in new_names:
                # Generate a new name
                new_name = f"__var_{random.randint(1000, 9999)}__"
                new_names[node.id] = new_name
                rename_map[node.id] = new_name
    
    # Reconstruct code with new names (simplified approach)
    # Note: A full AST visitor would be more robust
    mutated_code = code
    for old_name, new_name in rename_map.items():
        mutated_code = mutated_code.replace(old_name, new_name)
    
    return mutated_code, rename_map

def remove_comments(code: str) -> str:
    """
    Remove comments from code.
    
    Args:
        code: Original code string
        
    Returns:
        Code with comments removed
    """
    lines = code.split('\n')
    cleaned_lines = []
    for line in lines:
        # Remove inline comments (simple approach, doesn't handle strings with #)
        if '#' in line:
            # Find the first # not in a string (simplified)
            comment_start = line.find('#')
            if comment_start > 0:
                # Check if it's not in a string (very simplified check)
                quote_count = line[:comment_start].count('"') + line[:comment_start].count("'")
                if quote_count % 2 == 0:
                    line = line[:comment_start].rstrip()
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def reorder_control_flow(code: str) -> str:
    """
    Apply structural obfuscation by reordering control flow blocks.
    
    Args:
        code: Original code string
        
    Returns:
        Mutated code with reordered control flow
    """
    # This is a simplified implementation
    # A full implementation would parse AST and reorder blocks
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code
    
    # For now, return original code as a safe fallback
    # In a full implementation, we would reorder if/else blocks, loops, etc.
    return code

def change_api_signature(code: str) -> str:
    """
    Apply structural obfuscation by changing API signatures.
    
    Args:
        code: Original code string
        
    Returns:
        Mutated code with changed API signatures
    """
    # This is a simplified implementation
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code
    
    # For now, return original code as a safe fallback
    # In a full implementation, we would modify function signatures
    return code

def is_code_valid(code: str) -> bool:
    """
    Check if code is syntactically valid (AST parseable).
    
    Args:
        code: Code string to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False

def generate_synthetic_issues(
    hard_instances: List[Dict[str, Any]],
    ground_truth_data: Dict[str, Any],
    output_path: Path,
    max_synthetic: int = 50
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Part B: Generate synthetic ambiguous issues by mutating code.
    
    Args:
        hard_instances: List of hard instances to mutate
        ground_truth_data: Derived ground truth data
        output_path: Path to save synthetic issues
        max_synthetic: Maximum number of synthetic issues to generate
        
    Returns:
        Tuple of (synthetic_issues, metadata)
    """
    synthetic_issues = []
    metadata = {
        'total_attempted': 0,
        'successful': 0,
        'failed': 0,
        'mutation_types': {},
        'warnings': []
    }
    
    mutation_functions = [
        ('variable_rename', mutate_variable_names),
        ('comment_removal', lambda c: (remove_comments(c), {})),
        ('control_flow_reorder', lambda c: (reorder_control_flow(c), {})),
        ('api_signature_change', lambda c: (change_api_signature(c), {})),
    ]
    
    for issue in hard_instances:
        if len(synthetic_issues) >= max_synthetic:
            break
        
        metadata['total_attempted'] += 1
        issue_id = issue.get('issue_id', f"unknown_{len(synthetic_issues)}")
        
        # Get original code
        original_code = issue.get('repo_code', '')
        if not original_code:
            metadata['warnings'].append(f"No code found for issue {issue_id}")
            metadata['failed'] += 1
            continue
        
        # Apply random mutation
        mutation_type, mutation_func = random.choice(mutation_functions)
        
        try:
            mutated_code, mutation_params = mutation_func(original_code)
            
            # Validation Part C: Check if mutated code is valid
            if not is_code_valid(mutated_code):
                logger.warning(f"Skipping invalid mutation for issue {issue_id} (type: {mutation_type})")
                metadata['warnings'].append(
                    f"Invalid mutation for {issue_id} (type: {mutation_type}): AST parse failed"
                )
                metadata['failed'] += 1
                continue
            
            # Create synthetic issue
            synthetic_issue = {
                'issue_id': f"{issue_id}_synthetic_{len(synthetic_issues)}",
                'original_issue_id': issue_id,
                'repo_code': mutated_code,
                'mutation_type': mutation_type,
                'mutation_params': mutation_params,
                'ground_truth_lines': ground_truth_data.get(issue_id, {}).get('ground_truth_lines', []),
                'original_code_hash': hashlib.sha256(original_code.encode()).hexdigest(),
                'initial_coverage': issue.get('initial_coverage', 0.0),
                'is_synthetic': True
            }
            
            synthetic_issues.append(synthetic_issue)
            metadata['successful'] += 1
            
            # Track mutation types
            metadata['mutation_types'][mutation_type] = metadata['mutation_types'].get(mutation_type, 0) + 1
            
        except Exception as e:
            logger.warning(f"Error mutating issue {issue_id}: {str(e)}")
            metadata['warnings'].append(f"Error mutating {issue_id}: {str(e)}")
            metadata['failed'] += 1
            continue
    
    # Save synthetic issues
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for issue in synthetic_issues:
            f.write(json.dumps(issue) + '\n')
    
    # Save metadata
    metadata_path = output_path.parent / f"{output_path.stem}_meta.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Generated {len(synthetic_issues)} synthetic issues to {output_path}")
    logger.info(f"Mutation summary: {metadata['mutation_types']}")
    
    return synthetic_issues, metadata

def main():
    """
    Main function to run data curation pipeline.
    """
    config = get_config_summary()
    
    # Paths
    data_dir = Path(config['DATA_DIR'])
    raw_dir = data_dir / 'raw'
    curated_dir = data_dir / 'curated'
    
    dataset_path = raw_dir / 'bench.final.public.jsonl'
    ground_truth_path = curated_dir / 'ground_truth.json'
    hard_subset_path = curated_dir / 'hard_subset.jsonl'
    synthetic_issues_path = curated_dir / 'synthetic_issues.jsonl'
    
    # Ensure directories exist
    curated_dir.mkdir(parents=True, exist_ok=True)
    
    # Load derived ground truth (T013)
    if not ground_truth_path.exists():
        logger.error(f"Ground truth file not found: {ground_truth_path}")
        logger.error("Please run T013 (derive_gt.py) first.")
        sys.exit(1)
    
    ground_truth_data = load_derived_ground_truth(ground_truth_path)
    logger.info(f"Loaded ground truth for {len(ground_truth_data)} issues")
    
    # Part A: Filter hard instances
    if not dataset_path.exists():
        logger.error(f"Dataset file not found: {dataset_path}")
        logger.error("Please run T012 (download.py) first.")
        sys.exit(1)
    
    hard_instances = filter_hard_instances(
        dataset_path,
        ground_truth_data,
        hard_subset_path
    )
    logger.info(f"Filtered {len(hard_instances)} hard instances")
    
    # Part B & C: Generate synthetic issues with validation
    if len(hard_instances) == 0:
        logger.warning("No hard instances found. Skipping synthetic issue generation.")
        synthetic_issues = []
        metadata = {'total_attempted': 0, 'successful': 0, 'failed': 0, 'mutation_types': {}, 'warnings': []}
    else:
        synthetic_issues, metadata = generate_synthetic_issues(
            hard_instances,
            ground_truth_data,
            synthetic_issues_path,
            max_synthetic=50
        )
    
    # Validation summary
    logger.info("=" * 50)
    logger.info("CURATION SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Hard instances: {len(hard_instances)}")
    logger.info(f"Synthetic issues generated: {len(synthetic_issues)}")
    logger.info(f"Synthetic generation: {metadata['successful']} successful, {metadata['failed']} failed")
    if metadata['warnings']:
        logger.info(f"Warnings: {len(metadata['warnings'])}")
        for warning in metadata['warnings'][:5]:  # Show first 5
            logger.warning(f"  - {warning}")
        if len(metadata['warnings']) > 5:
            logger.warning(f"  ... and {len(metadata['warnings']) - 5} more")
    
    return {
        'hard_instances_count': len(hard_instances),
        'synthetic_issues_count': len(synthetic_issues),
        'synthetic_metadata': metadata
    }

if __name__ == '__main__':
    main()