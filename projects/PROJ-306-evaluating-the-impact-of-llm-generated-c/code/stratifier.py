import os
import json
import csv
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from visualizer import load_catalog, load_coverage_reports
from analyzer import pair_llm_human_results

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_annotated_dataset(annotated_path: Path) -> List[Dict[str, Any]]:
    """
    Load the dataset annotated with code patterns from T041.
    Expects a JSON file created by save_annotated_dataset in visualizer.py.
    """
    if not annotated_path.exists():
        logger.warning(f"Annotated dataset not found at {annotated_path}. "
                       "Ensure T041 has been run successfully.")
        return []
    
    with open(annotated_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_boundary_case_flags(task_data: Dict[str, Any]) -> Dict[str, bool]:
    """
    Determine boundary-case presence based on task data.
    Currently infers from prompt or test suite content if explicit flags aren't present.
    """
    prompt = task_data.get('prompt', '').lower()
    test_suite = task_data.get('test_suite', '').lower()
    
    boundary_keywords = [
        'zero', 'null', 'empty', 'negative', 'max', 'min', 
        'overflow', 'underflow', 'boundary', 'edge case', 'limit'
    ]
    
    flags = {
        'has_zero_case': 'zero' in prompt or '0' in prompt,
        'has_null_case': 'null' in prompt or 'none' in prompt,
        'has_empty_case': 'empty' in prompt or '[]' in prompt,
        'has_negative_case': 'negative' in prompt or '-' in prompt,
        'has_max_min_case': ('max' in prompt or 'min' in prompt) and ('value' in prompt or 'input' in prompt)
    }
    
    return flags

def stratify_data(
    catalog: List[Dict[str, Any]],
    coverage_pairs: List[Dict[str, Any]],
    pattern_summary: Optional[Path] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group data by difficulty, pattern, and boundary-case presence (FR-007).
    
    Args:
        catalog: List of task definitions from catalog.json
        coverage_pairs: List of paired LLM/Human coverage results
        pattern_summary: Optional path to pattern summary CSV from T041
        
    Returns:
        Dictionary mapping stratification keys to lists of enriched task records.
    """
    # Create a lookup for coverage data by task_id
    coverage_lookup = {}
    for pair in coverage_pairs:
        tid = pair.get('task_id')
        if tid:
            coverage_lookup[tid] = pair

    # Create a lookup for pattern data if available
    pattern_lookup = {}
    if pattern_summary and pattern_summary.exists():
        with open(pattern_summary, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                tid = row.get('task_id')
                if tid:
                    pattern_lookup[tid] = row

    stratified_groups = {}

    for task in catalog:
        task_id = task.get('task_id')
        if not task_id:
            continue

        # Get difficulty
        difficulty = task.get('difficulty', 'unknown')
        
        # Get primary pattern (most frequent or first detected)
        pattern_info = pattern_lookup.get(task_id, {})
        primary_pattern = pattern_info.get('primary_pattern', 'unknown')
        
        # Get boundary case flags
        boundary_flags = get_boundary_case_flags(task)
        has_boundary = any(boundary_flags.values())
        
        # Get coverage data
        cov_data = coverage_lookup.get(task_id, {})
        
        # Construct the enriched record
        record = {
            'task_id': task_id,
            'difficulty': difficulty,
            'primary_pattern': primary_pattern,
            'has_boundary_cases': has_boundary,
            'boundary_flags': boundary_flags,
            'llm_line_coverage': cov_data.get('llm_line_coverage'),
            'human_line_coverage': cov_data.get('human_line_coverage'),
            'line_coverage_gap': cov_data.get('line_coverage_gap'),
            'llm_branch_coverage': cov_data.get('llm_branch_coverage'),
            'human_branch_coverage': cov_data.get('human_branch_coverage'),
            'branch_coverage_gap': cov_data.get('branch_coverage_gap'),
            'dataset_source': task.get('dataset_source', 'unknown')
        }

        # Create stratification key
        key = f"{difficulty}_{primary_pattern}_{'boundary' if has_boundary else 'no_boundary'}"
        
        if key not in stratified_groups:
            stratified_groups[key] = []
        
        stratified_groups[key].append(record)

    return stratified_groups

def save_stratified_groups(
    stratified_groups: Dict[str, List[Dict[str, Any]]],
    output_dir: Path
) -> List[Path]:
    """
    Save each stratification group to a separate CSV file in the output directory.
    
    Args:
        stratified_groups: The dictionary of grouped records
        output_dir: Directory to write CSV files to
        
    Returns:
        List of paths to the created CSV files
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    created_files = []

    for key, records in stratified_groups.items():
        if not records:
            continue
        
        # Sanitize key for filename
        filename = f"stratified_{key.replace(' ', '_').replace('-', '_')}.csv"
        file_path = output_dir / filename
        
        # Write CSV
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            if records:
                fieldnames = list(records[0].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(records)
        
        created_files.append(file_path)
        logger.info(f"Saved stratified group '{key}' to {file_path}")

    return created_files

def generate_stratification_summary(
    stratified_groups: Dict[str, List[Dict[str, Any]]],
    output_path: Path
) -> Path:
    """
    Generate a summary CSV of the stratification groups with counts and average gaps.
    
    Args:
        stratified_groups: The dictionary of grouped records
        output_path: Path to write the summary CSV
        
    Returns:
        Path to the created summary file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    summary_rows = []
    
    for key, records in stratified_groups.items():
        if not records:
            continue
          
        # Parse key back into components
        parts = key.split('_')
        difficulty = parts[0] if parts else 'unknown'
        pattern = '_'.join(parts[1:-1]) if len(parts) > 2 else 'unknown'
        boundary_status = parts[-1] if parts else 'unknown'
        
        # Calculate statistics
        line_gaps = [r['line_coverage_gap'] for r in records 
                    if isinstance(r['line_coverage_gap'], (int, float))]
        branch_gaps = [r['branch_coverage_gap'] for r in records 
                      if isinstance(r['branch_coverage_gap'], (int, float))]
        
        avg_line_gap = sum(line_gaps) / len(line_gaps) if line_gaps else None
        avg_branch_gap = sum(branch_gaps) / len(branch_gaps) if branch_gaps else None
        
        summary_rows.append({
            'stratification_key': key,
            'difficulty': difficulty,
            'pattern': pattern,
            'boundary_status': boundary_status,
            'count': len(records),
            'avg_line_coverage_gap': avg_line_gap,
            'avg_branch_coverage_gap': avg_branch_gap
        })
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        if summary_rows:
            fieldnames = list(summary_rows[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(summary_rows)
    
    logger.info(f"Saved stratification summary to {output_path}")
    return output_path

def main():
    """
    Main entry point for stratification logic (T042).
    
    Reads:
      - data/benchmarks/processed/catalog.json
      - data/processed/coverage_pairs.csv (output from T024)
      - outputs/pattern_summary.csv (output from T041)
      
    Writes:
      - outputs/stratified_*.csv (individual groups)
      - outputs/stratification_summary.csv (aggregate stats)
    """
    # Define paths
    project_root = Path(__file__).parent.parent
    catalog_path = project_root / "data" / "benchmarks" / "processed" / "catalog.json"
    coverage_pairs_path = project_root / "data" / "processed" / "coverage_pairs.csv"
    pattern_summary_path = project_root / "outputs" / "pattern_summary.csv"
    output_dir = project_root / "outputs"
    summary_path = output_dir / "stratification_summary.csv"
    
    logger.info("Starting stratification logic (T042)...")
    
    # Load data
    if not catalog_path.exists():
        logger.error(f"Catalog not found at {catalog_path}. Run T006c first.")
        return
    
    catalog = load_catalog(catalog_path)
    logger.info(f"Loaded {len(catalog)} tasks from catalog.")
    
    # Load coverage pairs
    if not coverage_pairs_path.exists():
        logger.error(f"Coverage pairs not found at {coverage_pairs_path}. Run T024 first.")
        return
    
    with open(coverage_pairs_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        coverage_pairs = list(reader)
    logger.info(f"Loaded {len(coverage_pairs)} coverage pairs.")
    
    # Perform stratification
    stratified_groups = stratify_data(catalog, coverage_pairs, pattern_summary_path)
    logger.info(f"Stratified data into {len(stratified_groups)} groups.")
    
    # Save individual group files
    created_files = save_stratified_groups(stratified_groups, output_dir)
    logger.info(f"Created {len(created_files)} stratified CSV files.")
    
    # Save summary
    generate_stratification_summary(stratified_groups, summary_path)
    logger.info("Stratification complete.")

if __name__ == "__main__":
    main()