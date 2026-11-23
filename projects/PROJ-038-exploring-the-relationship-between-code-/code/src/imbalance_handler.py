"""
Module: code/src/imbalance_handler.py

Purpose:
Handle class imbalance in the bug prediction dataset.
Specifically detects projects (or the aggregate dataset) where the count of buggy files (is_buggy=1) is zero.
Logs warnings for such cases and filters them out gracefully to prevent model training failures.

Dependencies:
- pandas
- logging
- src.config (for memory limits)
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from src.config import get_memory_limit_bytes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ClassImbalanceError(Exception):
    """
    Custom exception raised when class imbalance is detected and cannot be handled gracefully,
    or when the dataset becomes empty after filtering.
    """
    pass

def detect_class_imbalance(df: pd.DataFrame, target_col: str = 'is_buggy') -> Dict[str, Any]:
    """
    Analyze the distribution of the target column to detect class imbalance.
    
    Args:
        df (pd.DataFrame): The input dataframe containing the target column.
        target_col (str): The name of the target column (default: 'is_buggy').
    
    Returns:
        Dict[str, Any]: A dictionary containing:
            - 'total_samples': Total number of rows.
            - 'class_0_count': Count of negative class (0).
            - 'class_1_count': Count of positive class (1).
            - 'imbalance_ratio': Ratio of class 0 to class 1 (or infinity if class 1 is 0).
            - 'has_zero_buggy': Boolean indicating if class 1 count is 0.
            - 'warning': Warning message if imbalance is critical.
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataframe.")
    
    total_samples = len(df)
    class_1_count = df[target_col].sum()
    class_0_count = total_samples - class_1_count
    
    has_zero_buggy = (class_1_count == 0)
    warning = None
    
    if has_zero_buggy:
        warning = f"CRITICAL: No buggy files (class 1) found in dataset. {class_0_count} clean files present."
    elif class_1_count < total_samples * 0.05:
        # Warning if less than 5% are buggy
        warning = f"WARNING: Severe class imbalance detected. Buggy files: {class_1_count} ({class_1_count/total_samples:.2%})."
    
    imbalance_ratio = class_0_count / class_1_count if class_1_count > 0 else float('inf')
    
    return {
        'total_samples': total_samples,
        'class_0_count': int(class_0_count),
        'class_1_count': int(class_1_count),
        'imbalance_ratio': imbalance_ratio,
        'has_zero_buggy': has_zero_buggy,
        'warning': warning
    }

def filter_imbalanced_projects(df: pd.DataFrame, project_col: str = 'project_id', target_col: str = 'is_buggy') -> Tuple[pd.DataFrame, List[str]]:
    """
    Filter out projects that have zero buggy files.
    
    This function groups the data by project, checks if any project has 0 buggy files,
    logs a warning for those projects, and returns a dataframe excluding them.
    
    Args:
        df (pd.DataFrame): The input dataframe.
        project_col (str): The column name identifying the project (default: 'project_id').
        target_col (str): The target column name (default: 'is_buggy').
    
    Returns:
        Tuple[pd.DataFrame, List[str]]:
            - Filtered dataframe with zero-buggy projects removed.
            - List of project IDs that were removed.
    
    Raises:
        ClassImbalanceError: If the resulting dataframe is empty.
    """
    if project_col not in df.columns:
        # If no project column exists, treat the whole dataset as one group
        logger.warning(f"Project column '{project_col}' not found. Treating entire dataset as one group.")
        stats = detect_class_imbalance(df, target_col)
        if stats['has_zero_buggy']:
            logger.error(stats['warning'])
            raise ClassImbalanceError("Dataset contains no buggy files and cannot be trained.")
        return df, []
    
    removed_projects = []
    
    # Group by project and count buggy files
    project_counts = df.groupby(project_col)[target_col].sum()
    
    # Identify projects with zero buggy files
    zero_buggy_projects = project_counts[project_counts == 0].index.tolist()
    
    if zero_buggy_projects:
        logger.warning(f"Detected {len(zero_buggy_projects)} projects with zero buggy files. Skipping them.")
        for proj in zero_buggy_projects:
            logger.warning(f"  - Skipping project: {proj}")
        removed_projects = zero_buggy_projects
        
        # Filter the dataframe
        filtered_df = df[~df[project_col].isin(removed_projects)]
        
        if filtered_df.empty:
            raise ClassImbalanceError(
                f"After filtering {len(removed_projects)} zero-buggy projects, the dataset is empty. "
                "Cannot proceed with modeling."
            )
        
        logger.info(f"Filtered dataset shape: {filtered_df.shape}. Removed {len(removed_projects)} projects.")
        return filtered_df, removed_projects
    
    logger.info("No zero-buggy projects detected. Proceeding with full dataset.")
    return df, []

def save_imbalance_report(stats: Dict[str, Any], removed_projects: List[str], output_path: Path) -> None:
    """
    Save the class imbalance analysis and filtering report to a file.
    
    Args:
        stats (Dict[str, Any]): The statistics dictionary from detect_class_imbalance.
        removed_projects (List[str]): List of project IDs that were removed.
        output_path (Path): Path to the output file (e.g., 'data/results/imbalance_report.json').
    """
    report = {
        'statistics': stats,
        'removed_projects': removed_projects,
        'num_removed_projects': len(removed_projects),
        'status': 'success' if not stats['has_zero_buggy'] else 'critical_zero_buggy_detected'
    }
    
    if stats['has_zero_buggy'] and not removed_projects:
        # This case implies the whole dataset was checked and found empty of bugs, but no project filtering happened
        report['status'] = 'critical_zero_buggy_detected'
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        import json
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Imbalance report saved to {output_path}")

def main() -> int:
    """
    Main entry point for the imbalance handler script.
    Reads the processed features CSV, performs imbalance detection and filtering,
    and saves the cleaned dataset and report.
    
    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    try:
        # Define paths relative to project root
        # Assuming this script runs from code/ directory
        project_root = Path(__file__).resolve().parent.parent
        input_path = project_root / 'data' / 'processed' / 'features.csv'
        output_path = project_root / 'data' / 'processed' / 'features_cleaned.csv'
        report_path = project_root / 'data' / 'results' / 'imbalance_report.json'
        
        if not input_path.exists():
            logger.error(f"Input file not found: {input_path}")
            return 1
        
        logger.info(f"Loading features from {input_path}...")
        df = pd.read_csv(input_path)
        
        # Detect imbalance on the full dataset
        stats = detect_class_imbalance(df)
        
        if stats['warning']:
            logger.warning(stats['warning'])
        
        # Filter out zero-buggy projects
        # Assuming 'project_id' is in the dataframe; if not, it treats whole dataset as one group
        filtered_df, removed_projects = filter_imbalanced_projects(df)
        
        # Save cleaned dataset
        filtered_df.to_csv(output_path, index=False)
        logger.info(f"Cleaned dataset saved to {output_path}")
        
        # Save report
        save_imbalance_report(stats, removed_projects, report_path)
        
        return 0
        
    except ClassImbalanceError as e:
        logger.error(f"Class Imbalance Error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())