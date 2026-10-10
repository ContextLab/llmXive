"""Run scVelo dynamical model on a preprocessed AnnData object.

This script loads a `.h5ad` file that contains the required
``spliced`` and ``unspliced`` layers, computes RNA velocity using 
the dynamical model on CPU, adds a pseudotime (latent time) 
annotation, and writes the enriched AnnData object to the 
specified output path.

It handles both direct file paths and directories (searching for 
GSE136103_processed.h5ad).
"""
import argparse
import logging
import sys
from pathlib import Path

import scvelo as scv

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
def _check_layers(adata) -> bool:
    """Ensure the AnnData object has the required spliced/unspliced layers."""
    missing = [layer for layer in ("spliced", "unspliced") if layer not in adata.layers]
    if missing:
        logger.error(
            f"Input AnnData is missing required layers: {', '.join(missing)}"
        )
        return False
    return True

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Estimate RNA velocity and pseudotime (latent time) using "
            "scVelo's dynamical model (CPU-only)."
        )
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the pre-processed .h5ad file or directory containing it.",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path where the output .h5ad with velocity information will be saved.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    # ------------------------------------------------------------------
    # Resolve Input Path
    # ------------------------------------------------------------------
    # If input is a directory, look for the specific dataset required for T004
    if input_path.is_dir():
        target_file = input_path / "GSE136103_processed.h5ad"
        if target_file.exists():
            input_path = target_file
        else:
            logger.error(f"Directory {input_path} does not contain GSE136103_processed.h5ad")
            sys.exit(1)

    if not input_path.is_file():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Load data
    # ------------------------------------------------------------------
    logger.info(f"Reading AnnData from {input_path}")
    try:
        adata = scv.read(str(input_path))
    except Exception as exc:
        logger.error(f"Failed to read AnnData: {exc}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Basic sanity checks
    # ------------------------------------------------------------------
    if not _check_layers(adata):
        sys.exit(1)

    # ------------------------------------------------------------------
    # scVelo pipeline (CPU-only)
    # ------------------------------------------------------------------
    logger.info("Running scVelo preprocessing (filter & normalize).")
    # We run this to identify the top genes that vary in splicing kinetics
    scv.pp.filter_and_normalize(
        adata,
        min_shared_counts=20,
        n_top_genes=2000,
        inplace=True,
    )

    logger.info("Computing moments.")
    scv.pp.moments(adata, n_pcs=30, n_neighbors=30)

    logger.info("Recovering dynamics (dynamical model).")
    # This is the most compute-intensive step; runs on CPU by default
    scv.tl.recover_dynamics(adata)

    logger.info("Computing velocities.")
    scv.tl.velocity(adata, mode="dynamical")

    logger.info("Building velocity graph.")
    scv.tl.velocity_graph(adata)

    logger.info("Estimating latent time (pseudotime).")
    scv.tl.latent_time(adata)

    # Store pseudotime in a more generic name expected by the integration test
    if "latent_time" in adata.obs:
        adata.obs["pseudotime"] = adata.obs["latent_time"]
    else:
        logger.warning("latent_time not found in adata.obs; pseudotime will be missing.")

    # ------------------------------------------------------------------
    # Write output
    # ------------------------------------------------------------------
    # If output_path is a directory, we use the filename from tasks.md
    final_output = output_path
    if output_path.is_dir():
        final_output = output_path / "velocity_graph.h5ad"

    final_output.parent.mkdir(parents=True, exist_ok=True)
    try:
        adata.write(str(final_output))
        logger.info(f"Velocity analysis completed. Output written to {final_output}")
    except Exception as exc:
        logger.error(f"Failed to write output file: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    main()
