"""
Motion parameter extraction from fMRIPrep output.

Extracts 6 rigid-body motion parameters (3 translations, 3 rotations)
from fMRIPrep confounds TSV files and outputs a consolidated CSV.
"""
import os
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class MotionExtractionError(Exception):
    """Raised when motion extraction fails."""
    pass


def find_fmriprep_confounds(
    processed_dir: Path,
    subject_id: str
) -> Optional[Path]:
    """
    Locate the fMRIPrep confounds TSV file for a given subject.

    fMRIPrep typically outputs files like:
    sub-<label>_task-<label>_desc-confounds_timeseries.tsv

    Args:
        processed_dir: Path to the processed data directory (data/processed/).
        subject_id: Subject identifier (e.g., 'sub-01').

    Returns:
        Path to the confounds TSV file if found, None otherwise.
    """
    # Look for confounds files matching the subject pattern
    pattern = f"{subject_id}_*confounds*.tsv"
    candidates = list(processed_dir.glob(f"**/{pattern}"))

    if not candidates:
        logger.warning(f"No confounds file found for {subject_id} in {processed_dir}")
        return None

    # Prefer the most specific match if multiple exist
    # Usually fMRIPrep outputs one per functional run, we take the first found
    return candidates[0]


def extract_subject_id_from_path(confounds_path: Path) -> str:
    """
    Extract subject ID from the confounds file path.

    Args:
        confounds_path: Path to the confounds TSV file.

    Returns:
        Extracted subject ID string.
    """
    # Expected format: .../sub-XX/.../sub-XX_task-..._desc-confounds_timeseries.tsv
    # We look for the 'sub-XX' part in the path
    parts = confounds_path.parts
    for part in parts:
        if part.startswith("sub-") and not part.startswith("sub-0"):
            # Fallback logic if sub-0 exists, but typically sub-XX is unique
            pass
        if part.startswith("sub-"):
            return part
    
    # Fallback: extract from filename
    filename = confounds_path.stem
    if filename.startswith("sub-"):
        return filename.split("_")[0]
    
    raise MotionExtractionError(
        f"Could not extract subject ID from path: {confounds_path}"
    )


def extract_motion_parameters(confounds_path: Path) -> pd.DataFrame:
    """
    Extract the 6 rigid-body motion parameters from a fMRIPrep confounds file.

    fMRIPrep provides:
    - trans_x, trans_y, trans_z (translations in mm)
    - rot_x, rot_y, rot_z (rotations in radians)

    Args:
        confounds_path: Path to the confounds TSV file.

    Returns:
        DataFrame with columns: subject_id, translation_x, translation_y, 
        translation_z, rotation_x, rotation_y, rotation_z.
        
        Note: We aggregate across time points (e.g., mean or max) to produce
        a single row per subject. For this task, we calculate the mean absolute
        displacement per parameter as a summary metric, or simply the mean if
        the requirement implies per-timepoint. 
        
        Re-reading task: "CSV with columns: subject_id, translation_x/y/z, rotation_x/y/z".
        Usually, motion analysis uses a summary (max or mean) per subject to filter outliers.
        However, if the requirement is strictly the parameters, we might output per-volume.
        Given the downstream task T015 (Motion Filter) which filters subjects based on 
        thresholds (>3mm), it implies a single value per subject per parameter or a max check.
        
        To be most useful for T015, we will output the MAX absolute displacement 
        for each parameter per subject, as this is the standard for exclusion criteria.
        Alternatively, we can output the mean. Let's output the MAX absolute value 
        to safely capture the worst-case motion for the filter.
    """
    if not confounds_path.exists():
        raise MotionExtractionError(f"Confounds file not found: {confounds_path}")

    try:
        df = pd.read_csv(confounds_path, sep='\t', comment='#')
    except Exception as e:
        raise MotionExtractionError(f"Failed to read confounds file {confounds_path}: {e}")

    required_cols = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise MotionExtractionError(
            f"Confounds file missing required columns: {missing}"
        )

    # Extract subject ID
    sub_id = extract_subject_id_from_path(confounds_path)

    # Calculate max absolute displacement for each parameter per subject
    # This creates a single row per subject, suitable for T015 filtering
    summary_data = {
        'subject_id': sub_id,
        'translation_x': df['trans_x'].abs().max(),
        'translation_y': df['trans_y'].abs().max(),
        'translation_z': df['trans_z'].abs().max(),
        'rotation_x': df['rot_x'].abs().max(),
        'rotation_y': df['rot_y'].abs().max(),
        'rotation_z': df['rot_z'].abs().max(),
    }

    return pd.DataFrame([summary_data])


def extract_all_motion_parameters(processed_dir: Path) -> pd.DataFrame:
    """
    Process all subjects in the processed directory and extract motion parameters.

    Args:
        processed_dir: Path to the data/processed/ directory.

    Returns:
        DataFrame with motion parameters for all valid subjects.
    """
    results = []
    
    # Find all sub- directories
    sub_dirs = [d for d in processed_dir.iterdir() if d.is_dir() and d.name.startswith("sub-")]
    
    if not sub_dirs:
        logger.warning(f"No subject directories found in {processed_dir}")
        return pd.DataFrame(columns=[
            'subject_id', 'translation_x', 'translation_y', 'translation_z',
            'rotation_x', 'rotation_y', 'rotation_z'
        ])

    for sub_dir in sub_dirs:
        subject_id = sub_dir.name
        confounds_path = find_fmriprep_confounds(processed_dir, subject_id)
        
        if confounds_path:
            try:
                motion_df = extract_motion_parameters(confounds_path)
                results.append(motion_df)
            except MotionExtractionError as e:
                logger.error(f"Skipping {subject_id}: {e}")
        else:
            logger.warning(f"Skipping {subject_id}: No confounds file found")

    if not results:
        return pd.DataFrame(columns=[
            'subject_id', 'translation_x', 'translation_y', 'translation_z',
            'rotation_x', 'rotation_y', 'rotation_z'
        ])

    return pd.concat(results, ignore_index=True)


def write_motion_csv(df: pd.DataFrame, output_path: Path) -> None:
    """
    Write the motion parameters DataFrame to a CSV file.

    Args:
        df: DataFrame containing motion parameters.
        output_path: Path to the output CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Wrote motion parameters to {output_path}")


def run_motion_extraction(
    processed_dir: Path,
    output_path: Path
) -> pd.DataFrame:
    """
    Main entry point for running the motion extraction pipeline.

    Args:
        processed_dir: Path to the data/processed/ directory.
        output_path: Path where the output CSV will be written.

    Returns:
        The DataFrame of extracted motion parameters.
    """
    logger.info(f"Starting motion extraction from {processed_dir}")
    
    motion_df = extract_all_motion_parameters(processed_dir)
    
    if motion_df.empty:
        logger.warning("No motion data extracted. Output file will be empty.")
    
    write_motion_csv(motion_df, output_path)
    
    return motion_df


def main() -> None:
    """
    CLI entry point for motion extraction.
    Reads configuration from environment or defaults.
    """
    import sys
    from src.config.env import get_data_dir

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        data_dir = Path(get_data_dir())
        processed_dir = data_dir / "processed"
        output_file = data_dir / "results" / "motion_parameters.csv"

        if not processed_dir.exists():
            raise FileNotFoundError(
                f"Processed data directory not found: {processed_dir}. "
                "Please run preprocessing first."
            )

        run_motion_extraction(processed_dir, output_file)
        print(f"Motion extraction complete. Output: {output_file}")

    except Exception as e:
        logger.error(f"Motion extraction failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
