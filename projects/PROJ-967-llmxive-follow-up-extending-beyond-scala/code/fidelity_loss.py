import argparse
import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd
import numpy as np

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('results/fidelity_loss.log')
        ]
    )
    return logging.getLogger(__name__)

def load_raw_data(base_dir: Path, logger: logging.Logger):
    path = base_dir / 'data' / 'processed' / 'raw_data.parquet'
    if not path.exists():
        raise FileNotFoundError(f"Raw data not found: {path}")
    return pd.read_parquet(path)

def calculate_fidelity_loss(df: pd.DataFrame, logger: logging.Logger):
    """
    Calculate MAE between student_scalar and human-annotated score for the primary_dimension.
    Filter out samples with missing data.
    """
    # Ensure primary_dimension exists
    if 'primary_dimension' not in df.columns:
        raise ValueError("primary_dimension column missing in dataframe")

    # Flatten human annotations if needed (should be done in ingest, but safety check)
    if 'human_Alignment' not in df.columns and 'human_annotations' in df.columns:
        if isinstance(df['human_annotations'].iloc[0], dict):
            human_df = pd.DataFrame(df['human_annotations'].tolist(), index=df.index)
            human_df.columns = [f'human_{c}' for c in human_df.columns]
            df = pd.concat([df, human_df], axis=1)
            df = df.drop('human_annotations', axis=1)

    # Identify columns for dynamic lookup
    dimensions = ['Alignment', 'Realism', 'Aesthetics', 'Plausibility']
    human_cols = {d: f'human_{d}' for d in dimensions}

    # Filter: exclude if primary_dimension is null, student_scalar is null, or human score is missing
    valid_mask = (
        df['primary_dimension'].notna() &
        df['student_scalar'].notna()
    )

    # Check human annotation availability
    def check_human(row):
        dim = row['primary_dimension']
        if dim not in human_cols:
            return False
        col = human_cols[dim]
        return col in df.columns and pd.notna(row[col])

    valid_mask = valid_mask & df.apply(check_human, axis=1)

    excluded_df = df[~valid_mask]
    valid_df = df[valid_mask].copy()

    # Log exclusions
    exclusions = []
    for idx, row in excluded_df.iterrows():
        reason = "missing_data"
        if pd.isna(row.get('primary_dimension')):
            reason = "missing_primary_dimension"
        elif pd.isna(row.get('student_scalar')):
            reason = "missing_student_scalar"
        elif row['primary_dimension'] not in human_cols:
            reason = "invalid_dimension"
        else:
            col = human_cols[row['primary_dimension']]
            if pd.isna(row.get(col)):
                reason = "missing_human_annotation"
        exclusions.append({
            'sample_id': idx,
            'reason': reason,
            'timestamp': pd.Timestamp.now().isoformat()
        })

    # Append to existing exclusions log if it exists
    exclusions_path = base_dir / 'data' / 'processed' / 'exclusions_log.json'
    if exclusions_path.exists():
        with open(exclusions_path, 'r') as f:
            existing = json.load(f)
        existing.extend(exclusions)
    else:
        existing = exclusions

    with open(exclusions_path, 'w') as f:
        json.dump(existing, f, indent=2)

    logger.info(f"Excluded {len(excluded_df)} samples. Remaining: {len(valid_df)}")

    # Calculate MAE
    valid_df['fidelity_loss'] = 0.0
    for dim in dimensions:
        col = human_cols[dim]
        mask = valid_df['primary_dimension'] == dim
        if mask.any():
            valid_df.loc[mask, 'fidelity_loss'] = np.abs(valid_df.loc[mask, 'student_scalar'] - valid_df.loc[mask, col])

    return valid_df, len(excluded_df)

def save_cleaned_data(df: pd.DataFrame, base_dir: Path, logger: logging.Logger):
    output_path = base_dir / 'data' / 'processed' / 'cleaned_data.parquet'
    df.to_parquet(output_path)
    logger.info(f"Saved cleaned data to {output_path}")

def save_summary(df: pd.DataFrame, excluded_count: int, base_dir: Path, logger: logging.Logger):
    summary = {
        'mean_fidelity_loss': float(df['fidelity_loss'].mean()) if not df.empty else 0.0,
        'median_fidelity_loss': float(df['fidelity_loss'].median()) if not df.empty else 0.0,
        'count': len(df),
        'excluded_count': excluded_count
    }
    output_path = base_dir / 'data' / 'processed' / 'fidelity_loss_summary.json'
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Saved summary to {output_path}")

def parse_args():
    parser = argparse.ArgumentParser(description='Calculate Fidelity Loss')
    parser.add_argument('--base-dir', type=str, default='projects/PROJ-967-llmxive-follow-up-extending-beyond-scala')
    return parser.parse_args()

def main():
    args = parse_args()
    base_dir = Path(args.base_dir)
    logger = setup_logging()

    try:
        df = load_raw_data(base_dir, logger)
        cleaned_df, excluded_count = calculate_fidelity_loss(df, logger)
        save_cleaned_data(cleaned_df, base_dir, logger)
        save_summary(cleaned_df, excluded_count, base_dir, logger)
        logger.info("Fidelity loss calculation completed.")
    except Exception as e:
        logger.error(f"Failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
