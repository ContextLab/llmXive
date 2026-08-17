import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from config import get_config, ensure_directories

class DataPipelineLog:
    """
    Centralized logging utility for the data pipeline.
    Records source URLs, download status, imputation details, merge statistics,
    and excluded species to satisfy FR-007 and ensure reproducibility.
    """

    def __init__(self, log_dir: Optional[str] = None, log_filename: str = "pipeline.log"):
        config = get_config()
        self.log_dir = log_dir or config.get("log_dir", "data/logs")
        self.log_filename = log_filename
        self.log_path = Path(self.log_dir) / self.log_filename

        # Ensure log directory exists
        ensure_directories([self.log_dir])

        # Setup standard logging to file
        self.logger = logging.getLogger("DataPipelineLog")
        self.logger.setLevel(logging.INFO)

        # Avoid duplicate handlers if logger already configured
        if not self.logger.handlers:
            file_handler = logging.FileHandler(self.log_path)
            file_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        # Also maintain an in-memory JSON log for programmatic access
        self.json_log_path = Path(self.log_dir) / "pipeline_records.json"
        self.records: List[Dict[str, Any]] = []
        self._load_existing_json_records()

    def _load_existing_json_records(self):
        """Load existing records from the JSON log file if it exists."""
        if self.json_log_path.exists():
            try:
                with open(self.json_log_path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.records = data
            except (json.JSONDecodeError, IOError):
                self.records = []

    def _save_json_records(self):
        """Persist records to the JSON log file."""
        with open(self.json_log_path, 'w') as f:
            json.dump(self.records, f, indent=2)

    def _log_record(self, category: str, details: Dict[str, Any]):
        """Helper to log a record both to text log and JSON store."""
        timestamp = datetime.now().isoformat()
        record = {
            "timestamp": timestamp,
            "category": category,
            **details
        }
        self.records.append(record)
        self._save_json_records()

        # Format message for text log
        msg_parts = [f"[{category}]"]
        for k, v in details.items():
            if isinstance(v, (dict, list)):
                msg_parts.append(f"{k}={json.dumps(v)}")
            else:
                msg_parts.append(f"{k}={v}")
        self.logger.info(" ".join(msg_parts))

    def record_source_url(self, source_name: str, url: str, expected_md5: Optional[str] = None):
        """
        Record the source URL for a dataset.
        FR-007: Record source URLs.
        """
        self._log_record("SOURCE_URL", {
            "source_name": source_name,
            "url": url,
            "expected_md5": expected_md5
        })

    def record_download_status(self, source_name: str, status: str, md5_hash: Optional[str] = None, error: Optional[str] = None):
        """
        Record the status of a download operation.
        FR-007: Record download status.
        """
        self._log_record("DOWNLOAD_STATUS", {
            "source_name": source_name,
            "status": status,
            "md5_hash": md5_hash,
            "error": error
        })

    def record_imputation_details(self, dataset_name: str, strategy: str, columns_imputed: List[str],
                                  rows_imputed: int, dropped_columns: List[str], failed_imputation_cols: List[str]):
        """
        Record details about the imputation process.
        FR-007: Record imputation details.
        """
        self._log_record("IMPUTATION", {
            "dataset_name": dataset_name,
            "strategy": strategy,
            "columns_imputed": columns_imputed,
            "rows_imputed": rows_imputed,
            "dropped_columns": dropped_columns,
            "failed_imputation_cols": failed_imputation_cols
        })

    def record_merge_statistics(self, left_dataset: str, right_dataset: str, join_type: str,
                                left_rows: int, right_rows: int, output_rows: int,
                                left_missing_in_right: int, right_missing_in_left: int,
                                excluded_species: List[str]):
        """
        Record statistics from a dataset merge operation.
        FR-007: Record merge statistics and excluded species.
        """
        self._log_record("MERGE", {
            "left_dataset": left_dataset,
            "right_dataset": right_dataset,
            "join_type": join_type,
            "left_rows": left_rows,
            "right_rows": right_rows,
            "output_rows": output_rows,
            "left_missing_in_right": left_missing_in_right,
            "right_missing_in_left": right_missing_in_left,
            "excluded_species": excluded_species
        })

    def record_excluded_species(self, dataset_name: str, reason: str, species_list: List[str]):
        """
        Explicitly record a list of excluded species.
        FR-007: Record excluded species.
        """
        self._log_record("EXCLUDED_SPECIES", {
            "dataset_name": dataset_name,
            "reason": reason,
            "species_list": species_list
        })

    def get_summary(self) -> Dict[str, Any]:
        """
        Return a summary of all recorded events.
        Useful for generating reports or validation checks.
        """
        summary = {
            "source_urls": [],
            "downloads": [],
            "imputations": [],
            "merges": [],
            "excluded_species": []
        }

        for record in self.records:
            cat = record.get("category")
            if cat == "SOURCE_URL":
                summary["source_urls"].append(record)
            elif cat == "DOWNLOAD_STATUS":
                summary["downloads"].append(record)
            elif cat == "IMPUTATION":
                summary["imputations"].append(record)
            elif cat == "MERGE":
                summary["merges"].append(record)
            elif cat == "EXCLUDED_SPECIES":
                summary["excluded_species"].append(record)

        return summary