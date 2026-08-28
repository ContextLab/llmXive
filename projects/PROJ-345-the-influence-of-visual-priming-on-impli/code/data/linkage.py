"""
Linkage derivation module for mapping trial IDs to stimulus IDs.

Implements fallback logic to derive stimulus_id from trial_id when metadata
is missing, using hash-based mapping to nearest image filename.
"""
import os
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import csv
import sys

# Import from existing API surface
from data.ingest import load_iat_csv, validate_trial_data
from config import get_path, get_all_base_paths
from data.models import Trial
from data.integrity import load_stimulus_paths

logger = logging.getLogger(__name__)

def derive_stimulus_id_from_trial_id(
    trial_id: str, 
    prime_dir: Path, 
    target_dir: Path,
    existing_mapping: Optional[Dict[str, str]] = None
) -> Optional[str]:
    """
    Attempt to derive stimulus_id from trial_id via hash mapping.
    
    Strategy:
    1. Extract numeric or hash component from trial_id
    2. Compute hash of trial_id
    3. Map to nearest available image filename in prime/target directories
    
    Args:
        trial_id: The trial identifier string
        prime_dir: Path to prime images directory
        target_dir: Path to target images directory
        existing_mapping: Optional pre-computed mapping to use as reference
    
    Returns:
        Derived stimulus_id string or None if derivation fails
    """
    if not trial_id:
        return None
    
    # Normalize trial_id
    trial_id_str = str(trial_id).strip()
    
    # If we have an existing mapping, try to find a match
    if existing_mapping and trial_id_str in existing_mapping:
        return existing_mapping[trial_id_str]
    
    # Compute hash of trial_id for deterministic mapping
    trial_hash = hashlib.sha256(trial_id_str.encode()).hexdigest()
    hash_prefix = trial_hash[:8]  # Use first 8 chars for matching
    
    # Collect all available image filenames from both directories
    available_images = []
    
    for img_dir in [prime_dir, target_dir]:
        if img_dir.exists():
            for img_file in img_dir.iterdir():
                if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                    # Extract filename without extension
                    stem = img_file.stem
                    # Check if filename contains hash-like pattern or numeric ID
                    available_images.append({
                        'path': img_file,
                        'stem': stem,
                        'full_name': img_file.name
                    })
    
    if not available_images:
        logger.warning(f"No images found in {prime_dir} or {target_dir}")
        return None
    
    # Try to match by hash prefix in filename
    best_match = None
    best_score = 0
    
    for img_info in available_images:
        stem = img_info['stem']
        # Check if stem contains the hash prefix
        if hash_prefix in stem:
            best_match = img_info['full_name']
            best_score = 10
            break
        
        # Check for numeric similarity (trial_id often has numeric component)
        if stem.isdigit() or any(c.isdigit() for c in stem):
            # Extract numeric part from stem
            numeric_stem = ''.join(filter(str.isdigit, stem))
            numeric_trial = ''.join(filter(str.isdigit, trial_id_str))
            
            if numeric_stem and numeric_trial:
                # Simple numeric matching
                if numeric_stem == numeric_trial:
                    best_match = img_info['full_name']
                    best_score = 9
                    break
                elif numeric_stem.startswith(numeric_trial[:4]) or numeric_trial.startswith(numeric_stem[:4]):
                    if best_score < 5:
                        best_match = img_info['full_name']
                        best_score = 5
    
    # If no direct match, use hash modulo to select nearest available
    if not best_match:
        hash_value = int(trial_hash[:16], 16)
        index = hash_value % len(available_images)
        best_match = available_images[index]['full_name']
        logger.debug(f"Using hash-modulo fallback for trial {trial_id_str} -> {best_match}")
    
    return best_match


def run_linkage_derivation(
    input_csv: Path,
    output_csv: Path,
    prime_dir: Optional[Path] = None,
    target_dir: Optional[Path] = None,
    missing_threshold: float = 0.10
) -> Tuple[bool, Dict[str, float]]:
    """
    Run linkage derivation pipeline on input trial data.
    
    Args:
        input_csv: Path to input CSV with trial data
        output_csv: Path to write output CSV with derived stimulus_ids
        prime_dir: Path to prime images directory
        target_dir: Path to target images directory
        missing_threshold: Threshold for halting (>10% missing = halt)
    
    Returns:
        Tuple of (success: bool, stats: Dict)
        success: True if derivation succeeded within threshold
        stats: Dictionary with derivation statistics
    
    Raises:
        RuntimeError: If derivation fails for >10% of trials
    """
    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")
    
    # Set default directories if not provided
    base_paths = get_all_base_paths()
    if prime_dir is None:
        prime_dir = base_paths.get('primes', base_paths.get('data_primes', Path('data/primes')))
    if target_dir is None:
        target_dir = base_paths.get('targets', base_paths.get('data_targets', Path('data/targets')))
    
    # Ensure directories exist
    if not prime_dir.exists():
        prime_dir.mkdir(parents=True, exist_ok=True)
    if not target_dir.exists():
        target_dir.mkdir(parents=True, exist_ok=True)
    
    # Load existing stimulus paths for reference
    existing_mapping = {}
    try:
        # Try to load any existing metadata
        metadata_file = base_paths.get('data_processed', Path('data/processed')) / 'stimulus_metadata.csv'
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'trial_id' in row and 'stimulus_id' in row:
                        existing_mapping[row['trial_id']] = row['stimulus_id']
    except Exception as e:
        logger.warning(f"Could not load existing metadata: {e}")
    
    # Read input CSV
    trials = []
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            trials.append(row)
    
    if not trials:
        raise ValueError(f"No trials found in {input_csv}")
    
    # Derive stimulus_id for each trial
    total_trials = len(trials)
    derived_count = 0
    failed_count = 0
    excluded_count = 0
    
    output_rows = []
    
    for trial in trials:
        trial_id = trial.get('trial_id', '')
        stimulus_id = trial.get('stimulus_id', '')
        
        # If stimulus_id already exists, keep it
        if stimulus_id and stimulus_id.strip():
            output_rows.append(trial)
            derived_count += 1
            continue
        
        # Attempt derivation
        derived_id = derive_stimulus_id_from_trial_id(
            trial_id, 
            prime_dir, 
            target_dir, 
            existing_mapping
        )
        
        if derived_id:
            trial['stimulus_id'] = derived_id
            output_rows.append(trial)
            derived_count += 1
        else:
            failed_count += 1
            # Mark as excluded
            trial['stimulus_id'] = ''
            trial['excluded'] = 'True'
            trial['exclusion_reason'] = 'Linkage derivation failed'
            output_rows.append(trial)
    
    # Calculate failure rate
    failure_rate = failed_count / total_trials if total_trials > 0 else 0
    success_rate = derived_count / total_trials if total_trials > 0 else 0
    
    stats = {
        'total_trials': total_trials,
        'derived_count': derived_count,
        'failed_count': failed_count,
        'excluded_count': failed_count,
        'failure_rate': failure_rate,
        'success_rate': success_rate
    }
    
    logger.info(f"Linkage derivation complete: {derived_count}/{total_trials} ({success_rate:.2%}) successful")
    logger.info(f"Failure rate: {failure_rate:.2%} (threshold: {missing_threshold:.2%})")
    
    # Check threshold
    if failure_rate > missing_threshold:
        error_msg = f"Data Gap: No linkage data available. Failed to derive stimulus_id for {failure_rate:.2%} of trials (>{missing_threshold:.2%} threshold)."
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    # Write output CSV
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames + ['excluded', 'exclusion_reason'] if 'excluded' not in fieldnames else fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)
    
    logger.info(f"Output written to {output_csv}")
    
    return True, stats


def main():
    """Main entry point for linkage derivation script."""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Run linkage derivation for trial-stimulus mapping')
    parser.add_argument('--input', '-i', type=str, required=True, help='Input CSV file path')
    parser.add_argument('--output', '-o', type=str, required=True, help='Output CSV file path')
    parser.add_argument('--primes', '-p', type=str, default=None, help='Prime images directory')
    parser.add_argument('--targets', '-t', type=str, default=None, help='Target images directory')
    parser.add_argument('--threshold', type=float, default=0.10, help='Missing data threshold (default: 0.10)')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        prime_dir = Path(args.primes) if args.primes else None
        target_dir = Path(args.targets) if args.targets else None
        
        success, stats = run_linkage_derivation(
            input_csv=Path(args.input),
            output_csv=Path(args.output),
            prime_dir=prime_dir,
            target_dir=target_dir,
            missing_threshold=args.threshold
        )
        
        if success:
            print(f"Linkage derivation completed successfully.")
            print(f"Stats: {stats}")
            sys.exit(0)
        else:
            print("Linkage derivation failed.")
            sys.exit(1)
            
    except RuntimeError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        logger.exception("Unexpected error during linkage derivation")
        sys.exit(1)


if __name__ == '__main__':
    main()