"""
Stratified sampling module for code functions.

Implements stratified sampling based on function length (LOC) strata:
- Stratum 1: 0-10 LOC
- Stratum 2: 11-50 LOC
- Stratum 3: 51+ LOC

Produces:
- data/processed/validated_functions.jsonl: Full validated set
- data/processed/pilot_sample.jsonl: Pilot sample of 50 functions
- data/processed/functions.jsonl: Final sample of 200 functions
"""

import json
import random
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_error


@dataclass
class Stratum:
    """Represents a stratum for stratified sampling."""
    name: str
    min_loc: int
    max_loc: int
    target_count: int


def count_lines(code: str) -> int:
    """Count lines of code in a function."""
    return len([line for line in code.strip().split('\n') if line.strip()])


def assign_stratum(code: str) -> str:
    """Assign a function to a stratum based on line count."""
    loc = count_lines(code)
    if loc <= 10:
        return "short"
    elif loc <= 50:
        return "medium"
    else:
        return "long"


def load_validated_functions(input_path: str) -> List[Dict[str, Any]]:
    """Load validated functions from JSONL file."""
    functions = []
    with open(input_path, 'r') as f:
        for line in f:
            if line.strip():
                functions.append(json.loads(line))
    return functions


def stratified_sample(
    functions: List[Dict[str, Any]], 
    strata: List[Stratum],
    total_sample_size: int
) -> List[Dict[str, Any]]:
    """
    Perform stratified sampling on functions.
    
    Args:
        functions: List of function dictionaries
        strata: List of stratum definitions
        total_sample_size: Total number of samples to draw
        
    Returns:
        List of sampled functions
    """
    # Group functions by stratum
    stratum_groups: Dict[str, List[Dict[str, Any]]] = {s.name: [] for s in strata}
    
    for func in functions:
        stratum_name = assign_stratum(func.get('code', ''))
        if stratum_name in stratum_groups:
            stratum_groups[stratum_name].append(func)
    
    # Calculate sample sizes per stratum (proportional)
    total_in_pool = sum(len(v) for v in stratum_groups.values())
    if total_in_pool == 0:
        return []
    
    sampled_functions = []
    
    for stratum in strata:
        group = stratum_groups.get(stratum.name, [])
        if not group:
            continue
        
        # Calculate proportional sample size
        proportion = len(group) / total_in_pool
        sample_size = max(1, int(proportion * total_sample_size))
        
        # Ensure we don't exceed available functions
        sample_size = min(sample_size, len(group))
        
        # Random sample from this stratum
        sample = random.sample(group, sample_size)
        sampled_functions.extend(sample)
    
    return sampled_functions


def run_sampling(input_path: str, output_dir: str) -> Dict[str, Any]:
    """
    Run the full sampling workflow.
    
    Args:
        input_path: Path to preprocessed functions JSONL
        output_dir: Directory for output files
        
    Returns:
        Dictionary with sampling statistics
    """
    logger = get_logger("sample")
    log_stage_start(logger, "sampling", "Starting stratified sampling")
    
    output_path = Path(output_dir)
    
    # Define strata
    strata = [
        Stratum(name="short", min_loc=0, max_loc=10, target_count=0),
        Stratum(name="medium", min_loc=11, max_loc=50, target_count=0),
        Stratum(name="long", min_loc=51, max_loc=float('inf'), target_count=0)
    ]
    
    # Load functions
    functions = load_validated_functions(input_path)
    logger.info(f"Loaded {len(functions)} functions for sampling")
    
    # Generate pilot sample (50 functions)
    pilot_sample = stratified_sample(functions, strata, 50)
    pilot_path = output_path / "pilot_sample.jsonl"
    with open(pilot_path, 'w') as f:
        for func in pilot_sample:
            f.write(json.dumps(func) + '\n')
    logger.info(f"Generated pilot sample: {len(pilot_sample)} functions")
    
    # Generate full validated functions list (output of T014b)
    validated_path = output_path / "validated_functions.jsonl"
    with open(validated_path, 'w') as f:
        for func in functions:
            f.write(json.dumps(func) + '\n')
    logger.info(f"Saved validated functions: {len(functions)} functions")
    
    # Generate final sample (200 functions)
    final_sample = stratified_sample(functions, strata, 200)
    final_path = output_path / "functions.jsonl"
    with open(final_path, 'w') as f:
        for func in final_sample:
            f.write(json.dumps(func) + '\n')
    logger.info(f"Generated final sample: {len(final_sample)} functions")
    
    log_stage_complete(logger, "sampling", "Sampling completed")
    
    return {
        "total_functions": len(functions),
        "pilot_sample_size": len(pilot_sample),
        "final_sample_size": len(final_sample),
        "output_files": [
            str(pilot_path),
            str(validated_path),
            str(final_path)
        ]
    }


def main():
    """Entry point for command-line execution."""
    if len(sys.argv) < 3:
        print("Usage: python -m data.sample <input_path> <output_dir>")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_dir = sys.argv[2]
    
    try:
        result = run_sampling(input_path, output_dir)
        print(f"Sampling completed: {result}")
        sys.exit(0)
    except Exception as e:
        print(f"Sampling failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
