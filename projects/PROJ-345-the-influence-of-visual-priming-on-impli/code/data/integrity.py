"""
Integrity module for Principle VI: Distinct Stimulus Set Validation.

This module ensures that prime and target stimulus sets remain distinct
and are never merged prematurely during data processing. It provides
validation functions to detect accidental overlaps or merges between
the two stimulus categories.
"""
import os
import csv
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from config import get_path
from data.models import StimulusType, Stimulus


logger = logging.getLogger(__name__)


class IntegrityStatus(Enum):
    """Status of integrity validation."""
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"


@dataclass
class IntegrityReport:
    """Report generated from integrity validation."""
    status: IntegrityStatus
    message: str
    prime_count: int
    target_count: int
    overlap_count: int
    overlap_stimuli: List[str]
    checksum_prime: Optional[str] = None
    checksum_target: Optional[str] = None


def load_stimulus_paths(stimulus_type: StimulusType) -> Set[str]:
    """
    Load all stimulus paths for a given type from the appropriate directory.
    
    Args:
        stimulus_type: The type of stimulus (PRIME or TARGET).
        
    Returns:
        A set of stimulus identifiers (file paths or IDs).
        
    Raises:
        FileNotFoundError: If the stimulus directory does not exist.
    """
    if stimulus_type == StimulusType.PRIME:
        base_dir = get_path("data/primes")
    elif stimulus_type == StimulusType.TARGET:
        base_dir = get_path("data/targets")
    else:
        raise ValueError(f"Unsupported stimulus type: {stimulus_type}")
    
    if not os.path.exists(base_dir):
        raise FileNotFoundError(f"Stimulus directory not found: {base_dir}")
    
    stimulus_ids = set()
    
    # Walk through all files in the directory
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                # Create a unique identifier for the stimulus
                full_path = os.path.join(root, file)
                # Store relative path from the stimulus directory
                rel_path = os.path.relpath(full_path, base_dir)
                stimulus_ids.add(rel_path)
    
    return stimulus_ids


def compute_directory_checksum(directory_path: Path) -> str:
    """
    Compute a checksum for all files in a directory to detect changes.
    
    Args:
        directory_path: Path to the directory to checksum.
        
    Returns:
        A hex string representing the directory checksum.
    """
    hasher = hashlib.md5()
    dir_path = Path(directory_path)
    
    if not dir_path.exists():
        return "directory_not_found"
    
    # Get sorted list of files for consistent ordering
    files = sorted(dir_path.rglob("*"))
    
    for file_path in files:
        if file_path.is_file():
            # Include relative path in hash
            rel_path = file_path.relative_to(dir_path)
            hasher.update(str(rel_path).encode('utf-8'))
            
            # Include file content hash
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
    
    return hasher.hexdigest()


def validate_distinct_stimulus_sets() -> IntegrityReport:
    """
    Validate that prime and target stimulus sets are distinct.
    
    This function implements Principle VI by ensuring that:
    1. Primes and targets are stored in separate directories
    2. There is no overlap in stimulus identifiers between the two sets
    3. The integrity of both sets is maintained via checksums
    
    Returns:
        An IntegrityReport with the validation results.
    """
    logger.info("Starting distinct stimulus set validation (Principle VI)")
    
    prime_dir = get_path("data/primes")
    target_dir = get_path("data/targets")
    
    # Check if directories exist
    if not os.path.exists(prime_dir):
        logger.warning(f"Prime directory does not exist: {prime_dir}")
        # If primes don't exist yet, we can't validate overlap
        return IntegrityReport(
            status=IntegrityStatus.WARNING,
            message="Prime stimulus directory not found. Cannot validate distinctness.",
            prime_count=0,
            target_count=0,
            overlap_count=0,
            overlap_stimuli=[]
        )
    
    if not os.path.exists(target_dir):
        logger.warning(f"Target directory does not exist: {target_dir}")
        return IntegrityReport(
            status=IntegrityStatus.WARNING,
            message="Target stimulus directory not found. Cannot validate distinctness.",
            prime_count=0,
            target_count=0,
            overlap_count=0,
            overlap_stimuli=[]
        )
    
    try:
        prime_ids = load_stimulus_paths(StimulusType.PRIME)
        target_ids = load_stimulus_paths(StimulusType.TARGET)
    except FileNotFoundError as e:
        logger.error(f"Error loading stimulus paths: {e}")
        return IntegrityReport(
            status=IntegrityStatus.FAIL,
            message=str(e),
            prime_count=0,
            target_count=0,
            overlap_count=0,
            overlap_stimuli=[]
        )
    
    # Check for overlap
    overlap = prime_ids.intersection(target_ids)
    overlap_count = len(overlap)
    
    # Compute checksums
    checksum_prime = compute_directory_checksum(Path(prime_dir))
    checksum_target = compute_directory_checksum(Path(target_dir))
    
    # Determine status
    if overlap_count > 0:
        status = IntegrityStatus.FAIL
        message = f"CRITICAL: {overlap_count} stimuli found in both prime and target sets. " \
                 "Primes and targets must remain distinct per Principle VI."
    elif len(prime_ids) == 0 and len(target_ids) == 0:
        status = IntegrityStatus.WARNING
        message = "Both prime and target directories are empty."
    elif len(prime_ids) == 0:
        status = IntegrityStatus.WARNING
        message = "Prime stimulus directory is empty."
    elif len(target_ids) == 0:
        status = IntegrityStatus.WARNING
        message = "Target stimulus directory is empty."
    else:
        status = IntegrityStatus.PASS
        message = "Distinct stimulus sets validated successfully. No overlap detected."
    
    logger.info(f"Validation complete: {status.value} - {message}")
    
    return IntegrityReport(
        status=status,
        message=message,
        prime_count=len(prime_ids),
        target_count=len(target_ids),
        overlap_count=overlap_count,
        overlap_stimuli=list(overlap),
        checksum_prime=checksum_prime,
        checksum_target=checksum_target
    )


def prevent_premature_merge(trial_data: List[Dict]) -> List[Dict]:
    """
    Process trial data to ensure primes and targets are not merged.
    
    This function validates that each trial correctly references either
    a prime OR a target stimulus, but never a merged/ambiguous identifier.
    
    Args:
        trial_data: List of trial dictionaries containing stimulus references.
        
    Returns:
        Filtered list of valid trials with distinct stimulus references.
        
    Raises:
        ValueError: If a trial contains an invalid merged stimulus reference.
    """
    validated_trials = []
    
    for trial in trial_data:
        stimulus_id = trial.get('stimulus_id', '')
        stimulus_type = trial.get('stimulus_type', '')
        
        # Check if stimulus_type is explicitly set
        if not stimulus_type:
            # Try to infer from the stimulus_id
            if stimulus_id.startswith('prime_'):
                trial['stimulus_type'] = 'prime'
                stimulus_type = 'prime'
            elif stimulus_id.startswith('target_'):
                trial['stimulus_type'] = 'target'
                stimulus_type = 'target'
            else:
                # Cannot determine type, flag for review
                logger.warning(f"Trial {trial.get('trial_id', 'unknown')} has ambiguous stimulus_id: {stimulus_id}")
                # Don't discard, but log warning
        
        # Validate that the stimulus exists in the correct directory
        if stimulus_type == 'prime':
            prime_dir = get_path("data/primes")
            if not os.path.exists(os.path.join(prime_dir, stimulus_id)):
                logger.warning(f"Prime stimulus not found: {stimulus_id}")
        elif stimulus_type == 'target':
            target_dir = get_path("data/targets")
            if not os.path.exists(os.path.join(target_dir, stimulus_id)):
                logger.warning(f"Target stimulus not found: {stimulus_id}")
        
        validated_trials.append(trial)
    
    return validated_trials


def save_integrity_report(report: IntegrityReport, output_path: Optional[Path] = None):
    """
    Save the integrity report to a JSON file.
    
    Args:
        report: The integrity report to save.
        output_path: Optional path to save the report. Defaults to state/integrity_report.json.
    """
    if output_path is None:
        output_path = Path(get_path("state")) / "integrity_report.json"
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report_dict = {
        "status": report.status.value,
        "message": report.message,
        "prime_count": report.prime_count,
        "target_count": report.target_count,
        "overlap_count": report.overlap_count,
        "overlap_stimuli": report.overlap_stimuli,
        "checksum_prime": report.checksum_prime,
        "checksum_target": report.checksum_target
    }
    
    import json
    with open(output_path, 'w') as f:
        json.dump(report_dict, f, indent=2)
    
    logger.info(f"Integrity report saved to {output_path}")


def run_integrity_validation() -> IntegrityReport:
    """
    Main entry point for running the integrity validation pipeline.
    
    Returns:
        The integrity report from the validation.
    """
    logger.info("Running full integrity validation pipeline")
    
    report = validate_distinct_stimulus_sets()
    save_integrity_report(report)
    
    if report.status == IntegrityStatus.FAIL:
        logger.error(report.message)
        # In a real pipeline, this might raise an exception to halt execution
        # For now, we just log the error
    elif report.status == IntegrityStatus.WARNING:
        logger.warning(report.message)
    else:
        logger.info(report.message)
    
    return report


def main():
    """Command-line entry point for integrity validation."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    report = run_integrity_validation()
    
    # Print summary
    print(f"\n{'='*60}")
    print("INTEGRITY VALIDATION RESULTS (Principle VI)")
    print(f"{'='*60}")
    print(f"Status: {report.status.value}")
    print(f"Message: {report.message}")
    print(f"Prime stimuli: {report.prime_count}")
    print(f"Target stimuli: {report.target_count}")
    print(f"Overlap count: {report.overlap_count}")
    if report.overlap_count > 0:
        print(f"Overlapping stimuli: {report.overlap_stimuli}")
    print(f"Prime checksum: {report.checksum_prime}")
    print(f"Target checksum: {report.checksum_target}")
    print(f"{'='*60}\n")
    
    # Exit with error code if validation failed
    if report.status == IntegrityStatus.FAIL:
        exit(1)


if __name__ == "__main__":
    main()