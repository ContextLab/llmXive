import json
from typing import Dict, List, Any, Optional
import numpy as np
import logging
from pathlib import Path

from config import get_processed_data_dir
from data_models.schemas import validate_coverage_record

logger = logging.getLogger(__name__)


def check_coverage(interval_lower: float, interval_upper: float, population_mean: float) -> bool:
    """
    Check if the population mean is contained within the interval [lower, upper].

    Args:
        interval_lower: Lower bound of the confidence interval.
        interval_upper: Upper bound of the confidence interval.
        population_mean: The true population mean (ground truth).

    Returns:
        True if population_mean is within the interval, False otherwise.
    """
    return interval_lower <= population_mean <= interval_upper


def calculate_coverage_rate(coverage_records: List[Dict[str, Any]]) -> float:
    """
    Calculate the empirical coverage rate from a list of coverage records.

    Args:
        coverage_records: List of records containing 'contains_mean' boolean.

    Returns:
        Float between 0.0 and 1.0 representing the proportion of intervals containing the mean.
    """
    if not coverage_records:
        return 0.0
    contains_count = sum(1 for rec in coverage_records if rec.get('contains_mean', False))
    return contains_count / len(coverage_records)


def create_coverage_record(
    dataset_id: str,
    sample_size: int,
    interval_lower: float,
    interval_upper: float,
    population_mean: float,
    confidence_level: float = 0.95
) -> Dict[str, Any]:
    """
    Create a single coverage record dictionary.

    Args:
        dataset_id: Identifier for the dataset used.
        sample_size: Size of the sample drawn.
        interval_lower: Lower bound of the calculated interval.
        interval_upper: Upper bound of the calculated interval.
        population_mean: The ground truth mean used for comparison.
        confidence_level: Nominal confidence level (e.g., 0.95).

    Returns:
        Dictionary representing the coverage record.
    """
    contains_mean = check_coverage(interval_lower, interval_upper, population_mean)
    record = {
        "dataset_id": dataset_id,
        "sample_size": sample_size,
        "interval_lower": float(interval_lower),
        "interval_upper": float(interval_upper),
        "contains_mean": bool(contains_mean),
        "confidence_level": float(confidence_level),
        "population_mean": float(population_mean)
    }
    
    # Validate against schema
    if not validate_coverage_record(record):
        logger.warning(f"Generated coverage record failed schema validation: {record}")
        
    return record


def aggregate_coverage_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate coverage records by dataset_id and sample_size.

    Args:
        records: List of coverage records.

    Returns:
        Dictionary mapping (dataset_id, sample_size) to coverage statistics.
    """
    aggregation: Dict[tuple, List[Dict]] = {}
    
    for rec in records:
        key = (rec['dataset_id'], rec['sample_size'])
        if key not in aggregation:
            aggregation[key] = []
        aggregation[key].append(rec)
    
    results = {}
    for key, group in aggregation.items():
        dataset_id, sample_size = key
        rate = calculate_coverage_rate(group)
        results[f"{dataset_id}_n{sample_size}"] = {
            "dataset_id": dataset_id,
            "sample_size": sample_size,
            "coverage_rate": rate,
            "total_trials": len(group),
            "successful_trials": sum(1 for r in group if r['contains_mean'])
        }
    return results


def save_coverage_records(records: List[Dict[str, Any]], output_path: Optional[str] = None) -> str:
    """
    Save raw coverage records to a JSON file.

    Args:
        records: List of coverage record dictionaries.
        output_path: Optional path to save to. If None, uses default processed data dir.

    Returns:
        The path where the file was saved.
    """
    if output_path is None:
        processed_dir = get_processed_data_dir()
        output_path = str(processed_dir / "coverage_records.json")
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2)
    
    logger.info(f"Saved {len(records)} coverage records to {output_path}")
    return output_path


def load_coverage_records(input_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load raw coverage records from a JSON file.

    Args:
        input_path: Optional path to load from. If None, uses default processed data dir.

    Returns:
        List of coverage record dictionaries.
    """
    if input_path is None:
        processed_dir = get_processed_data_dir()
        input_path = str(processed_dir / "coverage_records.json")
    
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Coverage records file not found at {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.info(f"Loaded {len(data)} coverage records from {input_path}")
    return data


def main():
    """
    Main entry point for testing coverage functionality.
    This is typically called by the simulation loop, but provided here for testing.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    record = create_coverage_record(
        dataset_id="wine_test",
        sample_size=10,
        interval_lower=0.4,
        interval_upper=0.6,
        population_mean=0.5,
        confidence_level=0.95
    )
    
    print(f"Generated Record: {record}")
    print(f"Contains Mean: {record['contains_mean']}")
    
    # Save to file
    path = save_coverage_records([record])
    print(f"Saved to: {path}")

if __name__ == "__main__":
    main()