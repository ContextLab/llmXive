import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

from src.config import get_config
from src.utils.logging import log_exclusion

# Configure logging for this module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_linked_data(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Load the linked data produced by T010 (src/data/linking.py).
    Expects the output file: data/processed/linked_data.json
    """
    paths = config.get('paths', {})
    input_path = Path(paths.get('linked_data', 'data/processed/linked_data.json'))
    
    if not input_path.exists():
        raise FileNotFoundError(f"Linked data file not found at {input_path}. "
                                "Please ensure T010 (linking.py) has been executed successfully.")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.info(f"Loaded {len(data)} records from linked data.")
    return data

def filter_false_memory_candidates(data: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Implements FR-005: False Memory Pre-filtering Logic.
    
    Criteria for inclusion as a candidate false memory:
    1. Transcript Presence: The record must have valid recall/transcript data.
       (Indicated by 'transcript' key being present and non-empty).
    2. VG Absence: The object in question must NOT be present in the Visual Genome
       ground truth for that image (indicating it was a false memory).
       (Indicated by 'vg_present' being False or missing).
    
    Records failing these criteria are excluded and logged.
    """
    candidates = []
    excluded_count = 0
    
    for record in data:
        # Check Criterion 1: Transcript Presence
        transcript = record.get('transcript')
        if not transcript or not isinstance(transcript, str) or transcript.strip() == "":
            reason = "Missing or empty transcript"
            log_exclusion(record.get('id', 'unknown'), reason, config)
            excluded_count += 1
            continue
        
        # Check Criterion 2: VG Absence (False Memory Indicator)
        # We assume the linking step added a 'vg_present' boolean.
        # If it's False, the object was mentioned in recall but not in VG.
        vg_present = record.get('vg_present', True)
        
        if vg_present:
            reason = "Object present in Visual Genome (True Memory)"
            log_exclusion(record.get('id', 'unknown'), reason, config)
            excluded_count += 1
            continue
        
        # If passed both checks, it's a candidate
        candidates.append(record)
    
    logger.info(f"Filtering complete. Included: {len(candidates)}, Excluded: {excluded_count}")
    return candidates

def save_candidates(candidates: List[Dict[str, Any]], config: Dict[str, Any]) -> Path:
    """
    Saves the filtered candidates to the specified output path.
    Output: data/processed/candidate_false_memories.json
    """
    paths = config.get('paths', {})
    output_path_str = paths.get('candidate_false_memories', 'data/processed/candidate_false_memories.json')
    output_path = Path(output_path_str)
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(candidates, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved {len(candidates)} candidates to {output_path}")
    return output_path

def main():
    """
    Main entry point for the preprocessing task (T015).
    Reads linked data, applies FR-005 filters, and writes candidates.
    """
    try:
        config = get_config()
        logger.info("Starting false-memory pre-filtering (T015)...")
        
        # 1. Load Linked Data (Output of T010)
        linked_data = load_linked_data(config)
        
        # 2. Apply Filtering Logic (FR-005)
        candidates = filter_false_memory_candidates(linked_data, config)
        
        # 3. Save Results
        output_path = save_candidates(candidates, config)
        
        logger.info(f"T015 completed successfully. Output: {output_path}")
        return 0
        
    except Exception as e:
        logger.error(f"T015 failed with error: {e}")
        raise

if __name__ == "__main__":
    main()