"""
Logging utilities for the plant drought tolerance prediction pipeline.

This module provides the DataPipelineLog class for recording
source URLs, download status, imputation details, merge statistics,
and excluded species as required by FR-007.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Ensure the log directory exists
LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

def _get_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class DataPipelineLog:
    """
    A structured logger for the data pipeline.

    Records events related to data ingestion, processing, and model training
    to a JSON file and optionally to the standard logging stream.
    """

    def __init__(
        self,
        log_file: Optional[str] = None,
        level: int = logging.INFO,
    ):
        """
        Initialize the logger.

        Args:
            log_file: Relative path to the JSON log file. Defaults to 'data/logs/pipeline.json'.
            level: Logging level for the console handler.
        """
        self.log_file = Path(log_file) if log_file else LOG_DIR / "pipeline.json"
        self.events: List[Dict[str, Any]] = []

        # Setup standard logging for console output
        self.logger = logging.getLogger("DataPipelineLog")
        self.logger.setLevel(level)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _add_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """
        Internal helper to add an event to the in-memory list and write to disk.

        Args:
            event_type: Type of event (e.g., 'source_url', 'download_status').
            details: Dictionary of event-specific data.
        """
        entry = {
            "timestamp": _get_timestamp(),
            "type": event_type,
            "details": details,
        }
        self.events.append(entry)
        self.logger.info(f"[{event_type}] {details}")

        # Persist to JSON file immediately
        try:
            with open(self.log_file, "w", encoding="utf-8") as f:
                json.dump(self.events, f, indent=2, default=str)
        except IOError as e:
            self.logger.error(f"Failed to write log to {self.log_file}: {e}")

    def record_source_url(self, url: str, description: Optional[str] = None) -> None:
        """
        Record a source URL for data retrieval.

        Args:
            url: The URL of the data source.
            description: Optional description of the source.
        """
        self._add_event("source_url", {"url": url, "description": description})

    def record_download_status(
        self,
        url: str,
        status: str,
        size_bytes: Optional[int] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Record the status of a download attempt.

        Args:
            url: The URL that was accessed.
            status: 'success' or 'failure'.
            size_bytes: Size of the downloaded file if successful.
            error: Error message if status is 'failure'.
        """
        details = {"url": url, "status": status}
        if size_bytes is not None:
            details["size_bytes"] = size_bytes
        if error is not None:
            details["error"] = error
        self._add_event("download_status", details)

    def record_imputation_details(
        self,
        strategy: str,
        columns_imputed: List[str],
        rows_imputed: int,
        columns_dropped: Optional[List[str]] = None,
    ) -> None:
        """
        Record details about the imputation process.

        Args:
            strategy: The imputation strategy used (e.g., 'MICE').
            columns_imputed: List of column names that had missing values filled.
            rows_imputed: Number of rows affected.
            columns_dropped: List of columns dropped due to imputation failure.
        """
        details = {
            "strategy": strategy,
            "columns_imputed": columns_imputed,
            "rows_imputed": rows_imputed,
        }
        if columns_dropped:
            details["columns_dropped"] = columns_dropped
        self._add_event("imputation_details", details)

    def record_merge_statistics(
        self,
        left_source: str,
        right_source: str,
        left_count: int,
        right_count: int,
        merged_count: int,
        dropped_count: int,
        join_keys: List[str],
    ) -> None:
        """
        Record statistics from a data merge operation.

        Args:
            left_source: Name of the left dataset.
            right_source: Name of the right dataset.
            left_count: Number of rows in left dataset.
            right_count: Number of rows in right dataset.
            merged_count: Number of rows in the resulting merged dataset.
            dropped_count: Number of rows dropped during merge.
            join_keys: List of keys used for joining.
        """
        details = {
            "left_source": left_source,
            "right_source": right_source,
            "left_count": left_count,
            "right_count": right_count,
            "merged_count": merged_count,
            "dropped_count": dropped_count,
            "join_keys": join_keys,
        }
        self._add_event("merge_statistics", details)

    def record_excluded_species(
        self,
        species_ids: List[str],
        reason: str,
        source_dataset: str,
    ) -> None:
        """
        Record species that were excluded from the dataset.

        Args:
            species_ids: List of species identifiers that were excluded.
            reason: The reason for exclusion (e.g., 'missing_genomic_data').
            source_dataset: The dataset from which these species were excluded.
        """
        details = {
            "species_ids": species_ids,
            "reason": reason,
            "source_dataset": source_dataset,
            "count": len(species_ids),
        }
        self._add_event("excluded_species", details)

    def get_events(self) -> List[Dict[str, Any]]:
        """Return the list of all recorded events."""
        return self.events

    def save(self) -> None:
        """Force save the current events to the log file."""
        self._add_event("checkpoint", {"message": "Log flushed to disk"})