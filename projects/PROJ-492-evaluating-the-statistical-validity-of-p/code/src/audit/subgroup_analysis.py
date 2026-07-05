"""
Subgroup Analysis Module

Implements subgroup prevalence analysis with Fisher's exact test and
dynamic Bonferroni correction. Ensures publication year is extracted
and available for stratified analysis.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from collections import defaultdict
import numpy as np
from scipy import stats

from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.config import set_rng_seed


def set_rng_seed_for_subgroup_analysis(seed: int = 42):
    """Set random seed for reproducibility in subgroup analysis."""
    set_rng_seed(seed)


def load_audit_records_from_json(file_path: Path) -> List[Dict[str, Any]]:
    """Load audit records from a JSON file."""
    logger = get_default_logger(__name__)
    try:
        with open(file_path, 'r') as f:
            records = json.load(f)
        logger.info(f"Loaded {len(records)} audit records from {file_path}")
        return records
    except Exception as e:
        logger.error(f"Failed to load audit records: {e}", extra={"error_code": "ERR-201"})
        raise


def extract_domain_from_record(record: Dict[str, Any]) -> Optional[str]:
    """Extract domain from an audit record."""
    return record.get('domain')


def extract_year_from_record(record: Dict[str, Any]) -> Optional[int]:
    """
    Extract publication year from an audit record.
    
    This function verifies that the publication year field exists and
    is accessible for subgroup analysis stratification.
    
    Args:
        record: Audit record dictionary containing extracted metadata
        
    Returns:
        The publication year as an integer, or None if not present
    """
    year = record.get('publication_year')
    if year is not None:
        # Ensure it's an integer
        try:
            return int(year)
        except (ValueError, TypeError):
            return None
    return None


def group_records_by_subgroup(
    records: List[Dict[str, Any]], 
    subgroup_key: str
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group audit records by a specific subgroup key (e.g., 'domain', 'publication_year').
    
    Args:
        records: List of audit records
        subgroup_key: The key to group by (e.g., 'domain', 'publication_year')
        
    Returns:
        Dictionary mapping subgroup values to lists of records
    """
    groups = defaultdict(list)
    for record in records:
        if subgroup_key == 'publication_year':
            value = extract_year_from_record(record)
        else:
            value = record.get(subgroup_key)
        
        if value is not None:
            groups[value].append(record)
        else:
            # Group missing values separately
            groups['Unknown'].append(record)
    
    return dict(groups)


def count_inconsistent_records(records: List[Dict[str, Any]]) -> int:
    """Count the number of inconsistent records in a list."""
    return sum(1 for r in records if r.get('is_inconsistent', False))


def compute_subgroup_prevalence(
    total_count: int, 
    inconsistent_count: int
) -> float:
    """Compute prevalence rate for a subgroup."""
    if total_count == 0:
        return 0.0
    return inconsistent_count / total_count


def compute_fisher_exact_pvalue(
    group1_inconsistent: int,
    group1_total: int,
    group2_inconsistent: int,
    group2_total: int
) -> Optional[float]:
    """
    Compute Fisher's exact test p-value for comparing two subgroups.
    
    Args:
        group1_inconsistent: Inconsistent count in group 1
        group1_total: Total count in group 1
        group2_inconsistent: Inconsistent count in group 2
        group2_total: Total count in group 2
        
    Returns:
        P-value from Fisher's exact test, or None if computation fails
    """
    try:
        # Create contingency table
        table = [
            [group1_inconsistent, group1_total - group1_inconsistent],
            [group2_inconsistent, group2_total - group2_inconsistent]
        ]
        
        _, p_value = stats.fisher_exact(table, alternative='two-sided')
        return p_value
    except Exception:
        return None


def apply_dynamic_bonferroni(p_value: float, num_comparisons: int) -> float:
    """
    Apply Bonferroni correction dynamically based on number of comparisons.
    
    Args:
        p_value: Raw p-value
        num_comparisons: Number of comparisons being made
        
    Returns:
        Bonferroni-corrected p-value
    """
    if num_comparisons == 0:
        return p_value
    return p_value * num_comparisons


def analyze_subgroups(
    records: List[Dict[str, Any]],
    subgroup_keys: List[str] = ['domain', 'publication_year']
) -> Dict[str, Any]:
    """
    Perform subgroup analysis on audit records.
    
    Args:
        records: List of audit records
        subgroup_keys: List of keys to analyze subgroups by
        
    Returns:
        Dictionary containing subgroup analysis results
    """
    results = {}
    
    for key in subgroup_keys:
        groups = group_records_by_subgroup(records, key)
        group_results = {}
        
        for group_name, group_records in groups.items():
            total = len(group_records)
            inconsistent = count_inconsistent_records(group_records)
            prevalence = compute_subgroup_prevalence(total, inconsistent)
            
            group_results[group_name] = {
                'total_count': total,
                'inconsistent_count': inconsistent,
                'prevalence': prevalence,
                'records': group_records
            }
        
        results[key] = group_results
    
    return results


def write_subgroup_report(
    results: Dict[str, Any],
    output_path: Path
):
    """Write subgroup analysis results to a JSON file."""
    logger = get_default_logger(__name__)
    try:
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Subgroup report written to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write subgroup report: {e}", extra={"error_code": "ERR-202"})
        raise


def write_subgroup_csv(
    results: Dict[str, Any],
    output_path: Path
):
    """Write subgroup analysis results to a CSV file."""
    import csv
    logger = get_default_logger(__name__)
    
    try:
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            # Header
            writer.writerow(['subgroup_key', 'group_name', 'total_count', 'inconsistent_count', 'prevalence'])
            
            for key, groups in results.items():
                for group_name, data in groups.items():
                    writer.writerow([
                        key,
                        group_name,
                        data['total_count'],
                        data['inconsistent_count'],
                        f"{data['prevalence']:.4f}"
                    ])
        
        logger.info(f"Subgroup CSV written to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write subgroup CSV: {e}", extra={"error_code": "ERR-202"})
        raise


def run_subgroup_analysis(
    input_path: Path,
    output_json_path: Path,
    output_csv_path: Path
):
    """
    Main entry point for running subgroup analysis.
    
    Args:
        input_path: Path to audit_report.json
        output_json_path: Path for JSON output
        output_csv_path: Path for CSV output
    """
    logger = get_default_logger(__name__)
    logger.info("Starting subgroup analysis")
    
    # Load records
    records = load_audit_records_from_json(input_path)
    
    # Verify publication year is available
    years_available = [extract_year_from_record(r) for r in records]
    valid_years = [y for y in years_available if y is not None]
    
    logger.info(f"Found {len(valid_years)} records with valid publication years")
    
    if len(valid_years) == 0:
        logger.warning("No valid publication years found. Year-based subgrouping will be limited.")
    
    # Run analysis
    results = analyze_subgroups(records)
    
    # Write outputs
    write_subgroup_report(results, output_json_path)
    write_subgroup_csv(results, output_csv_path)
    
    logger.info("Subgroup analysis completed successfully")


def main():
    """Command-line entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Run subgroup analysis on audit records")
    parser.add_argument("--input", type=Path, required=True, help="Input audit_report.json")
    parser.add_argument("--output-json", type=Path, required=True, help="Output JSON file")
    parser.add_argument("--output-csv", type=Path, required=True, help="Output CSV file")
    
    args = parser.parse_args()
    
    run_subgroup_analysis(args.input, args.output_json, args.output_csv)


if __name__ == "__main__":
    main()