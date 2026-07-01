"""
Module to calculate rejection rates from ICA logs and identify participants
exceeding the rejection threshold defined in SC-001 (>50% rejected trials).
"""
import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
REJECTION_THRESHOLD = 0.50  # 50%
LOG_PATTERN = r"Rejected (\d+) epochs out of (\d+)"
OUTPUT_DIR = "data/processed"
OUTPUT_FILE = "rejected_participants.log"

def parse_ica_log(log_path: Path) -> Tuple[int, int]:
    """
    Parse a single log file to extract total epochs and rejected epochs.
    
    Args:
        log_path: Path to the ICA log file.
        
    Returns:
        Tuple of (total_epochs, rejected_epochs).
    """
    total = 0
    rejected = 0
    
    if not log_path.exists():
        logger.warning(f"Log file not found: {log_path}")
        return 0, 0
        
    with open(log_path, 'r') as f:
        content = f.read()
        
    # Look for the specific pattern in the log
    matches = re.findall(LOG_PATTERN, content)
    if matches:
        # Take the last occurrence if multiple found (usually the summary)
        last_match = matches[-1]
        rejected = int(last_match[0])
        total = int(last_match[1])
        logger.info(f"Parsed {log_path}: {rejected}/{total} epochs rejected")
    else:
        logger.warning(f"No rejection stats found in {log_path}")
        
    return total, rejected

def find_ica_logs(processed_dir: Path) -> Dict[str, Path]:
    """
    Find all ICA log files in the processed directory.
    Assumes log files follow naming convention: sub-XX_ica.log
    
    Args:
        processed_dir: Path to the data/processed directory.
        
    Returns:
        Dictionary mapping subject ID to log file path.
    """
    logs = {}
    if not processed_dir.exists():
        logger.error(f"Processed directory not found: {processed_dir}")
        return logs
        
    for log_file in processed_dir.glob("sub-*_ica.log"):
        # Extract subject ID from filename (e.g., sub-01_ica.log -> 01)
        subject_id = log_file.stem.replace("_ica.log", "").replace("sub-", "")
        logs[subject_id] = log_file
        
    return logs

def analyze_rejection_rates(logs: Dict[str, Path]) -> Dict[str, Dict[str, int]]:
    """
    Calculate rejection rates for all participants.
    
    Args:
        logs: Dictionary of subject_id -> log_path.
        
    Returns:
        Dictionary mapping subject_id to stats dict containing:
            - total: total epochs
            - rejected: rejected epochs
            - rate: rejection rate (float)
    """
    results = {}
    
    for subject_id, log_path in logs.items():
        total, rejected = parse_ica_log(log_path)
        if total > 0:
            rate = rejected / total
        else:
            rate = 0.0
            
        results[subject_id] = {
            'total': total,
            'rejected': rejected,
            'rate': rate
        }
        
    return results

def identify_excluded_participants(results: Dict[str, Dict[str, int]], 
                                 threshold: float = REJECTION_THRESHOLD) -> Set[str]:
    """
    Identify participants exceeding the rejection threshold.
    
    Args:
        results: Dictionary of subject stats.
        threshold: Rejection rate threshold (default 0.50).
        
    Returns:
        Set of subject IDs to be excluded.
    """
    excluded = set()
    
    for subject_id, stats in results.items():
        if stats['rate'] > threshold:
            excluded.add(subject_id)
            logger.warning(f"Participant {subject_id} excluded: {stats['rejected']}/{stats['total']} ({stats['rate']:.2%}) rejected")
        else:
            logger.info(f"Participant {subject_id} included: {stats['rejected']}/{stats['total']} ({stats['rate']:.2%}) rejected")
            
    return excluded

def write_exclusion_log(excluded_ids: Set[str], output_path: Path) -> None:
    """
    Write the list of excluded participants to the log file.
    
    Args:
        excluded_ids: Set of subject IDs to exclude.
        output_path: Path to the output log file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(f"# Excluded Participants (Rejection Rate > {REJECTION_THRESHOLD * 100:.0f}%)\n")
        f.write(f"# Threshold: {REJECTION_THRESHOLD}\n")
        f.write(f"# Total Excluded: {len(excluded_ids)}\n")
        f.write("#\n")
        
        if not excluded_ids:
            f.write("# No participants excluded.\n")
        else:
            for subject_id in sorted(excluded_ids):
                f.write(f"{subject_id}\n")
                
    logger.info(f"Wrote {len(excluded_ids)} excluded participants to {output_path}")

def run_rejection_analysis(processed_dir: Path = None) -> Dict[str, Set[str]]:
    """
    Main entry point to run the rejection analysis pipeline.
    
    Args:
        processed_dir: Optional path to processed data directory.
        
    Returns:
        Dictionary with 'excluded' (set of IDs) and 'all_stats' (dict of stats).
    """
    if processed_dir is None:
        processed_dir = Path(OUTPUT_DIR)
        
    logger.info(f"Starting rejection analysis in {processed_dir}")
    
    # Find logs
    logs = find_ica_logs(processed_dir)
    if not logs:
        logger.warning("No ICA logs found. Assuming no rejections yet.")
        write_exclusion_log(set(), processed_dir / OUTPUT_FILE)
        return {'excluded': set(), 'all_stats': {}}
        
    # Analyze
    results = analyze_rejection_rates(logs)
    
    # Identify exclusions
    excluded = identify_excluded_participants(results)
    
    # Write output
    output_path = processed_dir / OUTPUT_FILE
    write_exclusion_log(excluded, output_path)
    
    return {
        'excluded': excluded,
        'all_stats': results
    }

if __name__ == "__main__":
    run_rejection_analysis()
