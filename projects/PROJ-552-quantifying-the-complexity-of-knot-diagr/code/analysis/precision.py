from __future__ import annotations

import pandas as pd
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pathlib import Path


from . import precision_reporting


def generate_precision_summary(
    entries: List[PrecisionValidationEntry],
) -> Dict[str, Any]:
    """
    Generate a summary dictionary from the list of validation entries.

    Args:
        entries: List of PrecisionValidationEntry objects.

    Returns:
        A dictionary containing summary statistics.
    """
    total = len(entries)
    if total == 0:
        return {
            "total_records": 0,
            "crossing_number_valid_count": 0,
            "braid_index_valid_count": 0,
            "crossing_number_valid_pct": 0.0,
            "braid_index_valid_pct": 0.0,
            "fully_valid_count": 0,
            "fully_valid_pct": 0.0,
        }

    cn_valid_count = sum(1 for e in entries if e.crossing_number_valid)
    bi_valid_count = sum(1 for e in entries if e.braid_index_valid)
    fully_valid_count = sum(
        1 for e in entries if e.crossing_number_valid and e.braid_index_valid
    )

    return {
        "total_records": total,
        "crossing_number_valid_count": cn_valid_count,
        "braid_index_valid_count": bi_valid_count,
        "crossing_number_valid_pct": (cn_valid_count / total) * 100,
        "braid_index_valid_pct": (bi_valid_count / total) * 100,
        "fully_valid_count": fully_valid_count,
        "fully_valid_pct": (fully_valid_count / total) * 100,
    }
