import json
import random
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
import sys
import os

# Ensure imports work relative to project root if run as script
if __name__ == "__main__":
    # Add parent to path if running directly
    sys.path.insert(0, str(Path(__file__).parent.parent))

from data.fetch_utils import DataFetchError

def filter_prompts_with_min_traces(prompts: List[Dict[str, Any]], min_traces: int = 4) -> List[Dict[str, Any]]:
    """
    Filter prompts to keep only those with at least `min_traces` distinct annotated reasoning traces.
    
    Args:
        prompts: List of prompt dictionaries, each containing a 'rationales' or 'responses' key.
        min_traces: Minimum number of distinct traces required.
        
    Returns:
        List of filtered prompts.
    """
    filtered = []
    for p in prompts:
        # Check for 'rationales' or 'responses' key
        traces = p.get("rationales") or p.get("responses") or []
        if len(traces) >= min_traces:
            filtered.append(p)
    return filtered

def simulate_context_split(prompt_data: Dict[str, Any], seed: Optional[int] = None) -> Tuple[Dict[str, Any], bool]:
    """
    Randomly sample 1 rationale as "privileged context" c, detect and re-sample if identical to unselected rationales.
    
    FR-002: Privileged context selection.
    Edge Case: If all rationales are identical, re-sampling loop will detect this and return False to indicate failure.
    
    Args:
        prompt_data: A single prompt dictionary containing 'rationales' or 'responses'.
        seed: Optional random seed for reproducibility.
        
    Returns:
        Tuple of (modified_prompt_data, success_flag).
        modified_prompt_data contains:
            - 'privileged_context': the selected rationale string
            - 'target_rationales': list of remaining rationale strings
            - 'original_id': prompt id
        success_flag: True if a valid split was found, False if all rationales were identical.
    """
    if seed is not None:
        random.seed(seed)
        
    traces = prompt_data.get("rationales") or prompt_data.get("responses") or []
    
    if len(traces) < 2:
        # Cannot split if less than 2 traces
        return prompt_data, False
        
    max_attempts = 100
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        
        # Randomly select index for privileged context
        priv_idx = random.randint(0, len(traces) - 1)
        privileged = traces[priv_idx]
        
        # Collect unselected rationales
        target_indices = [i for i in range(len(traces)) if i != priv_idx]
        target_rationales = [traces[i] for i in target_indices]
        
        # Check for identical content
        # If privileged context is identical to ANY unselected rationale, re-sample
        is_identical = False
        for target in target_rationales:
            if privileged == target:
                is_identical = True
                break
                
        if not is_identical:
            # Valid split found
            result = {
                "original_id": prompt_data.get("id", prompt_data.get("prompt_id", str(attempt))),
                "privileged_context": privileged,
                "target_rationales": target_rationales,
                "all_rationales": traces
            }
            return result, True
    
    # If we exhaust attempts, it likely means all rationales are identical
    return prompt_data, False

def process_and_split_dataset(
    input_file: Path, 
    output_file: Path, 
    min_traces: int = 4,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Main processing pipeline:
    1. Load dataset from input_file (JSON format)
    2. Filter prompts with >= min_traces
    3. Simulate context split for each valid prompt
    4. Write output to output_file
    
    Args:
        input_file: Path to input JSON file containing raw prompts.
        output_file: Path to output JSON file for context splits.
        min_traces: Minimum traces required (default 4 per FR-016).
        seed: Random seed for reproducibility.
        
    Returns:
        Dictionary with statistics about the processing.
    """
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
        
    # Load data
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # Ensure data is a list
    if isinstance(data, dict):
        if "data" in data:
            data = data["data"]
        elif "prompts" in data:
            data = data["prompts"]
        else:
            # Assume the dict itself is a single item or list of items in values
            data = list(data.values())
            
    if not isinstance(data, list):
        data = [data]
        
    # Filter
    filtered_prompts = filter_prompts_with_min_traces(data, min_traces)
    
    splits = []
    failed_count = 0
    
    for i, prompt in enumerate(filtered_prompts):
        # Use a deterministic seed per prompt for reproducibility if global seed is set
        local_seed = seed + i if seed is not None else None
        
        split_result, success = simulate_context_split(prompt, local_seed)
        
        if success:
            splits.append(split_result)
        else:
            failed_count += 1
            
    # Write output
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        "metadata": {
            "total_input": len(data),
            "filtered_input": len(filtered_prompts),
            "successful_splits": len(splits),
            "failed_splits": failed_count,
            "min_traces": min_traces,
            "seed": seed
        },
        "splits": splits
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
        
    return output_data["metadata"]

def main():
    """
    Entry point for running the context simulator as a standalone script.
    Expects input from data/ultrafeedback_dolly_filtered.json (generated by T016)
    and writes to data/context_splits.json.
    """
    # Default paths
    input_path = Path("data/ultrafeedback_dolly_filtered.json")
    output_path = Path("data/context_splits.json")
    
    # Allow override via environment or args
    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])
        
    print(f"Processing: {input_path} -> {output_path}")
    
    try:
        stats = process_and_split_dataset(input_path, output_path, min_traces=4, seed=42)
        print(f"Completed successfully.")
        print(f"  Input prompts: {stats['total_input']}")
        print(f"  Filtered (>=4 traces): {stats['filtered_input']}")
        print(f"  Successful splits: {stats['successful_splits']}")
        print(f"  Failed (identical rationales): {stats['failed_splits']}")
        
        if stats['successful_splits'] == 0:
            print("WARNING: No valid splits generated. Check data quality.")
            
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR during processing: {e}")
        raise

if __name__ == "__main__":
    main()