"""Preprocessing wrapper for the T-cell exhaustion project (T003).

This module provides a Python interface to execute the R-based Seurat
preprocessing pipeline or a Scanpy-based fallback.
"""
import argparse
import logging
import subprocess
import sys
from pathlib import Path

# ----------------------------------------------------------------------
# Logging configuration
# ----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def check_r_environment() -> bool:
    """Verify that R and the Seurat package are available."""
    try:
        # Check if R is installed
        subprocess.run(["R", "--version"], capture_output=True, check=True)
        # Check if Seurat is installed
        cmd = "library(Seurat)"
        subprocess.run(["R", "-e", cmd], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("R or Seurat not found in the environment.")
        return False

def run_r_preprocessing(input_path: Path, output_path: Path) -> bool:
    """Execute the R preprocessing script."""
    # The R script is expected to be at code/preprocess.R relative to project root
    project_root = Path(__file__).resolve().parent.parent
    r_script = project_root / "code" / "preprocess.R"
    
    if not r_script.exists():
        logger.error(f"R script not found: {r_script}")
        return False

    try:
        logger.info(f"Invoking R preprocessing: {r_script}")
        # Pass input and output as arguments to the R script
        subprocess.run(
            ["Rscript", str(r_script), str(input_path), str(output_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"R preprocessing failed: {e.stderr}")
        return False

def python_preprocess(input_path: Path, output_path: Path) -> bool:
    """Pure-Python fallback that mirrors the R QC/normalisation steps using Scanpy."""
    logger.info("Executing Python-based preprocessing fallback...")
    try:
        import scanpy as sc
        # This is a simplified mirror of the Seurat pipeline
        adata = sc.read_h5ad(str(input_path)) if input_path.suffix == ".h5ad" else sc.read_csv(str(input_path))
        
        # QC: Filter mitochondrial genes
        # Assume genes are in var_names
        adata.var['mt'] = adata.var_names.str.startswith('MT-')
        sc.pp.calculate_qc_metrics(adata, qc_vars=['mt'], percent_top=None, log1p=False, inplace=True)
        
        # Filter cells with > 20% mitochondrial reads
        adata = adata[adata.obs.pct_counts_mt < 20, :]
        
        # Normalization
        sc.pp.normalize_total(adata, target_sum=1e4)
        sc.pp.log1p(adata)
        
        # HVG selection
        sc.pp.highly_variable_genes(adata, n_top_genes=2000)
        
        adata.write_h5ad(str(output_path))
        return True
    except Exception as e:
        logger.error(f"Python preprocessing failed: {e}")
        return False

def verify_outputs(output_path: Path) -> bool:
    """Check that the .h5ad file exists and is non-empty."""
    return output_path.exists() and output_path.stat().st_size > 0

def main() -> None:
    parser = argparse.ArgumentParser(description="Preprocess scRNA-seq data.")
    parser.add_argument("--input", type=str, required=True, help="Input raw data path.")
    parser.add_argument("--output", type=str, required=True, help="Output processed path.")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if check_r_environment():
        success = run_r_preprocessing(input_path, output_path)
    else:
        success = python_preprocess(input_path, output_path)

    if success and verify_outputs(output_path):
        logger.info(f"Preprocessing successful. Output: {output_path}")
    else:
        logger.error("Preprocessing failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
