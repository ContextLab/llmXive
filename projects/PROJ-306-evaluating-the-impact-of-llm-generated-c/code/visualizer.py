import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_patterns(code: str) -> List[str]:
    """
    Extract code patterns from a string of Python code.
    Returns a list of detected pattern types: 'loops', 'conditionals', 'recursion'.
    """
    patterns = []
    
    # Check for loops (for, while)
    if re.search(r'\b(for|while)\b', code):
        patterns.append('loops')
    
    # Check for conditionals (if, elif, else)
    if re.search(r'\b(if|elif|else)\b', code):
        patterns.append('conditionals')
    
    # Check for recursion (function calling itself) - simple heuristic
    # Extract function name and check if it appears in the body
    func_match = re.search(r'def\s+(\w+)\s*\(', code)
    if func_match:
        func_name = func_match.group(1)
        # Check if function name appears after definition in the code
        body_start = func_match.end()
        if re.search(rf'\b{func_name}\s*\(', code[body_start:]):
            patterns.append('recursion')
    
    return patterns

def categorize_pattern(patterns: List[str]) -> str:
    """
    Categorize a list of patterns into a primary category.
    Priority: recursion > loops > conditionals > other
    """
    if 'recursion' in patterns:
        return 'recursion'
    if 'loops' in patterns:
        return 'loops'
    if 'conditionals' in patterns:
        return 'conditionals'
    return 'other'

def load_catalog_and_coverage(catalog_path: Path, coverage_dir: Path) -> pd.DataFrame:
    """
    Load the task catalog and merge with coverage reports.
    Returns a DataFrame with task details and coverage metrics.
    """
    # Load catalog
    with open(catalog_path, 'r') as f:
        catalog = json.load(f)
    
    catalog_df = pd.DataFrame(catalog)
    
    # Load coverage reports
    coverage_data = []
    for file in coverage_dir.glob('*.json'):
        try:
            with open(file, 'r') as f:
                report = json.load(f)
                if report.get('status') == 'success':
                    coverage_data.append(report)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Skipping invalid coverage report {file}: {e}")
    
    coverage_df = pd.DataFrame(coverage_data)
    
    # Merge on task_id
    if 'task_id' in coverage_df.columns and 'task_id' in catalog_df.columns:
        merged = pd.merge(catalog_df, coverage_df, on='task_id', how='inner')
    else:
        logger.error("Missing task_id column in catalog or coverage data")
        merged = catalog_df
    
    return merged

def analyze_pattern_distribution(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze the distribution of code patterns across tasks.
    """
    pattern_counts = df['code_patterns'].value_counts().to_dict()
    return {
        'total_tasks': len(df),
        'pattern_distribution': pattern_counts,
        'pattern_percentages': {k: v/len(df)*100 for k, v in pattern_counts.items()}
    }

def generate_pattern_visualization(df: pd.DataFrame, output_path: Path, pattern: str):
    """
    Generate a visualization for a specific code pattern.
    """
    # Filter for the pattern
    pattern_df = df[df['code_patterns'].str.contains(pattern, na=False)]
    
    if len(pattern_df) == 0:
        logger.warning(f"No tasks found for pattern: {pattern}")
        return
    
    # Create box plot of coverage by difficulty
    plt.figure(figsize=(10, 6))
    sns.boxplot(x='difficulty', y='line_coverage', data=pattern_df)
    plt.title(f'Line Coverage by Difficulty for {pattern} Pattern')
    plt.xlabel('Difficulty')
    plt.ylabel('Line Coverage (%)')
    plt.tight_layout()
    plt.savefig(output_path, dpi=100)
    plt.close()
    logger.info(f"Visualization saved to {output_path}")

def create_stratified_report(df: pd.DataFrame, output_dir: Path):
    """
    Create stratified reports by difficulty and pattern.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Group by difficulty and pattern
    stratified = df.groupby(['difficulty', 'code_patterns']).agg({
        'line_coverage': ['mean', 'count'],
        'branch_coverage': ['mean', 'count']
    }).reset_index()
    
    # Flatten column names
    stratified.columns = ['difficulty', 'pattern', 'mean_line_cov', 'line_cov_count', 'mean_branch_cov', 'branch_cov_count']
    
    # Save stratified report
    stratified_path = output_dir / 'stratified_summary.csv'
    stratified.to_csv(stratified_path, index=False)
    logger.info(f"Stratified report saved to {stratified_path}")
    
    return stratified

def calculate_branch_coverage_gaps_by_difficulty(df: pd.DataFrame, difficulty: str, output_path: Path) -> Optional[pd.DataFrame]:
    """
    Calculate and report mean branch-coverage gaps for a specific difficulty tier.
    Filters for difficulty="hard" AND branch_coverage != "N/A".
    Calculates mean(branch_coverage_gap) and appends to stratified_summary.csv.
    
    Args:
        df: DataFrame containing coverage data with columns: task_id, difficulty, branch_coverage, branch_coverage_gap
        difficulty: The difficulty tier to filter (e.g., "hard")
        output_path: Path to the stratified_summary.csv file
    
    Returns:
        DataFrame with the new row, or None if no matching data
    """
    # Filter for the specific difficulty
    filtered_df = df[df['difficulty'] == difficulty]
    
    if filtered_df.empty:
        logger.warning(f"No tasks found for difficulty: {difficulty}")
        return None
    
    # Filter out tasks where branch_coverage is "N/A" (HumanEval tasks)
    # Check for string "N/A", float NaN, or None
    valid_branch_df = filtered_df[
        (filtered_df['branch_coverage'] != "N/A") & 
        (filtered_df['branch_coverage'].notna()) &
        (filtered_df['branch_coverage'] != "None")
    ]
    
    if valid_branch_df.empty:
        logger.warning(f"No valid branch coverage data for difficulty: {difficulty}")
        return None
    
    # Calculate mean branch coverage gap
    mean_gap = valid_branch_df['branch_coverage_gap'].mean()
    count = len(valid_branch_df)
    
    # Determine the primary pattern for this difficulty (mode of code_patterns)
    if 'code_patterns' in valid_branch_df.columns:
        primary_pattern = valid_branch_df['code_patterns'].mode()[0] if not valid_branch_df['code_patterns'].mode().empty else 'mixed'
    else:
        primary_pattern = 'mixed'
    
    # Create the new row
    new_row = pd.DataFrame([{
        'pattern': primary_pattern,
        'difficulty': difficulty,
        'mean_gap': mean_gap,
        'count': count
    }])
    
    # Load existing summary if it exists, otherwise create new
    if output_path.exists():
        existing_summary = pd.read_csv(output_path)
        # Ensure columns match
        if set(existing_summary.columns) != set(new_row.columns):
            # Reindex to match new_row columns if necessary
            existing_summary = existing_summary.reindex(columns=new_row.columns)
        summary_df = pd.concat([existing_summary, new_row], ignore_index=True)
    else:
        summary_df = new_row
    
    # Save to CSV
    summary_df.to_csv(output_path, index=False)
    logger.info(f"Appended branch coverage gap data for difficulty '{difficulty}' to {output_path}")
    
    return new_row

def main():
    """
    Main function to run the visualizer pipeline.
    """
    base_dir = Path(__file__).parent.parent
    catalog_path = base_dir / 'data' / 'benchmarks' / 'processed' / 'catalog.json'
    coverage_dir = base_dir / 'data' / 'coverage_reports'
    outputs_dir = base_dir / 'outputs'
    
    # Ensure output directory exists
    outputs_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    logger.info("Loading catalog and coverage data...")
    df = load_catalog_and_coverage(catalog_path, coverage_dir)
    
    if df.empty:
        logger.error("No data loaded. Exiting.")
        return
    
    # Analyze pattern distribution
    pattern_stats = analyze_pattern_distribution(df)
    logger.info(f"Pattern distribution: {pattern_stats['pattern_distribution']}")
    
    # Create stratified report
    stratified_path = outputs_dir / 'stratified_summary.csv'
    create_stratified_report(df, outputs_dir)
    
    # Calculate branch coverage gaps for "hard" difficulty
    logger.info("Calculating branch coverage gaps for 'hard' difficulty...")
    calculate_branch_coverage_gaps_by_difficulty(
        df, 
        difficulty="hard", 
        output_path=stratified_path
    )
    
    # Generate visualizations for each pattern
    patterns = ['loops', 'conditionals', 'recursion']
    for pattern in patterns:
        viz_path = outputs_dir / f'coverage_by_pattern_{pattern}.png'
        generate_pattern_visualization(df, viz_path, pattern)
    
    logger.info("Visualization pipeline completed.")

if __name__ == '__main__':
    main()