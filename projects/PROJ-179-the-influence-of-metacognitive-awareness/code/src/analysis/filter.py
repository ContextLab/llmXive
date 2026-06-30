"""
Filter analysis for User Story 3: Modality-Specific Robustness Analysis.

This module splits the trial data by stimulus modality (visual vs auditory)
to enable separate analysis of each modality.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd

from code.config.env_config import load_config, setup_logging, get_seed

logger = logging.getLogger(__name__)

def setup_directories(base_dir: Path = None, output_dir: Path = None) -> tuple:
    """
    Create necessary directories for filter analysis.

    Args:
        base_dir: Base directory for input data
        output_dir: Directory for output files

    Returns:
        Tuple of (base_dir, output_dir)
    """
    if base_dir is None:
        base_dir = Path("data/derived")
    if output_dir is None:
        output_dir = Path("data/derived")

    base_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Directories ready: base={base_dir}, output={output_dir}")
    return base_dir, output_dir

def load_trial_data(input_path: Path = None) -> pd.DataFrame:
    """
    Load trial data from CSV file.

    Args:
        input_path: Path to input trial data CSV

    Returns:
        DataFrame with trial data
    """
    if input_path is None:
        input_path = Path("data/derived/trial_data.csv")

    if not input_path.exists():
        raise FileNotFoundError(
            f"Trial data file not found: {input_path}. "
            "Run preprocess.py (T012) first."
        )

    logger.info(f"Loading trial data from {input_path}")
    df = pd.read_csv(input_path)

    # Validate required columns
    required_cols = ['participant_id', 'trial_id', 'stimulus_modality',
                    'source_label', 'participant_response', 'confidence_rating']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    logger.info(f"Loaded {len(df)} trials")
    return df

def filter_by_modality(df: pd.DataFrame, modality: str) -> pd.DataFrame:
    """
    Filter trials by stimulus modality.

    Args:
        df: Full trial DataFrame
        modality: Modality to filter by ('visual' or 'auditory')

    Returns:
        Filtered DataFrame
    """
    logger.info(f"Filtering for {modality} modality...")

    # Normalize modality string
    modality_lower = modality.lower()

    # Filter data
    filtered = df[df['stimulus_modality'].str.lower() == modality_lower].copy()

    logger.info(f"Found {len(filtered)} {modality} trials "
               f"({len(filtered)/len(df)*100:.1f}% of total)")

    return filtered

def write_output(df: pd.DataFrame, output_path: Path) -> None:
    """
    Write filtered data to CSV file.

    Args:
        df: DataFrame to write
        output_path: Path to output file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Wrote {len(df)} trials to {output_path}")

def run_filter_analysis(
    input_path: Path = None,
    output_dir: Path = None
) -> Dict[str, Any]:
    """
    Main function to run filter analysis.

    Args:
        input_path: Path to input trial data
        output_dir: Directory for output files

    Returns:
        Dictionary with analysis results
    """
    # Setup
    base_dir, output_dir = setup_directories(
        output_dir=output_dir or Path("data/derived")
    )

    # Load data
    df = load_trial_data(input_path)

    results = {
        'total_trials': len(df),
        'modalities': {}
    }

    # Process each modality
    modalities = ['visual', 'auditory']

    for modality in modalities:
        filtered_df = filter_by_modality(df, modality)

        output_path = output_dir / f"{modality}_trials.csv"
        write_output(filtered_df, output_path)

        results['modalities'][modality] = {
            'n_trials': len(filtered_df),
            'output_file': str(output_path),
            'status': 'success'
        }

        logger.info(f"{modality}: {len(filtered_df)} trials -> {output_path}")

    return results

def main():
    """Main entry point for filter analysis."""
    # Setup logging
    logger = setup_logging()
    get_seed()

    logger.info("Starting filter analysis (T026)")

    try:
        results = run_filter_analysis()

        # Write summary
        summary_path = Path("data/derived/filter_summary.json")
        with open(summary_path, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Filter analysis complete. Summary: {summary_path}")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Filter analysis failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()