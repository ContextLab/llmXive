"""
Entry‑point for the planetary nebula artifact analysis pipeline.

The CLI supports a small set of sub‑commands that correspond to the
major pipeline stages.  For the purpose of task **T006b** only the
``generate`` mode is fully implemented – it invokes the synthetic
generator to create 50 FITS images and the accompanying ground‑truth
manifest.

The implementation deliberately avoids any heavy‑weight dependencies
and performs only the minimal validation required for the current
test suite.
"""

import argparse
import logging
import sys
from pathlib import Path

# Local imports – the ``code`` package is the top‑level module.
# Using explicit relative imports makes the module layout robust
# regardless of the current working directory.
from .synthetic.generator import main as generate_main
from .io.writer import write_run_manifest_for_pipeline

# ----------------------------------------------------------------------
# Argument parsing
# ----------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    """Create the top‑level argument parser."""
    parser = argparse.ArgumentParser(
        description="Planetary Nebula Artifact Analysis Pipeline"
    )
    parser.add_argument(
        "--mode",
        choices=["generate", "process", "calibrate", "validate", "verify"],
        help="Pipeline stage to execute",
    )
    parser.add_argument(
        "--n-images",
        type=int,
        default=50,
        help="Number of synthetic images to generate (generate mode only)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/synthetic",
        help="Output directory for generated artefacts (generate mode only)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility (optional)",
    )
    parser.add_argument(
        "--run-all",
        action="store_true",
        help="Convenience flag to run the full pipeline (not implemented yet)",
    )
    return parser

# ----------------------------------------------------------------------
# Helper to run the ``generate`` stage
# ----------------------------------------------------------------------
def _run_generate(args: argparse.Namespace) -> None:
    """Execute the synthetic‑image generator."""
    seed = args.seed
    # ``generate_main`` expects ``seed`` to be an ``int``; if the user
    # did not supply one we fall back to the default defined in
    # ``code.config`` via the generator's own default argument.
    generate_main(
        n_images=args.n_images,
        output_dir=args.output,
        seed=seed if seed is not None else 42,
    )
    # Record a run‑manifest for reproducibility.
    write_run_manifest_for_pipeline(Path(__file__).resolve().parents[2])

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """Dispatch to the requested pipeline stage."""
    parser = build_parser()
    args = parser.parse_args()

    # Configure a very simple console logger – useful for debugging
    # and for the unit‑test output capture.
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger = logging.getLogger(__name__)

    if args.run_all:
        logger.info("Run‑all flag received – full pipeline not yet implemented.")
        # In a complete implementation this would sequentially call all
        # stages; for now we simply exit with a helpful message.
        sys.exit(0)

    if not args.mode:
        # No mode supplied – show help and exit with a non‑zero status
        parser.print_help()
        sys.exit(1)

    if args.mode == "generate":
        logger.info(
            "Generating %d synthetic nebulae in %s",
            args.n_images,
            args.output,
        )
        _run_generate(args)
    else:
        # Placeholder for the remaining stages – they are outside the
        # scope of T006b but the CLI must still handle the arguments
        # gracefully.
        logger.error("Mode '%s' is not implemented in this stub.", args.mode)
        sys.exit(1)

if __name__ == "__main__":
    main()