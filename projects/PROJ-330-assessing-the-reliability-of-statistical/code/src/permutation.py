"""
Permutation module for Stratified Block Permutation Null Modeling.

This module implements the Fixed-Dispersion Wald Perturbation strategy.
It shuffles sample labels within batch groups and recomputes Wald statistics
using fixed dispersion parameters saved from T021 (de_analysis.py).
"""
import os
import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

import numpy as np
import pandas as pd

from src.config import PROJECT_ROOT, ensure_directories
from src.preprocessing import stratify_samples

logger = logging.getLogger(__name__)


def load_dispersion_params(dispersion_file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load fixed dispersion parameters from the artifact saved by T021.

    Args:
        dispersion_file_path: Path to the JSON file containing dispersion parameters.

    Returns:
        Dictionary containing gene-wise dispersion estimates and metadata.

    Raises:
        FileNotFoundError: If the dispersion file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = Path(dispersion_file_path)
    if not path.exists():
        raise FileNotFoundError(f"Dispersion parameter file not found: {path}")

    with open(path, 'r') as f:
        return json.load(f)


def shuffle_labels_stratified(
    sample_metadata: pd.DataFrame,
    batch_column: str,
    condition_column: str,
    random_seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Shuffle sample condition labels within batch groups.

    This preserves the batch structure while randomizing the condition assignment,
    creating a valid null distribution for the permutation test.

    Args:
        sample_metadata: DataFrame containing sample information with batch and condition columns.
        batch_column: Name of the column containing batch identifiers.
        condition_column: Name of the column containing condition labels (e.g., 'treatment', 'control').
        random_seed: Optional random seed for reproducibility.

    Returns:
        DataFrame with shuffled condition labels, preserving batch structure.

    Raises:
        ValueError: If batch or condition columns are missing.
    """
    if batch_column not in sample_metadata.columns:
        raise ValueError(f"Batch column '{batch_column}' not found in metadata")
    if condition_column not in sample_metadata.columns:
        raise ValueError(f"Condition column '{condition_column}' not found in metadata")

    if random_seed is not None:
        np.random.seed(random_seed)

    shuffled_metadata = sample_metadata.copy()
    shuffled_metadata[condition_column] = sample_metadata.groupby(batch_column)[condition_column].transform(
        lambda x: np.random.permutation(x.values)
    )

    return shuffled_metadata


def run_wald_perturbation(
    count_data: pd.DataFrame,
    shuffled_metadata: pd.DataFrame,
    dispersion_params: Dict[str, Any],
    batch_column: str,
    condition_column: str,
    output_dir: Union[str, Path],
    r_script_path: Union[str, Path],
    random_seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Run the Fixed-Dispersion Wald Perturbation analysis.

    This function calls the R script to recompute Wald statistics using the
    fixed dispersion parameters and shuffled sample labels.

    Args:
        count_data: DataFrame with gene counts (rows=genes, columns=samples).
        shuffled_metadata: DataFrame with shuffled condition labels.
        dispersion_params: Dictionary containing fixed dispersion parameters.
        batch_column: Name of the batch column in metadata.
        condition_column: Name of the condition column in metadata.
        output_dir: Directory to save intermediate and final results.
        r_script_path: Path to the R script that performs the DE analysis.
        random_seed: Optional random seed for reproducibility.

    Returns:
        DataFrame with permuted Wald statistics and p-values.

    Raises:
        FileNotFoundError: If the R script is not found.
        subprocess.CalledProcessError: If the R script fails.
    """
    ensure_directories(output_dir)
    output_dir = Path(output_dir)

    # Prepare temporary files for R script
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Save count data
        count_file = tmpdir / "permuted_counts.csv"
        count_data.to_csv(count_file)

        # Save shuffled metadata
        meta_file = tmpdir / "permuted_metadata.csv"
        shuffled_metadata.to_csv(meta_file)

        # Save dispersion parameters
        disp_file = tmpdir / "dispersion_params.json"
        with open(disp_file, 'w') as f:
            json.dump(dispersion_params, f)

        # Prepare R output paths
        r_output_file = output_dir / "permuted_results.csv"

        # Build R command
        r_cmd = [
            "Rscript", str(r_script_path),
            "--args",
            "mode=permute",
            f"--counts={count_file}",
            f"--metadata={meta_file}",
            f"--dispersion={disp_file}",
            f"--output={r_output_file}",
            f"--batch_col={batch_column}",
            f"--cond_col={condition_column}",
        ]

        if random_seed is not None:
            r_cmd.append(f"--seed={random_seed}")

        logger.info(f"Running permutation R script: {' '.join(r_cmd)}")
        result = subprocess.run(
            r_cmd,
            capture_output=True,
            text=True,
            check=True
        )

        if result.stderr:
            logger.warning(f"R script stderr: {result.stderr}")

        if not r_output_file.exists():
            raise FileNotFoundError(f"R script did not produce output: {r_output_file}")

        # Load and return results
        results = pd.read_csv(r_output_file)
        return results


def run_permutation_test(
    count_data: pd.DataFrame,
    sample_metadata: pd.DataFrame,
    dispersion_params: Dict[str, Any],
    batch_column: str,
    condition_column: str,
    n_permutations: int,
    output_dir: Union[str, Path],
    r_script_path: Union[str, Path],
    base_seed: int = 42
) -> Tuple[pd.DataFrame, List[pd.DataFrame]]:
    """
    Run the full stratified block permutation test.

    This function iteratively shuffles sample labels and recomputes Wald statistics
    for the specified number of permutations.

    Args:
        count_data: DataFrame with gene counts (rows=genes, columns=samples).
        sample_metadata: DataFrame with original sample information.
        dispersion_params: Dictionary containing fixed dispersion parameters.
        batch_column: Name of the batch column in metadata.
        condition_column: Name of the condition column in metadata.
        n_permutations: Number of permutations to perform.
        output_dir: Directory to save permutation results.
        r_script_path: Path to the R script for DE analysis.
        base_seed: Base random seed for reproducibility.

    Returns:
        Tuple of:
            - DataFrame with aggregated permutation statistics (mean, std across perms)
            - List of DataFrames, one per permutation iteration

    Raises:
        ValueError: If n_permutations is less than 1.
        FileNotFoundError: If the R script is not found.
    """
    if n_permutations < 1:
        raise ValueError("n_permutations must be at least 1")

    ensure_directories(output_dir)
    output_dir = Path(output_dir)

    # Create subdirectory for permutation runs
    perm_dir = output_dir / "permutations"
    ensure_directories(perm_dir)

    all_results = []
    logger.info(f"Starting {n_permutations} permutations...")

    for i in range(n_permutations):
        seed = base_seed + i
        logger.info(f"Permutation {i+1}/{n_permutations} (seed={seed})")

        # Shuffle labels within batch groups
        shuffled_meta = shuffle_labels_stratified(
            sample_metadata,
            batch_column=batch_column,
            condition_column=condition_column,
            random_seed=seed
        )

        # Run Wald perturbation
        perm_results = run_wald_perturbation(
            count_data=count_data,
            shuffled_metadata=shuffled_meta,
            dispersion_params=dispersion_params,
            batch_column=batch_column,
            condition_column=condition_column,
            output_dir=perm_dir,
            r_script_path=r_script_path,
            random_seed=seed
        )

        all_results.append(perm_results)

        # Save individual permutation result
        perm_output = perm_dir / f"perm_{i+1:04d}.csv"
        perm_results.to_csv(perm_output, index=False)

    # Aggregate results
    logger.info("Aggregating permutation results...")
    aggregated = aggregate_permutation_results(all_results)
    aggregated.to_csv(output_dir / "permutation_summary.csv", index=False)

    return aggregated, all_results


def aggregate_permutation_results(results: List[pd.DataFrame]) -> pd.DataFrame:
    """
    Aggregate results from multiple permutation iterations.

    Computes mean and standard deviation of statistics across permutations.

    Args:
        results: List of DataFrames, each containing statistics from one permutation.

    Returns:
        DataFrame with aggregated statistics (mean, std) per gene.
    """
    if not results:
        raise ValueError("No results to aggregate")

    # Ensure all results have the same columns
    base_cols = results[0].columns.tolist()
    for i, res in enumerate(results[1:], 1):
        if list(res.columns) != base_cols:
            logger.warning(f"Permutation {i} has different columns. Aligning...")
            res = res.reindex(columns=base_cols)

    # Stack all results
    stacked = pd.concat(results, ignore_index=True)

    # Identify numeric columns for aggregation
    numeric_cols = stacked.select_dtypes(include=[np.number]).columns

    # Compute mean and std for each gene (assuming 'gene' or 'id' column exists)
    id_col = None
    for col in ['gene', 'id', 'gene_id', 'gene_symbol']:
        if col in stacked.columns:
            id_col = col
            break

    if id_col is None:
        raise ValueError("Could not identify gene identifier column in results")

    # Group by gene and compute statistics
    agg_stats = stacked.groupby(id_col)[numeric_cols].agg(['mean', 'std']).reset_index()
    agg_stats.columns = [id_col] + [f"{col}_{stat}" for col, stat in agg_stats.columns]

    return agg_stats


def main():
    """
    Main entry point for running permutation tests.

    This function demonstrates how to use the permutation module.
    In a real scenario, this would be called from main.py with proper arguments.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Run stratified block permutation test")
    parser.add_argument("--counts", required=True, help="Path to count data CSV")
    parser.add_argument("--metadata", required=True, help="Path to sample metadata CSV")
    parser.add_argument("--dispersion", required=True, help="Path to dispersion parameters JSON")
    parser.add_argument("--batch-col", default="batch", help="Name of batch column")
    parser.add_argument("--cond-col", default="condition", help="Name of condition column")
    parser.add_argument("--n-perms", type=int, default=100, help="Number of permutations")
    parser.add_argument("--output", default="data/permutation_results", help="Output directory")
    parser.add_argument("--r-script", required=True, help="Path to R DE analysis script")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    # Load data
    logger.info("Loading count data...")
    count_data = pd.read_csv(args.counts, index_col=0)
    logger.info(f"Loaded {count_data.shape[0]} genes, {count_data.shape[1]} samples")

    logger.info("Loading sample metadata...")
    sample_metadata = pd.read_csv(args.metadata)
    logger.info(f"Loaded {len(sample_metadata)} samples")

    logger.info("Loading dispersion parameters...")
    dispersion_params = load_dispersion_params(args.dispersion)
    logger.info(f"Loaded dispersion parameters for {len(dispersion_params.get('genes', []))} genes")

    # Run permutation test
    aggregated, all_results = run_permutation_test(
        count_data=count_data,
        sample_metadata=sample_metadata,
        dispersion_params=dispersion_params,
        batch_column=args.batch_col,
        condition_column=args.cond_col,
        n_permutations=args.n_perms,
        output_dir=args.output,
        r_script_path=args.r_script,
        base_seed=args.seed
    )

    logger.info(f"Permutation test complete. Results saved to {args.output}")
    logger.info(f"Aggregated summary: {aggregated.shape[0]} genes")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
