import argparse
import logging
import sys
from pathlib import Path
from typing import List, Tuple, Optional
import pandas as pd
import numpy as np

from src.utils.logger import get_logger
from src.preprocessing.covariate_handler import calculate_missing_ratio

def get_project_root() -> Path:
    """Determine the project root directory."""
    current = Path(__file__).resolve()
    # Traverse up until we find a marker or hit root
    for parent in current.parents:
        if (parent / ".git").exists() or (parent / "README.md").exists():
            return parent
    return current.parent.parent.parent

def load_covariate_data(file_path: Path) -> pd.DataFrame:
    """
    Load covariate data from a TSV/CSV file.
    
    Args:
        file_path: Path to the covariate file.
        
    Returns:
        DataFrame containing covariate data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file cannot be parsed.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Covariate file not found: {file_path}")
    
    try:
        if file_path.suffix.lower() == '.tsv':
            df = pd.read_csv(file_path, sep='\t')
        elif file_path.suffix.lower() == '.csv':
            df = pd.read_csv(file_path)
        else:
            # Try TSV first, then CSV
            try:
                df = pd.read_csv(file_path, sep='\t')
            except Exception:
                df = pd.read_csv(file_path)
        
        if df.empty:
            logging.warning(f"Loaded covariate file is empty: {file_path}")
        
        return df
    except Exception as e:
        raise ValueError(f"Failed to parse covariate file {file_path}: {e}")

def generate_exclusion_log(
    covariate_df: pd.DataFrame,
    output_path: Path,
    missing_threshold: float = 0.20,
    id_column: Optional[str] = None
) -> int:
    """
    Calculate missing data ratios per sample and generate an exclusion log.
    
    This function identifies samples where the proportion of missing values
    across all covariate columns exceeds the specified threshold (default 20%).
    
    Args:
        covariate_df: DataFrame containing covariate data.
        output_path: Path where the exclusion log file will be written.
        missing_threshold: Threshold (0.0-1.0) for missing data ratio to exclude a sample.
        id_column: Column name to use as sample ID. If None, uses the index.
        
    Returns:
        The number of samples excluded due to high missingness.
        
    Raises:
        ValueError: If the DataFrame is empty or has no numeric/non-object columns.
    """
    if covariate_df.empty:
        raise ValueError("Input DataFrame is empty.")
    
    # Identify covariate columns (exclude ID columns if present)
    # Usually covariates are numeric or object/string, excluding obvious ID columns
    covariate_cols = [
        col for col in covariate_df.columns 
        if col.lower() not in ['sample_id', 'id', 'subject_id', 'cohort_id']
    ]
    
    if not covariate_cols:
        raise ValueError("No covariate columns found in DataFrame.")
    
    # Calculate missing ratio per row (sample)
    missing_ratios = covariate_df[covariate_cols].isna().mean(axis=1)
    
    # Identify excluded samples
    excluded_mask = missing_ratios > missing_threshold
    excluded_count = excluded_mask.sum()
    included_count = (~excluded_mask).sum()
    
    # Prepare output directory
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write the log file
    with open(output_path, 'w') as f:
        f.write(f"Covariate Exclusion Log\n")
        f.write(f"=======================\n")
        f.write(f"Threshold: {missing_threshold * 100:.1f}% missing data\n")
        f.write(f"Total samples processed: {len(covariate_df)}\n")
        f.write(f"Samples excluded: {excluded_count}\n")
        f.write(f"Samples retained: {included_count}\n")
        f.write(f"\n")
        f.write(f"Excluded Sample IDs:\n")
        
        if id_column and id_column in covariate_df.columns:
            excluded_ids = covariate_df.loc[excluded_mask, id_column].tolist()
        else:
            # Use index as ID if no specific column provided
            excluded_ids = covariate_df.loc[excluded_mask].index.tolist()
        
        for idx, sample_id in enumerate(excluded_ids, 1):
            ratio = missing_ratios.loc[excluded_mask].iloc[idx-1]
            f.write(f"  {idx}. ID: {sample_id}, Missing Ratio: {ratio:.2%}\n")
        
        if excluded_count == 0:
            f.write("  (None)\n")
    
    logging.info(f"Exclusion log written to {output_path}")
    logging.info(f"Excluded {excluded_count} samples with >{missing_threshold*100:.1f}% missing covariates.")
    
    return int(excluded_count)

def build_arg_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate a log of samples excluded due to high missing covariate data."
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        required=True,
        help="Path to the input covariate file (TSV or CSV)."
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Path to the output exclusion log file. Defaults to data/processed/results/covariate_exclusion_log.txt"
    )
    parser.add_argument(
        "--threshold", "-t",
        type=float,
        default=0.20,
        help="Missing data threshold (0.0 to 1.0). Samples exceeding this are excluded. Default: 0.20"
    )
    parser.add_argument(
        "--id-column",
        type=str,
        default=None,
        help="Column name to use as sample ID. If not provided, the index is used."
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level. Default: INFO"
    )
    return parser

def main():
    """Main entry point for the script."""
    parser = build_arg_parser()
    args = parser.parse_args()
    
    # Setup logging
    logger = get_logger("generate_exclusion_log")
    logger.setLevel(getattr(logging, args.log_level))
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
    
    # Determine output path
    if args.output is None:
        project_root = get_project_root()
        args.output = project_root / "data" / "processed" / "results" / "covariate_exclusion_log.txt"
    
    try:
        logger.info(f"Loading covariate data from {args.input}")
        df = load_covariate_data(args.input)
        
        logger.info(f"Generating exclusion log with threshold {args.threshold}")
        excluded_count = generate_exclusion_log(
            df, 
            args.output, 
            missing_threshold=args.threshold,
            id_column=args.id_column
        )
        
        logger.info(f"Successfully generated exclusion log. Excluded {excluded_count} samples.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
