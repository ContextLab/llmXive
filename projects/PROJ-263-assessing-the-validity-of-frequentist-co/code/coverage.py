import json
from typing import Dict, List, Any, Optional
import numpy as np
import logging
from pathlib import Path

def check_coverage(lower: float, upper: float, true_value: float) -> bool:
    """Check if the interval contains the true value."""
    return lower <= true_value <= upper

def calculate_coverage_rate(records: List[Dict[str, Any]]) -> float:
    """Calculate the empirical coverage rate from a list of records."""
    if not records:
        return 0.0
    contains_count = sum(1 for r in records if r.get('contains_mean', False))
    return contains_count / len(records)

def create_coverage_record(dataset_id: str, sample_size: int, interval_type: str,
                           interval_lower: float, interval_upper: float,
                           contains_mean: bool, confidence_level: float) -> Dict[str, Any]:
    """Create a coverage record dictionary."""
    return {
        "dataset_id": dataset_id,
        "sample_size": sample_size,
        "interval_type": interval_type,
        "interval_lower": interval_lower,
        "interval_upper": interval_upper,
        "contains_mean": contains_mean,
        "confidence_level": confidence_level
    }

def aggregate_coverage_records(records: List[Dict[str, Any]], 
                               group_by: List[str] = ['dataset_id', 'sample_size', 'interval_type']) -> Dict[str, Any]:
    """Aggregate coverage records by specified keys."""
    groups = {}
    for record in records:
        key = tuple(record.get(k) for k in group_by)
        if key not in groups:
            groups[key] = []
        groups[key].append(record)
    
    aggregated = []
    for key, group_records in groups.items():
        coverage_rate = calculate_coverage_rate(group_records)
        agg_record = {
            "group": dict(zip(group_by, key)),
            "count": len(group_records),
            "coverage_rate": coverage_rate,
            "records": group_records
        }
        aggregated.append(agg_record)
    
    return aggregated

def save_coverage_records(records: List[Dict[str, Any]], output_path: Path):
    """Save coverage records to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(records, f, indent=2)
    logging.info(f"Saved {len(records)} coverage records to {output_path}")

def load_coverage_records(input_path: Path) -> List[Dict[str, Any]]:
    """Load coverage records from a JSON file."""
    if not input_path.exists():
        raise FileNotFoundError(f"File not found: {input_path}")
    
    with open(input_path, 'r') as f:
        return json.load(f)

def main():
    """Test the coverage module."""
    # Create dummy records
    records = [
        create_coverage_record("ds1", 10, "t", 0.1, 0.9, True, 0.95),
        create_coverage_record("ds1", 10, "t", 0.2, 0.8, False, 0.95),
        create_coverage_record("ds1", 10, "boot", 0.15, 0.85, True, 0.95)
    ]
    
    rate = calculate_coverage_rate(records)
    print(f"Coverage rate: {rate}")
    
    # Save to temp file
    test_path = Path("test_coverage.json")
    save_coverage_records(records, test_path)
    
    # Load back
    loaded = load_coverage_records(test_path)
    print(f"Loaded {len(loaded)} records")
    
    test_path.unlink()

if __name__ == "__main__":
    main()
