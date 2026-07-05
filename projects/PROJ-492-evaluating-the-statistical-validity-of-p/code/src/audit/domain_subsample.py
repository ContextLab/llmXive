"""
Domain Bias Subsampling Module (FR-027)

Implements logic to create a balanced subsample of the audit corpus such that
no single domain exceeds 30% of the total subsample size.

This module reads the audit report (JSON) or a CSV summary, extracts domain
information, calculates current proportions, and performs a stratified
subsampling to enforce the 30% cap.
"""
import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter

# Import from project API
from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.config import set_rng_seed

# Constants
DOMAIN_CAP_THRESHOLD = 0.30  # 30%
DEFAULT_SEED = 42

def load_audit_records_from_json(path: Path) -> List[Dict[str, Any]]:
    """Load audit records from a JSON file."""
    logger = get_default_logger()
    if not path.exists():
        logger.error(f"File not found: {path}")
        return []
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Handle both list of records and dict with 'records' key
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'records' in data:
                return data['records']
            else:
                logger.warning("JSON format unexpected, attempting to treat as list of records")
                return [data] if data else []
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON: {e}")
        return []

def load_summaries_from_csv(path: Path) -> List[Dict[str, Any]]:
    """Load summaries from a CSV file."""
    logger = get_default_logger()
    if not path.exists():
        logger.error(f"File not found: {path}")
        return []
    
    records = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
    
    return records

def extract_domain_from_record(record: Dict[str, Any]) -> str:
    """
    Extract the domain from a record.
    Looks for 'domain' key, or derives from 'url' if present.
    """
    if 'domain' in record and record['domain']:
        return str(record['domain'])
    
    url = record.get('url', '')
    if url:
        # Simple domain extraction: protocol://domain/path
        # Remove protocol
        if '://' in url:
            url = url.split('://')[1]
        # Remove path
        domain = url.split('/')[0]
        # Remove port
        if ':' in domain:
            domain = domain.split(':')[0]
        return domain
    
    return "unknown"

def calculate_domain_proportions(records: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate the proportion of each domain in the records."""
    if not records:
        return {}
    
    domain_counts = Counter()
    for record in records:
        domain = extract_domain_from_record(record)
        domain_counts[domain] += 1
    
    total = len(records)
    return {domain: count / total for domain, count in domain_counts.items()}

def create_balanced_subsample(
    records: List[Dict[str, Any]], 
    max_domain_ratio: float = DOMAIN_CAP_THRESHOLD,
    seed: int = DEFAULT_SEED
) -> List[Dict[str, Any]]:
    """
    Create a balanced subsample where no domain exceeds max_domain_ratio.
    
    Algorithm:
    1. Identify the domain with the highest count (dominant domain).
    2. If dominant domain > max_domain_ratio * total, calculate the target total size
       such that the dominant domain fits within the cap.
       Target Total = Dominant Count / max_domain_ratio
    3. If the calculated target is larger than current total, no subsampling needed.
    4. Otherwise, subsample the dominant domain to fit the cap, and subsample
       other domains proportionally to maintain relative distribution among them,
       or simply keep all non-dominant records if they fit.
       
    Simplified Robust Strategy:
    - Calculate the maximum allowed count for the dominant domain:
      max_count = floor(total * max_domain_ratio)
    - If dominant_count <= max_count, return all records.
    - If dominant_count > max_count:
      - We must reduce the total size to at least: min_total = dominant_count / max_domain_ratio
      - We will subsample the dominant domain down to max_count.
      - We will subsample other domains proportionally to the reduction factor,
        ensuring we don't exceed the new total.
    """
    if not records:
        return []
    
    set_rng_seed(seed)
    import random
    random.seed(seed)
    
    # Group records by domain
    domain_groups: Dict[str, List[Dict[str, Any]]] = {}
    for record in records:
        domain = extract_domain_from_record(record)
        if domain not in domain_groups:
            domain_groups[domain] = []
        domain_groups[domain].append(record)
    
    total_records = len(records)
    dominant_domain = max(domain_groups.keys(), key=lambda d: len(domain_groups[d]))
    dominant_count = len(domain_groups[dominant_domain])
    
    # Check if constraint is already satisfied
    if dominant_count / total_records <= max_domain_ratio:
        return records
    
    # Calculate target total size
    # We need: dominant_count / target_total <= max_domain_ratio
    # target_total >= dominant_count / max_domain_ratio
    target_total = int(dominant_count / max_domain_ratio)
    
    # Ensure target_total is at least the sum of all non-dominant records
    non_dominant_count = total_records - dominant_count
    if target_total < non_dominant_count + 1: # +1 to ensure we keep at least one dominant
        target_total = non_dominant_count + 1
    
    # Cap target_total at original total (shouldn't happen if logic is right, but safety)
    target_total = min(target_total, total_records)
    
    # Calculate how many we need from the dominant domain
    # We want to keep exactly dominant_count (which is the limit) or less?
    # Actually, we want the final dominant count to be <= max_domain_ratio * target_total
    # Let's set the dominant count to exactly floor(max_domain_ratio * target_total)
    # But we must ensure we don't exceed the available dominant_count
    max_allowed_dominant = int(target_total * max_domain_ratio)
    final_dominant_count = min(dominant_count, max_allowed_dominant)
    
    # The remaining slots go to non-dominant domains
    remaining_slots = target_total - final_dominant_count
    
    # Subsample dominant domain
    dominant_records = domain_groups[dominant_domain]
    # Shuffle and pick
    random.shuffle(dominant_records)
    selected_dominant = dominant_records[:final_dominant_count]
    
    # Subsample non-dominant domains proportionally
    non_dominant_records = []
    for domain, recs in domain_groups.items():
        if domain != dominant_domain:
            non_dominant_records.extend(recs)
    
    # Shuffle non-dominant
    random.shuffle(non_dominant_records)
    
    # We need to take 'remaining_slots' from non-dominant
    # If we have more non-dominant than slots, subsample. If less, take all.
    final_non_dominant = non_dominant_records[:remaining_slots]
    
    # Combine
    final_subsample = selected_dominant + final_non_dominant
    
    # Shuffle final result to remove ordering bias
    random.shuffle(final_subsample)
    
    return final_subsample

def write_subsample_to_csv(records: List[Dict[str, Any]], output_path: Path) -> bool:
    """Write the subsampled records to a CSV file."""
    logger = get_default_logger()
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not records:
            logger.warning("No records to write.")
            # Write empty file with headers if possible, or just empty
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                f.write("")
            return True

        # Determine headers from the first record
        headers = list(records[0].keys())
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(records)
        
        logger.info(f"Wrote {len(records)} records to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to write CSV: {e}")
        return False

def run_domain_subsample(
    input_json_path: Path,
    output_csv_path: Path,
    max_domain_ratio: float = DOMAIN_CAP_THRESHOLD,
    seed: int = DEFAULT_SEED
) -> Tuple[bool, Dict[str, Any]]:
    """
    Main entry point to run the domain subsampling process.
    
    Args:
        input_json_path: Path to the audit report JSON.
        output_csv_path: Path to write the subsampled CSV.
        max_domain_ratio: Maximum allowed proportion for any single domain.
        seed: Random seed for reproducibility.
    
    Returns:
        Tuple of (success: bool, stats: dict)
    """
    logger = get_default_logger()
    logger.info(f"Starting domain subsampling. Input: {input_json_path}, Output: {output_csv_path}")
    logger.info(f"Max domain ratio: {max_domain_ratio}, Seed: {seed}")
    
    # Load data
    records = load_audit_records_from_json(input_json_path)
    if not records:
        logger.error("No records loaded. Aborting.")
        return False, {"error": "No records loaded"}
    
    # Calculate initial stats
    initial_counts = Counter(extract_domain_from_record(r) for r in records)
    initial_total = len(records)
    initial_proportions = calculate_domain_proportions(records)
    
    logger.info(f"Loaded {initial_total} records. Initial proportions: {initial_proportions}")
    
    # Perform subsampling
    subsampled_records = create_balanced_subsample(records, max_domain_ratio, seed)
    subsampled_total = len(subsampled_records)
    
    # Calculate final stats
    final_counts = Counter(extract_domain_from_record(r) for r in subsampled_records)
    final_proportions = calculate_domain_proportions(subsampled_records)
    
    # Verify constraint
    max_final_prop = max(final_proportions.values()) if final_proportions else 0
    constraint_met = max_final_prop <= max_domain_ratio + 1e-9 # Floating point tolerance
    
    logger.info(f"Subsampled to {subsampled_total} records. Final max proportion: {max_final_prop:.4f}")
    logger.info(f"Constraint met: {constraint_met}")
    
    if not constraint_met:
        logger.error(f"Constraint NOT met. Max proportion {max_final_prop} > {max_domain_ratio}")
        return False, {
            "error": "Constraint not met",
            "max_prop": max_final_prop,
            "limit": max_domain_ratio
        }
    
    # Write output
    success = write_subsample_to_csv(subsampled_records, output_csv_path)
    
    if not success:
        return False, {"error": "Failed to write output"}
    
    stats = {
        "input_count": initial_total,
        "output_count": subsampled_total,
        "max_domain_ratio_limit": max_domain_ratio,
        "actual_max_domain_ratio": max_final_prop,
        "constraint_met": constraint_met,
        "domains": {
            "initial": {k: v for k, v in initial_proportions.items()},
            "final": {k: v for k, v in final_proportions.items()}
        },
        "timestamp": datetime.now().isoformat()
    }
    
    return True, stats

def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Domain Bias Subsampling (FR-027)")
    parser.add_argument("--input", type=str, default="output/audit_report.json",
                        help="Path to input audit report JSON")
    parser.add_argument("--output", type=str, default="data/subsampled_balanced.csv",
                        help="Path to output subsampled CSV")
    parser.add_argument("--ratio", type=float, default=0.30,
                        help="Maximum domain ratio (default: 0.30)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed (default: 42)")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    success, stats = run_domain_subsample(
        input_json_path=input_path,
        output_csv_path=output_path,
        max_domain_ratio=args.ratio,
        seed=args.seed
    )
    
    if success:
        print(f"Subsampling successful. Output written to {output_path}")
        print(f"Stats: {stats}")
        return 0
    else:
        print(f"Subsampling failed: {stats.get('error', 'Unknown error')}")
        return 1

if __name__ == "__main__":
    exit(main())
