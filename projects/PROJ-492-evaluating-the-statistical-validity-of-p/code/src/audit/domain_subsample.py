import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from code.src.utils.logger import get_default_logger
from code.src.config import set_rng_seed

logger = get_default_logger()

def load_audit_records_from_json(input_path: Path) -> List[Dict[str, Any]]:
    """Load audit records from a JSON file."""
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both list format and dict with 'records' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'records' in data:
        return data['records']
    else:
        logger.error(f"Unexpected JSON structure in {input_path}")
        raise ValueError(f"Unexpected JSON structure in {input_path}")

def load_summaries_from_csv(input_path: Path) -> List[Dict[str, Any]]:
    """Load summaries from a CSV file."""
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    records = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(dict(row))
    return records

def extract_domain_from_record(record: Dict[str, Any]) -> str:
    """Extract domain from an audit record."""
    # Try multiple possible field names
    if 'domain' in record:
        return record['domain']
    elif 'source_domain' in record:
        return record['source_domain']
    elif 'url' in record:
        # Extract domain from URL if domain field is missing
        url = record['url']
        if url.startswith('http://') or url.startswith('https://'):
            url = url.split('://')[1]
        domain = url.split('/')[0]
        return domain
    else:
        logger.warning(f"Could not extract domain from record: {record}")
        return "unknown"

def calculate_domain_proportions(records: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate the proportion of records for each domain."""
    domain_counts = {}
    total = len(records)
    
    if total == 0:
        return {}
    
    for record in records:
        domain = extract_domain_from_record(record)
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
    
    proportions = {domain: count / total for domain, count in domain_counts.items()}
    return proportions

def create_balanced_subsample(
    records: List[Dict[str, Any]], 
    max_domain_proportion: float = 0.30
) -> List[Dict[str, Any]]:
    """
    Create a balanced subsample where no single domain exceeds max_domain_proportion.
    
    This function:
    1. Calculates current domain proportions
    2. Identifies dominant domains (those exceeding max_domain_proportion)
    3. Randomly subsamples dominant domains to meet the threshold
    4. Preserves all records from non-dominant domains
    """
    set_rng_seed(42)  # Ensure reproducibility per Constitution Principle I
    
    if not records:
        return []
    
    import random
    
    # Group records by domain
    domain_groups: Dict[str, List[Dict[str, Any]]] = {}
    for record in records:
        domain = extract_domain_from_record(record)
        if domain not in domain_groups:
            domain_groups[domain] = []
        domain_groups[domain].append(record)
    
    # Calculate target counts
    total_records = len(records)
    target_max_per_domain = int(total_records * max_domain_proportion)
    
    # If even the max allowed per domain is less than 1, we need to adjust
    if target_max_per_domain < 1 and total_records > 0:
        target_max_per_domain = 1
    
    balanced_records = []
    
    for domain, domain_records in domain_groups.items():
        current_count = len(domain_records)
        
        if current_count <= target_max_per_domain:
            # Keep all records for this domain
            balanced_records.extend(domain_records)
        else:
            # Subsample to meet the threshold
            # Randomly select target_max_per_domain records
            subsampled = random.sample(domain_records, target_max_per_domain)
            balanced_records.extend(subsampled)
            logger.info(f"Subsampled domain '{domain}': {current_count} -> {target_max_per_domain}")
    
    return balanced_records

def write_subsample_to_csv(
    records: List[Dict[str, Any]], 
    output_path: Path
) -> None:
    """Write the subsampled records to a CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not records:
        logger.warning("No records to write to subsample CSV")
        # Write empty file with headers if possible
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            f.write("")
        return
    
    # Determine headers from the first record
    fieldnames = list(records[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    
    logger.info(f"Wrote {len(records)} records to {output_path}")

def run_domain_subsample(
    input_path: Path,
    output_path: Path,
    max_domain_proportion: float = 0.30,
    input_format: str = "json"
) -> Tuple[int, int, Dict[str, float]]:
    """
    Run the domain subsampling process.
    
    Args:
        input_path: Path to input JSON or CSV file
        output_path: Path to output CSV file
        max_domain_proportion: Maximum proportion allowed for any single domain
        input_format: "json" or "csv"
    
    Returns:
        Tuple of (original_count, subsampled_count, domain_proportions_after)
    """
    logger.info(f"Starting domain subsampling: {input_path} -> {output_path}")
    
    # Load records
    if input_format == "json":
        records = load_audit_records_from_json(input_path)
    elif input_format == "csv":
        records = load_summaries_from_csv(input_path)
    else:
        raise ValueError(f"Unsupported input format: {input_format}")
    
    original_count = len(records)
    logger.info(f"Loaded {original_count} records")
    
    # Calculate initial proportions
    initial_proportions = calculate_domain_proportions(records)
    logger.info(f"Initial domain proportions: {initial_proportions}")
    
    # Create balanced subsample
    balanced_records = create_balanced_subsample(records, max_domain_proportion)
    subsampled_count = len(balanced_records)
    
    # Calculate final proportions
    final_proportions = calculate_domain_proportions(balanced_records)
    logger.info(f"Final domain proportions: {final_proportions}")
    
    # Write output
    write_subsample_to_csv(balanced_records, output_path)
    
    # Verify no domain exceeds threshold
    for domain, proportion in final_proportions.items():
        if proportion > max_domain_proportion:
            logger.error(f"Domain '{domain}' still exceeds threshold: {proportion:.4f} > {max_domain_proportion}")
            raise ValueError(f"Domain '{domain}' exceeds maximum proportion")
    
    logger.info(f"Domain subsampling complete: {original_count} -> {subsampled_count} records")
    return original_count, subsampled_count, final_proportions

def main() -> int:
    """Main entry point for domain subsampling script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Create a balanced subsample of audit records")
    parser.add_argument(
        "--input", 
        type=Path, 
        default=Path("output/audit_report.json"),
        help="Path to input JSON or CSV file"
    )
    parser.add_argument(
        "--output", 
        type=Path, 
        default=Path("data/subsampled_balanced.csv"),
        help="Path to output CSV file"
    )
    parser.add_argument(
        "--max-proportion", 
        type=float, 
        default=0.30,
        help="Maximum proportion allowed for any single domain (default: 0.30)"
    )
    parser.add_argument(
        "--format", 
        type=str, 
        choices=["json", "csv"], 
        default="json",
        help="Input file format (default: json)"
    )
    
    args = parser.parse_args()
    
    try:
        run_domain_subsample(
            args.input, 
            args.output, 
            args.max_proportion, 
            args.format
        )
        return 0
    except Exception as e:
        logger.error(f"Domain subsampling failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
