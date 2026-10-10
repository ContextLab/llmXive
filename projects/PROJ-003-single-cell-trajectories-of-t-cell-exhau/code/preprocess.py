"""
Wrapper script to invoke preprocess.R for Seurat-based QC and normalization,
with a Python fallback using Scanpy when R is unavailable.

Fixes the previous issue where providing a directory for --output caused
a failure in adata.write_h5ad. Now correctly iterates over datasets in
the input directory and writes individual .h5ad files.
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
    """
    logger.info(f"Running R preprocessing for {input_path} → {output_path}")

    if not input_path.exists():
        logger.error(f"Input path does not exist: {input_path}")
        return False

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

    try:
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"R script failed (return code {e.returncode}): {e.stderr}")
        return False
    except FileNotFoundError:
        logger.error("Rscript executable not found.")
        return False


def python_preprocess(input_path: Path, output_path: Path) -> bool:
    """
    Pure‑Python fallback that mirrors the R QC/normalisation steps using Scanpy.
    """
    logger.info(f"Running Python fallback preprocessing for {input_path}")

    if input_path.is_dir():
        candidates = list(input_path.rglob("*.h5")) + list(input_path.rglob("*.mtx*"))
        if not candidates:
            logger.error(f"No supported matrix files found in directory {input_path}")
            return False
        input_file = candidates[0]
    else:
        input_file = input_path

    try:
        if input_file.suffix.lower() == ".h5":
            adata = sc.read_10x_h5(str(input_file))
        else:
            adata = sc.read_mtx(str(input_file)).T
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
        mito_counts = adata[:, mito_mask].X.sum(axis=1)
        total_counts = adata.X.sum(axis=1)
        if hasattr(mito_counts, "A"): mito_counts = mito_counts.A.ravel()
        if hasattr(total_counts, "A"): total_counts = total_counts.A.ravel()
        adata.obs["percent.mt"] = (mito_counts / total_counts) * 100

    initial_n = adata.n_obs
    adata = adata[adata.obs["percent.mt"] <= 20].copy()
    final_n = adata.n_obs
    logger.info(f"Cells before QC: {initial_n}, after QC (<=20% mito): {final_n}")
    if final_n == 0:
        logger.error("All cells filtered out by mitochondrial QC.")
        return False

    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        adata.write_h5ad(str(output_path))
        return True
    except Exception as exc:
        logger.error(f"Failed to write .h5ad file: {exc}")
        return False


def verify_outputs(output_path: Path) -> bool:
    """Check that the .h5ad file exists and is non‑empty."""
    if output_path.is_file() and output_path.stat().st_size > 0:
        return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Seurat QC/normalisation via R, with a Scanpy fallback.")
    parser.add_argument("--input", type=str, required=True, help="Path to raw count matrix (file or directory).")
    parser.add_argument("--output", type=str, required=True, help="Path for the processed .h5ad file or directory.")
    parser.add_argument("--check-only", action="store_true", help="Only verify the R environment and exit.")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    r_available = check_r_environment()
    if args.check_only:
        sys.exit(0 if r_available else 1)

    # Handle directory-to-directory processing
    if input_path.is_dir():
        # Find subdirectories (datasets)
        datasets = [d for d in input_path.iterdir() if d.is_dir()]
        if not datasets:
            logger.error(f"No dataset directories found in {input_path}")
            sys.exit(1)
        
        # Ensure output is a directory
        output_path.mkdir(parents=True, exist_ok=True)
        
        all_success = True
        for ds_dir in datasets:
            ds_id = ds_dir.name
            # Find the raw matrix file in the dataset directory
            raw_files = list(ds_dir.rglob("*.mtx*")) + list(ds_dir.rglob("*.h5"))
            if not raw_files:
                logger.warning(f"No raw matrix found for {ds_id}, skipping.")
                continue
            
            target_out = output_path / f"{ds_id}.h5ad"
            logger.info(f"Processing dataset {ds_id}...")
            
            success = False
            if r_available:
                if run_r_preprocessing(raw_files[0], target_out):
                    success = verify_outputs(target_out)
            
            if not success:
                logger.warning(f"R failed for {ds_id}, trying Python fallback.")
                if python_preprocess(raw_files[0], target_out):
                    success = verify_outputs(target_out)
            
            if not success:
                logger.error(f"Preprocessing failed for {ds_id}")
                all_success = False
            else:
                logger.info(f"Successfully processed {ds_id} -> {target_out}")
        
        if not all_success:
            sys.exit(1)
    else:
        # Single file processing
        success = False
        if r_available:
            if run_r_preprocessing(input_path, output_path):
                success = verify_outputs(output_path)
        
        if not success:
            if python_preprocess(input_path, output_path):
                success = verify_outputs(output_path)
        
        if not success:
            sys.exit(1)

if __name__ == "__main__":
    main()
