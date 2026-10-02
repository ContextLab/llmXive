"""
Logging utilities for the data pipeline.
Provides DataPipelineLog for structured logging of data operations.
"""
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from config import ensure_directories, get_config

class DataPipelineLog:
    """
    Logger for data pipeline operations.
    Records source URLs, download status, imputation details, merge statistics, and excluded species.
    """
    def __init__(self, component_name: str):
        self.component_name = component_name
        self.log_dir = Path(get_config()["paths"]["logs"])
        ensure_directories([self.log_dir])
        
        self.log_file = self.log_dir / f"{component_name}.log"
        self.metrics_file = self.log_dir / "metrics.json"
        
        # Setup standard logging
        self.logger = logging.getLogger(f"pipeline.{component_name}")
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.FileHandler(self.log_file)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Initialize metrics file if not exists
        if not self.metrics_file.exists():
            with open(self.metrics_file, 'w') as f:
                json.dump({}, f)

    def record_source_url(self, source: str, url: str) -> None:
        """Record the URL of a data source."""
        self.logger.info(f"Source URL: {source} -> {url}")
        self._update_metrics("source_urls", {source: url})

    def record_download_status(self, operation: str, status: str, details: str) -> None:
        """Record the status of a download operation."""
        self.logger.info(f"Download Status: {operation} - {status} - {details}")
        self._update_metrics(f"download_{operation}", {"status": status, "details": details})

    def record_imputation_details(self, method: str, missing_count: int, imputed_count: int) -> None:
        """Record details of imputation process."""
        self.logger.info(f"Imputation: {method} - Missing: {missing_count}, Imputed: {imputed_count}")
        self._update_metrics("imputation", {
            "method": method,
            "missing_count": missing_count,
            "imputed_count": imputed_count
        })

    def record_merge_statistics(self, total_rows: int, excluded_count: int, excluded_species: List[str]) -> None:
        """Record statistics from dataset merging."""
        self.logger.info(f"Merge Stats: Total Rows: {total_rows}, Excluded: {excluded_count}")
        self._update_metrics("merge", {
            "total_rows": total_rows,
            "excluded_count": excluded_count,
            "excluded_species": excluded_species
        })

    def record_metrics(self, metrics: Dict[str, Any]) -> None:
        """Record arbitrary metrics."""
        self._update_metrics("custom", metrics)

    def _update_metrics(self, key: str, value: Any) -> None:
        """Update the metrics JSON file."""
        try:
            with open(self.metrics_file, 'r') as f:
                metrics = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            metrics = {}
        
        metrics[key] = value
        
        with open(self.metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)

    def get_metrics(self) -> Dict[str, Any]:
        """Retrieve current metrics."""
        try:
            with open(self.metrics_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
