import os
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from utils.logging import setup_logger
from utils.config import get_config

def load_retention_metrics(retention_path: str) -> Optional[Dict]:
    """Load retention metrics from JSON file."""
    path = Path(retention_path)
    if not path.exists():
        logging.error(f"Retention metrics file not found: {retention_path}")
        return None
    
    try:
        with open(path, 'r') as f:
            import json
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading retention metrics: {e}")
        return None

def load_behavioral_data(behavioral_path: str) -> pd.DataFrame:
    """Load behavioral data from CSV file."""
    path = Path(behavioral_path)
    if not path.exists():
        raise FileNotFoundError(f"Behavioral data file not found: {behavioral_path}")
    
    df = pd.read_csv(path)
    required_cols = ['subject_id', 'pre_motor_score', 'post_motor_score', 'age', 'sex']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in behavioral data: {missing_cols}")
    
    return df

def determine_exclusions(retention_metrics: Dict, behavioral_df: pd.DataFrame, 
                         fmriprep_dir: str, fd_threshold: float = 0.5) -> List[Dict]:
    """
    Determine excluded subjects and reasons.
    
    Checks:
    1. Subjects missing from behavioral data (if retention < 100%)
    2. Subjects with high motion artifacts (Mean FD > threshold)
    3. Subjects with missing pre/post motor scores
    """
    exclusions = []
    all_subject_ids = set(behavioral_df['subject_id'].tolist())
    
    # Check for missing behavioral data
    total_subjects = retention_metrics.get('total_subjects', 0)
    retained_subjects = retention_metrics.get('retained_subjects', 0)
    retention_rate = retention_metrics.get('retention_rate', 0.0)
    
    if total_subjects > 0 and len(all_subject_ids) < total_subjects:
        # Find subjects that were downloaded but not in behavioral data
        # This assumes the raw metadata had all subjects
        missing_count = total_subjects - len(all_subject_ids)
        # We'll log generic exclusion for missing subjects
        # In a real scenario, we'd track which specific subjects were missing
        for i in range(missing_count):
            exclusions.append({
                'subject_id': f'missing_subject_{i+1}',
                'reason': 'missing_behavioral_data',
                'details': 'Subject ID not found in behavioral metadata'
            })
    
    # Check for missing pre/post motor scores
    for _, row in behavioral_df.iterrows():
        if pd.isna(row['pre_motor_score']) or pd.isna(row['post_motor_score']):
            exclusions.append({
                'subject_id': row['subject_id'],
                'reason': 'missing_motor_scores',
                'details': 'Missing pre or post motor task scores'
            })
    
    # Check for high motion artifacts (Mean FD > threshold)
    fmriprep_path = Path(fmriprep_dir)
    if fmriprep_path.exists():
        high_motion_subjects = []
        for subject_dir in fmriprep_path.iterdir():
            if subject_dir.is_dir():
                confounds_file = subject_dir / 'desc-confounds_timeseries.tsv'
                if confounds_file.exists():
                    try:
                        confounds = pd.read_csv(confounds_file, sep='\t')
                        if 'mean_fd' in confounds.columns:
                            mean_fd = confounds['mean_fd'].mean()
                            if mean_fd > fd_threshold:
                                high_motion_subjects.append({
                                    'subject_id': subject_dir.name,
                                    'mean_fd': mean_fd
                                })
                    except Exception as e:
                        logging.warning(f"Could not process confounds for {subject_dir.name}: {e}")
        
        # Mark high motion subjects as excluded (with warning, not fatal per T003)
        for sub in high_motion_subjects:
            exclusions.append({
                'subject_id': sub['subject_id'],
                'reason': 'high_motion_artifacts',
                'details': f"Mean FD {sub['mean_fd']:.4f} exceeds threshold {fd_threshold}"
            })
    
    return exclusions

def save_exclusion_log(exclusions: List[Dict], output_path: str):
    """Save exclusion log to CSV file."""
    if not exclusions:
        # Create empty log with headers
        df = pd.DataFrame(columns=['subject_id', 'reason', 'details'])
    else:
        df = pd.DataFrame(exclusions)
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_file, index=False)
    logging.info(f"Exclusion log saved to {output_path} with {len(exclusions)} entries")

def run_exclusion_logging(retention_metrics_path: str = None,
                          behavioral_data_path: str = None,
                          fmriprep_dir: str = None,
                          output_path: str = None):
    """
    Main function to run exclusion logging pipeline.
    
    Args:
        retention_metrics_path: Path to retention_metrics.json
        behavioral_data_path: Path to subject_scores.csv
        fmriprep_dir: Path to fmriprep processed data directory
        output_path: Path to save exclusion_log.csv
    """
    config = get_config()
    retention_path = retention_metrics_path or config.output_paths.retention_metrics
    behavioral_path = behavioral_data_path or config.output_paths.behavioral_scores
    fmriprep_path = fmriprep_dir or config.output_paths.fmriprep_dir
    output_file = output_path or config.output_paths.exclusion_log
    
    # Setup logger
    logger = setup_logger('exclusion_logging')
    logger.info("Starting exclusion logging process")
    
    try:
        # Load retention metrics
        retention_metrics = load_retention_metrics(retention_path)
        if not retention_metrics:
            logger.warning("No retention metrics found, proceeding with behavioral data only")
            retention_metrics = {'total_subjects': 0, 'retained_subjects': 0, 'retention_rate': 0.0}
        
        # Load behavioral data
        behavioral_df = load_behavioral_data(behavioral_path)
        logger.info(f"Loaded behavioral data for {len(behavioral_df)} subjects")
        
        # Determine exclusions
        exclusions = determine_exclusions(
            retention_metrics, 
            behavioral_df, 
            fmriprep_path,
            fd_threshold=config.get_fd_threshold()
        )
        
        # Save exclusion log
        save_exclusion_log(exclusions, output_file)
        
        logger.info(f"Exclusion logging completed. Total exclusions: {len(exclusions)}")
        return True
        
    except Exception as e:
        logger.error(f"Error in exclusion logging: {e}")
        raise

def main():
    """Entry point for exclusion logging script."""
    run_exclusion_logging()

if __name__ == '__main__':
    main()
