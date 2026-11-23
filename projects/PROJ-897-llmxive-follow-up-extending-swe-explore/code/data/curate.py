import ast
import copy
import hashlib
import json
import logging
import random
import sys
import libcst as cst
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from config import get_path, get_config_summary, DATA_CURATED, DATA_RAW, MIN_SYNTHETIC_ISSUES, HARD_INSTANCE_PERCENTILE, COVERAGE_COLUMN_NAME

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def compute_sha256(data: str) -> str:
    """Compute SHA-256 hash of a string."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def is_code_valid(code: str) -> bool:
    """Check if code is valid Python by attempting to parse it."""
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False

def load_derived_ground_truth() -> List[Dict[str, Any]]:
    """Load the derived ground truth data."""
    path = get_path(DATA_RAW, "swe_explore_with_gt.jsonl")
    if not path.exists():
        raise FileNotFoundError(f"Ground truth file not found at {path}. Run T011 first.")
    
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    return data

def load_hard_subset() -> Set[str]:
    """Load the hard subset and return a set of excluded issue IDs."""
    path = get_path(DATA_CURATED, "hard_subset.jsonl")
    if not path.exists():
        raise FileNotFoundError(f"Hard subset not found at {path}. Run T012 first.")
    
    excluded_ids = set()
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            record = json.loads(line)
            if 'issue_id' in record:
                excluded_ids.add(record['issue_id'])
            elif 'id' in record:
                excluded_ids.add(record['id'])
    return excluded_ids

def mutate_variable_names(tree: cst.Module, mutation_rate: float = 0.3) -> cst.Module:
    """Rename variables in the code tree."""
    class VariableRenamer(cst.CSTTransformer):
        def __init__(self, rate: float):
            self.rate = rate
            self.renamed_vars: Dict[str, str] = {}
        
        def _get_new_name(self, old_name: str) -> str:
            if old_name not in self.renamed_vars:
                self.renamed_vars[old_name] = f"var_{compute_sha256(old_name)[:8]}"
            return self.renamed_vars[old_name]
        
        def leave_Name(self, original_node: cst.Name, updated_node: cst.Name) -> cst.Name:
            if random.random() < self.rate:
                # Skip Python built-ins and keywords
                if not isinstance(original_node.value, str) or original_node.value in dir(__builtins__):
                    return updated_node
                new_name = self._get_new_name(original_node.value)
                return updated_node.with_changes(value=new_name)
            return updated_node

    transformer = VariableRenamer(mutation_rate)
    return tree.visit(transformer)

def remove_comments(tree: cst.Module) -> cst.Module:
    """Remove all comments from the code tree."""
    class CommentRemover(cst.CSTTransformer):
        def leave_Comment(self, original_node: cst.Comment, updated_node: cst.Comment) -> cst.MaybeSentinel:
            return cst.MaybeSentinel.DEFAULT
        
        def leave_EmptyLine(self, original_node: cst.EmptyLine, updated_node: cst.EmptyLine) -> cst.EmptyLine:
            # Keep empty lines but remove their comments
            return updated_node.with_changes(comment=None)
    
    transformer = CommentRemover()
    return tree.visit(transformer)

def reorder_control_flow(tree: cst.Module) -> cst.Module:
    """Reorder control flow statements (if/elif/else blocks) to create ambiguity."""
    class ControlFlowReorderer(cst.CSTTransformer):
        def __init__(self):
            self.swap_chance = 0.5
        
        def leave_If(self, original_node: cst.If, updated_node: cst.If) -> cst.If:
            if random.random() < self.swap_chance and len(updated_node.orelse) > 1:
                # Swap the first two elif/else branches if possible
                if len(updated_node.orelse) >= 2:
                    # This is a simplified reordering; in practice, we'd need more complex logic
                    # to properly handle nested structures
                    pass
            return updated_node

    transformer = ControlFlowReorderer()
    return tree.visit(transformer)

def change_api_signature(tree: cst.Module) -> cst.Module:
    """Modify function signatures to create ambiguity."""
    class SignatureChanger(cst.CSTTransformer):
        def __init__(self):
            self.change_chance = 0.3
        
        def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef) -> cst.FunctionDef:
            if random.random() < self.change_chance:
                # Add a dummy parameter with a default value
                new_params = list(updated_node.params.params)
                new_params.append(
                    cst.Param(
                        name=cst.Name(value="aux_param"),
                        default=cst.SimpleString(value="'_hidden_")
                    )
                )
                return updated_node.with_changes(params=updated_node.params.with_changes(params=tuple(new_params)))
            return updated_node

    transformer = SignatureChanger()
    return tree.visit(transformer)

def apply_mutations(code: str) -> Optional[str]:
    """Apply all mutation types to code and return the result if valid."""
    try:
        tree = cst.parse_module(code)
        
        # Apply mutations in sequence
        tree = mutate_variable_names(tree)
        tree = remove_comments(tree)
        tree = reorder_control_flow(tree)
        tree = change_api_signature(tree)
        
        mutated_code = tree.code
        
        # Validate the mutated code
        if is_code_valid(mutated_code):
            return mutated_code
        else:
            logger.warning("Mutation resulted in invalid code, skipping.")
            return None
    except Exception as e:
        logger.warning(f"Mutation failed with error: {e}, skipping.")
        return None

def generate_synthetic_issues() -> List[Dict[str, Any]]:
    """Generate synthetic ambiguous issues from the non-hard subset."""
    logger.info("Loading ground truth data...")
    gt_data = load_derived_ground_truth()
    
    logger.info("Loading hard subset to identify excluded IDs...")
    excluded_ids = load_hard_subset()
    
    # Filter to non-hard issues
    candidate_pool = [
        item for item in gt_data 
        if item.get('issue_id') not in excluded_ids and item.get('id') not in excluded_ids
    ]
    
    logger.info(f"Candidate pool size: {len(candidate_pool)}")
    logger.info(f"MIN_SYNTHETIC_ISSUES config: {MIN_SYNTHETIC_ISSUES}")
    
    if len(candidate_pool) < MIN_SYNTHETIC_ISSUES:
        logger.warning(f"Candidate pool ({len(candidate_pool)}) is smaller than MIN_SYNTHETIC_ISSUES ({MIN_SYNTHETIC_ISSUES}). Generating all possible mutations.")
    
    synthetic_issues = []
    mutation_count = 0
    
    for item in candidate_pool:
        code = item.get('code', '')
        if not code:
            continue
        
        # Apply mutations
        mutated_code = apply_mutations(code)
        if mutated_code:
            # Create a synthetic issue record
            synthetic_record = copy.deepcopy(item)
            synthetic_record['issue_id'] = f"synthetic_{mutation_count}_{item.get('issue_id', item.get('id', ''))}"
            synthetic_record['code'] = mutated_code
            synthetic_record['is_synthetic'] = True
            synthetic_record['mutation_applied'] = True
            
            # Preserve ground truth lines from original unmutated code
            if 'ground_truth_lines' in item:
                synthetic_record['ground_truth_lines'] = item['ground_truth_lines']
            
            synthetic_issues.append(synthetic_record)
            mutation_count += 1
            
            # Stop if we have enough
            if mutation_count >= MIN_SYNTHETIC_ISSUES:
                break
    
    logger.info(f"Generated {mutation_count} valid synthetic issues.")
    
    if mutation_count == 0:
        raise RuntimeError("No valid synthetic issues generated. Pipeline halted.")
    
    if mutation_count < MIN_SYNTHETIC_ISSUES:
        logger.warning(f"Only generated {mutation_count} synthetic issues, which is less than MIN_SYNTHETIC_ISSUES ({MIN_SYNTHETIC_ISSUES}).")
    
    return synthetic_issues

def main():
    """Main entry point for synthetic issue generation."""
    logger.info("Starting T013: Generate Synthetic Ambiguous Issues")
    
    try:
        synthetic_issues = generate_synthetic_issues()
        
        # Write output
        output_path = get_path(DATA_CURATED, "synthetic_issues.jsonl")
        logger.info(f"Writing synthetic issues to {output_path}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for issue in synthetic_issues:
                f.write(json.dumps(issue) + '\n')
        
        logger.info(f"Successfully wrote {len(synthetic_issues)} synthetic issues to {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to generate synthetic issues: {e}")
        raise

if __name__ == "__main__":
    main()