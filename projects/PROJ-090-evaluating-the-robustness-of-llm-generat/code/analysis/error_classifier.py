"""
Error classifier for stratified sampling of execution failures.

This module implements the error classification logic for User Story 3.
It reads execution results, filters for failures, stratifies by perturbation type,
samples up to 50 failures (or all if fewer), and tags them as 'syntax' or 'logic'.

Deliverable: data/processed/error_classification_report.json
"""
import json
import logging
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict

# Import from project API surface
from config import ensure_directories
from model.execution_results import ExecutionTag, load_results_from_json

logger = logging.getLogger(__name__)

# Configuration
MAX_SAMPLE_SIZE = 50
RANDOM_SEED = 42

def load_execution_results() -> List[Dict[str, Any]]:
    """
    Load execution results from the standard output file.
    
    Returns:
        List of execution result dictionaries.
    """
    results_path = Path("data/processed/execution_results.json")
    if not results_path.exists():
        raise FileNotFoundError(
            f"Execution results file not found at {results_path}. "
            "Please ensure Phase 4 (T024, T025) has completed successfully."
        )
    
    return load_results_from_json(results_path)

def filter_failures(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter results to include only failed executions.
    
    Args:
        results: List of execution result dictionaries.
        
    Returns:
        List of failed execution results.
    """
    failures = []
    for result in results:
        # Check if the result indicates a failure (not pass)
        # Based on ExecutionTag enum, we look for tags that are not 'pass'
        tag = result.get("tag", "")
        if tag != ExecutionTag.PASS.value:
            failures.append(result)
    
    logger.info(f"Found {len(failures)} failed executions out of {len(results)} total.")
    return failures

def stratify_by_perturbation_type(failures: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group failures by perturbation type for stratified sampling.
    
    Args:
        failures: List of failed execution results.
        
    Returns:
        Dictionary mapping perturbation_type to list of failures.
    """
    stratified = defaultdict(list)
    for failure in failures:
        perturbation_type = failure.get("perturbation_type", "unknown")
        stratified[perturbation_type].append(failure)
    
    logger.info(f"Stratified failures into {len(stratified)} perturbation types.")
    return dict(stratified)

def sample_stratified(stratified_failures: Dict[str, List[Dict[str, Any]]], 
                     max_sample_size: int = MAX_SAMPLE_SIZE, 
                     seed: int = RANDOM_SEED) -> List[Dict[str, Any]]:
    """
    Perform stratified sampling of failures.
    
    Samples proportionally from each perturbation type, ensuring representation
    from all types, up to a maximum of max_sample_size total items.
    
    Args:
        stratified_failures: Dictionary of failures grouped by perturbation type.
        max_sample_size: Maximum total number of samples to return.
        seed: Random seed for reproducibility.
        
    Returns:
        List of sampled failure dictionaries.
    """
    random.seed(seed)
    
    if not stratified_failures:
        logger.warning("No stratified failures to sample from.")
        return []
    
    total_failures = sum(len(items) for items in stratified_failures.values())
    
    if total_failures <= max_sample_size:
        # If total failures are within limit, return all
        all_failures = []
        for items in stratified_failures.values():
            all_failures.extend(items)
        logger.info(f"Total failures ({total_failures}) <= max sample size ({max_sample_size}). Returning all.")
        return all_failures
    
    # Calculate proportional sample size for each stratum
    sample_sizes = {}
    remaining = max_sample_size
    types = list(stratified_failures.keys())
    
    # First pass: calculate proportional allocation
    for ptype, items in stratified_failures.items():
        proportion = len(items) / total_failures
        allocated = max(1, int(proportion * max_sample_size))  # Ensure at least 1 per type if possible
        sample_sizes[ptype] = allocated
        remaining -= allocated
    
    # Adjust if we have remaining slots (due to rounding)
    if remaining > 0:
        # Distribute remaining slots to largest strata
        sorted_types = sorted(stratified_failures.keys(), 
                            key=lambda x: len(stratified_failures[x]), 
                            reverse=True)
        for ptype in sorted_types:
            if remaining <= 0:
                break
            # Can we add more?
            current_count = len(stratified_failures[ptype])
            if sample_sizes[ptype] < current_count:
                sample_sizes[ptype] += 1
                remaining -= 1
    
    # Sample from each stratum
    sampled_failures = []
    for ptype, items in stratified_failures.items():
        sample_size = min(sample_sizes[ptype], len(items))
        sampled = random.sample(items, sample_size)
        sampled_failures.extend(sampled)
    
    logger.info(f"Sampled {len(sampled_failures)} failures from {len(stratified_failures)} perturbation types.")
    return sampled_failures

def classify_error(result: Dict[str, Any]) -> str:
    """
    Classify an error as 'syntax' or 'logic' based on error message.
    
    Args:
        result: Execution result dictionary containing error information.
        
    Returns:
        Error classification string: 'syntax' or 'logic'.
    """
    error_message = result.get("error_message", "").lower()
    tag = result.get("tag", "").lower()
    
    # Syntax error indicators
    syntax_indicators = [
        "syntaxerror", "indentationerror", "nameerror", "importerror",
        "module not found", "invalid syntax", "unexpected indent",
        "eof while", "invalid token", "unexpected token"
    ]
    
    # Logic error indicators (more general, as logic errors are harder to detect automatically)
    # If it's not a syntax error and the code ran but failed, it's likely logic
    logic_indicators = [
        "assertionerror", "valueerror", "typeerror", "indexerror",
        "keyerror", "timeout", "runtime error", "failed", "incorrect"
    ]
    
    # Check for syntax errors first
    for indicator in syntax_indicators:
        if indicator in error_message or indicator in tag:
            return "syntax"
    
    # Check for logic errors
    for indicator in logic_indicators:
        if indicator in error_message or indicator in tag:
            return "logic"
    
    # Default to logic if we can't determine (most runtime failures are logic errors)
    # or if the error is ambiguous
    if tag in ["timeout", "oom", "fail"]:
        return "logic"
    
    # If we still can't classify, default to 'logic' as it's the more common case
    # for LLM-generated code that compiles but produces wrong output
    return "logic"

def create_error_classification_report(sampled_failures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Create the final error classification report.
    
    Args:
        sampled_failures: List of sampled failure dictionaries.
        
    Returns:
        List of dictionaries with error classification tags.
    """
    report = []
    
    for i, failure in enumerate(sampled_failures):
        entry = {
            "task_id": failure.get("task_id", f"unknown_{i}"),
            "perturbation_type": failure.get("perturbation_type", "unknown"),
            "original_tag": failure.get("tag", "unknown"),
            "error_message": failure.get("error_message", ""),
            "classification": classify_error(failure),
            "sample_index": i
        }
        report.append(entry)
    
    return report

def save_report(report: List[Dict[str, Any]], output_path: Optional[str] = None) -> Path:
    """
    Save the error classification report to JSON.
    
    Args:
        report: List of error classification entries.
        output_path: Optional custom output path.
        
    Returns:
        Path to the saved file.
    """
    if output_path is None:
        output_path = "data/processed/error_classification_report.json"
    
    output_path = Path(output_path)
    ensure_directories(output_path.parent)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Error classification report saved to {output_path}")
    return output_path

def main():
    """
    Main entry point for error classification.
    
    This function orchestrates the entire error classification pipeline:
    1. Load execution results
    2. Filter for failures
    3. Stratify by perturbation type
    4. Sample up to 50 failures (stratified)
    5. Classify each as syntax or logic
    6. Save report to JSON
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting error classification pipeline (T035)...")
    
    try:
        # Step 1: Load execution results
        logger.info("Loading execution results...")
        results = load_execution_results()
        
        if not results:
            logger.warning("No execution results found. Creating empty report.")
            save_report([])
            return
        
        # Step 2: Filter for failures
        logger.info("Filtering for failed executions...")
        failures = filter_failures(results)
        
        if not failures:
            logger.info("No failed executions found. Creating empty report.")
            save_report([])
            return
        
        # Step 3: Stratify by perturbation type
        logger.info("Stratifying failures by perturbation type...")
        stratified = stratify_by_perturbation_type(failures)
        
        # Step 4: Sample stratified
        logger.info(f"Performing stratified sampling (max {MAX_SAMPLE_SIZE} samples)...")
        sampled = sample_stratified(stratified, MAX_SAMPLE_SIZE, RANDOM_SEED)
        
        # Step 5: Classify errors
        logger.info("Classifying errors as syntax or logic...")
        report = create_error_classification_report(sampled)
        
        # Step 6: Save report
        logger.info("Saving error classification report...")
        output_path = save_report(report)
        
        # Summary
        syntax_count = sum(1 for item in report if item["classification"] == "syntax")
        logic_count = sum(1 for item in report if item["classification"] == "logic")
        
        logger.info(f"Classification complete: {syntax_count} syntax errors, {logic_count} logic errors.")
        logger.info(f"Total samples: {len(report)}")
        logger.info(f"Report saved to: {output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during error classification: {e}")
        raise

if __name__ == "__main__":
    main()
