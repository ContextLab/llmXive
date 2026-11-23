"""Visualization and stratification logic for code coverage analysis."""
import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_patterns(code: str) -> Dict[str, int]:
    """Extract code patterns (loops, conditionals, recursion) from code."""
    patterns = {
        'loops': 0,
        'conditionals': 0,
        'recursion': 0
    }

    # Count loops (for, while)
    patterns['loops'] = len(re.findall(r'\b(for|while)\b', code))

    # Count conditionals (if, elif, else)
    patterns['conditionals'] = len(re.findall(r'\b(if|elif|else)\b', code))

    # Detect recursion (function calls itself)
    # Extract function name
    func_match = re.search(r'def\s+(\w+)\s*\(', code)
    if func_match:
        func_name = func_match.group(1)
        # Count calls to same function (excluding definition)
        patterns['recursion'] = len(re.findall(rf'\b{func_name}\s*\(', code)) - 1
        if patterns['recursion'] < 0:
            patterns['recursion'] = 0

    return patterns

def categorize_pattern(patterns: Dict[str, int]) -> str:
    """Categorize the dominant pattern in code."""
    if patterns['recursion'] > 0:
        return 'recursion'
    elif patterns['loops'] > patterns['conditionals']:
        return 'loops'
    elif patterns['conditionals'] > 0:
        return 'conditionals'
    else:
        return 'other'

def load_catalog_and_coverage(catalog_path: str, coverage_dir: str) -> pd.DataFrame:
    """Load catalog and merge with coverage reports."""
    # Load catalog
    catalog = pd.read_json(catalog_path)

    # Load all coverage reports
    coverage_data = []
    for file in Path(coverage_dir).glob('*.json'):
        with open(file, 'r') as f:
            report = json.load(f)
            if report.get('status') == 'success':
                coverage_data.append(report)

    coverage_df = pd.DataFrame(coverage_data)

    # Merge on task_id
    if 'task_id' in coverage_df.columns:
        merged = pd.merge(catalog, coverage_df, on='task_id', how='inner')
    else:
        # Handle case where coverage reports might have different structure
        logger.warning("Coverage reports do not contain task_id column. Skipping merge.")
        merged = catalog

    return merged

def analyze_pattern_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Analyze distribution of code patterns across difficulty levels."""
    pattern_counts = df.groupby(['difficulty', 'pattern']).size().reset_index(name='count')
    return pattern_counts

def generate_pattern_visualization(df: pd.DataFrame, output_path: str):
    """Generate visualization of pattern distribution."""
    plt.figure(figsize=(10, 6))
    sns.barplot(data=df, x='difficulty', y='count', hue='pattern')
    plt.title('Code Pattern Distribution by Difficulty')
    plt.xlabel('Difficulty')
    plt.ylabel('Count')
    plt.legend(title='Pattern')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Visualization saved to {output_path}")

def create_stratified_report(df: pd.DataFrame, output_dir: str):
    """Create stratified reports by difficulty and pattern."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Stratify by difficulty and pattern
    stratified = df.groupby(['difficulty', 'pattern']).agg({
        'line_coverage': 'mean',
        'branch_coverage': lambda x: x.mean() if pd.notna(x).all() else 'N/A'
    }).reset_index()

    # Save stratified report
    stratified_path = output_path / 'stratified_summary.csv'
    stratified.to_csv(stratified_path, index=False)
    logger.info(f"Stratified report saved to {stratified_path}")

    return stratified

def calculate_branch_coverage_gaps_by_difficulty(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate mean branch coverage gaps for specific difficulty tiers."""
    # Filter out HumanEval tasks (branch_coverage == N/A)
    valid_df = df[df['branch_coverage'] != 'N/A'].copy()

    if valid_df.empty:
        logger.warning("No valid branch coverage data found. Skipping calculation.")
        return pd.DataFrame(columns=['pattern', 'difficulty', 'mean_gap', 'count'])

    # Convert branch_coverage to numeric
    valid_df['branch_coverage'] = pd.to_numeric(valid_df['branch_coverage'], errors='coerce')

    # Calculate gaps (assuming we have llm and human coverage)
    # If we have both, calculate gap; otherwise, use available data
    if 'llm_branch_coverage' in valid_df.columns and 'human_branch_coverage' in valid_df.columns:
        valid_df['gap'] = valid_df['llm_branch_coverage'] - valid_df['human_branch_coverage']
    elif 'line_coverage' in valid_df.columns:
        # Fallback to line coverage if branch not available
        valid_df['gap'] = 0.0  # Placeholder if no direct comparison

    # Group by pattern and difficulty
    result = valid_df.groupby(['pattern', 'difficulty']).agg({
        'gap': 'mean',
        'task_id': 'count'
    }).reset_index()
    result.columns = ['pattern', 'difficulty', 'mean_gap', 'count']

    return result

def check_stratification_sufficient_data(df: pd.DataFrame, min_count: int = 30) -> Tuple[bool, List[str]]:
    """
    Pre-flight check: verify sufficient data points (n >= min_count) for each stratification group.
    
    Args:
        df: DataFrame containing coverage pairs with 'difficulty' and 'pattern' columns
        min_count: Minimum number of data points required per group
    
    Returns:
        Tuple of (is_sufficient, list_of_insufficient_groups)
    """
    if df.empty:
        logger.warning("Input DataFrame is empty. Cannot perform stratification check.")
        return False, ["DataFrame is empty"]

    # Group by difficulty and pattern
    grouped = df.groupby(['difficulty', 'pattern']).size()
    
    insufficient_groups = []
    for (difficulty, pattern), count in grouped.items():
        if count < min_count:
          insufficient_groups.append(f"difficulty={difficulty}, pattern={pattern} (n={count})")
    
    is_sufficient = len(insufficient_groups) == 0

    if not is_sufficient:
        logger.warning(
            f"Insufficient data for stratification (min required: {min_count}). "
            f"Affected groups: {', '.join(insufficient_groups)}. "
            f"Visualizations for these groups will be skipped to prevent misleading plots."
        )
    else:
        logger.info(f"Stratification check passed. All groups have n >= {min_count}.")

    return is_sufficient, insufficient_groups

def main():
    """Main entry point for visualization and stratification."""
    import argparse

    parser = argparse.ArgumentParser(description='Generate visualizations and stratified reports')
    parser.add_argument('--catalog-path', type=str, required=True, help='Path to catalog.json')
    parser.add_argument('--coverage-dir', type=str, required=True, help='Directory containing coverage reports')
    parser.add_argument('--output-dir', type=str, default='outputs', help='Output directory for visualizations')
    parser.add_argument('--min-stratification-count', type=int, default=30, help='Minimum data points per stratification group')
    
    args = parser.parse_args()

    # Load data
    logger.info("Loading catalog and coverage data...")
    df = load_catalog_and_coverage(args.catalog_path, args.coverage_dir)

    if df.empty:
        logger.error("No data loaded. Exiting.")
        return

    # Pre-flight check for sufficient data
    logger.info(f"Checking stratification sufficiency (min count: {args.min_stratification_count})...")
    is_sufficient, insufficient_groups = check_stratification_sufficient_data(
        df, 
        min_count=args.min_stratification_count
    )

    if not is_sufficient:
        logger.warning(
            f"Stratification groups with insufficient data will be skipped: {insufficient_groups}. "
            "Proceeding with available data."
        )

    # Extract patterns if not already present
    if 'pattern' not in df.columns:
        logger.info("Extracting code patterns...")
        df['patterns'] = df['human_solution'].apply(extract_patterns)
        df['pattern'] = df['patterns'].apply(categorize_pattern)

    # Create output directory
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate visualizations only for groups with sufficient data
    if is_sufficient:
        logger.info("Generating pattern distribution visualization...")
        pattern_dist = analyze_pattern_distribution(df)
        viz_path = output_path / 'coverage_by_pattern.png'
        generate_pattern_visualization(pattern_dist, str(viz_path))

        logger.info("Creating stratified report...")
        stratified = create_stratified_report(df, str(output_path))

        logger.info("Calculating branch coverage gaps by difficulty...")
        gaps_df = calculate_branch_coverage_gaps_by_difficulty(df)
        gaps_path = output_path / 'branch_coverage_gaps_by_difficulty.csv'
        gaps_df.to_csv(gaps_path, index=False)
        logger.info(f"Branch coverage gaps saved to {gaps_path}")
    else:
        logger.warning("Skipping visualization generation due to insufficient data in stratification groups.")
        # Still create a report indicating the issue
        report_path = output_path / 'stratification_sufficiency_report.json'
        report = {
            "is_sufficient": is_sufficient,
            "min_required_count": args.min_stratification_count,
            "insufficient_groups": insufficient_groups
        }
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Sufficiency report saved to {report_path}")

    logger.info("Visualization pipeline completed.")

if __name__ == '__main__':
    main()