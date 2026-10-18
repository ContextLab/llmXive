"""Run the full pipeline (currently only ingestion) for the corrosion project.

This entry point is referenced by ``quickstart.md`` which expects the command:
    python -m src.pipeline.run_all

At this stage of the project only the ingestion step (T001) is implemented.
The script invokes :func:`src.pipeline.ingest.main` which fetches a real
corrosion dataset from OpenML, writes the raw CSV to ``data/raw/`` and records
provenance in ``metadata/dataset.yaml``.  It exits with the same return code
as the ingestion script, allowing the quickstart command to succeed even
though later pipeline stages are not yet implemented.
"""

from __future__ import annotations

import sys

from src.pipeline.ingest import main as ingest_main

def main(argv: list[str] | None = None) -> int:
    """Entry point for ``python -m src.pipeline.run_all``.

    Delegates to :func:`src.pipeline.ingest.main`.  Any command‑line arguments
    are passed through unchanged so that the ingestion script’s ``--dataset-id``
    and ``--max‑candidates`` options remain available.
    """
    return ingest_main(argv)

if __name__ == "__main__":
    sys.exit(main())
