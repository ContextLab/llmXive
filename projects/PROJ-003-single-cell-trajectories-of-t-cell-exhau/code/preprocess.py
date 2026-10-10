"""
Wrapper script to invoke preprocess.R for Seurat-based QC and normalization,
with a Python fallback using Scanpy when R is unavailable.

This script attempts to run the R script `preprocess.R`. If the R environment
(R executable and Seurat package) is not detected, it falls back to a pure
Python implementation that performs the same QC steps:
  * Load raw count matrix (10x .mtx or .h5 formats)
  * Compute percent mitochondrial reads per cell
  * Filter out cells with >20% mitochondrial reads
  * Log‑normalize the data
  * Save the result as a `.h5ad` file compatible with downstream Scanpy/scVelo steps.

The fallback ensures that the pipeline can run on CI runners where R may not be
installed, while still allowing users with R/Seurat to use the original R workflow.
"""
import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path

import scanpy as sc

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def check_r_environment() -> bool:
    """Verify that R and the Seurat package are available."""
    logger.info("Checking R environment...")
    try:
        # Check R executable
        result = subprocess.run(
            ["R", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        logger.info(f"R version found: {result.stdout.decode().splitlines()[0]}")

        # Check Seurat package
        result = subprocess.run(
            [
                "Rscript",
                "-e",
                "if (!requireNamespace('Seurat', quietly=TRUE)) stop('Seurat not installed')",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        logger.info("Seurat package is installed.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"R environment check failed: {e.stderr.decode().strip()}")
        return False
    except FileNotFoundError:
        logger.error("R executable not found in PATH.")
        return False


def run_r_preprocessing(input_path: Path, output_path: Path) -> bool:
    """
    Execute the R preprocessing script.

    Returns True if the script exits with code 0, False otherwise.
    """
    logger.info(f"Running R preprocessing for {input_path} → {output_path}")

    if not input_path.exists():
        logger.error(f"Input path does not exist: {input_path}")
        return False

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    script_dir = Path(__file__).resolve().parent
    r_script_path = script_dir / "preprocess.R"

    if not r_script_path.exists():
        logger.error(f"R script not found at {r_script_path}")
        return False

    cmd = [
        "Rscript",
        str(r_script_path),
        "--input",
        str(input_path),
        "--output",
        str(output_path),
    ]

    logger.info(f"Executing command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.stdout:
            logger.info("R script stdout:\n" + result.stdout)
        if result.stderr:
            logger.info("R script stderr:\n" + result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"R script failed (return code {e.returncode})")
        if e.stdout:
            logger.error(f"STDOUT: {e.stdout}")
        if e.stderr:
            logger.error(f"STDERR: {e.stderr}")
        return False
    except FileNotFoundError:
        logger.error("Rscript executable not found.")
        return False


def python_preprocess(input_path: Path, output_path: Path) -> bool:
    """
    Pure‑Python fallback that mirrors the R QC/normalisation steps using Scanpy.

    Steps:
      1. Load raw matrix (supports .mtx/.mtx.gz or 10x .h5 files).
      2. Identify mitochondrial genes (prefix MT- or mt-).
      3. Compute percent mitochondrial reads per cell.
      4. Filter cells with percent.mt > 20.
      5. Log‑normalize (total counts per cell = 1e4) and log1p transform.
      6. Write the AnnData object to the requested .h5ad path.
    """
    logger.info(f"Running Python fallback preprocessing for {input_path}")

    # Resolve input: if a directory is given, look for a supported file inside
    if input_path.is_dir():
        # Prefer .h5 first, then .mtx
        candidates = list(input_path.rglob("*.h5")) + list(input_path.rglob("*.mtx*"))
        if not candidates:
            logger.error(f"No supported matrix files found in directory {input_path}")
            return False
        input_file = candidates[0]
        logger.info(f"Detected input file {input_file}")
    else:
        input_file = input_path

    # Load data
    try:
        if input_file.suffix.lower() == ".h5":
            adata = sc.read_10x_h5(str(input_file))
        else:
            # Assume Matrix Market format; need accompanying genes/barcodes files
            # Scanpy can infer them if they are in the same directory with standard names
            adata = sc.read_mtx(str(input_file)).T  # Scanpy returns cells × genes after transpose
            # Attach gene and barcode names if present
            dir_path = input_file.parent
            genes_path = dir_path / "genes.tsv"
            barcodes_path = dir_path / "barcodes.tsv"
            if genes_path.exists():
                genes = [line.split("\t")[0] for line in genes_path.read_text().splitlines()]
                adata.var_names = genes
            if barcodes_path.exists():
                barcodes = [line.split("\t")[0] for line in barcodes_path.read_text().splitlines()]
                adata.obs_names = barcodes
    except Exception as exc:
        logger.error(f"Failed to load matrix: {exc}")
        return False

    # Identify mitochondrial genes
    mito_mask = adata.var_names.str.startswith("MT-") | adata.var_names.str.startswith("mt-")
    if not mito_mask.any():
        logger.warning("No mitochondrial genes detected; setting percent.mt to 0 for all cells.")
        adata.obs["percent.mt"] = 0.0
    else:
        # Compute percent mitochondrial reads per cell
        mito_counts = adata[:, mito_mask].X.sum(axis=1)
        total_counts = adata.X.sum(axis=1)
        # Handle sparse matrix sums returning matrix objects
        if hasattr(mito_counts, "A"):
            mito_counts = mito_counts.A.ravel()
        if hasattr(total_counts, "A"):
            total_counts = total_counts.A.ravel()
        percent_mt = (mito_counts / total_counts) * 100
        adata.obs["percent.mt"] = percent_mt

    # Filter cells
    initial_n = adata.n_obs
    adata = adata[adata.obs["percent.mt"] <= 20].copy()
    final_n = adata.n_obs
    logger.info(f"Cells before QC: {initial_n}, after QC (<=20% mito): {final_n}")
    if final_n == 0:
        logger.error("All cells filtered out by mitochondrial QC.")
        return False

    # Normalisation (LogNormalize analogue)
    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        adata.write_h5ad(str(output_path))
        logger.info(f"Python preprocessing completed, output saved to {output_path}")
        return True
    except Exception as exc:
        logger.error(f"Failed to write .h5ad file: {exc}")
        return False


def verify_outputs(output_path: Path) -> bool:
    """Check that the .h5ad file exists and is non‑empty."""
    if output_path.is_file() and output_path.stat().st_size > 0:
        logger.info(f"Verification succeeded: {output_path} exists and is non‑empty.")
        return True
    logger.error(f"Verification failed: {output_path} missing or empty.")
    return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Seurat QC/normalisation via R, with a Scanpy fallback."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to raw count matrix (file or directory).",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path for the processed .h5ad file.",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only verify the R environment and exit.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    # Step 1: Verify R environment
    r_available = check_r_environment()
    if args.check_only:
        sys.exit(0 if r_available else 1)

    # Step 2: Prefer R processing if possible
    if r_available:
        logger.info("R environment detected – attempting R preprocessing.")
        if run_r_preprocessing(input_path, output_path):
            if verify_outputs(output_path):
                logger.info("Preprocessing finished via R.")
                sys.exit(0)
            else:
                logger.error("R preprocessing succeeded but output verification failed.")
                sys.exit(1)
        else:
            logger.warning("R preprocessing failed – falling back to Python implementation.")

    # Step 3: Python fallback
    if python_preprocess(input_path, output_path):
        if verify_outputs(output_path):
            logger.info("Preprocessing finished via Python fallback.")
            sys.exit(0)
        else:
            logger.error("Python preprocessing succeeded but output verification failed.")
            sys.exit(1)
    else:
        logger.error("Both R and Python preprocessing failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
