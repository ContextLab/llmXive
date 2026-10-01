import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

MEMORY_LOG_PATH = Path("data/processed/memory_log.json")
VERIFICATION_OUTPUT_PATH = Path("data/processed/memory_verification.json")
MAX_RAM_GB = 7.0
MAX_RAM_MB = MAX_RAM_GB * 1024


def load_memory_log(log_path: Path) -> List[Dict[str, Any]]:
    """
    Load the memory log JSON file.
    
    Args:
        log_path: Path to the memory log JSON file.
        
    Returns:
        List of memory log entries.
        
    Raises:
        FileNotFoundError: If the log file does not exist.
        json.JSONDecodeError: If the log file is not valid JSON.
    """
    if not log_path.exists():
        raise FileNotFoundError(f"Memory log not found at {log_path}")
    
    with open(log_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # Handle case where data might be a dict with a 'entries' key or a direct list
    if isinstance(data, dict):
        if 'entries' in data:
            return data['entries']
        elif 'log' in data:
            return data['log']
        else:
            # If it's a dict but not the expected format, try to treat values as entries
            # or return the dict itself if it looks like a single entry
            logger.warning(f"Unexpected memory log structure: {list(data.keys())}")
            return [data] if len(data) > 0 else []
    elif isinstance(data, list):
        return data
    else:
        raise ValueError(f"Unexpected memory log data type: {type(data)}")


def analyze_memory_usage(entries: List[Dict[str, Any]]) -> Tuple[float, float, List[Dict[str, Any]]]:
    """
    Analyze memory usage entries to find peak RAM and other statistics.
    
    Args:
        entries: List of memory log entries.
        
    Returns:
        Tuple of (peak_memory_mb, average_memory_mb, list of entries exceeding 90% of max)
    """
    if not entries:
        return 0.0, 0.0, []
    
    peak_memory_mb = 0.0
    total_memory_mb = 0.0
    count = 0
    high_usage_entries = []
    
    for entry in entries:
        # Try to extract memory usage from various possible keys
        memory_mb = entry.get('memory_mb') or entry.get('peak_memory_mb') or entry.get('usage_mb') or 0.0
        
        if not isinstance(memory_mb, (int, float)):
            try:
                memory_mb = float(memory_mb)
            except (ValueError, TypeError):
                memory_mb = 0.0
        
        if memory_mb > peak_memory_mb:
            peak_memory_mb = memory_mb
        
        total_memory_mb += memory_mb
        count += 1
        
        # Check if usage is above 90% of limit
        threshold = MAX_RAM_MB * 0.9
        if memory_mb > threshold:
            high_usage_entries.append({
                'entry': entry,
                'memory_mb': memory_mb,
                'threshold_mb': threshold
            })
    
    average_memory_mb = total_memory_mb / count if count > 0 else 0.0
    
    return peak_memory_mb, average_memory_mb, high_usage_entries


def generate_verification_report(
    peak_memory_mb: float,
    average_memory_mb: float,
    high_usage_entries: List[Dict[str, Any]],
    log_path: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Generate and save the memory verification report.
    
    Args:
        peak_memory_mb: Peak memory usage in MB.
        average_memory_mb: Average memory usage in MB.
        high_usage_entries: List of entries exceeding 90% of max limit.
        log_path: Path to the source memory log.
        output_path: Path to save the verification report.
        
    Returns:
        The verification report dictionary.
    """
    passed = peak_memory_mb < MAX_RAM_MB
    
    report = {
        "status": "pass" if passed else "fail",
        "constraint_gb": MAX_RAM_GB,
        "peak_memory_mb": round(peak_memory_mb, 2),
        "peak_memory_gb": round(peak_memory_mb / 1024, 4),
        "average_memory_mb": round(average_memory_mb, 2),
        "log_file_checked": str(log_path),
        "entries_analyzed": len(high_usage_entries) if high_usage_entries else 0,
        "high_usage_entries": high_usage_entries,
        "message": f"Peak memory usage ({peak_memory_mb:.2f} MB) {'is within' if passed else 'exceeds'} the limit of {MAX_RAM_GB} GB ({MAX_RAM_MB} MB)."
    }
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save report
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Verification report saved to {output_path}")
    logger.info(report["message"])
    
    return report


def main():
    """Main entry point for memory constraint verification."""
    logger.info("Starting memory constraint verification...")
    
    try:
        # Load memory log
        logger.info(f"Loading memory log from {MEMORY_LOG_PATH}")
        entries = load_memory_log(MEMORY_LOG_PATH)
        logger.info(f"Loaded {len(entries)} memory log entries")
        
        if not entries:
            logger.warning("Memory log is empty. Creating a failing report.")
            report = generate_verification_report(
                0.0, 0.0, [], MEMORY_LOG_PATH, VERIFICATION_OUTPUT_PATH
            )
            report["status"] = "fail"
            report["message"] = "Memory log is empty. Cannot verify constraint."
            with open(VERIFICATION_OUTPUT_PATH, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            sys.exit(1)
        
        # Analyze usage
        peak_mb, avg_mb, high_entries = analyze_memory_usage(entries)
        logger.info(f"Peak memory: {peak_mb:.2f} MB, Average: {avg_mb:.2f} MB")
        
        # Generate and save report
        report = generate_verification_report(
            peak_mb, avg_mb, high_entries, MEMORY_LOG_PATH, VERIFICATION_OUTPUT_PATH
        )
        
        # Exit with appropriate code
        if report["status"] == "fail":
            logger.error("Memory constraint verification FAILED.")
            sys.exit(1)
        else:
            logger.info("Memory constraint verification PASSED.")
            sys.exit(0)
            
    except FileNotFoundError as e:
        logger.error(f"Memory log file not found: {e}")
        # Create a failure report
        report = {
            "status": "fail",
            "error": str(e),
            "message": f"Could not verify memory constraint: {e}"
        }
        VERIFICATION_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(VERIFICATION_OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in memory log: {e}")
        report = {
            "status": "fail",
            "error": str(e),
            "message": f"Could not parse memory log: {e}"
        }
        VERIFICATION_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(VERIFICATION_OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        raise


if __name__ == "__main__":
    main()
