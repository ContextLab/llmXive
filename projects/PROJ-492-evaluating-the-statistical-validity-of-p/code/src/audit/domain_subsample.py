"""
Domain Bias Subsampling Module (FR-027)

Creates a balanced subsample of the audit corpus so that no single domain
exceeds 30% of the total before bias adjustment is applied.

This module addresses Constitution Principle I (deterministic reproducibility)
by using seeded random sampling.
"""

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import random

from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.utils.helpers import domain_from_url
from code.src.config import set_rng_seed


MAX_DOMAIN_PROPORTION = 0.30  # No domain should exceed 30% of subsample


def load_audit_records_from_json(json_path: Path) -> List[Dict[str, Any]]:
    """
    Load audit records from the audit_report.json file.

    Args:
        json_path: Path to the audit_report.json file

    Returns:
        List of audit record dictionaries
    """
    logger = get_default_logger()
    logger.info(f"Loading audit records from {json_path}")

    if not json_path.exists():
        logger.error(f"Audit report not found at {json_path}")
        raise FileNotFoundError(f"Audit report not found: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle both list format and dict with 'records' key
    if isinstance(data, list):
        records = data
    elif isinstance(data, dict) and 'records' in data:
        records = data['records']
    else:
        records = data.get('records', [])

    logger.info(f"Loaded {len(records)} audit records")
    return records


def load_summaries_from_csv(csv_path: Path) -> List[Dict[str, Any]]:
    """
    Load summaries from a CSV file (e.g., synthetic validation set).

    Args:
        csv_path: Path to the CSV file

    Returns:
        List of summary dictionaries
    """
    logger = get_default_logger()
    logger.info(f"Loading summaries from {csv_path}")

    if not csv_path.exists():
        logger.error(f"Summaries CSV not found at {csv_path}")
        raise FileNotFoundError(f"Summaries CSV not found: {csv_path}")

    records = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(dict(row))

    logger.info(f"Loaded {len(records)} summaries from CSV")
    return records


def extract_domain_from_record(record: Dict[str, Any]) -> Optional[str]:
    """
    Extract domain from an audit record or summary.

    Looks for domain in the following order:
    1. 'domain' field directly
    2. 'url' field (extracts domain from URL)
    3. 'source_url' field (extracts domain from URL)

    Args:
        record: The record dictionary

    Returns:
        Domain string or None if not found
    """
    # Try direct domain field first
    if 'domain' in record and record['domain']:
        return str(record['domain']).strip().lower()

    # Try URL field
    if 'url' in record and record['url']:
        return domain_from_url(str(record['url']))

    # Try source_url field
    if 'source_url' in record and record['source_url']:
        return domain_from_url(str(record['source_url']))

    return None


def calculate_domain_proportions(records: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate the proportion of records for each domain.

    Args:
        records: List of records with domain information

    Returns:
        Dictionary mapping domain to proportion (0.0 to 1.0)
    """
    domain_counts: Dict[str, int] = {}
    total = 0

    for record in records:
        domain = extract_domain_from_record(record)
        if domain:
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
            total += 1

    if total == 0:
        return {}

    return {domain: count / total for domain, count in domain_counts.items()}


def create_balanced_subsample(
    records: List[Dict[str, Any]],
    max_proportion: float = MAX_DOMAIN_PROPORTION,
    seed: int = 42
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Create a balanced subsample where no domain exceeds max_proportion.

    Uses deterministic seeded sampling for reproducibility (Constitution
    Principle I).

    Algorithm:
    1. Group records by domain
    2. Calculate target count per domain (max_proportion * total)
    3. For each domain, randomly sample up to target count
    4. If total subsample size < 10% of original, raise warning

    Args:
        records: List of all records
        max_proportion: Maximum allowed proportion for any domain (default 0.30)
        seed: Random seed for reproducibility (default 42 from config)

    Returns:
        Tuple of (subsampled records, domain counts in subsample)
    """
    set_rng_seed(seed)
    logger = get_default_logger()
    logger.info(f"Creating balanced subsample with max_proportion={max_proportion}, seed={seed}")

    # Group records by domain
    domain_groups: Dict[str, List[Dict[str, Any]]] = {}
    for record in records:
        domain = extract_domain_from_record(record)
        if domain:
            if domain not in domain_groups:
                domain_groups[domain] = []
            domain_groups[domain].append(record)

    if not domain_groups:
        logger.warning("No records with valid domain found")
        return [], {}

    total_records = len(records)
    target_total = int(total_records * max_proportion) * len(domain_groups)

    # Cap at original total (in case of small number of domains)
    target_total = min(target_total, total_records)

    # Calculate target per domain
    domain_targets: Dict[str, int] = {}
    for domain, group in domain_groups.items():
        # Each domain can contribute up to max_proportion of final subsample
        # But we need to ensure we don't exceed available records
        domain_targets[domain] = min(len(group), int(target_total * max_proportion))

    # Randomly sample from each domain
    subsampled = []
    subsampled_domain_counts: Dict[str, int] = {}

    for domain, group in domain_groups.items():
        target = domain_targets[domain]
        if target >= len(group):
            # Take all records from this domain
            subsampled.extend(group)
            subsampled_domain_counts[domain] = len(group)
        else:
            # Randomly sample
            sampled = random.sample(group, target)
            subsampled.extend(sampled)
            subsampled_domain_counts[domain] = target

    # Shuffle the final subsample for randomness
    random.shuffle(subsampled)

    logger.info(f"Created balanced subsample: {len(subsampled)} records from {len(records)} original")
    logger.info(f"Domain distribution: {subsampled_domain_counts}")

    # Verify no domain exceeds max_proportion
    if len(subsampled) > 0:
        for domain, count in subsampled_domain_counts.items():
            actual_proportion = count / len(subsampled)
            if actual_proportion > max_proportion:
                logger.warning(
                    f"Domain {domain} exceeds max proportion: "
                    f"{actual_proportion:.3f} > {max_proportion}"
                )

    return subsampled, subsampled_domain_counts


def write_subsample_to_csv(
    records: List[Dict[str, Any]],
    output_path: Path,
    domain_counts: Dict[str, int]
) -> None:
    """
    Write subsampled records to a CSV file.

    Args:
        records: List of subsampled records
        output_path: Path to output CSV file
        domain_counts: Dictionary of domain counts for metadata
    """
    logger = get_default_logger()
    logger.info(f"Writing {len(records)} subsampled records to {output_path}")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine fieldnames from first record
    if records:
        fieldnames = list(records[0].keys())
    else:
        fieldnames = ['domain', 'url', 'p_value', 'effect_size']

    # Add metadata fields if not present
    if 'subsampled_at' not in fieldnames:
        fieldnames.append('subsampled_at')
    if 'subsample_seed' not in fieldnames:
        fieldnames.append('subsample_seed')

    # Write CSV
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for record in records:
            row = dict(record)
            row['subsampled_at'] = datetime.utcnow().isoformat() + 'Z'
            row['subsample_seed'] = 42
            writer.writerow(row)

    logger.info(f"Wrote {len(records)} records to {output_path}")

    # Write domain summary as metadata comment in a separate file
    metadata_path = output_path.with_suffix('.domain_summary.json')
    metadata = {
        'total_records': len(records),
        'domain_counts': domain_counts,
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'max_proportion': MAX_DOMAIN_PROPORTION,
        'seed': 42
    }
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Wrote domain summary to {metadata_path}")


def run_domain_subsample(
    input_json_path: Optional[Path] = None,
    input_csv_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    max_proportion: float = MAX_DOMAIN_PROPORTION,
    seed: int = 42
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Main entry point for domain bias subsampling.

    Args:
        input_json_path: Path to audit_report.json (optional)
        input_csv_path: Path to summaries CSV (optional, used if JSON not provided)
        output_path: Path for output CSV (default: data/subsampled_balanced.csv)
        max_proportion: Maximum domain proportion (default: 0.30)
        seed: Random seed (default: 42)

    Returns:
        Tuple of (subsampled records, domain counts)
    """
    logger = get_default_logger()

    # Set default paths
    if output_path is None:
        output_path = Path('data/subsampled_balanced.csv')

    # Load records
    records = []
    if input_json_path and input_json_path.exists():
        records = load_audit_records_from_json(input_json_path)
    elif input_csv_path and input_csv_path.exists():
        records = load_summaries_from_csv(input_csv_path)
    else:
        # Try default paths
        default_json = Path('output/audit_report.json')
        if default_json.exists():
            records = load_audit_records_from_json(default_json)
        else:
            logger.error("No input file provided or found")
            raise FileNotFoundError(
                "No input file provided. Provide input_json_path or input_csv_path"
            )

    if not records:
        logger.warning("No records loaded from input")
        return [], {}

    # Calculate original domain proportions
    original_proportions = calculate_domain_proportions(records)
    logger.info(f"Original domain proportions: {original_proportions}")

    # Create balanced subsample
    subsampled, domain_counts = create_balanced_subsample(
        records, max_proportion=max_proportion, seed=seed
    )

    # Write output
    write_subsample_to_csv(subsampled, output_path, domain_counts)

    return subsampled, domain_counts


def main() -> int:
    """
    CLI entry point for domain subsampling.

    Usage:
        python -m code.src.audit.domain_subsample

    Returns:
        Exit code (0 for success)
    """
    logger = get_default_logger()
    logger.info("Starting domain bias subsampling")

    try:
        # Use default paths
        input_json = Path('output/audit_report.json')
        output_csv = Path('data/subsampled_balanced.csv')

        if input_json.exists():
            logger.info(f"Using input from {input_json}")
        else:
            logger.warning(f"Input file {input_json} not found, will fail if no data available")

        subsampled, domain_counts = run_domain_subsample(
            input_json_path=input_json,
            output_path=output_csv,
            max_proportion=MAX_DOMAIN_PROPORTION,
            seed=42
        )

        logger.info(f"Domain subsampling complete: {len(subsampled)} records")
        logger.info(f"Domain distribution: {domain_counts}")

        # Verify constraint
        if len(subsampled) > 0:
            for domain, count in domain_counts.items():
                proportion = count / len(subsampled)
                if proportion > MAX_DOMAIN_PROPORTION:
                    logger.error(
                        f"CONSTRAINT VIOLATION: Domain {domain} has "
                        f"proportion {proportion:.3f} > {MAX_DOMAIN_PROPORTION}"
                    )
                    return 1

        logger.info("All domain proportions within 30% limit")
        return 0

    except Exception as e:
        logger.error(f"Domain subsampling failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    exit(main())