from __future__ import annotations
import logging
from pathlib import Path
import sys

# Import pipeline components
from code.ast_cloner import compute_clone_density_batch
from code.model_metrics import compute_perplexity_batch

logger = logging.getLogger(__name__)

def run_pipeline(*args, **kwargs) -> None:
    """
    Orchestrate the end‑to‑end US 1 pipeline.

    The function is tolerant to a variety of signatures used by the
    integration test:

    - ``run_pipeline(raw_dir)`` (positional)
    - ``run_pipeline(input_path=raw_dir)`` (keyword)
    - ``run_pipeline(raw_dir=raw_dir)`` (alternative keyword)
    """
    # Resolve the raw directory argument
    if args:
        raw_dir = Path(args[0])
    else:
        raw_dir = kwargs.get("input_path") or kwargs.get("raw_dir")
    if not raw_dir:
        raise TypeError("run_pipeline() missing required raw directory argument")

    raw_dir = Path(raw_dir)

    if not raw_dir.is_dir():
        raise FileNotFoundError(f"Raw directory {raw_dir} does not exist")

    logger.info(f"Starting pipeline with raw data at {raw_dir}")

    # Step 1: Compute clone density metrics
    compute_clone_density_batch(input_path=raw_dir)

    # Step 2: Compute perplexity scores using the model
    # The model_metrics module expects an ``input_path`` argument that points
    # to the same raw directory.
    compute_perplexity_batch(input_path=raw_dir)

    logger.info("Pipeline completed successfully")

def validate_schema_compliance():
    """
    Placeholder for schema validation logic required by other tasks.
    """
    logger.debug("Schema validation placeholder executed")

def main(argv: list[str] | None = None) -> int:
    """
    CLI entry point – simply forwards arguments to ``run_pipeline``.
    """
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        logger.error("No raw directory supplied to the pipeline")
        return 1

    try:
        run_pipeline(Path(argv[0]))
    except Exception as e:
        logger.exception(f"Pipeline execution failed: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())