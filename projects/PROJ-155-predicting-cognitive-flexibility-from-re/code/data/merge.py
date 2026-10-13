"""
Merge neuroimaging and behavioral data.
Updated to work with the simplified directory layout used by T002 and to
generate ``exclusion_log.csv`` when missing behavioral scores are filtered.
"""
import os
import logging
import pandas as pd
from typing import Tuple, List, Dict, Any

from code.data.paths import get_processed_path, get_raw_path
from code.utils.logging import log_error, init_logging, log_exclusion

logger = logging.getLogger(__name__)

def load_neuro_features() -> pd.DataFrame:
    """Load neuroimaging features from ``neuro_features.csv``."""
    processed_path = get_processed_path()
    neuro_features_path = os.path.join(processed_path, "neuro_features.csv")

    if not os.path.exists(neuro_features_path):
        raise FileNotFoundError(f"Neuro features file not found: {neuro_features_path}")

    df = pd.read_csv(neuro_features_path, dtype=str)
    logger.info(f"Loaded {len(df)} rows from neuro features")
    return df

def load_behavioral_scores() -> pd.DataFrame:
    """Load behavioral scores from ``behavioral_scores.csv``."""
    raw_path = get_raw_path()
    behavioral_path = os.path.join(raw_path, "behavioral_scores.csv")

    if not os.path.exists(behavioral_path):
        raise FileNotFoundError(f"Behavioral scores file not found: {behavioral_path}")

    df = pd.read_csv(behavioral_path, dtype=str)
    logger.info(f"Loaded {len(df)} rows from behavioral scores")
    return df

def merge_datasets(neuro_df: pd.DataFrame, behavioral_df: pd.DataFrame) -> pd.DataFrame:
    """Merge on ``Subject_ID``."""
    neuro_df['Subject_ID'] = neuro_df['Subject_ID'].astype(str)
    behavioral_df['Subject_ID'] = behavioral_df['Subject_ID'].astype(str)

    merged = pd.merge(neuro_df, behavioral_df, on='Subject_ID', how='inner')
    logger.info(f"Merged dataset has {len(merged)} rows")
    return merged

def validate_merged_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate required columns."""
    required = [
        'Subject_ID', 'Mean_FD', 'Age', 'Sex',
        'Flexibility_Score', 'Total_Scan_Time'
    ]
    missing = [c for c in required if c not in df.columns]
    return (len(missing) == 0, missing)

def filter_missing_behavioral_scores(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """Exclude rows with missing Flexibility_Score and log them."""
    if 'Flexibility_Score' not in df.columns:
        logger.warning("Flexibility_Score column not found – skipping filter.")
        return df, []

    missing = df['Flexibility_Score'].isna()
    excluded = df[missing].copy()
    kept = df[~missing].copy()

    exclusion_records = []
    for _, row in excluded.iterrows():
        record = {
            'Subject_ID': row['Subject_ID'],
            'Exclusion_Reason': 'Missing_Behavioral_Score',
            'Mean_FD': float(row.get('Mean_FD', 0.0))
        }
        exclusion_records.append(record)
        log_exclusion(
            subject_id=row['Subject_ID'],
            reason='Missing_Behavioral_Score',
            metadata={'Mean_FD': record['Mean_FD']}
        )

    logger.info(f"Filtered out {len(excluded)} subjects with missing behavioral scores.")
    return kept, exclusion_records

def save_exclusion_log(records: List[Dict[str, Any]]) -> None:
    """Write exclusion records to ``exclusion_log.csv``."""
    if not records:
        return
    path = os.path.join(get_processed_path(), "exclusion_log.csv")
    df = pd.DataFrame(records)
    df.to_csv(path, index=False)
    logger.info(f"Wrote exclusion log with {len(records)} rows to {path}")

def run_merge_pipeline() -> Tuple[pd.DataFrame, bool]:
    """Full merge pipeline."""
    init_logging()
    try:
        neuro_df = load_neuro_features()
        behavioral_df = load_behavioral_scores()
        merged = merge_datasets(neuro_df, behavioral_df)
        merged, exclusions = filter_missing_behavioral_scores(merged)
        save_exclusion_log(exclusions)

        valid, missing = validate_merged_schema(merged)
        if not valid:
            raise ValueError(f"Schema validation failed – missing columns: {missing}")

        out_path = os.path.join(get_processed_path(), "merged_dataset.csv")
        merged.to_csv(out_path, index=False)
        logger.info(f"Saved merged dataset to {out_path}")

        return merged, True
    except Exception as e:
        log_error("merge_pipeline", str(e))
        raise

def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Merge neuroimaging and behavioral data")
    parser.add_argument('--verify', action='store_true', help="Verify output schema after merge")
    parser.add_argument('--filter', action='store_true', help="Apply missing score filter and log exclusions")
    args = parser.parse_args()

    logger.info("Starting merge pipeline...")
    merged_df, success = run_merge_pipeline()

    if args.verify:
        ok, miss = validate_merged_schema(merged_df)
        if ok:
            logger.info("Verification PASSED.")
        else:
            logger.error(f"Verification FAILED – missing columns {miss}")
            raise ValueError("Schema verification failed")

    if args.filter:
        # Filtering already happened inside ``run_merge_pipeline``; just report.
        logger.info(f"Exclusion log written to {os.path.join(get_processed_path(), 'exclusion_log.csv')}")

    logger.info("Merge pipeline completed.")
    return 0

if __name__ == "__main__":
    main()
