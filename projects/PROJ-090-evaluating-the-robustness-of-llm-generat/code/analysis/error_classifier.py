import json
import logging
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict

# Import from sibling modules based on provided API surface
from model.execution_results import load_results_from_json, ExecutionTag
from config import get_config_dict

logger = logging.getLogger(__name__)

def load_execution_results(results_path: str) -> List[Dict[str, Any]]:
    """
    Load execution results from a JSON file.
    
    Args:
        results_path: Path to the execution results JSON file.
        
    Returns:
        List of execution result dictionaries.
    """
    config = get_config_dict()
    if not Path(results_path).exists():
        # Try relative to data/processed if absolute path not found
        alt_path = Path(config.get('data_dir', 'data')) / 'processed' / Path(results_path).name
        if alt_path.exists():
            results_path = str(alt_path)
    
    return load_results_from_json(results_path)

def filter_failures(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter results to keep only failed executions.
    
    Args:
        results: List of execution result dictionaries.
        
    Returns:
        List of failed execution result dictionaries.
    """
    failures = []
    for r in results:
        # Check if the execution status indicates failure
        status = r.get('status', '')
        if status in ['fail', 'error', 'timeout', 'syntax_error', 'runtime_error']:
            failures.append(r)
        # Also check for explicit error tags if present
        elif r.get('error_tag') in ['syntax', 'logic', 'timeout', 'runtime']:
            failures.append(r)
    return failures

def stratify_by_perturbation_type(failures: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group failures by their perturbation type for stratified sampling.
    
    Args:
        failures: List of failed execution result dictionaries.
        
    Returns:
        Dictionary mapping perturbation_type to list of failures.
    """
    stratified = defaultdict(list)
    for f in failures:
        pert_type = f.get('perturbation_type', 'unknown')
        stratified[pert_type].append(f)
    return dict(stratified)

def sample_stratified(stratified_failures: Dict[str, List[Dict[str, Any]]], 
                     max_total: int = 50, 
                     seed: int = 42) -> List[Dict[str, Any]]:
    """
    Perform stratified sampling from failures, respecting a maximum total sample size.
    
    Args:
        stratified_failures: Dictionary mapping perturbation_type to list of failures.
        max_total: Maximum total number of samples to return.
        seed: Random seed for reproducibility.
        
    Returns:
        List of sampled failure dictionaries, stratified by perturbation type.
    """
    random.seed(seed)
    sampled = []
    
    # Calculate proportional allocation
    total_failures = sum(len(v) for v in stratified_failures.values())
    if total_failures == 0:
        return []
        
    # If total failures <= max_total, return all
    if total_failures <= max_total:
        for group in stratified_failures.values():
            sampled.extend(group)
        return sampled
    
    # Otherwise, sample proportionally
    # Ensure each group gets at least 1 sample if it has failures, up to max_total
    groups = list(stratified_failures.keys())
    samples_per_group = {}
    remaining = max_total
    
    # First pass: ensure minimum representation
    for group in groups:
        count = len(stratified_failures[group])
        if count > 0:
            # Allocate proportional to group size, at least 1
            alloc = max(1, int((count / total_failures) * max_total))
            alloc = min(alloc, count)  # Don't exceed group size
            samples_per_group[group] = alloc
            remaining -= alloc
    
    # Second pass: distribute remaining samples proportionally
    if remaining > 0:
        for group in groups:
            count = len(stratified_failures[group])
            already_sampled = samples_per_group.get(group, 0)
            available = count - already_sampled
            if available > 0 and remaining > 0:
                extra = min(remaining, int((count / total_failures) * remaining))
                extra = min(extra, available)
                samples_per_group[group] = samples_per_group.get(group, 0) + extra
                remaining -= extra
    
    # Final sampling
    for group, sample_count in samples_per_group.items():
        group_failures = stratified_failures[group]
        if sample_count >= len(group_failures):
            sampled.extend(group_failures)
        else:
            sampled.extend(random.sample(group_failures, sample_count))
    
    return sampled

def classify_error(result: Dict[str, Any]) -> str:
    """
    Classify an error as 'syntax' or 'logic' based on error message or tags.
    
    Args:
        result: Execution result dictionary.
        
    Returns:
        Error classification: 'syntax', 'logic', or 'unknown'.
    """
    # Check for explicit error tags
    error_tag = result.get('error_tag', '').lower()
    if error_tag == 'syntax':
        return 'syntax'
    if error_tag == 'logic':
        return 'logic'
    
    # Check status
    status = result.get('status', '').lower()
    if status in ['syntax_error', 'error']:
        # Try to infer from message
        message = result.get('message', '').lower()
        if any(kw in message for kw in ['syntax', 'indentation', 'invalid syntax', 'unexpected']):
            return 'syntax'
        return 'logic'
    
    # Check message for keywords
    message = result.get('message', '').lower()
    if any(kw in message for kw in ['syntax', 'indentation', 'invalid syntax', 'unexpected', 'eof']):
        return 'syntax'
    
    # Default to logic for runtime errors, timeouts, etc.
    if status in ['fail', 'timeout', 'runtime_error']:
        return 'logic'
        
    return 'unknown'

def create_error_classification_report(sampled_failures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Create the error classification report by tagging each sampled failure.
    
    Args:
        sampled_failures: List of sampled failure dictionaries.
        
    Returns:
        List of dictionaries with error classification tags.
    """
    report = []
    for failure in sampled_failures:
        entry = {
            'task_id': failure.get('task_id', 'unknown'),
            'perturbation_type': failure.get('perturbation_type', 'unknown'),
            'error_tag': failure.get('error_tag', 'unknown'),
            'status': failure.get('status', 'unknown'),
            'classification': classify_error(failure),
            'message': failure.get('message', '')[:200]  # Truncate long messages
        }
        report.append(entry)
    return report

def save_report(report: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save the error classification report to a JSON file.
    
    Args:
        report: List of classification report entries.
        output_path: Path to the output JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved error classification report to {output_path} with {len(report)} entries.")

def main():
    """
    Main entry point for the error classifier.
    Reads execution results, filters failures, stratifies by perturbation type,
    samples up to 50, classifies errors, and saves the report.
    """
    config = get_config_dict()
    data_dir = Path(config.get('data_dir', 'data'))
    processed_dir = data_dir / 'processed'
    
    # Input: execution results from T024/T025
    results_file = processed_dir / 'execution_results.json'
    if not results_file.exists():
        logger.error(f"Execution results file not found: {results_file}")
        # Try alternative path
        results_file = Path('data/processed/execution_results.json')
        if not results_file.exists():
            raise FileNotFoundError(f"Cannot find execution results at {results_file}")
    
    logger.info(f"Loading execution results from {results_file}")
    results = load_execution_results(str(results_file))
    logger.info(f"Loaded {len(results)} execution results")
    
    # Filter failures
    failures = filter_failures(results)
    logger.info(f"Found {len(failures)} failed executions")
    
    if len(failures) == 0:
        logger.warning("No failures found to classify. Creating empty report.")
        save_report([], str(processed_dir / 'error_classification_report.json'))
        return
    
    # Stratify by perturbation type
    stratified = stratify_by_perturbation_type(failures)
    logger.info(f"Stratified into {len(stratified)} perturbation types: {list(stratified.keys())}")
    
    # Sample stratified (max 50)
    sampled = sample_stratified(stratified, max_total=50, seed=42)
    logger.info(f"Sampled {len(sampled)} failures for classification")
    
    # Classify errors
    report = create_error_classification_report(sampled)
    
    # Save report
    output_file = processed_dir / 'error_classification_report.json'
    save_report(report, str(output_file))
    
    logger.info("Error classification complete.")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
