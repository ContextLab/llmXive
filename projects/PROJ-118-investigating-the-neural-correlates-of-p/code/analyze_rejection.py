import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Set

# Configure logging for this module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_ica_logs(processed_dir: Path) -> List[Path]:
    """
    Scan the processed directory for ICA log files generated during preprocessing.
    We expect logs to be named like 'sub-XX_ica_rejection.log' or similar patterns.
    
    Args:
        processed_dir: Path to the data/processed directory.
        
    Returns:
        List of paths to found ICA log files.
    """
    if not processed_dir.exists():
        logger.warning(f"Processed directory does not exist: {processed_dir}")
        return []
    
    # Pattern to match log files related to ICA rejection
    # We look for files containing 'ica' and 'log' in the name
    pattern = processed_dir.glob("*ica*log")
    logs = [p for p in pattern if p.suffix == '.log']
    
    # Also check for generic rejection logs if specific ICA ones aren't found
    if not logs:
        pattern = processed_dir.glob("*rejection*.log")
        logs = [p for p in pattern if p.suffix == '.log']
        
    logger.info(f"Found {len(logs)} ICA/rejection log files.")
    return logs

def parse_ica_log(log_path: Path) -> Tuple[int, int, str]:
    """
    Parse an ICA log file to extract total trials and rejected trials.
    
    Expected log format (based on MNE-Python standard outputs or custom logs):
    - "Total epochs: X"
    - "Rejected epochs: Y"
    - Or specific lines indicating rejection counts.
    
    Args:
        log_path: Path to the log file.
        
    Returns:
        Tuple of (total_trials, rejected_trials, participant_id).
        If parsing fails, returns (0, 0, "unknown").
    """
    total_trials = 0
    rejected_trials = 0
    participant_id = "unknown"
    
    # Extract participant ID from filename (e.g., sub-01_ica_rejection.log -> sub-01)
    stem = log_path.stem
    match = re.match(r"(sub-\d+)", stem)
    if match:
        participant_id = match.group(1)
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Try to find "Total epochs" or "Total trials"
        total_match = re.search(r"(?:Total\s+(?:epochs|trials))[:\s]+(\d+)", content, re.IGNORECASE)
        if total_match:
            total_trials = int(total_match.group(1))
        
        # Try to find "Rejected epochs" or "Rejected trials"
        reject_match = re.search(r"(?:Rejected\s+(?:epochs|trials))[:\s]+(\d+)", content, re.IGNORECASE)
        if reject_match:
            rejected_trials = int(reject_match.group(1))
            
        # Fallback: Look for "Dropped" or "Excluded" if standard keys aren't found
        if total_trials == 0:
            total_match = re.search(r"Dropped:\s+(\d+)", content)
            if total_match:
                # Sometimes logs only list dropped, we might need context to know total
                # Assuming if only dropped is listed, we might need to infer or skip
                pass 
        
        # Specific MNE pattern: "Rejected [n] epochs"
        if rejected_trials == 0:
            reject_match = re.search(r"Rejected\s+(\d+)\s+epochs", content)
            if reject_match:
                rejected_trials = int(reject_match.group(1))
                
        # If we found valid numbers, return them
        if total_trials > 0 or rejected_trials > 0:
            logger.info(f"Parsed {participant_id}: Total={total_trials}, Rejected={rejected_trials}")
            return total_trials, rejected_trials, participant_id
        
    except Exception as e:
        logger.error(f"Failed to parse log {log_path}: {e}")
        
    return total_trials, rejected_trials, participant_id

def analyze_rejection_rates(logs: List[Path]) -> Dict[str, Dict[str, int]]:
    """
    Analyze rejection rates for all participants based on their ICA logs.
    
    Args:
        logs: List of paths to ICA log files.
        
    Returns:
        Dictionary mapping participant_id to {'total': int, 'rejected': int, 'rate': float}.
    """
    results = {}
    
    for log_path in logs:
        total, rejected, pid = parse_ica_log(log_path)
        
        if total > 0:
            rate = rejected / total
            results[pid] = {
                'total': total,
                'rejected': rejected,
                'rate': rate
            }
            logger.info(f"Participant {pid}: Rejection rate {rate:.2%} ({rejected}/{total})")
        elif rejected > 0:
            # Edge case: log only mentions rejected but not total?
            # We cannot calculate rate without total, so we log a warning
            logger.warning(f"Participant {pid}: Found rejected count ({rejected}) but no total count. Cannot calculate rate.")
            results[pid] = {
                'total': 0,
                'rejected': rejected,
                'rate': 1.0 # Assume worst case if total is unknown but rejected exists? Or skip?
            }
        else:
            logger.warning(f"Participant {pid}: Could not parse valid trial counts from log.")
            
    return results

def identify_excluded_participants(rejection_data: Dict[str, Dict[str, int]], threshold: float = 0.50) -> Set[str]:
    """
    Identify participants whose rejection rate exceeds the threshold (default 50%).
    
    Args:
        rejection_data: Dictionary from analyze_rejection_rates.
        threshold: Maximum allowed rejection rate (e.g., 0.50 for 50%).
        
    Returns:
        Set of participant IDs to be excluded.
    """
    excluded = set()
    
    for pid, data in rejection_data.items():
        if data['total'] == 0:
            # If we have no data, we might exclude to be safe, or skip. 
            # Per SC-001, we exclude >50%. If data is missing, we can't verify.
            # Let's assume missing data means we can't include them safely.
            logger.warning(f"Participant {pid} has no valid trial data. Excluding.")
            excluded.add(pid)
            continue
            
        if data['rate'] > threshold:
            excluded.add(pid)
            logger.warning(f"Participant {pid} exceeds rejection threshold ({data['rate']:.2%} > {threshold}). Excluded.")
        else:
            logger.info(f"Participant {pid} within rejection threshold ({data['rate']:.2%} <= {threshold}).")
            
    return excluded

def write_exclusion_log(excluded_ids: Set[str], output_path: Path) -> None:
    """
    Write the list of excluded participant IDs to a log file.
    
    Args:
        excluded_ids: Set of participant IDs to exclude.
        output_path: Path to the output log file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Excluded Participants\n")
        f.write(f"# Reason: Rejection rate > 50% (SC-001)\n")
        f.write(f"# Total excluded: {len(excluded_ids)}\n\n")
        
        for pid in sorted(excluded_ids):
            f.write(f"{pid}\n")
            
    logger.info(f"Wrote {len(excluded_ids)} excluded participants to {output_path}")

def run_rejection_analysis(processed_dir: Path, output_file: str = "rejected_participants.log") -> Dict[str, List[str]]:
    """
    Main entry point to run the full rejection analysis pipeline.
    
    1. Find all ICA logs in processed_dir.
    2. Parse logs to get rejection rates.
    3. Identify participants exceeding 50% rejection.
    4. Write exclusion log.
    
    Args:
        processed_dir: Path to data/processed.
        output_file: Name of the output log file.
        
    Returns:
        Dictionary with summary stats: {'excluded': [ids], 'included': [ids], 'total_analyzed': count}
    """
    logger.info(f"Starting rejection analysis in {processed_dir}")
    
    # 1. Find logs
    logs = find_ica_logs(processed_dir)
    if not logs:
        logger.error("No ICA log files found. Cannot perform analysis.")
        # Write an empty log to indicate failure/no data
        write_exclusion_log(set(), processed_dir / output_file)
        return {'excluded': [], 'included': [], 'total_analyzed': 0}
    
    # 2. Analyze rates
    rejection_data = analyze_rejection_rates(logs)
    
    # 3. Identify exclusions
    excluded_ids = identify_excluded_participants(rejection_data, threshold=0.50)
    
    # 4. Write log
    output_path = processed_dir / output_file
    write_exclusion_log(excluded_ids, output_path)
    
    # Prepare summary
    all_ids = set(rejection_data.keys())
    included_ids = all_ids - excluded_ids
    
    return {
        'excluded': sorted(list(excluded_ids)),
        'included': sorted(list(included_ids)),
        'total_analyzed': len(all_ids)
    }

if __name__ == "__main__":
    # Example execution if run directly
    import sys
    base_dir = Path(__file__).parent.parent
    processed_dir = base_dir / "data" / "processed"
    
    if not processed_dir.exists():
        print(f"Error: Processed directory not found at {processed_dir}")
        sys.exit(1)
        
    result = run_rejection_analysis(processed_dir)
    print(f"Analysis complete. Excluded: {result['excluded']}, Included: {result['included']}")
