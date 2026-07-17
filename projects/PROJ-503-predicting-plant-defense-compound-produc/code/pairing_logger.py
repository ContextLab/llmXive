"""
Pairing Logger Module (T026)

Implements logging of sample-level mismatches between expression and metabolite data.
Logs to: projects/PROJ-503-predicting-plant-defense-compound-produc/logs/data_pairing.json

Fields logged per mismatch:
- sample_id: The identifier that failed to match
- expression_source: Source file or accession for expression data
- metabolite_source: Source file or accession for metabolite data
- reason: "no_sample_level_pair"
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Project root relative to this file (assuming code/ directory)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
PAIRING_LOG_PATH = LOGS_DIR / "data_pairing.json"

# Ensure logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)

def load_pairing_log() -> List[Dict[str, Any]]:
    """
    Load existing pairing mismatches from the log file.
    Returns an empty list if the file does not exist.
    """
    if not PAIRING_LOG_PATH.exists():
        return []
    
    try:
        with open(PAIRING_LOG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Ensure it's a list even if file was corrupted or empty
            if not isinstance(data, list):
                logger.warning(f"Pairing log at {PAIRING_LOG_PATH} is not a list. Resetting to empty list.")
                return []
            return data
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load pairing log from {PAIRING_LOG_PATH}: {e}")
        return []

def save_pairing_log(mismatches: List[Dict[str, Any]]) -> None:
    """
    Save the list of pairing mismatches to the log file.
    Overwrites the existing file.
    """
    try:
        with open(PAIRING_LOG_PATH, 'w', encoding='utf-8') as f:
            json.dump(mismatches, f, indent=2, default=str)
        logger.info(f"Saved {len(mismatches)} mismatch entries to {PAIRING_LOG_PATH}")
    except IOError as e:
        logger.error(f"Failed to save pairing log to {PAIRING_LOG_PATH}: {e}")
        raise

def log_data_pairing_mismatch(
    sample_id: str,
    expression_source: str,
    metabolite_source: str,
    reason: str = "no_sample_level_pair"
) -> None:
    """
    Log a single sample-level pairing mismatch.
    
    Args:
        sample_id: The identifier that failed to match
        expression_source: Source file or accession for expression data
        metabolite_source: Source file or accession for metabolite data
        reason: Reason for the mismatch (default: "no_sample_level_pair")
    """
    mismatch_entry = {
        "sample_id": sample_id,
        "expression_source": expression_source,
        "metabolite_source": metabolite_source,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    current_log = load_pairing_log()
    current_log.append(mismatch_entry)
    save_pairing_log(current_log)
    
    logger.debug(f"Logged pairing mismatch for sample_id: {sample_id}")

def log_data_pairing_mismatches_batch(
    mismatches: List[Dict[str, str]]
) -> int:
    """
    Log a batch of pairing mismatches.
    
    Args:
        mismatches: List of dicts with keys: sample_id, expression_source, 
                    metabolite_source, reason (optional)
                    
    Returns:
        Number of entries successfully logged.
    """
    current_log = load_pairing_log()
    added_count = 0
    
    for m in mismatches:
        sample_id = m.get("sample_id")
        expr_src = m.get("expression_source")
        metab_src = m.get("metabolite_source")
        reason = m.get("reason", "no_sample_level_pair")
        
        if not all([sample_id, expr_src, metab_src]):
            logger.warning(f"Skipping malformed mismatch entry: {m}")
            continue
        
        entry = {
            "sample_id": sample_id,
            "expression_source": expr_src,
            "metabolite_source": metab_src,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        current_log.append(entry)
        added_count += 1
    
    if added_count > 0:
        save_pairing_log(current_log)
        logger.info(f"Batch logged {added_count} mismatch entries.")
    
    return added_count

def get_pairing_log_stats() -> Dict[str, Any]:
    """
    Get statistics about the current pairing log.
    
    Returns:
        Dict with total_count and breakdown by reason.
    """
    current_log = load_pairing_log()
    
    stats = {
        "total_mismatches": len(current_log),
        "by_reason": {}
    }
    
    for entry in current_log:
        reason = entry.get("reason", "unknown")
        stats["by_reason"][reason] = stats["by_reason"].get(reason, 0) + 1
    
    return stats

def clear_pairing_log() -> None:
    """
    Clear the pairing log file. Useful for fresh runs.
    """
    if PAIRING_LOG_PATH.exists():
        PAIRING_LOG_PATH.unlink()
        logger.info(f"Cleared pairing log at {PAIRING_LOG_PATH}")
    else:
        logger.info("Pairing log does not exist, nothing to clear.")

def main():
    """
    CLI entry point for testing the logger.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Pairing Logger Utility")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Log a single mismatch
    log_parser = subparsers.add_parser("log", help="Log a single mismatch")
    log_parser.add_argument("--sample-id", required=True, help="Sample ID")
    log_parser.add_argument("--expr-src", required=True, help="Expression source")
    log_parser.add_argument("--metab-src", required=True, help="Metabolite source")
    log_parser.add_argument("--reason", default="no_sample_level_pair", help="Reason")
    
    # Stats
    subparsers.add_parser("stats", help="Show log statistics")
    
    # Clear
    subparsers.add_parser("clear", help="Clear the log")
    
    args = parser.parse_args()
    
    if args.command == "log":
        log_data_pairing_mismatch(
            args.sample_id,
            args.expr_src,
            args.metab_src,
            args.reason
        )
        print(f"Logged mismatch for {args.sample_id}")
    elif args.command == "stats":
        stats = get_pairing_log_stats()
        print(json.dumps(stats, indent=2))
    elif args.command == "clear":
        clear_pairing_log()
        print("Log cleared.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()