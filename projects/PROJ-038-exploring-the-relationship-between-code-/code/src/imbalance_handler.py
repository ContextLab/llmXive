"""
Imbalance handling module for bug prediction pipeline.

This module detects projects with zero buggy files (class imbalance)
and handles them gracefully by logging warnings and skipping them
from further analysis.
"""
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from src.config import get_memory_limit_bytes

logger = logging.getLogger(__name__)


class ClassImbalanceError(Exception):
    """Exception raised when a project has no buggy files."""
    pass


def detect_class_imbalance(df: pd.DataFrame, 
                           project_id_col: str = 'project_id',
                           target_col: str = 'is_buggy') -> Dict[str, List[str]]:
    """
    Detect projects with zero buggy files in the dataset.
    
    Args:
        df: DataFrame containing feature data with project_id and target columns.
        project_id_col: Name of the column containing project identifiers.
        target_col: Name of the column containing the bug label (0 or 1).
        
    Returns:
        Dictionary with two keys:
            - 'zero_buggy': List of project IDs with zero buggy files
            - 'all_buggy': List of project IDs where all files are buggy (edge case)
    """
    if project_id_col not in df.columns:
        raise ValueError(f"Column '{project_id_col}' not found in DataFrame")
    if target_col not in df.columns:
        raise ValueError(f"Column '{target_col}' not found in DataFrame")
        
    zero_buggy_projects = []
    all_buggy_projects = []
    
    # Group by project and check bug distribution
    project_stats = df.groupby(project_id_col)[target_col].agg(['sum', 'count'])
    
    for project_id, stats in project_stats.iterrows():
        buggy_count = int(stats['sum'])
        total_count = int(stats['count'])
        
        if buggy_count == 0:
            zero_buggy_projects.append(project_id)
            logger.warning(
                f"Project '{project_id}' has {total_count} files but ZERO buggy files. "
                f"This project will be skipped from modeling to avoid class imbalance issues."
            )
        elif buggy_count == total_count:
            all_buggy_projects.append(project_id)
            logger.warning(
                f"Project '{project_id}' has {total_count} files and ALL are buggy. "
                f"This edge case may also cause modeling issues."
            )
    
    return {
        'zero_buggy': zero_buggy_projects,
        'all_buggy': all_buggy_projects
    }


def filter_imbalanced_projects(df: pd.DataFrame,
                               project_id_col: str = 'project_id',
                               target_col: str = 'is_buggy',
                               min_buggy_ratio: float = 0.01,
                               min_buggy_count: int = 1) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Filter out projects with severe class imbalance.
    
    Args:
        df: Input DataFrame with project and target columns.
        project_id_col: Column name for project identifiers.
        target_col: Column name for bug labels.
        min_buggy_ratio: Minimum ratio of buggy files to keep a project (default 0.01 = 1%).
        min_buggy_count: Minimum absolute count of buggy files to keep a project.
        
    Returns:
        Tuple of (filtered_df, filter_stats) where filter_stats contains:
            - 'removed_projects': List of removed project IDs
            - 'removed_count': Number of rows removed
            - 'zero_buggy': Projects removed due to zero buggy files
            - 'low_buggy': Projects removed due to low buggy ratio/count
    """
    if project_id_col not in df.columns:
        raise ValueError(f"Column '{project_id_col}' not found in DataFrame")
    if target_col not in df.columns:
        raise ValueError(f"Column '{target_col}' not found in DataFrame")
        
    # Detect imbalanced projects
    imbalance_info = detect_class_imbalance(df, project_id_col, target_col)
    
    zero_buggy = set(imbalance_info['zero_buggy'])
    all_buggy = set(imbalance_info['all_buggy'])
    
    # Additional check for low buggy ratio
    project_stats = df.groupby(project_id_col)[target_col].agg(['sum', 'count'])
    low_buggy = set()
    
    for project_id, stats in project_stats.iterrows():
        buggy_count = int(stats['sum'])
        total_count = int(stats['count'])
        
        if buggy_count > 0:  # Already handled zero case
            ratio = buggy_count / total_count
            if ratio < min_buggy_ratio or buggy_count < min_buggy_count:
                low_buggy.add(project_id)
                logger.warning(
                    f"Project '{project_id}' has only {buggy_count}/{total_count} buggy files "
                    f"(ratio={ratio:.4f}). This is below threshold and will be skipped."
                )
    
    # Combine all projects to remove
    projects_to_remove = zero_buggy | all_buggy | low_buggy
    
    if not projects_to_remove:
        logger.info("No projects with class imbalance detected. Keeping all data.")
        return df, {
            'removed_projects': [],
            'removed_count': 0,
            'zero_buggy': [],
            'all_buggy': [],
            'low_buggy': []
        }
    
    # Filter the DataFrame
    filtered_df = df[~df[project_id_col].isin(projects_to_remove)]
    removed_count = len(df) - len(filtered_df)
    
    logger.info(
        f"Class imbalance handling complete. Removed {removed_count} rows "
        f"from {len(projects_to_remove)} projects. "
        f"Remaining: {len(filtered_df)} rows."
    )
    
    return filtered_df, {
        'removed_projects': list(projects_to_remove),
        'removed_count': removed_count,
        'zero_buggy': list(zero_buggy),
        'all_buggy': list(all_buggy),
        'low_buggy': list(low_buggy)
    }


def save_imbalance_report(stats: Dict[str, Any], output_path: Path) -> None:
    """
    Save the class imbalance handling report to a JSON file.
    
    Args:
        stats: Dictionary containing imbalance statistics from filter_imbalanced_projects.
        output_path: Path to save the JSON report.
    """
    import json
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        'summary': {
            'total_removed_projects': len(stats['removed_projects']),
            'total_removed_rows': stats['removed_count'],
            'projects_with_zero_buggy': len(stats['zero_buggy']),
            'projects_with_all_buggy': len(stats['all_buggy']),
            'projects_with_low_buggy_ratio': len(stats['low_buggy'])
        },
        'details': {
            'zero_buggy_projects': stats['zero_buggy'],
            'all_buggy_projects': stats['all_buggy'],
            'low_buggy_ratio_projects': stats['low_buggy']
        }
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
        
    logger.info(f"Class imbalance report saved to {output_path}")


def main() -> int:
    """
    Main entry point for class imbalance handling.
    
    Reads the features.csv, detects and filters imbalanced projects,
    saves the filtered dataset and a report.
    
    Returns:
        0 on success, 1 on failure.
    """
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(
        description='Handle class imbalance in bug prediction dataset'
    )
    parser.add_argument(
        '--input', '-i',
        type=str,
        default='code/data/processed/features.csv',
        help='Path to input features CSV'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='code/data/processed/features_balanced.csv',
        help='Path to output balanced features CSV'
    )
    parser.add_argument(
        '--report', '-r',
        type=str,
        default='code/data/results/imbalance_report.json',
        help='Path to save imbalance handling report'
    )
    parser.add_argument(
        '--min-buggy-ratio',
        type=float,
        default=0.01,
        help='Minimum ratio of buggy files to keep a project'
    )
    parser.add_argument(
        '--min-buggy-count',
        type=int,
        default=1,
        help='Minimum absolute count of buggy files to keep a project'
    )
    
    args = parser.parse_args()
    
    try:
        # Load data
        input_path = Path(args.input)
        if not input_path.exists():
            logger.error(f"Input file not found: {input_path}")
            return 1
        
        logger.info(f"Loading data from {input_path}")
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
        
        # Check required columns
        required_cols = ['project_id', 'is_buggy']
        for col in required_cols:
            if col not in df.columns:
                logger.error(f"Required column '{col}' not found in input data")
                return 1
        
        # Handle imbalance
        filtered_df, stats = filter_imbalanced_projects(
            df,
            project_id_col='project_id',
            target_col='is_buggy',
            min_buggy_ratio=args.min_buggy_ratio,
            min_buggy_count=args.min_buggy_count
        )
        
        # Save filtered data
        output_path = Path(args.output)
        filtered_df.to_csv(output_path, index=False)
        logger.info(f"Saved filtered data to {output_path}")
        
        # Save report
        report_path = Path(args.report)
        save_imbalance_report(stats, report_path)
        
        # Summary
        logger.info("=" * 60)
        logger.info("CLASS IMBALANCE HANDLING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Original rows: {len(df)}")
        logger.info(f"Filtered rows: {len(filtered_df)}")
        logger.info(f"Rows removed: {stats['removed_count']}")
        logger.info(f"Projects with zero buggy files: {len(stats['zero_buggy'])}")
        logger.info(f"Projects with all buggy files: {len(stats['all_buggy'])}")
        logger.info(f"Projects with low buggy ratio: {len(stats['low_buggy'])}")
        logger.info("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"Error during class imbalance handling: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
