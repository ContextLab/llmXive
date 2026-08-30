import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from datetime import datetime

# Ensure logging is configured
from utils.logging_config import get_logger, ensure_log_dir
logger = get_logger(__name__)

# Ensure data directories exist
from utils.data_manifest import create_directory_structure

def load_generated_proposals(input_path: str) -> List[Dict[str, Any]]:
    """
    Load generated proposals from a JSONL file.
    
    Args:
        input_path: Path to the generated proposals JSONL file.
        
    Returns:
        List of proposal dictionaries.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Generated proposals file not found: {input_path}")
        
    proposals = []
    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                proposal = json.loads(line)
                proposals.append(proposal)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON on line {line_num}: {e}")
                raise
                
    logger.info(f"Loaded {len(proposals)} proposals from {input_path}")
    return proposals

def validate_two_group_pairing(proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate that proposals follow the strict two-group design (pattern-guided vs baseline).
    
    Args:
        proposals: List of proposal dictionaries.
        
    Returns:
        Dictionary containing validation results.
        
    Raises:
        ValueError: If invalid group assignments are found.
    """
    valid_groups = {'pattern-guided', 'baseline'}
    found_groups = set()
    invalid_entries = []
    
    for idx, proposal in enumerate(proposals):
        group = proposal.get('generation_group')
        if group not in valid_groups:
            invalid_entries.append({
                'index': idx,
                'proposal_id': proposal.get('proposal_id'),
                'found_group': group
            })
        found_groups.add(group)
        
    if invalid_entries:
        error_msg = f"Found {len(invalid_entries)} proposals with invalid groups: {invalid_entries}"
        logger.error(error_msg)
        raise ValueError(error_msg)
        
    if found_groups != valid_groups:
        logger.warning(f"Expected groups {valid_groups}, but found {found_groups}")
        
    logger.info(f"Validation passed. Found groups: {found_groups}")
    return {
        'valid': True,
        'found_groups': list(found_groups),
        'total_proposals': len(proposals)
    }

def strip_metadata_for_evaluation(proposal: Dict[str, Any]) -> Dict[str, Any]:
    """
    Strip sensitive or evaluation-biasing metadata from a proposal.
    
    Keeps only fields needed for expert evaluation:
    - proposal_id (blinded)
    - text (the actual proposal content)
    - generation_group (pattern-guided or baseline)
    - problem_id (for pairing verification)
    
    Args:
        proposal: The full proposal dictionary with metadata.
        
    Returns:
        A stripped dictionary suitable for evaluation.
    """
    # Define fields to keep
    keep_fields = {
        'proposal_id',
        'text',
        'generation_group',
        'problem_id',
        'timestamp'  # Keep timestamp for audit, but not model/version info
    }
    
    stripped = {}
    for key in keep_fields:
        if key in proposal:
            stripped[key] = proposal[key]
            
    # Ensure generation_group is present and valid
    if 'generation_group' not in stripped:
        raise ValueError(f"Proposal {proposal.get('proposal_id')} missing generation_group")
        
    return stripped

def save_proposals_stripped(proposals: List[Dict[str, Any]], output_path: str) -> int:
    """
    Save stripped proposals to a JSONL file.
    
    Args:
        proposals: List of full proposal dictionaries.
        output_path: Path to the output JSONL file.
        
    Returns:
        Number of proposals saved.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    saved_count = 0
    with open(output_path, 'w', encoding='utf-8') as f:
        for proposal in proposals:
            try:
                stripped = strip_metadata_for_evaluation(proposal)
                f.write(json.dumps(stripped, ensure_ascii=False) + '\n')
                saved_count += 1
            except ValueError as e:
                logger.warning(f"Skipping proposal due to metadata error: {e}")
                continue
                
    logger.info(f"Saved {saved_count} stripped proposals to {output_path}")
    return saved_count

def main():
    """
    Main entry point for T026: Save generated proposals with stripped metadata.
    
    Reads from data/results/generated_proposals.jsonl and writes
    to data/results/generated_proposals_stripped.jsonl (or overwrites
    if that's the intended output file per spec).
    
    Per task T026 description: "Save generated proposals to `data/results/generated_proposals.jsonl` 
    with generation metadata (stripped for evaluation)."
    
    This implies we read the raw generation output and write the stripped version 
    to the same path (overwriting) or a specific evaluation path.
    Given the task says "Save ... to data/results/generated_proposals.jsonl", 
    we will read from a temporary raw file if it exists, or assume the previous 
    step wrote to a raw file.
    
    However, looking at T024: "Output: Save to `data/results/generated_proposals.jsonl` with metadata stripped for evaluation."
    This suggests the final output file IS `data/results/generated_proposals.jsonl`.
    
    To avoid data loss, we will:
    1. Check if data/results/generated_proposals.jsonl exists (raw version from T021/022/024).
    2. If it exists, we assume it might be the raw version. We'll rename it to .raw.jsonl.
    3. We'll write the stripped version to data/results/generated_proposals.jsonl.
    
    Wait, T024 says "Output: Save to `data/results/generated_proposals.jsonl` with metadata stripped".
    So T024 should have already done this? But T024 is marked done.
    Let's re-read T026: "Save generated proposals to `data/results/generated_proposals.jsonl` with generation metadata (stripped for evaluation)."
    
    It seems T024 and T026 overlap. T024 says "Ensure strict two-group pairing... Output: Save to...".
    T026 says "Save generated proposals... with generation metadata (stripped)".
    
    Perhaps T024 generated the file with some metadata, and T026 is the final cleanup.
    Or T024 was a validation step and didn't write the final file.
    
    Given the task list, T026 is the one explicitly responsible for the final output.
    We will assume the raw proposals are in `data/results/generated_proposals_raw.jsonl` 
    or we will look for `data/results/generated_proposals.jsonl` and treat it as the input 
    if it exists, then write the stripped version back (overwriting).
    
    To be safe and non-destructive in a real pipeline, we would read from a "raw" input 
    and write to a "stripped" output. But the task explicitly says the output path is 
    `data/results/generated_proposals.jsonl`.
    
    Strategy:
    1. Look for `data/results/generated_proposals_raw.jsonl`. If found, use as input.
    2. If not found, look for `data/results/generated_proposals.jsonl`. If found, assume it's the raw version 
       (from T024) and use it as input, then overwrite it with stripped version.
    3. If neither found, error out.
    """
    # Ensure directory structure exists
    create_directory_structure()
    
    # Define paths
    results_dir = Path("data/results")
    raw_candidates = [
        results_dir / "generated_proposals_raw.jsonl",
        results_dir / "generated_proposals.jsonl"
    ]
    
    input_path = None
    for candidate in raw_candidates:
        if candidate.exists():
            input_path = candidate
            break
            
    if not input_path:
        logger.error("No input file found for proposal stripping.")
        sys.exit(1)
        
    logger.info(f"Using input file: {input_path}")
    
    # Load proposals
    try:
        proposals = load_generated_proposals(str(input_path))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load proposals: {e}")
        sys.exit(1)
        
    # Validate two-group design
    try:
        validation_result = validate_two_group_pairing(proposals)
        logger.info(f"Validation result: {validation_result}")
    except ValueError as e:
        logger.error(f"Two-group validation failed: {e}")
        sys.exit(1)
        
    # If the input was the .jsonl file, we need to handle the overwrite carefully.
    # If input_path is generated_proposals.jsonl, we should read it, process, and write back.
    # If input_path is generated_proposals_raw.jsonl, we write to generated_proposals.jsonl.
    
    output_path = results_dir / "generated_proposals.jsonl"
    
    # If input is the raw file, we write to the main file.
    # If input is the main file, we overwrite it (after reading).
    
    # Save stripped proposals
    count = save_proposals_stripped(proposals, str(output_path))
    
    # Update state
    from utils.update_state import update_state_for_artifact
    try:
        update_state_for_artifact("generated_proposals", str(output_path))
        logger.info("State updated successfully.")
    except Exception as e:
        logger.warning(f"Failed to update state: {e}")
        
    logger.info(f"T026 completed. Saved {count} proposals to {output_path}")

if __name__ == "__main__":
    main()