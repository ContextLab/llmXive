import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Set

from config_loader import get_project_root, get_config, ensure_directory

logger = logging.getLogger(__name__)

def find_ica_logs(processed_dir: Path) -> List[Path]:
    """
    Find all ICA log files in the processed directory.
    Expected pattern: ica_log_<subject_id>.txt or similar.
    """
    log_files = list(processed_dir.glob("ica_log_*.txt"))
    if not log_files:
        # Fallback to generic log if naming convention differs
        generic_logs = list(processed_dir.glob("ica*.log"))
        log_files.extend(generic_logs)
    
    logger.info(f"Found {len(log_files)} ICA log files: {[f.name for f in log_files]}")
    return log_files

def parse_ica_log(log_path: Path) -> Dict[str, float]:
    """
    Parse a single ICA log file to extract rejection statistics.
    
    Expected log format (per task T020 description):
    - Lines indicating total epochs processed
    - Lines indicating rejected epochs/components
    - Pattern: "Total epochs: X", "Rejected epochs: Y", "Components removed: Z"
    
    Returns:
        Dict with keys: 'total_epochs', 'rejected_epochs', 'components_removed'
    """
    stats = {
        'total_epochs': 0,
        'rejected_epochs': 0,
        'components_removed': 0
    }
    
    try:
        with open(log_path, 'r') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Failed to read log file {log_path}: {e}")
        return stats
    
    # Regex patterns to extract numbers
    total_match = re.search(r'Total epochs[:\s]+(\d+)', content)
    rejected_match = re.search(r'Rejected epochs[:\s]+(\d+)', content)
    components_match = re.search(r'Components removed[:\s]+(\d+)', content)
    
    if total_match:
        stats['total_epochs'] = int(total_match.group(1))
    if rejected_match:
        stats['rejected_epochs'] = int(rejected_match.group(1))
    if components_match:
        stats['components_removed'] = int(components_match.group(1))
    
    # If no specific format found, try to infer from generic "rejected" mentions
    if stats['total_epochs'] == 0 and stats['rejected_epochs'] == 0:
        # Try alternative parsing for different log formats
        lines = content.split('\n')
        for line in lines:
            if 'epoch' in line.lower() and 'total' in line.lower():
                try:
                    num = int(re.search(r'\d+', line).group())
                    stats['total_epochs'] = num
                except:
                    pass
            if 'epoch' in line.lower() and 'reject' in line.lower():
                try:
                    num = int(re.search(r'\d+', line).group())
                    stats['rejected_epochs'] = num
                except:
                    pass
    
    return stats

def analyze_rejection_rates(log_files: List[Path]) -> Dict[str, Dict[str, float]]:
    """
    Analyze rejection rates across all participants.
    
    Returns:
        Dict mapping subject_id -> {
            'total_epochs': int,
            'rejected_epochs': int,
            'rejection_rate': float (0.0 to 1.0),
            'components_removed': int
        }
    """
    results = {}
    
    for log_path in log_files:
        # Extract subject ID from filename (e.g., ica_log_sub-01.txt -> sub-01)
        filename = log_path.name
        match = re.search(r'(sub-\d+|sub[0-9]+)', filename)
        subject_id = match.group(1) if match else filename.replace('.txt', '').replace('ica_log_', '')
        
        stats = parse_ica_log(log_path)
        
        if stats['total_epochs'] > 0:
            rejection_rate = stats['rejected_epochs'] / stats['total_epochs']
        else:
            rejection_rate = 0.0
        
        results[subject_id] = {
            'total_epochs': stats['total_epochs'],
            'rejected_epochs': stats['rejected_epochs'],
            'rejection_rate': rejection_rate,
            'components_removed': stats['components_removed']
        }
        
        logger.info(f"Subject {subject_id}: {stats['rejected_epochs']}/{stats['total_epochs']} epochs rejected ({rejection_rate:.2%})")
    
    return results

def identify_excluded_participants(rejection_data: Dict[str, Dict[str, float]], threshold: float = 0.5) -> Set[str]:
    """
    Identify participants with rejection rates exceeding the threshold.
    
    Args:
        rejection_data: Output from analyze_rejection_rates
        threshold: Maximum allowed rejection rate (default 0.5 = 50%)
    
    Returns:
        Set of subject IDs to exclude
    """
    excluded = set()
    
    for subject_id, stats in rejection_data.items():
        if stats['rejection_rate'] > threshold:
            excluded.add(subject_id)
            logger.warning(f"Excluding {subject_id}: rejection rate {stats['rejection_rate']:.2%} > {threshold:.2%}")
        else:
            logger.info(f"Including {subject_id}: rejection rate {stats['rejection_rate']:.2%} <= {threshold:.2%}")
    
    return excluded

def write_exclusion_log(excluded_participants: Set[str], output_path: Path) -> None:
    """
    Write the list of excluded participants to a log file.
    
    Args:
        excluded_participants: Set of subject IDs to exclude
        output_path: Path to the output log file
    """
    ensure_directory(output_path.parent)
    
    with open(output_path, 'w') as f:
        f.write("# Excluded Participants Log\n")
        f.write("# Criteria: Rejection rate > 50% (SC-001)\n")
        f.write(f"# Total excluded: {len(excluded_participants)}\n")
        f.write("#" + "=" * 50 + "\n")
        
        if excluded_participants:
            for subject_id in sorted(excluded_participants):
                f.write(f"{subject_id}\n")
        else:
            f.write("# No participants excluded\n")
    
    logger.info(f"Exclusion log written to {output_path}")

def run_rejection_analysis(processed_dir: Optional[Path] = None, output_file: Optional[str] = None) -> Dict[str, any]:
    """
    Main entry point for rejection analysis pipeline.
    
    Args:
        processed_dir: Directory containing ICA logs (default: data/processed)
        output_file: Output log file name (default: rejected_participants.log)
    
    Returns:
        Dict with analysis results
    """
    project_root = get_project_root()
    processed_dir = processed_dir or project_root / "data" / "processed"
    output_file = output_file or "rejected_participants.log"
    output_path = processed_dir / output_file
    
    if not processed_dir.exists():
        logger.error(f"Processed directory does not exist: {processed_dir}")
        return {'error': 'processed_dir_not_found', 'path': str(processed_dir)}
    
    # Find and analyze logs
    log_files = find_ica_logs(processed_dir)
    if not log_files:
        logger.warning("No ICA log files found. Creating empty exclusion log.")
        write_exclusion_log(set(), output_path)
        return {'excluded_participants': [], 'total_analyzed': 0}
    
    # Analyze rejection rates
    rejection_data = analyze_rejection_rates(log_files)
    
    # Identify excluded participants
    excluded = identify_excluded_participants(rejection_data, threshold=0.5)
    
    # Write exclusion log
    write_exclusion_log(excluded, output_path)
    
    return {
        'excluded_participants': list(excluded),
        'total_analyzed': len(rejection_data),
        'rejection_data': rejection_data,
        'output_path': str(output_path)
    }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run_rejection_analysis()
    print(f"Analysis complete. Excluded {len(result['excluded_participants'])} participants.")
    if result.get('error'):
        print(f"Error: {result['error']}")
