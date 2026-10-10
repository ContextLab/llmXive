"""Run scVelo dynamical model on a preprocessed AnnData object.

This script loads a `.h5ad` file that already contains the required
``spliced`` and ``unspliced`` layers (produced by the preprocessing step),
computes RNA velocity using the dynamical model on CPU, adds a pseudotime
(latent time) annotation, and writes the enriched AnnData object to the
specified output path.

The script is deliberately lightweight and avoids any GPU‑specific
configuration – scVelo defaults to CPU execution unless a CUDA‑enabled
PyTorch backend is detected, which is not installed in the CI environment.
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
            "scVelo's dynamical model (CPU‑only)."
        )
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the pre‑processed .h5ad file (must contain spliced/unspliced layers).",
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
    # Load data
    # ------------------------------------------------------------------
    if not input_path.is_file():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

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
    # scVelo pipeline (CPU‑only)
    # ------------------------------------------------------------------
    logger.info("Running scVelo preprocessing (filter & normalize).")
    # The data is already normalized by the preprocessing step, but we still
    # run a lightweight filter to remove any low‑quality genes/cells that
    # might have been missed.
    scv.pp.filter_and_normalize(
        adata,
        min_shared_counts=20,
        n_top_genes=2000,
        inplace=True,
    )

    logger.info("Computing moments.")
    scv.pp.moments(adata, n_pcs=30, n_neighbors=30)

    logger.info("Recovering dynamics (dynamical model).")
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
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        adata.write(str(output_path))
        logger.info(f"Velocity analysis completed. Output written to {output_path}")
    except Exception as exc:
        logger.error(f"Failed to write output file: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    main()
