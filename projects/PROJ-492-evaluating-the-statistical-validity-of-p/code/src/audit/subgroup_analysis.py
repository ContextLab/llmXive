"""
Subgroup prevalence and Fisher's exact-test analysis (FR-032).

Produces output/subgroup_report.json with domain, year, counts, prevalence,
and p-value. Applies dynamic Bonferroni correction per constraint-preservation-925e1e46.
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
from code.src.audit.prevalence import apply_bonferroni_correction
from code.src.models.data_models import AuditRecord

# Constants
MIN_SUBGROUP_SIZE = 10  # Minimum number of summaries per subgroup to include
DEFAULT_ALPHA = 0.05
OUTPUT_FILENAME = "subgroup_report.json"
OUTPUT_CSV_FILENAME = "subgroup_report.csv"

def set_rng_seed_for_subgroup_analysis(seed: int = 42) -> None:
    """Set RNG seed for reproducibility (Constitution Principle I)."""
    set_rng_seed(seed)
    logging.getLogger(__name__).info(f"Set RNG seed for subgroup analysis: {seed}")

def load_audit_records_from_json(input_path: Path) -> List[Dict[str, Any]]:
    """Load audit records from the audit report JSON file."""
    logger = get_default_logger(__name__)
    if not input_path.exists():
        logger.error(f"Audit report not found: {input_path}")
        raise FileNotFoundError(f"Audit report not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both list format and dict with 'records' key
    if isinstance(data, list):
        records = data
    elif isinstance(data, dict) and 'records' in data:
        records = data['records']
    else:
        records = [data] if isinstance(data, dict) else []
    
    logger.info(f"Loaded {len(records)} audit records from {input_path}")
    return records

def extract_domain_from_record(record: Dict[str, Any]) -> Optional[str]:
    """Extract domain from an audit record."""
    # Try multiple possible field names
    for field in ['domain', 'url_domain', 'source_domain']:
        if field in record and record[field]:
            return str(record[field])
    
    # Extract from URL if available
    if 'url' in record and record['url']:
        url = str(record['url'])
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            pass
    
    return "unknown"

def extract_year_from_record(record: Dict[str, Any]) -> Optional[int]:
    """Extract publication year from an audit record."""
    # Try multiple possible field names
    for field in ['year', 'publication_year', 'test_year', 'date_year']:
        if field in record and record[field]:
            try:
                return int(record[field])
            except (ValueError, TypeError):
                pass
    
    # Try to extract from date field
    if 'date' in record and record['date']:
        date_str = str(record['date'])
        try:
            # Try YYYY format
            if len(date_str) == 4:
                return int(date_str)
            # Try YYYY-MM-DD format
            if '-' in date_str:
                year_str = date_str.split('-')[0]
                return int(year_str)
        except (ValueError, TypeError):
            pass
    
    return None

def group_records_by_subgroup(
    records: List[Dict[str, Any]],
    group_by: str = "domain"
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group audit records by subgroup (domain or year).
    
    Args:
        records: List of audit records
        group_by: Either "domain" or "year"
    
    Returns:
        Dictionary mapping subgroup key to list of records
    """
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    
    for record in records:
        if group_by == "domain":
            key = extract_domain_from_record(record)
        elif group_by == "year":
            year = extract_year_from_record(record)
            key = str(year) if year else "unknown"
        else:
            key = "unknown"
        
        groups[key].append(record)
    
    return dict(groups)

def count_inconsistent_records(records: List[Dict[str, Any]]) -> int:
    """Count records flagged as inconsistent."""
    count = 0
    for record in records:
        # Check various inconsistency flag field names
        is_inconsistent = False
        for field in ['is_inconsistent', 'inconsistent', 'flagged', 'inconsistency_flag']:
            if field in record:
                val = record[field]
                if isinstance(val, bool):
                    is_inconsistent = val
                elif isinstance(val, str):
                    is_inconsistent = val.lower() in ('true', 'yes', '1')
                break
        if is_inconsistent:
            count += 1
    return count

def compute_subgroup_prevalence(
    records: List[Dict[str, Any]]
) -> Tuple[int, int, float]:
    """
    Compute prevalence statistics for a subgroup.
    
    Returns:
        Tuple of (total_count, inconsistent_count, prevalence_rate)
    """
    total = len(records)
    inconsistent = count_inconsistent_records(records)
    prevalence = inconsistent / total if total > 0 else 0.0
    return total, inconsistent, prevalence

def compute_fisher_exact_pvalue(
    records: List[Dict[str, Any]],
    reference_records: List[Dict[str, Any]]
) -> float:
    """
    Compute Fisher's exact test p-value comparing subgroup to reference.
    
    Uses a 2x2 contingency table:
    - Subgroup: inconsistent vs consistent
    - Reference: inconsistent vs consistent
    
    Args:
        records: Records in the subgroup
        reference_records: Reference records (e.g., all other groups combined)
    
    Returns:
        Two-sided p-value from Fisher's exact test
    """
    # Build contingency table
    subgroup_inconsistent = count_inconsistent_records(records)
    subgroup_total = len(records)
    subgroup_consistent = subgroup_total - subgroup_inconsistent
    
    ref_inconsistent = count_inconsistent_records(reference_records)
    ref_total = len(reference_records)
    ref_consistent = ref_total - ref_inconsistent
    
    # Avoid zero counts in contingency table
    contingency = [
        [subgroup_inconsistent, subgroup_consistent],
        [ref_inconsistent, ref_consistent]
    ]
    
    # Fisher's exact test (two-sided)
    try:
        _, p_value = stats.fisher_exact(contingency, alternative='two-sided')
        return float(p_value)
    except Exception as e:
        # Fallback to chi-square if Fisher's fails
        try:
            _, p_value, _, _ = stats.chi2_contingency(contingency)
            return float(p_value)
        except Exception:
            return 1.0  # Return non-significant if all else fails

def apply_dynamic_bonferroni(
    p_values: List[float],
    alpha: float = DEFAULT_ALPHA
) -> Tuple[List[float], List[float]]:
    """
    Apply Bonferroni correction dynamically based on number of comparisons.
    
    Args:
        p_values: List of raw p-values
        alpha: Significance threshold (default 0.05)
    
    Returns:
        Tuple of (adjusted_p_values, corrected_thresholds)
    """
    n_comparisons = len(p_values)
    if n_comparisons == 0:
        return [], []
    
    # Bonferroni correction: alpha / n
    corrected_alpha = alpha / n_comparisons
    
    # Adjusted p-values (multiply by n, capped at 1.0)
    adjusted = [min(p * n_comparisons, 1.0) for p in p_values]
    
    return adjusted, [corrected_alpha] * n_comparisons

def analyze_subgroups(
    records: List[Dict[str, Any]],
    group_by: str = "domain",
    alpha: float = DEFAULT_ALPHA,
    min_size: int = MIN_SUBGROUP_SIZE
) -> List[Dict[str, Any]]:
    """
    Perform subgroup analysis with Fisher's exact test and Bonferroni correction.
    
    Args:
        records: List of audit records
        group_by: Either "domain" or "year"
        alpha: Significance threshold
        min_size: Minimum subgroup size to include in analysis
    
    Returns:
        List of subgroup analysis results
    """
    logger = get_default_logger(__name__)
    
    # Group records
    groups = group_records_by_subgroup(records, group_by)
    logger.info(f"Found {len(groups)} unique {group_by}s")
    
    # Filter groups by minimum size
    filtered_groups = {
        k: v for k, v in groups.items() 
        if len(v) >= min_size
    }
    logger.info(f"Groups meeting minimum size ({min_size}): {len(filtered_groups)}")
    
    if not filtered_groups:
        logger.warning(f"No groups meet minimum size requirement of {min_size}")
        return []
    
    # Create reference group (all records not in each subgroup)
    all_records = records
    results = []
    raw_p_values = []
    
    # First pass: collect all raw p-values
    for subgroup_key, subgroup_records in filtered_groups.items():
        # Create reference: all records minus this subgroup
        reference_ids = set(id(r) for r in all_records) - set(id(r) for r in subgroup_records)
        reference_records = [r for r in all_records if id(r) in reference_ids]
        
        if len(reference_records) == 0:
            reference_records = all_records[:1]  # Fallback
        
        p_value = compute_fisher_exact_pvalue(subgroup_records, reference_records)
        raw_p_values.append(p_value)
    
    # Apply Bonferroni correction
    adjusted_p_values, corrected_thresholds = apply_dynamic_bonferroni(
        raw_p_values, alpha
    )
    
    # Second pass: build results with adjusted p-values
    for idx, (subgroup_key, subgroup_records) in enumerate(filtered_groups.items()):
        total, inconsistent, prevalence = compute_subgroup_prevalence(subgroup_records)
        
        # Create reference for p-value computation
        reference_ids = set(id(r) for r in all_records) - set(id(r) for r in subgroup_records)
        reference_records = [r for r in all_records if id(r) in reference_ids]
        if len(reference_records) == 0:
            reference_records = all_records[:1]
        
        raw_p = raw_p_values[idx]
        adjusted_p = adjusted_p_values[idx]
        threshold = corrected_thresholds[idx]
        
        result = {
            "subgroup_key": subgroup_key,
            "subgroup_type": group_by,
            "total_count": total,
            "inconsistent_count": inconsistent,
            "prevalence": round(prevalence, 6),
            "raw_p_value": round(raw_p, 6),
            "adjusted_p_value": round(adjusted_p, 6),
            "bonferroni_threshold": round(threshold, 6),
            "is_significant": adjusted_p < threshold,
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
        
        # Add year-specific fields
        if group_by == "year":
            try:
                result["year"] = int(subgroup_key)
            except ValueError:
                result["year"] = None
        else:
            result["domain"] = subgroup_key
        
        results.append(result)
        logger.info(
            f"Subgroup {subgroup_key}: n={total}, inconsistent={inconsistent}, "
            f"prevalence={prevalence:.4f}, p_adj={adjusted_p:.4f}"
        )
    
    # Sort by adjusted p-value
    results.sort(key=lambda x: x["adjusted_p_value"])
    
    return results

def write_subgroup_report(
    results: List[Dict[str, Any]],
    output_dir: Path,
    filename: str = OUTPUT_FILENAME
) -> Path:
    """Write subgroup analysis results to JSON file."""
    output_path = output_dir / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat(),
            "version": "1.0",
            "min_subgroup_size": MIN_SUBGROUP_SIZE,
            "bonferroni_correction": True,
            "fisher_exact_test": True
        },
        "summary": {
            "total_subgroups": len(results),
            "significant_subgroups": sum(1 for r in results if r["is_significant"])
        },
        "subgroups": results
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    
    logging.getLogger(__name__).info(f"Wrote subgroup report to {output_path}")
    return output_path

def write_subgroup_csv(
    results: List[Dict[str, Any]],
    output_dir: Path,
    filename: str = OUTPUT_CSV_FILENAME
) -> Path:
    """Write subgroup analysis results to CSV file for easy inspection."""
    import csv
    output_path = output_dir / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not results:
        # Write empty file with headers
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "subgroup_key", "subgroup_type", "total_count",
                "inconsistent_count", "prevalence", "raw_p_value",
                "adjusted_p_value", "bonferroni_threshold", "is_significant"
            ])
        return output_path
    
    # Determine columns
    columns = [
        "subgroup_key", "subgroup_type", "total_count",
        "inconsistent_count", "prevalence", "raw_p_value",
        "adjusted_p_value", "bonferroni_threshold", "is_significant"
    ]
    
    # Add domain or year column
    if results[0].get("domain"):
        columns.insert(1, "domain")
    elif results[0].get("year"):
        columns.insert(1, "year")
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(results)
    
    logging.getLogger(__name__).info(f"Wrote subgroup CSV to {output_path}")
    return output_path

def run_subgroup_analysis(
    input_path: Path,
    output_dir: Path,
    group_by: str = "domain",
    alpha: float = DEFAULT_ALPHA,
    min_size: int = MIN_SUBGROUP_SIZE,
    seed: int = 42
) -> Dict[str, Path]:
    """
    Run complete subgroup analysis pipeline.
    
    Args:
        input_path: Path to audit report JSON
        output_dir: Directory for output files
        group_by: Grouping variable ("domain" or "year")
        alpha: Significance threshold
        min_size: Minimum subgroup size
        seed: RNG seed for reproducibility
    
    Returns:
        Dictionary mapping output type to file path
    """
    set_rng_seed_for_subgroup_analysis(seed)
    logger = get_default_logger(__name__)
    
    logger.info(f"Starting subgroup analysis (group_by={group_by})")
    
    # Load records
    records = load_audit_records_from_json(input_path)
    
    # Perform analysis
    results = analyze_subgroups(records, group_by, alpha, min_size)
    
    # Write outputs
    json_path = write_subgroup_report(results, output_dir)
    csv_path = write_subgroup_csv(results, output_dir)
    
    logger.info(f"Subgroup analysis complete: {len(results)} subgroups analyzed")
    
    return {
        "json_report": json_path,
        "csv_report": csv_path
    }

def main() -> int:
    """Main entry point for subgroup analysis CLI."""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(
        description="Run subgroup prevalence and Fisher's exact-test analysis"
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=Path("output/audit_report.json"),
        help="Path to input audit report JSON"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=Path("output"),
        help="Directory for output files"
    )
    parser.add_argument(
        "--group-by", "-g",
        choices=["domain", "year"],
        default="domain",
        help="Grouping variable for subgroup analysis"
    )
    parser.add_argument(
        "--alpha", "-a",
        type=float,
        default=DEFAULT_ALPHA,
        help=f"Significance threshold (default: {DEFAULT_ALPHA})"
    )
    parser.add_argument(
        "--min-size", "-m",
        type=int,
        default=MIN_SUBGROUP_SIZE,
        help=f"Minimum subgroup size (default: {MIN_SUBGROUP_SIZE})"
    )
    parser.add_argument(
        "--seed", "-s",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    
    args = parser.parse_args()
    
    try:
        paths = run_subgroup_analysis(
            input_path=args.input,
            output_dir=args.output_dir,
            group_by=args.group_by,
            alpha=args.alpha,
            min_size=args.min_size,
            seed=args.seed
        )
        
        print(f"Subgroup analysis complete.")
        print(f"  JSON report: {paths['json_report']}")
        print(f"  CSV report: {paths['csv_report']}")
        return 0
        
    except Exception as e:
        logger = get_default_logger(__name__)
        logger.error(f"Subgroup analysis failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())