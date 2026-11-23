"""Stratified sampling for validation."""
import os
import json
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from utils.logging import log_operation, get_logger, retry_on_failure
from utils.io import safe_write_csv, load_json

logger = get_logger()


class StratifiedSamplingError(Exception):
    pass


def load_generated_reports(input_path: str) -> List[Dict[str, Any]]:
    """Load generated reports from CSV or JSON."""
    log_operation("load_generated_reports", path=input_path)
    if not os.path.exists(input_path):
        # Try to find the merged dataset
        merged_path = "data/processed/merged_dataset.csv"
        if os.path.exists(merged_path):
            input_path = merged_path
        else:
            raise FileNotFoundError(f"Reports not found at {input_path}")
    
    if input_path.endswith('.csv'):
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    else:
        return load_json(input_path)


def validate_report_structure(reports: List[Dict[str, Any]]) -> bool:
    """Ensure reports have required fields."""
    required = ['id', 'text']
    for r in reports:
        if not all(k in r for k in required):
            return False
    return True


def stratify_reports(reports: List[Dict[str, Any]], stratify_by: str = 'strategy') -> Dict[str, List[Dict[str, Any]]]:
    """Group reports by a specific field."""
    strata = {}
    for r in reports:
        key = r.get(stratify_by, 'unknown')
        if key not in strata:
            strata[key] = []
        strata[key].append(r)
    return strata


def sample_from_strata(strata: Dict[str, List[Dict[str, Any]]], n_per_strata: int) -> List[Dict[str, Any]]:
    """Sample n items from each stratum."""
    import random
    sample = []
    for key, items in strata.items():
        if len(items) <= n_per_strata:
            sample.extend(items)
        else:
            sample.extend(random.sample(items, n_per_strata))
    return sample


def save_sampled_reports(sample: List[Dict[str, Any]], output_path: str) -> None:
    """Save sampled reports."""
    log_operation("save_sampled_reports", path=output_path)
    safe_write_csv(sample, output_path)


def run_stratified_sampling(config: Dict[str, Any]) -> None:
    """
    Run stratified sampling.
    Accepts config dict or path string for backward compatibility.
    """
    # Handle flexible calling
    if isinstance(config, dict):
        input_path = config.get("input_path", "data/processed/merged_dataset.csv")
        output_file = config.get("output_file", "data/qualitative/sampling_list.csv")
        n = config.get("n_per_strata", 10)
    else:
        # Fallback for direct calls
        input_path = "data/processed/merged_dataset.csv"
        output_file = "data/qualitative/sampling_list.csv"
        n = 10

    log_operation("run_stratified_sampling", input=input_path, output=output_file)
    
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    reports = load_generated_reports(input_path)
    if not validate_report_structure(reports):
        raise StratifiedSamplingError("Invalid report structure")
    
    strata = stratify_reports(reports, stratify_by='strategy')
    sample = sample_from_strata(strata, n)
    
    save_sampled_reports(sample, output_file)
    log_operation("run_stratified_sampling_complete", count=len(sample))


def main():
    """CLI entry."""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/processed/merged_dataset.csv")
    parser.add_argument("--output", default="data/qualitative/sampling_list.csv")
    parser.add_argument("--n", type=int, default=10)
    args = parser.parse_args()
    
    config = {
        "input_path": args.input,
        "output_file": args.output,
        "n_per_strata": args.n
    }
    run_stratified_sampling(config)


if __name__ == "__main__":
    main()
