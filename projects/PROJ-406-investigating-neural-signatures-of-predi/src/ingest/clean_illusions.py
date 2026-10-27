"""
src.ingest.clean_illusions
===========================

Command‑line interface that ensures both the Müller‑Lyer and Ponzo
illusion datasets are downloaded (if necessary), cleaned, and written
to the standardised CSV locations:

    data/clean/clean_muller_lyer.csv
    data/clean/clean_ponzo.csv

The script is deliberately lightweight – it re‑uses the existing
``download_and_clean_muller`` and ``download_and_clean_ponzo`` helpers
from :pymod:`src.ingest.load_illusions`.  Those helpers already implement
the full download‑and‑clean pipeline, including schema mapping,
aggregation, checksum recording and logging.  By delegating to them we
avoid code duplication and guarantee that the cleaning behaviour is
identical whether the user invokes the original ``load_illusions`` flag
interface or this dedicated cleaning module.

The expected usage (as referenced by ``tasks.md``) is::

    python -m src.ingest.clean_illusions

which will produce the two cleaned CSV files under ``data/clean``.
"""

import sys
from pathlib import Path

from src.ingest.load_illusions import (
    download_and_clean_muller,
    download_and_clean_ponzo,
)
from src.utils.seed import set_global_seed, DEFAULT_SEED

def main(argv: list[str] | None = None) -> None:
    """
    Entry point for the ``src.ingest.clean_illusions`` module.

    Parameters
    ----------
    argv : list[str] | None
        Command‑line arguments passed to the script.  The cleaning
        routine does not accept any options; the argument list is
        ignored so that the script can be invoked as a module
        (``python -m src.ingest.clean_illusions``) without requiring
        additional flags.
    """
    # Ensure deterministic behaviour for any stochastic steps that might be
    # introduced in future cleaning stages (e.g., imputation).
    set_global_seed(DEFAULT_SEED)

    # The helper functions internally check whether the raw parquet files
    # already exist; if they do, the download step is skipped and only the
    # cleaning phase is performed.
    download_and_clean_muller()
    download_and_clean_ponzo()

    # Provide a short, user‑friendly confirmation that the artefacts have
    # been created.  This message is printed to stdout so that CI logs can
    # verify successful execution.
    clean_dir = Path(__file__).parents[2] / "data" / "clean"
    print(f"✅ Cleaned CSVs written to: {clean_dir}")

if __name__ == "__main__":
    main(sys.argv[1:])
