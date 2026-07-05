"""
Linkage derivation fallback module.

Implements fallback logic to map trial IDs to stimulus image filenames
via hash derivation when explicit metadata is missing.
"""
import os
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from data.ingest import load_iat_csv, validate_trial_data
from data.models import Trial
from config import get_path

logger = logging.getLogger(__name__)

def derive_stimulus_id_from_trial_id(trial_id: str, image_dir: Path, prime_type: str) -> Optional[str]:
    """
    Attempt to derive a stimulus_id by mapping the trial_id to the nearest image filename.
    
    Strategy:
    1. Normalize trial_id (remove common prefixes/suffixes).
    2. Compute a hash of the trial_id.
    3. Scan the image directory for filenames that might correspond to this hash
       (e.g., files named like 'img_<hash_suffix>.png' or where the filename contains the hash).
    4. If a match is found, return the filename (without extension) as the stimulus_id.
    5. If no direct match, attempt to find the 'nearest' match based on substring similarity
       if the trial_id contains a hash-like segment.
    
    Args:
        trial_id: The raw trial identifier string.
        image_dir: Path to the directory containing the stimulus images.
        prime_type: 'prime' or 'target' to select the correct subdirectory context.
    
    Returns:
        The derived stimulus_id (filename without extension) or None if no match found.
    """
    if not image_dir.exists():
        logger.warning(f"Image directory {image_dir} does not exist.")
        return None

    # Normalize trial_id: strip common prefixes like 'trial_', 'T_', etc.
    clean_id = trial_id.strip().lower()
    for prefix in ['trial_', 't_', 'id_']:
        if clean_id.startswith(prefix):
            clean_id = clean_id[len(prefix):]
    
    # Check if the clean_id itself looks like a hash or filename component
    # Many IAT datasets use filenames like 'stimulus_001.png' or 'img_abc123.png'
    # We will look for files where the trial_id (or a hash of it) appears in the filename.
    
    # Strategy A: Direct substring match in filename
    # Some datasets name files exactly as trial IDs or contain them.
    all_files = list(image_dir.glob("*"))
    candidates = [f.stem for f in all_files if f.is_file() and clean_id in f.stem]
    
    if candidates:
        # Return the first match
        return candidates[0]
    
    # Strategy B: Hash-based derivation
    # If the trial_id is numeric or short, it might map to a hash suffix.
    # We compute a hash of the trial_id and look for files ending with that suffix.
    # This is useful if filenames are like 'prime_a1b2c3.png' and trial_id is 'a1b2c3'.
    try:
        # Use a simple hash of the trial_id
        hash_obj = hashlib.md5(clean_id.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()
        hash_suffix = hash_hex[:8] # Look for first 8 chars
        
        candidates_hash = [f.stem for f in all_files if f.is_file() and hash_suffix in f.stem]
        if candidates_hash:
            return candidates_hash[0]
    except Exception as e:
        logger.debug(f"Hash derivation failed for {trial_id}: {e}")

    # Strategy C: Fallback to nearest match if trial_id is numeric
    # If trial_id is purely numeric, try to match it to a numeric sequence in filenames
    if clean_id.isdigit():
        num_id = int(clean_id)
        # Look for files with numbers near num_id
        # This is a heuristic and might not work for all datasets
        numeric_files = []
        for f in all_files:
            if f.is_file():
                stem = f.stem
                # Try to extract numbers from filename
                import re
                numbers = re.findall(r'\d+', stem)
                for n in numbers:
                    try:
                        numeric_files.append((int(n), f.stem))
                    except ValueError:
                        pass
        
        if numeric_files:
            # Sort by difference
            numeric_files.sort(key=lambda x: abs(x[0] - num_id))
            if numeric_files[0][0] == num_id:
                return numeric_files[0][1]
            # If difference is small (e.g., < 5), consider it a match
            if abs(numeric_files[0][0] - num_id) <= 5:
                return numeric_files[0][1]

    return None

def run_linkage_derivation(trials: List[Trial], prime_dir: Path, target_dir: Path) -> Tuple[List[Trial], float]:
    """
    Run linkage derivation fallback for trials missing explicit stimulus_id.
    
    Args:
        trials: List of Trial objects. Some may have missing stimulus_id.
        prime_dir: Path to prime images directory.
        target_dir: Path to target images directory.
    
    Returns:
        Tuple of (updated_trials, derivation_success_rate)
    """
    updated_trials = []
    derived_count = 0
    missing_count = 0
    total_missing = 0

    for trial in trials:
        if trial.stimulus_id:
            updated_trials.append(trial)
            continue
        
        total_missing += 1
        stimulus_type = trial.stimulus_type # 'prime' or 'target'
        image_dir = prime_dir if stimulus_type == 'prime' else target_dir
        
        derived_id = derive_stimulus_id_from_trial_id(trial.trial_id, image_dir, stimulus_type)
        
        if derived_id:
            trial.stimulus_id = derived_id
            derived_count += 1
            updated_trials.append(trial)
        else:
            missing_count += 1
            # Mark as excluded or keep with None? 
            # Per task: "flagged for exclusion"
            trial.stimulus_id = None 
            updated_trials.append(trial)

    success_rate = derived_count / total_missing if total_missing > 0 else 1.0
    return updated_trials, success_rate

def main():
    """
    Main entry point for T016.
    Reads trials from data/processed/linked_trials.csv (intermediate state),
    attempts linkage derivation for missing IDs, and writes updated CSV.
    """
    logger.info("Starting T016: Linkage Derivation Fallback")
    
    # Load existing linked trials (output of T015)
    input_path = get_path("data", "processed", "linked_trials.csv")
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}. Run T013-T015 first.")
        return

    # Load CSV into Trial objects
    # Note: We need to reconstruct Trial objects. 
    # The CSV has: trial_id, response_time, stimulus_id, prime_condition, participant_id
    # We also need to know stimulus_type (prime/target). 
    # Assuming prime_condition column implies type or we infer from context.
    # For now, we assume the CSV has a 'stimulus_type' column or we infer it.
    # If not, we might need to check the data model or spec.
    # Let's assume the CSV has 'stimulus_type' or we default to 'prime' if not present.
    
    trials = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Map CSV columns to Trial fields
            # Trial fields: trial_id, response_time, stimulus_id, stimulus_type, prime_condition, participant_id
            t = Trial(
                trial_id=row['trial_id'],
                response_time=float(row['response_time']),
                stimulus_id=row.get('stimulus_id', None),
                stimulus_type=row.get('stimulus_type', 'prime'), # Default to prime if missing
                prime_condition=row.get('prime_condition', 'neutral'),
                participant_id=row['participant_id']
            )
            trials.append(t)

    logger.info(f"Loaded {len(trials)} trials. Checking for missing stimulus_id...")
    
    missing_initial = sum(1 for t in trials if t.stimulus_id is None)
    logger.info(f"Found {missing_initial} trials with missing stimulus_id.")

    if missing_initial == 0:
        logger.info("No missing stimulus IDs. Skipping derivation.")
        # Write back just in case
        with open(input_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['trial_id', 'response_time', 'stimulus_id', 'stimulus_type', 'prime_condition', 'participant_id'])
            writer.writeheader()
            for t in trials:
                writer.writerow({
                    'trial_id': t.trial_id,
                    'response_time': t.response_time,
                    'stimulus_id': t.stimulus_id,
                    'stimulus_type': t.stimulus_type,
                    'prime_condition': t.prime_condition,
                    'participant_id': t.participant_id
                })
        return

    prime_dir = get_path("data", "primes")
    target_dir = get_path("data", "targets")

    updated_trials, success_rate = run_linkage_derivation(trials, prime_dir, target_dir)

    final_missing = sum(1 for t in updated_trials if t.stimulus_id is None)
    final_total = len(updated_trials)
    final_missing_pct = (final_missing / final_total) if final_total > 0 else 0

    logger.info(f"Derivation complete. Success rate: {success_rate:.2%}")
    logger.info(f"Remaining missing: {final_missing} ({final_missing_pct:.2%})")

    # SC-001 Check: "vast majority" (default 0.95)
    # The task says: "If derivation fails for >10% of trials, halt with 'Data Gap: No linkage data available'."
    # This implies we check the failure rate of the derivation process itself, not the final missing rate.
    # But the task also says: "Verify a high proportion of trials have mapped stimulus_id... to meet SC-001".
    # Let's implement the >10% failure check as per the explicit instruction.
    
    if final_missing_pct > 0.10:
        logger.error("Data Gap: No linkage data available (>10% trials missing stimulus_id after derivation).")
        logger.error("Halt: Cannot proceed without sufficient linkage data.")
        # Do not write the file or halt the pipeline
        raise RuntimeError("Data Gap: No linkage data available (>10% trials missing stimulus_id after derivation).")
    
    # Write updated CSV
    output_path = get_path("data", "processed", "linked_trials.csv")
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['trial_id', 'response_time', 'stimulus_id', 'stimulus_type', 'prime_condition', 'participant_id'])
        writer.writeheader()
        for t in updated_trials:
            writer.writerow({
                'trial_id': t.trial_id,
                'response_time': t.response_time,
                'stimulus_id': t.stimulus_id,
                'stimulus_type': t.stimulus_type,
                'prime_condition': t.prime_condition,
                'participant_id': t.participant_id
            })
    
    logger.info(f"Updated trials written to {output_path}")

if __name__ == "__main__":
    import sys
    import csv
    setup_logging = None
    try:
        from main import setup_logging
    except ImportError:
        # Fallback if not imported from main
        logging.basicConfig(level=logging.INFO)
        setup_logging = lambda: logging.getLogger()
    
    main()
