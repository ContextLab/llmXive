import argparse
import csv
import json
import logging
import os
import sys
import pandas as pd
import numpy as np

def setup_logging():
    """Configure logging for the ingestion module."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def setup_directories():
    """Ensure required directories exist."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_dir = os.path.join(base_dir, 'projects', 'PROJ-967-llmxive-follow-up-extending-beyond-scala')
    
    directories = [
        os.path.join(project_dir, 'data', 'raw'),
        os.path.join(project_dir, 'data', 'processed'),
        os.path.join(project_dir, 'code'),
        os.path.join(project_dir, 'tests'),
        os.path.join(project_dir, 'results')
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    return project_dir

def load_and_align_data(raw_data_path, project_dir):
    """
    Load and align dataset with teacher scores, student scores, and human annotations.
    
    Args:
        raw_data_path: Path to raw dataset file
        project_dir: Project root directory
        
    Returns:
        DataFrame: Aligned dataset
    """
    logger = logging.getLogger(__name__)
    
    # Load data
    if raw_data_path.endswith('.parquet'):
        df = pd.read_parquet(raw_data_path)
    else:
        df = pd.read_csv(raw_data_path)
    
    logger.info(f"Loaded dataset with {len(df)} rows")
    logger.info(f"Columns: {list(df.columns)}")
    
    # Ensure required columns exist
    required_cols = ['prompt', 'image_url', 'teacher_scores', 'student_scalar', 
                    'human_annotations', 'primary_dimension']
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.warning(f"Missing columns: {missing_cols}")
        # Add placeholder columns for missing ones
        for col in missing_cols:
            df[col] = None
    
    # Handle missing student_scalar
    if 'student_scalar' in df.columns:
        missing_scalar = df['student_scalar'].isna().sum()
        logger.info(f"Samples with missing student_scalar: {missing_scalar}")
        df['excluded_reason'] = df['student_scalar'].isna().map(
            lambda x: 'missing_student_scalar' if x else None
        )
    
    # Handle missing primary_dimension
    if 'primary_dimension' in df.columns:
        missing_dim = df['primary_dimension'].isna().sum()
        logger.info(f"Samples with missing primary_dimension: {missing_dim}")
        # Mark samples with missing primary_dimension
        df.loc[df['primary_dimension'].isna(), 'excluded_reason'] = \
            df.loc[df['primary_dimension'].isna(), 'excluded_reason'].apply(
                lambda x: 'missing_primary_dimension' if pd.isna(x) else x
            )
    
    # Align teacher scores and human annotations
    if 'teacher_scores' in df.columns:
        # Ensure teacher_scores is a dict
        if isinstance(df['teacher_scores'].iloc[0], str):
            df['teacher_scores'] = df['teacher_scores'].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
    
    if 'human_annotations' in df.columns:
        # Ensure human_annotations is a dict
        if isinstance(df['human_annotations'].iloc[0], str):
            df['human_annotations'] = df['human_annotations'].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
    
    return df

def identify_primary_quality_dimension(df):
    """
    Identify the primary quality dimension for each sample.
    
    Args:
        df: DataFrame with primary_dimension column
        
    Returns:
        DataFrame: Updated with primary dimension identification
    """
    logger = logging.getLogger(__name__)
    
    if 'primary_dimension' not in df.columns:
        logger.warning("primary_dimension column not found")
        return df
    
    # Count dimension occurrences
    dimension_counts = df['primary_dimension'].value_counts()
    logger.info(f"Primary dimension distribution:\n{dimension_counts}")
    
    # Mark samples with missing primary_dimension
    missing_count = df['primary_dimension'].isna().sum()
    logger.info(f"Samples with missing primary_dimension: {missing_count}")
    
    return df

def print_summary(df):
    """Print summary statistics of the aligned dataset."""
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 50)
    logger.info("DATASET SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Total samples: {len(df)}")
    logger.info(f"Columns: {list(df.columns)}")
    
    if 'excluded_reason' in df.columns:
        exclusion_summary = df['excluded_reason'].value_counts()
        logger.info(f"Exclusion reasons:\n{exclusion_summary}")
    
    if 'teacher_scores' in df.columns:
        score_cols = ['Alignment', 'Realism', 'Aesthetics', 'Plausibility']
        for col in score_cols:
            if col in df.columns:
                non_null = df[col].notna().sum()
                logger.info(f"{col}: {non_null}/{len(df)} non-null")
    
    if 'primary_dimension' in df.columns:
        logger.info(f"Primary dimension coverage: {df['primary_dimension'].notna().sum()}/{len(df)}")
    
    logger.info("=" * 50)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Dataset ingestion and alignment')
    parser.add_argument('--input', type=str, required=True, help='Input raw data file path')
    parser.add_argument('--output', type=str, required=True, help='Output processed data file path')
    return parser.parse_args()

def main():
    """Main entry point for dataset ingestion."""
    logger = setup_logging()
    project_dir = setup_directories()
    args = parse_args()
    
    logger.info(f"Starting dataset ingestion from {args.input}")
    
    # Load and align data
    df = load_and_align_data(args.input, project_dir)
    
    # Identify primary dimension
    df = identify_primary_quality_dimension(df)
    
    # Print summary
    print_summary(df)
    
    # Save processed data
    if args.output.endswith('.parquet'):
        df.to_parquet(args.output, index=False)
    else:
        df.to_csv(args.output, index=False)
    
    logger.info(f"Saved aligned dataset to {args.output}")

if __name__ == '__main__':
    main()
