"""
Subgroup Analysis Module.

Performs subgroup prevalence analysis and Fisher's exact test with
Bonferroni correction.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from collections import defaultdict

import numpy as np
from scipy import stats

from code.src.config import set_rng_seed, SEED
from code.src.utils.logger import get_default_logger, AuditLogger

logger = get_default_logger(__name__)

def set_rng_seed_for_subgroup_analysis(seed: Optional[int] = None) -> None:
    """Set RNG seed for subgroup analysis."""
    set_rng_seed(seed)

def load_audit_records_from_json(filepath: Path) -> List[Dict[str, Any]]:
    """Load audit records from JSON."""
    with open(filepath, 'r') as f:
        return json.load(f)

def extract_domain_from_record(record: Dict[str, Any]) -> str:
    """Extract domain from record."""
    return record.get("domain", "unknown")

def extract_year_from_record(record: Dict[str, Any]) -> int:
    """Extract year from record."""
    year = record.get("year")
    if year is None:
        return 0
    return int(year)

def group_records_by_subgroup(records: List[Dict[str, Any]], key: str = "domain") -> Dict[str, List[Dict[str, Any]]]:
    """Group records by a specific key (e.g., domain, year)."""
    groups = defaultdict(list)
    for record in records:
        val = record.get(key, "unknown")
        groups[val].append(record)
    return dict(groups)

def count_inconsistent_records(records: List[Dict[str, Any]]) -> int:
    """Count inconsistent records in a group."""
    return sum(1 for r in records if r.get("is_inconsistent", False))

def compute_subgroup_prevalence(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute prevalence for a subgroup."""
    total = len(records)
    if total == 0:
        return {"prevalence": 0.0, "count": 0}
    
    inconsistent = count_inconsistent_records(records)
    return {
        "prevalence": inconsistent / total,
        "inconsistent_count": inconsistent,
        "total_count": total
    }

def compute_fisher_exact_pvalue(records: List[Dict[str, Any]], reference_records: List[Dict[str, Any]]) -> float:
    """
    Compute Fisher's exact test p-value comparing subgroup to reference.

    Args:
        records: Subgroup records.
        reference_records: Reference records (e.g., rest of corpus).

    Returns:
        Two-tailed p-value.
    """
    set_rng_seed_for_subgroup_analysis()
    
    # Build contingency table
    # Rows: Subgroup, Reference
    # Cols: Inconsistent, Consistent
    
    a = count_inconsistent_records(records)
    b = len(records) - a
    
    c = count_inconsistent_records(reference_records)
    d = len(reference_records) - c
    
    if a + b == 0 or c + d == 0:
        return 1.0
    
    # Fisher's exact test
    _, p_value = stats.fisher_exact([[a, b], [c, d]], alternative='two-sided')
    return p_value

def apply_dynamic_bonferroni(p_value: float, n_groups: int) -> float:
    """Apply Bonferroni correction dynamically based on number of groups."""
    return min(p_value * n_groups, 1.0)

def analyze_subgroups(records: List[Dict[str, Any]], group_by: str = "domain") -> List[Dict[str, Any]]:
    """
    Analyze all subgroups.

    Args:
        records: Full list of records.
        group_by: Key to group by.

    Returns:
        List of analysis results per group.
    """
    set_rng_seed_for_subgroup_analysis()
    groups = group_records_by_subgroup(records, group_by)
    results = []
    
    n_groups = len(groups)
    
    for group_name, group_records in groups.items():
        if len(group_records) < 10: # Minimum size filter
            continue
        
        prevalence_data = compute_subgroup_prevalence(group_records)
        
        # Reference is everything else
        reference = [r for r in records if r not in group_records]
        
        p_val = compute_fisher_exact_pvalue(group_records, reference)
        corrected_p = apply_dynamic_bonferroni(p_val, n_groups)
        
        results.append({
            "group": group_name,
            "count": len(group_records),
            **prevalence_data,
            "fisher_p_value": p_val,
            "bonferroni_corrected_p": corrected_p
        })
    
    return results

def write_subgroup_report(results: List[Dict[str, Any]], output_path: Path) -> None:
    """Write subgroup analysis results to JSON."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Subgroup report written to {output_path}")

def write_subgroup_csv(results: List[Dict[str, Any]], output_path: Path) -> None:
    """Write subgroup analysis results to CSV."""
    import csv
    with open(output_path, 'w', newline='') as f:
        if not results:
            return
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    logger.info(f"Subgroup CSV written to {output_path}")

def run_subgroup_analysis(input_path: Path, output_json: Path, output_csv: Path, group_by: str = "domain") -> None:
    """Run full subgroup analysis pipeline."""
    records = load_audit_records_from_json(input_path)
    results = analyze_subgroups(records, group_by)
    write_subgroup_report(results, output_json)
    write_subgroup_csv(results, output_csv)

def main():
    """Main entry point."""
    input_path = Path("output/audit_report.json")
    output_json = Path("output/subgroup_report.json")
    output_csv = Path("output/subgroup_report.csv")
    
    if not input_path.exists():
        logger.warning(f"Input file {input_path} not found.")
        return
        
    run_subgroup_analysis(input_path, output_json, output_csv)

if __name__ == "__main__":
    main()
