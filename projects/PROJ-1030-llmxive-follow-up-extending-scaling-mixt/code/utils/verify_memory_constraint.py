import json
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MAX_RAM_MB = 7000  # 7 GB limit in MB

def load_memory_log(log_path: str) -> List[Dict[str, Any]]:
    """
    Load the memory log JSON file.
    
    Args:
        log_path: Path to the memory log JSON file
        
    Returns:
        List of memory log entries
        
    Raises:
        FileNotFoundError: If the log file does not exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    path = Path(log_path)
    if not path.exists():
        raise FileNotFoundError(f"Memory log file not found: {log_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
        
    # Ensure we have a list of entries
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'entries' in data:
        return data['entries']
    else:
        raise ValueError(f"Unexpected memory log format: {type(data)}")

def analyze_memory_usage(entries: List[Dict[str, Any]]) -> Tuple[float, float, float, List[Dict[str, Any]]]:
    """
    Analyze memory usage from log entries.
    
    Args:
        entries: List of memory log entries
        
    Returns:
        Tuple of (min_peak, max_peak, avg_peak, list of all entries with peak_mb)
    """
    if not entries:
        logger.warning("No memory log entries found")
        return 0.0, 0.0, 0.0, []
    
    peak_values = []
    for entry in entries:
        if 'peak_mb' in entry:
            peak_values.append(entry['peak_mb'])
        elif 'peak_memory_mb' in entry:
            peak_values.append(entry['peak_memory_mb'])
        else:
            logger.warning(f"Entry missing peak memory: {entry}")
    
    if not peak_values:
        logger.warning("No valid peak memory values found in entries")
        return 0.0, 0.0, 0.0, entries
        
    min_peak = min(peak_values)
    max_peak = max(peak_values)
    avg_peak = sum(peak_values) / len(peak_values)
    
    return min_peak, max_peak, avg_peak, entries

def generate_verification_report(
    min_peak: float,
    max_peak: float,
    avg_peak: float,
    entries: List[Dict[str, Any]],
    max_limit: float = MAX_RAM_MB
) -> Dict[str, Any]:
    """
    Generate a verification report for memory usage.
    
    Args:
        min_peak: Minimum peak memory observed
        max_peak: Maximum peak memory observed
        avg_peak: Average peak memory observed
        entries: All memory log entries
        max_limit: Maximum allowed memory in MB
        
    Returns:
        Verification report dictionary
    """
    passed = max_peak < max_limit
    
    report = {
        "status": "passed" if passed else "failed",
        "max_limit_mb": max_limit,
        "observed": {
            "min_peak_mb": min_peak,
            "max_peak_mb": max_peak,
            "avg_peak_mb": avg_peak,
            "entry_count": len(entries)
        },
        "details": {
            "all_entries_within_limit": all(
                e.get('peak_mb', 0) < max_limit or e.get('peak_memory_mb', 0) < max_limit 
                for e in entries
            ),
            "worst_entry": max(
                entries, 
                key=lambda e: e.get('peak_mb', 0) or e.get('peak_memory_mb', 0)
            ) if entries else None
        }
    }
    
    return report

def save_verification_report(report: Dict[str, Any], output_path: str) -> None:
    """
    Save the verification report to a JSON file.
    
    Args:
        report: Verification report dictionary
        output_path: Path to save the report
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Verification report saved to {output_path}")

def main() -> int:
    """
    Main entry point for memory constraint verification.
    
    Returns:
        0 if verification passed, 1 if failed or error occurred
    """
    # Default paths
    log_path = "data/processed/memory_log.json"
    output_path = "data/processed/memory_verification.json"
    
    # Allow override via command line
    if len(sys.argv) > 1:
        log_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
        
    logger.info(f"Loading memory log from: {log_path}")
    logger.info(f"Verification output will be saved to: {output_path}")
    
    try:
        # Load log
        entries = load_memory_log(log_path)
        logger.info(f"Loaded {len(entries)} memory log entries")
        
        # Analyze
        min_peak, max_peak, avg_peak, _ = analyze_memory_usage(entries)
        logger.info(f"Memory analysis - Min: {min_peak:.2f} MB, Max: {max_peak:.2f} MB, Avg: {avg_peak:.2f} MB")
        
        # Generate report
        report = generate_verification_report(min_peak, max_peak, avg_peak, entries)
        
        # Save report
        save_verification_report(report, output_path)
        
        # Print result
        status = "PASSED" if report["status"] == "passed" else "FAILED"
        print(f"Memory Verification: {status}")
        print(f"  Max Observed: {max_peak:.2f} MB")
        print(f"  Limit: {MAX_RAM_MB} MB")
        
        return 0 if report["status"] == "passed" else 1
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        print(f"ERROR: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in log file: {e}")
        print(f"ERROR: Invalid JSON in log file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
