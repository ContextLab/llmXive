"""
Task T036: Validate Dataset Statistics for US1

This module validates that the dataset generation process for N=10..500
produces a statistically representative sample of constraint types.

Checks:
1. Distribution of puzzle types (Sudoku vs. Pathfinding) matches intended ratio (balanced).
2. Complexity scaling is continuous across N=10..500.

Outputs:
- Prints validation results to stdout.
- Writes detailed report to data/processed/statistics_validation.json
"""
import json
import os
import sys
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Container for validation results."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)

def load_dataset_metadata(data_dir: Path) -> List[Dict[str, Any]]:
    """
    Load metadata from all puzzle files in the data directory.
    
    Args:
        data_dir: Path to the data/raw directory containing puzzle files.
        
    Returns:
        List of metadata dictionaries for each puzzle.
    """
    metadata = []
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    
    for file_path in data_dir.glob("*.json"):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                # Extract key fields for validation
                meta = {
                    'filename': file_path.name,
                    'n': data.get('n'),
                    'type': data.get('type'),
                    'constraints': data.get('constraints', []),
                    'is_valid': data.get('is_valid', False)
                }
                metadata.append(meta)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Skipping malformed file {file_path.name}: {e}")
            
    return metadata

def validate_type_distribution(metadata: List[Dict[str, Any]], tolerance: float = 0.1) -> ValidationResult:
    """
    Validate that the distribution of puzzle types matches the intended ratio.
    
    Args:
        metadata: List of puzzle metadata dictionaries.
        tolerance: Allowed deviation from the expected 50/50 ratio.
        
    Returns:
        ValidationResult with type distribution analysis.
    """
    if not metadata:
        return ValidationResult(is_valid=False, errors=["No metadata found"])
        
    type_counts = {}
    for item in metadata:
        puzzle_type = item.get('type', 'unknown')
        type_counts[puzzle_type] = type_counts.get(puzzle_type, 0) + 1
        
    total = len(metadata)
    expected_ratio = 0.5  # Balanced: 50% each
    
    errors = []
    warnings = []
    
    logger.info(f"Total puzzles: {total}")
    for p_type, count in type_counts.items():
        ratio = count / total
        logger.info(f"Type '{p_type}': {count} ({ratio:.2%})")
        
        # Check if ratio is within tolerance of expected (assuming 2 types)
        if len(type_counts) == 2:
            if abs(ratio - expected_ratio) > tolerance:
                errors.append(f"Type '{p_type}' ratio {ratio:.2%} deviates significantly from expected {expected_ratio:.0%} (tolerance: {tolerance:.0%})")
        elif len(type_counts) > 2:
            # For more than 2 types, check if any dominant type exceeds 60%
            if ratio > 0.6:
                warnings.append(f"Type '{p_type}' dominates with {ratio:.2%}")
                
    is_valid = len(errors) == 0
    return ValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        stats={'type_counts': type_counts, 'total': total}
    )

def validate_complexity_scaling(metadata: List[Dict[str, Any]]) -> ValidationResult:
    """
    Validate that complexity scaling is continuous across N=10..500.
    
    Args:
        metadata: List of puzzle metadata dictionaries.
        
    Returns:
        ValidationResult with complexity scaling analysis.
    """
    if not metadata:
        return ValidationResult(is_valid=False, errors=["No metadata found"])
        
    # Extract N values
    n_values = [item.get('n') for item in metadata if item.get('n') is not None]
    
    if not n_values:
        return ValidationResult(is_valid=False, errors=["No 'n' values found in metadata"])
        
    # Define expected N range
    expected_range = list(range(10, 501))  # 10 to 500 inclusive
    n_set = set(n_values)
    expected_set = set(expected_range)
    
    missing_n = sorted(expected_set - n_set)
    extra_n = sorted(n_set - expected_set)
    
    errors = []
    warnings = []
    
    # Check for missing N values (continuity)
    if missing_n:
        # Allow some gaps but flag significant ones
        gaps = []
        for i in range(len(expected_range) - 1):
            if expected_range[i] not in n_set and expected_range[i+1] not in n_set:
                gaps.append((expected_range[i], expected_range[i+1]))
                
        if len(gaps) > 5:
            errors.append(f"Significant gaps in complexity scaling found: {gaps[:10]}...")
        elif len(gaps) > 0:
            warnings.append(f"Minor gaps in complexity scaling found: {gaps}")
            
    # Check for N values outside expected range
    if extra_n:
        warnings.append(f"Found N values outside expected range (10-500): {extra_n}")
        
    # Check distribution of N values
    n_counts = {}
    for n in n_values:
        n_counts[n] = n_counts.get(n, 0) + 1
        
    # Ensure at least some representation at each complexity level
    min_expected_per_level = 1
    underrepresented = [n for n in expected_set if n not in n_set or n_counts.get(n, 0) < min_expected_per_level]
    
    if len(underrepresented) > 10:
        warnings.append(f"Many N values have insufficient representation: {underrepresented[:10]}...")
        
    is_valid = len(errors) == 0
    return ValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        stats={'n_counts': n_counts, 'min_n': min(n_values), 'max_n': max(n_values), 'unique_n': len(n_set)}
    )

def main():
    """Main entry point for dataset statistics validation."""
    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent
    data_raw_dir = project_root / "data" / "raw"
    data_processed_dir = project_root / "data" / "processed"
    output_file = data_processed_dir / "statistics_validation.json"
    
    # Ensure output directory exists
    data_processed_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting dataset statistics validation for {data_raw_dir}")
    
    try:
        # Load metadata
        metadata = load_dataset_metadata(data_raw_dir)
        logger.info(f"Loaded metadata for {len(metadata)} puzzles")
        
        # Validate type distribution
        type_result = validate_type_distribution(metadata)
        logger.info(f"Type distribution validation: {'PASSED' if type_result.is_valid else 'FAILED'}")
        
        # Validate complexity scaling
        scaling_result = validate_complexity_scaling(metadata)
        logger.info(f"Complexity scaling validation: {'PASSED' if scaling_result.is_valid else 'FAILED'}")
        
        # Aggregate results
        overall_valid = type_result.is_valid and scaling_result.is_valid
        all_errors = type_result.errors + scaling_result.errors
        all_warnings = type_result.warnings + scaling_result.warnings
        
        report = {
            'timestamp': str(Path(output_file).parent), # Placeholder for actual timestamp
            'dataset_path': str(data_raw_dir),
            'overall_valid': overall_valid,
            'type_distribution': {
                'valid': type_result.is_valid,
                'errors': type_result.errors,
                'warnings': type_result.warnings,
                'stats': type_result.stats
            },
            'complexity_scaling': {
                'valid': scaling_result.is_valid,
                'errors': scaling_result.errors,
                'warnings': scaling_result.warnings,
                'stats': scaling_result.stats
            },
            'summary': {
                'total_errors': len(all_errors),
                'total_warnings': len(all_warnings),
                'errors': all_errors,
                'warnings': all_warnings
            }
        }
        
        # Write report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"Validation report written to {output_file}")
        
        # Print summary
        print("\n=== Dataset Statistics Validation Summary ===")
        print(f"Overall Valid: {overall_valid}")
        print(f"Type Distribution Valid: {type_result.is_valid}")
        print(f"Complexity Scaling Valid: {scaling_result.is_valid}")
        
        if all_errors:
            print("\nErrors:")
            for err in all_errors:
                print(f"  - {err}")
                
        if all_warnings:
            print("\nWarnings:")
            for warn in all_warnings:
                print(f"  - {warn}")
                
        if not overall_valid:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Validation failed with exception: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()