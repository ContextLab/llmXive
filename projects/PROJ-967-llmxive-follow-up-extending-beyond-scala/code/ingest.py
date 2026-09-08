import argparse
import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd
from scipy import stats

# Import from primary_dimension_util as per API surface
from primary_dimension_util import derive_primary_dimension_from_metadata, get_derivation_rule_hash, process_dataframe_primary_dimensions

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('results/ingest.log')
        ]
    )
    return logging.getLogger(__name__)

def setup_directories(base_dir: Path):
    (base_dir / 'data' / 'raw').mkdir(parents=True, exist_ok=True)
    (base_dir / 'data' / 'processed').mkdir(parents=True, exist_ok=True)
    (base_dir / 'results').mkdir(parents=True, exist_ok=True)

def load_and_align_data(base_dir: Path, logger: logging.Logger, use_mock: bool = False):
    """
    Load raw data (real or mock), align teacher/student/human scores,
    and handle missing data.
    """
    if use_mock:
        input_path = base_dir / 'data' / 'raw' / 'mock_z_reward.parquet'
    else:
        input_path = base_dir / 'data' / 'raw' / 'z_reward.parquet'

    if not input_path.exists():
        raise FileNotFoundError(f"Input dataset not found: {input_path}")

    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} samples from {input_path}")

    # Ensure required columns exist
    required_cols = ['prompt', 'image_url', 'teacher_scores', 'student_scalar', 'human_annotations', 'primary_dimension']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        logger.warning(f"Missing columns in raw data: {missing}. Attempting to handle gracefully.")

    # Align and process primary dimension (T014 logic)
    # This ensures primary_dimension is never null, or sample is excluded
    df, exclusions = process_dataframe_primary_dimensions(df, logger)

    # Save exclusions
    exclusions_path = base_dir / 'data' / 'processed' / 'exclusions_log.json'
    with open(exclusions_path, 'w') as f:
        json.dump(exclusions, f, indent=2)
    logger.info(f"Logged {len(exclusions)} excluded samples to {exclusions_path}")

    # Align teacher scores, student scalars, human annotations by sample ID
    # (Assuming sample_id is the index or a column; if not, use index)
    if 'sample_id' not in df.columns:
        df['sample_id'] = df.index

    # Flatten teacher_scores and human_annotations if they are nested objects
    # Example: teacher_scores: {"Alignment": 5.0, ...} -> columns: Alignment, Realism...
    if isinstance(df['teacher_scores'].iloc[0], dict):
        teacher_df = pd.DataFrame(df['teacher_scores'].tolist(), index=df.index)
        teacher_df.columns = [f'teacher_{c}' for c in teacher_df.columns]
        df = pd.concat([df, teacher_df], axis=1)
        df = df.drop('teacher_scores', axis=1)

    if 'human_annotations' in df.columns and isinstance(df['human_annotations'].iloc[0], dict):
        human_df = pd.DataFrame(df['human_annotations'].tolist(), index=df.index)
        human_df.columns = [f'human_{c}' for c in human_df.columns]
        df = pd.concat([df, human_df], axis=1)
        df = df.drop('human_annotations', axis=1)

    # Save aligned data
    output_path = base_dir / 'data' / 'processed' / 'raw_data.parquet'
    df.to_parquet(output_path)
    logger.info(f"Saved aligned data to {output_path}")

    return df

def print_summary(df: pd.DataFrame, logger: logging.Logger):
    logger.info("=== Ingestion Summary ===")
    logger.info(f"Total samples: {len(df)}")
    logger.info(f"Columns: {list(df.columns)}")
    if 'primary_dimension' in df.columns:
        logger.info(f"Dimension coverage: {df['primary_dimension'].value_counts().to_dict()}")
    if 'student_scalar' in df.columns:
        logger.info(f"Missing student_scalar: {df['student_scalar'].isna().sum()}")
    logger.info("========================")

def parse_args():
    parser = argparse.ArgumentParser(description='Ingest and align Z-Reward dataset')
    parser.add_argument('--base-dir', type=str, default='projects/PROJ-967-llmxive-follow-up-extending-beyond-scala',
                        help='Base directory of the project')
    parser.add_argument('--use-mock-data', action='store_true',
                        help='Use mock data for testing (manual only)')
    return parser.parse_args()

def main():
    args = parse_args()
    base_dir = Path(args.base_dir)
    logger = setup_logging()

    setup_directories(base_dir)

    try:
        df = load_and_align_data(base_dir, logger, use_mock=args.use_mock_data)
        print_summary(df, logger)
        logger.info("Ingestion completed successfully.")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
