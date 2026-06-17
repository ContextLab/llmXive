"""
Helper class that orchestrates the end‑to‑end data‑saving workflow.

The original implementation used a ``log_operation`` decorator with a keyword
argument that did not exist in the logger utilities.  The decorator has been
updated to accept ``output_path_arg`` (see ``reproducibility.logs``), so the
wrapper below now works without raising ``TypeError``.
"""

from __future__ import annotations

from pathlib import Path

from reproducibility.logs import get_logger, log_operation


class DataSaver:
    """
    Simple façade that triggers the download and parsing steps.
    """

    @log_operation(
        operation_name="save_raw_and_cleaned_data",
        output_path_arg="output_path",
    )
    def save_raw_and_cleaned_data(self, output_path: Path | None = None) -> None:
        """
        Execute the full pipeline:
          1. Download the raw KnotInfo JSON.
          2. Parse the JSON into a cleaned CSV.

        ``output_path`` is accepted for API compatibility but is not used
        directly – the underlying functions know their default destinations.
        """
        logger = get_logger()
        logger.info("Starting full data‑saving pipeline.")

        # Import locally to avoid circular imports.
        from data.parser import save_raw_and_cleaned_data

        save_raw_and_cleaned_data()
        logger.info("Data‑saving pipeline completed.")


def main() -> None:  # pragma: no cover
    """
    Entry‑point that can be invoked as::

        python -m code.data.data_saver
    """
    saver = DataSaver()
    saver.save_raw_and_cleaned_data()