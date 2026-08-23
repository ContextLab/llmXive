import os
import sys
import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional

from .config import get_project_root, ensure_directories
from .utils import setup_logging

logger = logging.getLogger(__name__)

def setup_r_environment() -> None:
    """
    Setup the R environment for DESeq2 analysis.

    Raises:
        RuntimeError: If R or required packages are not available.
    """
    import subprocess

    # Check if R is installed
    try:
        result = subprocess.run(["R", "--version"], check=True, capture_output=True, text=True)
        logger.info(f"R version: {result.stdout.splitlines()[0]}")
    except FileNotFoundError:
        raise RuntimeError("R is not installed or not in PATH")

    # Check if DESeq2 is installed
    try:
        check_cmd = [
            "Rscript",
            "-e",
            "if (!requireNamespace('DESeq2', quietly=TRUE)) quit(status=1)",
        ]
        subprocess.run(check_cmd, check=True, capture_output=True, text=True)
        logger.info("DESeq2 is installed")
    except subprocess.CalledProcessError:
        raise RuntimeError("DESeq2 is not installed. Please install it in the R environment.")

def load_discovery_set(tumor_type: str, data_dir: str) -> tuple:
    """
    Load the discovery set for a tumor type.

    Args:
        tumor_type: Tumor type identifier.
        data_dir: Directory containing the data.

    Returns:
        Tuple of (expression DataFrame, metadata DataFrame).
    """
    import pandas as pd

    expression_file = Path(data_dir) / f"{tumor_type}_discovery_vst.csv"
    metadata_file = Path(data_dir) / f"{tumor_type}_discovery_metadata.csv"

    if not expression_file.exists():
        raise FileNotFoundError(f"Discovery expression file not found: {expression_file}")
    if not metadata_file.exists():
        raise FileNotFoundError(f"Discovery metadata file not found: {metadata_file}")

    expression_df = pd.read_csv(expression_file, index_col=0)
    metadata_df = pd.read_csv(metadata_file, index_col=0)

    return expression_df, metadata_df

def run_deseq2_analysis(
    tumor_type: str,
    expression_df: pd.DataFrame,
    metadata_df: pd.DataFrame,
    output_dir: str,
    response_column: str = "response_label",
    lfc_threshold: float = 1.0,
) -> Path:
    """
    Run DESeq2 analysis for a tumor type.

    Args:
        tumor_type: Tumor type identifier.
        expression_df: Expression DataFrame (rows=genes, cols=samples).
        metadata_df: Metadata DataFrame (rows=samples).
        output_dir: Directory to save results.
        response_column: Column name for response labels.
        lfc_threshold: Log2 fold change threshold.

    Returns:
        Path to the results file.
    """
    import subprocess
    import tempfile

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Create temporary files for input
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Write expression data
        expr_file = tmpdir_path / "expression.csv"
        expression_df.to_csv(expr_file)

        # Write metadata
        meta_file = tmpdir_path / "metadata.csv"
        metadata_df.to_csv(meta_file)

        # Path to the R script
        r_script_path = Path(get_project_root()) / "code" / "src" / "scripts" / "run_deseq2.R"

        if not r_script_path.exists():
            raise FileNotFoundError(f"DESeq2 script not found: {r_script_path}")

        # Output file
        output_file = output_path / f"{tumor_type}_de_results.csv"

        # Construct R command
        cmd = [
            "Rscript",
            str(r_script_path),
            str(expr_file),
            str(meta_file),
            str(output_file),
            response_column,
            str(lfc_threshold),
        ]

        try:
            logger.info(f"Running DESeq2 for {tumor_type}...")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(result.stdout)

            if not output_file.exists():
                raise RuntimeError(f"DESeq2 script completed but output file not found: {output_file}")

            return output_file

        except subprocess.CalledProcessError as e:
            logger.error(f"Error running DESeq2 for {tumor_type}: {e.stderr}")
            raise RuntimeError(f"Failed to run DESeq2 for {tumor_type}: {e.stderr}")

def run_deseq2_analysis_loo(
    tumor_type: str,
    expression_df: pd.DataFrame,
    metadata_df: pd.DataFrame,
    output_dir: str,
    response_column: str = "response_label",
    lfc_threshold: float = 1.0,
    exclude_type: Optional[str] = None,
) -> Path:
    """
    Run DESeq2 analysis for LOO validation.

    Args:
        tumor_type: Tumor type identifier.
        expression_df: Expression DataFrame.
        metadata_df: Metadata DataFrame.
        output_dir: Directory to save results.
        response_column: Column name for response labels.
        lfc_threshold: Log2 fold change threshold.
        exclude_type: Tumor type to exclude (for LOO).

    Returns:
        Path to the results file.
    """
    # For now, this is the same as run_deseq2_analysis
    # In a full implementation, this would handle the LOO logic
    return run_deseq2_analysis(
        tumor_type, expression_df, metadata_df, output_dir, response_column, lfc_threshold
    )

def process_tumor_type_loo(
    tumor_type: str,
    data_dir: str,
    output_dir: str,
    response_column: str = "response_label",
    lfc_threshold: float = 1.0,
    exclude_type: Optional[str] = None,
) -> Path:
    """
    Process a tumor type for LOO DE analysis.

    Args:
        tumor_type: Tumor type identifier.
        data_dir: Directory containing discovery data.
        output_dir: Directory to save results.
        response_column: Column name for response labels.
        lfc_threshold: Log2 fold change threshold.
        exclude_type: Tumor type to exclude.

    Returns:
        Path to the results file.
    """
    expression_df, metadata_df = load_discovery_set(tumor_type, data_dir)
    return run_deseq2_analysis_loo(
        tumor_type, expression_df, metadata_df, output_dir, response_column, lfc_threshold, exclude_type
    )

def process_tumor_type(
    tumor_type: str,
    data_dir: str,
    output_dir: str,
    response_column: str = "response_label",
    lfc_threshold: float = 1.0,
) -> Path:
    """
    Process a tumor type for DE analysis.

    Args:
        tumor_type: Tumor type identifier.
        data_dir: Directory containing discovery data.
        output_dir: Directory to save results.
        response_column: Column name for response labels.
        lfc_threshold: Log2 fold change threshold.

    Returns:
        Path to the results file.
    """
    expression_df, metadata_df = load_discovery_set(tumor_type, data_dir)
    return run_deseq2_analysis(
        tumor_type, expression_df, metadata_df, output_dir, response_column, lfc_threshold
    )

def main():
    """Main entry point for differential expression module."""
    import argparse

    parser = argparse.ArgumentParser(description="Differential Expression Module")
    parser.add_argument("--tumor-type", type=str, required=True, help="Tumor type to process")
    parser.add_argument("--mode", choices=["standard", "loo"], default="standard")
    parser.add_argument("--data-dir", type=str, default=None)
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--exclude-type", type=str, default=None, help="Tumor type to exclude for LOO")
    args = parser.parse_args()

    setup_logging(level=logging.INFO)

    # Setup R environment
    try:
        setup_r_environment()
    except RuntimeError as e:
        logger.error(f"R environment setup failed: {e}")
        sys.exit(1)

    project_root = get_project_root()
    data_dir = args.data_dir or str(Path(project_root) / "code" / "data" / "processed")
    output_dir = args.output_dir or str(Path(project_root) / "results" / "de")

    if args.mode == "loo":
        if not args.exclude_type:
            logger.error("exclude-type is required for LOO mode")
            sys.exit(1)
        process_tumor_type_loo(
            args.tumor_type, data_dir, output_dir, exclude_type=args.exclude_type
        )
    else:
        process_tumor_type(args.tumor_type, data_dir, output_dir)

if __name__ == "__main__":
    main()