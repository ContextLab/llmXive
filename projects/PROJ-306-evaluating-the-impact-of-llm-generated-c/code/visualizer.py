import os
import re
import json
import csv
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_patterns_from_code(code: str) -> Dict[str, bool]:
    """
    Extract code patterns from a code snippet.
    Returns a dictionary of pattern flags.
    """
    patterns = {
        "loops": bool(re.search(r'\b(for|while)\b', code)),
        "conditionals": bool(re.search(r'\b(if|elif|else)\b', code)),
        "recursion": False,
        "list_comprehension": bool(re.search(r'\[.*\sfor\s.*\sin\s.*\]', code)),
        "try_except": bool(re.search(r'\btry\b.*\bexcept\b', code, re.DOTALL))
    }
    
    # Simple recursion detection (very heuristic)
    if patterns["loops"] or patterns["conditionals"]:
        func_name_match = re.search(r'def\s+(\w+)\s*\(', code)
        if func_name_match:
            func_name = func_name_match.group(1)
            # Check if function calls itself
            if re.search(rf'\b{func_name}\s*\(', code):
                patterns["recursion"] = True
    
    return patterns

def load_coverage_reports(report_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load all coverage report JSON files from the specified directory.
    """
    if report_dir is None:
        report_dir = "data/coverage_reports"
    
    report_path = Path(report_dir)
    reports = []
    
    if not report_path.exists():
        logger.warning(f"Coverage report directory {report_dir} does not exist.")
        return reports
    
    for json_file in report_path.glob("*.json"):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                data['source_file'] = json_file.name
                reports.append(data)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load {json_file}: {e}")
    
    return reports

def load_catalog(catalog_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load the task catalog JSON.
    """
    if catalog_path is None:
        catalog_path = "data/benchmarks/processed/catalog.json"
    
    catalog_file = Path(catalog_path)
    if not catalog_file.exists():
        logger.error(f"Catalog file not found: {catalog_path}")
        return []
    
    with open(catalog_file, 'r') as f:
        data = json.load(f)
        # Handle both list and dict with 'tasks' key
        if isinstance(data, dict) and 'tasks' in data:
            return data['tasks']
        elif isinstance(data, list):
            return data
        else:
            logger.error("Invalid catalog format")
            return []

def annotate_tasks_with_patterns(catalog: List[Dict[str, Any]], 
                                 generated_code_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Annotate catalog tasks with code patterns from generated code.
    """
    if generated_code_dir is None:
        generated_code_dir = "data/generated"
    
    generated_dir = Path(generated_code_dir)
    
    for task in catalog:
        task_id = task.get('task_id', '')
        patterns = {}
        
        # Try to find generated code
        code_file = generated_dir / f"{task_id}.py"
        if code_file.exists():
            try:
                with open(code_file, 'r') as f:
                    code = f.read()
                    patterns = extract_patterns_from_code(code)
            except IOError as e:
                logger.warning(f"Could not read code for {task_id}: {e}")
        else:
            # Try human solution from catalog
            human_solution = task.get('human_solution', '')
            if human_solution:
                patterns = extract_patterns_from_code(human_solution)
        
        task['patterns'] = patterns
    
    return catalog

def save_annotated_dataset(annotated_tasks: List[Dict[str, Any]], 
                           output_path: Optional[str] = None):
    """
    Save the annotated dataset to a JSON file.
    """
    if output_path is None:
        output_path = "data/processed/annotated_dataset.json"
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(annotated_tasks, f, indent=2)
    
    logger.info(f"Saved annotated dataset to {output_path}")

def generate_pattern_summary_csv(annotated_tasks: List[Dict[str, Any]], 
                                 coverage_reports: List[Dict[str, Any]],
                                 output_path: Optional[str] = None):
    """
    Generate a summary CSV of patterns and their coverage statistics.
    """
    if output_path is None:
        output_path = "outputs/pattern_summary.csv"
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Create a mapping of task_id to coverage
    coverage_map = {}
    for report in coverage_reports:
        task_id = report.get('task_id', '')
        if task_id:
            coverage_map[task_id] = report
    
    rows = []
    for task in annotated_tasks:
        task_id = task.get('task_id', '')
        patterns = task.get('patterns', {})
        coverage = coverage_map.get(task_id, {})
        
        row = {
            'task_id': task_id,
            'difficulty': task.get('difficulty', 'unknown'),
            'pattern_loops': patterns.get('loops', False),
            'pattern_conditionals': patterns.get('conditionals', False),
            'pattern_recursion': patterns.get('recursion', False),
            'line_coverage': coverage.get('line_coverage', None),
            'branch_coverage': coverage.get('branch_coverage', None)
        }
        rows.append(row)
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=row[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    
    logger.info(f"Saved pattern summary to {output_path}")

def calculate_stratified_branch_coverage_gaps(coverage_pairs_path: str, 
                                              output_path: Optional[str] = None):
    """
    Calculate and report mean branch-coverage gaps for specific difficulty tiers.
    
    Filters coverage_pairs.csv for difficulty="hard" AND branch_coverage != "N/A",
    calculates mean(branch_coverage_gap), and appends the result to 
    outputs/stratified_summary.csv.
    
    Constraint: Explicitly exclude tasks where branch_coverage == "N/A" (HumanEval).
    
    Args:
        coverage_pairs_path: Path to the coverage_pairs.csv file
        output_path: Path to the output stratified_summary.csv file
    """
    if output_path is None:
        output_path = "outputs/stratified_summary.csv"
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Read the coverage pairs
    try:
        df = pd.read_csv(coverage_pairs_path)
    except FileNotFoundError:
        logger.error(f"Coverage pairs file not found: {coverage_pairs_path}")
        return
    except Exception as e:
        logger.error(f"Error reading coverage pairs file: {e}")
        return
    
    # Filter for hard difficulty and valid branch coverage
    # Exclude "N/A" strings and None/NaN values
    mask = (df['difficulty'] == 'hard') & (df['branch_coverage'] != 'N/A')
    # Ensure branch_coverage is numeric before calculating gap if it's stored as string
    # We assume the gap column might already exist or we calculate it
    # If 'branch_coverage_gap' column exists, use it. Otherwise, calculate from human - llm if available.
    # Based on task description, we assume 'branch_coverage_gap' exists in coverage_pairs.csv.
    
    filtered_df = df[mask].copy()
    
    if filtered_df.empty:
        logger.warning("No hard difficulty tasks with valid branch coverage found.")
        # Create empty file with headers if it doesn't exist
        if not output_file.exists():
            with open(output_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['pattern', 'difficulty', 'mean_gap', 'count'])
                writer.writeheader()
        return
    
    # Ensure branch_coverage_gap is numeric
    if 'branch_coverage_gap' not in filtered_df.columns:
        logger.error("Column 'branch_coverage_gap' not found in coverage_pairs.csv")
        return
    
    filtered_df['branch_coverage_gap'] = pd.to_numeric(filtered_df['branch_coverage_gap'], errors='coerce')
    filtered_df = filtered_df.dropna(subset=['branch_coverage_gap'])
    
    if filtered_df.empty:
        logger.warning("No valid numeric branch coverage gaps found after filtering.")
        return
    
    mean_gap = filtered_df['branch_coverage_gap'].mean()
    count = len(filtered_df)
    
    # Determine pattern: Since the task asks for specific difficulty tiers, 
    # and the output format includes 'pattern', we need to aggregate by pattern if multiple exist,
    # or use a general pattern label if the data is aggregated by difficulty only.
    # The task description says: "filters ... for difficulty='hard' ... and appends ... with columns: [pattern, difficulty, mean_gap, count]"
    # If the input data has multiple patterns, we might need to group. 
    # However, the filter is strictly on difficulty="hard". 
    # If the dataset is already stratified by pattern in the input, we might group by that.
    # But the task specifically says "for specific difficulty tiers (e.g., 'hard')".
    # Let's assume the input `coverage_pairs.csv` might have a 'pattern' column.
    # If it does, we group by pattern. If not, we use a default or aggregate all.
    
    if 'pattern' in filtered_df.columns:
        # Group by pattern if available
        grouped = filtered_df.groupby('pattern').agg({
            'branch_coverage_gap': 'mean',
            'task_id': 'count' # assuming task_id exists for counting
        }).reset_index()
        grouped.columns = ['pattern', 'mean_gap', 'count']
        grouped['difficulty'] = 'hard'
        # Reorder columns
        grouped = grouped[['pattern', 'difficulty', 'mean_gap', 'count']]
    else:
        # No pattern column, treat all as one group or use 'all'
        result = {
            'pattern': 'all',
            'difficulty': 'hard',
            'mean_gap': mean_gap,
            'count': count
        }
        grouped = pd.DataFrame([result])
    
    # Prepare to append to existing file
    file_exists = output_file.exists()
    
    # Write/Append
    mode = 'a' if file_exists else 'w'
    header = not file_exists
    
    with open(output_file, mode, newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['pattern', 'difficulty', 'mean_gap', 'count'])
        if header:
            writer.writeheader()
        
        for _, row in grouped.iterrows():
            writer.writerow({
                'pattern': row['pattern'],
                'difficulty': row['difficulty'],
                'mean_gap': f"{row['mean_gap']:.4f}",
                'count': int(row['count'])
            })
    
    logger.info(f"Appended stratified branch coverage gaps for 'hard' difficulty to {output_path}")

def main():
    """
    Main entry point for visualizer tasks.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Visualizer and Stratified Analysis")
    parser.add_argument('--coverage-pairs', type=str, default='data/processed/coverage_pairs.csv',
                        help='Path to the coverage pairs CSV file')
    parser.add_argument('--output', type=str, default='outputs/stratified_summary.csv',
                        help='Path for the output stratified summary CSV')
    
    args = parser.parse_args()
    
    # Execute the specific task T044 logic
    calculate_stratified_branch_coverage_gaps(args.coverage_pairs, args.output)

if __name__ == "__main__":
    main()