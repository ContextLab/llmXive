"""
download_data.py
----------------
Placeholder module that satisfies the import in ``code.src.pipeline``.

The full HCP download logic is implemented later (Task T002).  For the
purposes of a dry‑run and for the test suite we provide a minimal
``main`` function that simply logs its invocation and exits successfully.
"""
import argparse
from llmxive_toolkit import get_logger


def main() -> None:
    """
    CLI entry point used by the orchestrator.

    In a dry‑run this function is never called, but it must exist so that
    ``code.src.pipeline`` can import it without raising ``ImportError``.
    """
    logger = get_logger(__name__)
    parser = argparse.ArgumentParser(
        description="Placeholder download step (real implementation in Task T002)."
    )
    parser.add_argument(
        "--subject-limit",
        type=int,
        default=5,
        help="Number of subjects to download (placeholder).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data",
        help="Base output directory (placeholder).",
    )
    args = parser.parse_args()
    logger.info(
        "download_data placeholder invoked with subject_limit=%s, output_dir=%s",
        args.subject_limit,
        args.output_dir,
    )
    # No actual download performed – this is a no‑op placeholder.
