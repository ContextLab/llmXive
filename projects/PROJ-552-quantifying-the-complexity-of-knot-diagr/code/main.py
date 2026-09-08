"""Top‑level entry point for the project run‑book.

The quickstart script expects `python code/main.py` to execute the full
analysis pipeline.  This thin wrapper simply delegates to the orchestrator
defined in `code/analysis/run_pipeline.py`.
"""

from __future__ import annotations

from analysis.run_pipeline import main as run_pipeline_main


def main() -> None:
    """Run the complete analysis pipeline."""
    run_pipeline_main()


if __name__ == "__main__":  # pragma: no cover
    main()
