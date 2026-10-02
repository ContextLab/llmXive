"""
Entry‑point module invoked by the quickstart run‑book:
    python -m src.pipeline.run --seed 42 --output-dir output/

The original pipeline implementation resides in ``code/data/pipeline.py``.
This wrapper sets the random seed (via the project's logging utilities),
forwards the output directory argument, and calls the pipeline's
``run_pipeline`` function.  The pipeline is expected to:
  * download the raw HEA dataset (if missing),
  * preprocess the data,
  * compute descriptors,
  * write the processed descriptor table to ``data/processed/hea_descriptors.csv``,
  * write a status JSON file to ``output/data_status.json``.

If any step fails an exception is raised, causing a non‑zero exit code.
"""

import argparse
import sys

# Import project utilities – these are part of the existing API surface.
from utils.logging import set_seeds, get_logger
from data.pipeline import run_pipeline

def main(argv: list | None = None) -> None:
    """
    Parse command‑line arguments, configure the environment and invoke the
    data pipeline.

    Parameters
    ----------
    argv: list | None
        Argument list to parse; if ``None`` the arguments are taken from
        ``sys.argv`` (default behaviour of ``argparse``).
    """
    parser = argparse.ArgumentParser(
        description="Run the full HEA yield‑strength data pipeline."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic behaviour (default: 42).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Directory where pipeline artefacts such as status JSON are written.",
    )

    args = parser.parse_args(argv)

    # Initialise deterministic logging and seed handling.
    logger = get_logger(__name__)
    logger.info("Starting pipeline with seed=%s, output_dir=%s", args.seed, args.output_dir)
    set_seeds(args.seed)

    try:
        # ``run_pipeline`` is the central orchestrator implemented in
        # ``code/data/pipeline.py``.  It returns a status dict that is also
        # written to ``output/data_status.json`` by the pipeline itself.
        run_pipeline(output_dir=args.output_dir)
        logger.info("Pipeline completed successfully.")
    except Exception as exc:  # pragma: no cover – any exception is fatal.
        logger.exception("Pipeline execution failed: %s", exc)
        # Re‑raise to ensure a non‑zero exit status for the runner.
        raise

if __name__ == "__main__":
    # When executed as a script ``python -m src.pipeline.run`` forward the
    # real ``sys.argv`` (excluding the module name) to ``main``.
    main(sys.argv[1:])