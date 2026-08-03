import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from code.utils.config import set_global_seed, get_seed
from code.utils.logger import get_logger, log_data_completeness, log_power_insufficiency, log_validation_error
from code.data.fetch import fetch_dataset

# Constants for validation thresholds
COMPLETENESS_THRESHOLD = 0.95
POWER_INSUFFICIENCY_THRESHOLD = 500

logger = get_logger(__name__)

def load_keywords(keywords_path: Optional[Path] = None) -> List[str]:
    """Load keywords from YAML file."""
    if keywords_path is None:
        keywords_path = Path(__file__).parent.parent / "labeling" / "keywords.yaml"
    
    try:
        import yaml
        with open(keywords_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data.get('keywords', [])
    except FileNotFoundError:
        logger.error(f"Keywords file not found at {keywords_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing keywords YAML: {e}")
        raise

def classify_pr(row: pd.Series, keywords: List[str], threshold: int = 2) -> str:
    """
    Classify a PR as 'llm' or 'human' based on keyword matching in commit message and description.
    Returns 'llm' if >= threshold keywords are found (case-insensitive), else 'human'.
    """
    text_parts = []
    if pd.notna(row.get('commit_message')):
        text_parts.append(str(row['commit_message']).lower())
    if pd.notna(row.get('description')):
        text_parts.append(str(row['description']).lower())
    
    full_text = " ".join(text_parts)
    
    match_count = 0
    for keyword in keywords:
        if keyword.lower() in full_text:
            match_count += 1
            if match_count >= threshold:
                return 'llm'
    
    return 'human'

def load_dataset_from_fetch(dataset_id: str, split: str = "train") -> pd.DataFrame:
    """Wrapper to fetch dataset using the fetch module."""
    logger.info(f"Loading dataset {dataset_id} split {split}...")
    ds = fetch_dataset(dataset_id, split=split)
    return ds.to_pandas()

def filter_nulls(df: pd.DataFrame) -> pd.DataFrame:
    """Filter out rows where critical fields (code_diff, review_comments) are null or empty."""
    critical_cols = ['code_diff', 'review_comments']
    initial_count = len(df)
    
    # Filter rows where critical columns are not null and not empty strings
    mask = pd.Series(True, index=df.index)
    for col in critical_cols:
        if col in df.columns:
            mask &= df[col].notna()
            mask &= (df[col].astype(str).str.strip() != "")
    
    filtered_df = df[mask].reset_index(drop=True)
    dropped = initial_count - len(filtered_df)
    
    if dropped > 0:
        logger.warning(f"Dropped {dropped} rows due to null/empty critical fields.")
    
    return filtered_df

def compute_basic_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute basic statistics about the dataset."""
    stats = {
        "total_records": len(df),
        "columns": list(df.columns),
        "null_counts": df.isnull().sum().to_dict(),
        "dtypes": df.dtypes.astype(str).to_dict()
    }
    
    # Group by classification if available
    if 'classification' in df.columns:
        group_counts = df['classification'].value_counts().to_dict()
        stats['classification_counts'] = group_counts
    
    return stats

def check_completeness(df: pd.DataFrame) -> float:
    """
    Check data completeness: percentage of rows with all required fields populated.
    Required fields: code_diff, review_comments, project_id, commit_id.
    """
    required_cols = ['code_diff', 'review_comments', 'project_id', 'commit_id']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        logger.error(f"Missing required columns for completeness check: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Check for non-null values in required columns
    complete_mask = df[required_cols].notna().all(axis=1)
    completeness_rate = complete_mask.sum() / len(df)
    
    log_data_completeness(completeness_rate)
    return completeness_rate

def check_power_insufficiency(df: pd.DataFrame) -> Dict[str, int]:
    """
    Check for power insufficiency: ensure each classification group has >= 500 samples.
    Returns a dict of group sizes.
    """
    if 'classification' not in df.columns:
        logger.error("Classification column missing for power check.")
        raise ValueError("Classification column missing.")
    
    group_counts = df['classification'].value_counts().to_dict()
    
    insufficiency_found = False
    for group, count in group_counts.items():
        if count < POWER_INSUFFICIENCY_THRESHOLD:
            logger.warning(f"Group '{group}' has insufficient samples: {count} < {POWER_INSUFFICIENCY_THRESHOLD}")
            insufficiency_found = True
    
    if insufficiency_found:
        log_power_insufficiency(group_counts, POWER_INSUFFICIENCY_THRESHOLD)
    
    return group_counts

def write_error_report(reason: str, details: Dict[str, Any], output_path: Path) -> None:
    """Write a detailed error report to JSON."""
    error_report = {
        "status": "failed",
        "reason": reason,
        "details": details,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(error_report, f, indent=2)
    
    logger.error(f"Error report written to {output_path}")

def write_stats_report(stats: Dict[str, Any], output_path: Path) -> None:
    """Write statistics report to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Stats report written to {output_path}")

def run_validation_pipeline(
    df: pd.DataFrame,
    completeness_threshold: float = COMPLETENESS_THRESHOLD,
    power_threshold: int = POWER_INSUFFICIENCY_THRESHOLD,
    error_report_path: Optional[Path] = None,
    stats_report_path: Optional[Path] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Run validation checks: completeness and power insufficiency.
    Halts execution (raises ValueError) if checks fail.
    Writes error_report.json if validation fails.
    """
    if error_report_path is None:
        error_report_path = Path(__file__).parent.parent.parent / "docs" / "reports" / "error_report.json"
    
    if stats_report_path is None:
        stats_report_path = Path(__file__).parent.parent.parent / "docs" / "reports" / "stats_report.json"

    # 1. Check Completeness
    completeness = check_completeness(df)
    if completeness < completeness_threshold:
        reason = f"Data completeness {completeness:.2%} is below threshold {completeness_threshold:.2%}"
        details = {
            "completeness_rate": completeness,
            "threshold": completeness_threshold,
            "missing_columns": [c for c in ['code_diff', 'review_comments', 'project_id', 'commit_id'] if c not in df.columns or df[c].isna().any()]
        }
        log_validation_error(reason)
        write_error_report(reason, details, error_report_path)
        raise ValueError(reason)
    
    # 2. Check Power Insufficiency
    group_counts = check_power_insufficiency(df)
    insufficiency_groups = {k: v for k, v in group_counts.items() if v < power_threshold}
    
    if insufficiency_groups:
        reason = f"Power insufficiency detected: groups {insufficiency_groups} have fewer than {power_threshold} samples"
        details = {
            "group_counts": group_counts,
            "threshold": power_threshold,
            "insufficient_groups": insufficiency_groups
        }
        log_validation_error(reason)
        write_error_report(reason, details, error_report_path)
        raise ValueError(reason)
    
    # If all checks pass
    logger.info("Validation passed: completeness and power requirements met.")
    
    # Write stats report on success
    basic_stats = compute_basic_stats(df)
    basic_stats['validation_status'] = 'passed'
    write_stats_report(basic_stats, stats_report_path)
    
    return True, basic_stats

def main():
    """Main execution function for preprocessing and validation."""
    set_global_seed(get_seed())
    
    # Configuration
    DATASET_ID = "codeparliament/github-code-search"
    SPLIT = "train"
    KEYWORDS_PATH = Path(__file__).parent.parent / "labeling" / "keywords.yaml"
    
    try:
        # 1. Load Dataset
        df = load_dataset_from_fetch(DATASET_ID, split=SPLIT)
        logger.info(f"Loaded {len(df)} records from {DATASET_ID}")
        
        # 2. Filter Nulls
        df = filter_nulls(df)
        logger.info(f"Filtered to {len(df)} records after removing nulls")
        
        # 3. Load Keywords and Classify
        keywords = load_keywords(KEYWORDS_PATH)
        logger.info(f"Loaded {len(keywords)} keywords for classification")
        
        df['classification'] = df.apply(lambda row: classify_pr(row, keywords), axis=1)
        logger.info("Classification complete")
        
        # 4. Run Validation Pipeline (T018 Requirement)
        # This will halt and raise ValueError if checks fail
        success, stats = run_validation_pipeline(df)
        
        if success:
            logger.info("Preprocessing and validation completed successfully.")
            logger.info(f"Final stats: {stats}")
        
    except ValueError as e:
        # This block catches the validation errors raised by run_validation_pipeline
        # The error report has already been written by that function
        logger.error(f"Validation failed: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during preprocessing: {e}")
        raise

if __name__ == "__main__":
    main()
