"""
Pure calculation functions for invariant coverage analysis.

This module contains the core logic for analyzing invariant coverage
across the knot dataset, separated from reporting concerns.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from reproducibility.logs import get_logger

logger = get_logger(__name__)

REQUIRED_INVARIANTS = [
    "crossing_number",
    "braid_index",
    "hyperbolic_volume",
    "is_alternating",
    "dt_code",
    "braid_word",
]

@dataclass
class InvariantCoverageEntry:
    """Record of invariant availability for a single knot."""
    knot_id: str
    crossing_number_present: bool
    braid_index_present: bool
    hyperbolic_volume_present: bool
    is_alternating_present: bool
    dt_code_present: bool
    braid_word_present: bool
    total_present: int
    total_required: int

@dataclass
class InvariantCoverageReport:
    """Aggregated statistics on invariant coverage."""
    total_knots: int
    coverage_per_invariant: Dict[str, float]
    missing_per_invariant: Dict[str, int]
    fully_covered_count: int
    partially_covered_count: int
    fully_missing_count: int
    entries: List[InvariantCoverageEntry] = field(default_factory=list)

def load_cleaned_knots_data(data_path: Path) -> List[Dict[str, Any]]:
    """Load cleaned knot data from CSV."""
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        return []
    
    records = []
    with open(data_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    return records

def _is_present(value: Any) -> bool:
    """Check if a value is considered present (not None, not empty string)."""
    if value is None:
        return False
    if isinstance(value, str) and value.strip() == "":
        return False
    return True

def analyze_knot_invariant_coverage(
    records: List[Dict[str, Any]]
) -> Tuple[List[InvariantCoverageEntry], Dict[str, int]]:
    """
    Analyze invariant coverage for each knot and compute missing counts.
    
    Returns:
        Tuple of (list of coverage entries, dict of missing counts per invariant)
    """
    entries = []
    missing_counts = {inv: 0 for inv in REQUIRED_INVARIANTS}
    
    for record in records:
        knot_id = record.get("knot_id", "unknown")
        
        # Check each invariant
        checks = {}
        for inv in REQUIRED_INVARIANTS:
            present = _is_present(record.get(inv))
            checks[inv] = present
            if not present:
                missing_counts[inv] += 1
        
        total_present = sum(1 for v in checks.values() if v)
        
        entry = InvariantCoverageEntry(
            knot_id=knot_id,
            crossing_number_present=checks["crossing_number"],
            braid_index_present=checks["braid_index"],
            hyperbolic_volume_present=checks["hyperbolic_volume"],
            is_alternating_present=checks["is_alternating"],
            dt_code_present=checks["dt_code"],
            braid_word_present=checks["braid_word"],
            total_present=total_present,
            total_required=len(REQUIRED_INVARIANTS),
        )
        entries.append(entry)
    
    return entries, missing_counts

def calculate_coverage_statistics(
    entries: List[InvariantCoverageEntry],
    missing_counts: Dict[str, int],
    total_knots: int
) -> InvariantCoverageReport:
    """
    Calculate aggregated coverage statistics from individual entries.
    
    Args:
        entries: List of InvariantCoverageEntry objects
        missing_counts: Dict mapping invariant name to missing count
        total_knots: Total number of knots in dataset
        
    Returns:
        InvariantCoverageReport with aggregated statistics
    """
    if total_knots == 0:
        total_knots = len(entries)
        
    coverage_per_inv = {}
    for inv in REQUIRED_INVARIANTS:
        missing = missing_counts.get(inv, 0)
        present = total_knots - missing
        coverage_per_inv[inv] = (present / total_knots * 100) if total_knots > 0 else 0.0
    
    fully_covered = sum(1 for e in entries if e.total_present == e.total_required)
    fully_missing = sum(1 for e in entries if e.total_present == 0)
    partially_covered = total_knots - fully_covered - fully_missing
    
    return InvariantCoverageReport(
        total_knots=total_knots,
        coverage_per_invariant=coverage_per_inv,
        missing_per_invariant=missing_counts,
        fully_covered_count=fully_covered,
        partially_covered_count=partially_covered,
        fully_missing_count=fully_missing,
        entries=entries,
    )
