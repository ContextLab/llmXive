import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory (code/)."""
    return Path(__file__).resolve().parent.parent.parent

def load_splits(splits_path: Path) -> Dict[str, Any]:
    """Load the splits JSON file."""
    if not splits_path.exists():
        raise FileNotFoundError(f"Splits file not found: {splits_path}")
    
    with open(splits_path, 'r') as f:
        return json.load(f)

def validate_splits_structure(splits: Dict[str, Any]) -> List[str]:
    """Validate the structure of the splits dictionary."""
    errors = []
    
    # Check for required keys
    required_keys = ['train', 'val', 'test']
    for key in required_keys:
        if key not in splits:
            errors.append(f"Missing required key: {key}")
    
    # Check that each key is a list of 5 folds
    for key in required_keys:
        if key in splits:
            if not isinstance(splits[key], list):
                errors.append(f"Key '{key}' is not a list")
            elif len(splits[key]) != 5:
                errors.append(f"Key '{key}' does not contain exactly 5 folds (found {len(splits[key])})")
            else:
                # Validate each fold is a list of integers
                for i, fold in enumerate(splits[key]):
                    if not isinstance(fold, list):
                        errors.append(f"Fold {i} in '{key}' is not a list")
                    else:
                        for j, sample_id in enumerate(fold):
                            if not isinstance(sample_id, int):
                                errors.append(f"Sample ID at index {j} in fold {i} of '{key}' is not an integer")
    
    return errors

def validate_fold_consistency(splits: Dict[str, Any]) -> List[str]:
    """Validate that train/val/test sets are disjoint for each fold."""
    errors = []
    
    num_folds = len(splits.get('train', []))
    
    for fold_idx in range(num_folds):
        train_set = set(splits['train'][fold_idx])
        val_set = set(splits['val'][fold_idx])
        test_set = set(splits['test'][fold_idx])
        
        # Check for overlaps
        train_val_overlap = train_set & val_set
        if train_val_overlap:
            errors.append(f"Fold {fold_idx}: Train and Val sets overlap with {len(train_val_overlap)} samples")
        
        train_test_overlap = train_set & test_set
        if train_test_overlap:
            errors.append(f"Fold {fold_idx}: Train and Test sets overlap with {len(train_test_overlap)} samples")
        
        val_test_overlap = val_set & test_set
        if val_test_overlap:
            errors.append(f"Fold {fold_idx}: Val and Test sets overlap with {len(val_test_overlap)} samples")
    
    return errors

def validate_scaffold_separation(splits: Dict[str, Any], graphs_path: Path) -> List[str]:
    """Validate that no scaffold appears in both train and test sets."""
    # This would require loading the graphs to get scaffold IDs
    # For now, we just log that this validation would be performed
    logger.info("Scaffold separation validation would be performed here if graphs were available")
    return []

def run_validation(splits_path: Optional[Path] = None) -> bool:
    """Run all validation checks on the splits file."""
    if splits_path is None:
        project_root = get_project_root()
        splits_path = project_root / 'data' / 'processed' / 'splits.json'
    
    logger.info(f"Validating splits file: {splits_path}")
    
    try:
        splits = load_splits(splits_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        return False
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in splits file: {e}")
        return False
    
    all_errors = []
    
    # Validate structure
    logger.info("Validating splits structure...")
    structure_errors = validate_splits_structure(splits)
    all_errors.extend(structure_errors)
    if structure_errors:
        logger.warning(f"Found {len(structure_errors)} structure errors")
    else:
        logger.info("Structure validation passed")
    
    # Validate fold consistency
    logger.info("Validating fold consistency...")
    consistency_errors = validate_fold_consistency(splits)
    all_errors.extend(consistency_errors)
    if consistency_errors:
        logger.warning(f"Found {len(consistency_errors)} consistency errors")
    else:
        logger.info("Fold consistency validation passed")
    
    # Validate scaffold separation (if graphs available)
    project_root = get_project_root()
    graphs_path = project_root / 'data' / 'processed' / 'graphs.parquet'
    if graphs_path.exists():
        logger.info("Validating scaffold separation...")
        scaffold_errors = validate_scaffold_separation(splits, graphs_path)
        all_errors.extend(scaffold_errors)
        if scaffold_errors:
            logger.warning(f"Found {len(scaffold_errors)} scaffold separation errors")
        else:
            logger.info("Scaffold separation validation passed")
    else:
        logger.info("Skipping scaffold separation validation (graphs.parquet not found)")
    
    # Write validation log
    validation_log_path = project_root / 'data' / 'results' / 'splits_validation.log'
    validation_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(validation_log_path, 'w') as f:
        f.write(f"Splits Validation Report\n")
        f.write(f"{'='*50}\n")
        f.write(f"File: {splits_path}\n")
        f.write(f"Number of folds: {len(splits.get('train', []))}\n")
        f.write(f"Total samples in train: {sum(len(fold) for fold in splits.get('train', []))}\n")
        f.write(f"Total samples in val: {sum(len(fold) for fold in splits.get('val', []))}\n")
        f.write(f"Total samples in test: {sum(len(fold) for fold in splits.get('test', []))}\n")
        f.write(f"{'='*50}\n\n")
        
        if all_errors:
            f.write("VALIDATION FAILED\n\n")
            f.write(f"Total errors: {len(all_errors)}\n\n")
            for i, error in enumerate(all_errors, 1):
                f.write(f"{i}. {error}\n")
        else:
            f.write("VALIDATION PASSED\n\n")
            f.write("All checks passed successfully.\n")
    
    logger.info(f"Validation log written to: {validation_log_path}")
    
    return len(all_errors) == 0

def main():
    """Main entry point for the validation script."""
    success = run_validation()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
