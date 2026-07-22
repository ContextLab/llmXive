"""
Data Loaders for the llmXive pipeline.

This module provides utility classes for loading traces, metrics, and other
data artifacts from disk in a consistent and validated manner.
"""
import json
import csv
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator
import sys

class TraceLoader:
    """
    Loader for synthetic trace data.
    
    Handles loading individual trace files and iterating over batches of traces
    from the training, held-out, or raw data directories.
    """
    def __init__(self, config):
        self.config = config
        self._cache = {}

    def load_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a single trace by ID.
        
        Args:
            trace_id: The unique identifier for the trace.
            
        Returns:
            The trace dictionary or None if not found.
        """
        if trace_id in self._cache:
            return self._cache[trace_id]
        
        # Determine the search path based on config
        # Priority: held_out -> training -> raw
        search_paths = [
            self.config.data_held_out_path,
            self.config.data_training_path,
            self.config.data_raw_path
        ]
        
        for base_path in search_paths:
            if not base_path:
                continue
            trace_path = base_path / f"session_{trace_id}.json"
            if trace_path.exists():
                try:
                    with open(trace_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self._cache[trace_id] = data
                    return data
                except (json.JSONDecodeError, IOError):
                    continue
        
        return None

    def load_all_traces(self, directory: Optional[Path] = None) -> Iterator[Dict[str, Any]]:
        """
        Load all trace files from a specified directory.
        
        Args:
            directory: The directory to search for trace files. If None, uses data_raw_path.
            
        Yields:
            Trace dictionaries one by one.
        """
        base_path = directory or self.config.data_raw_path
        if not base_path.exists():
            raise FileNotFoundError(f"Data directory not found: {base_path}")
        
        for json_file in base_path.glob("session_*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                yield data
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Failed to load {json_file}: {e}", file=sys.stderr)
                continue

class MetricsLoader:
    """
    Loader for extracted metrics and feature matrices.
    
    Handles loading CSV files containing structural metrics and compressibility scores.
    """
    def __init__(self, config):
        self.config = config
        self._cache = {}

    def load_feature_matrix(self) -> List[Dict[str, Any]]:
        """
        Load the global feature matrix CSV.
        
        Returns:
            List of dictionaries representing rows in the feature matrix.
        """
        matrix_path = self.config.data_processed_path / "feature_matrix.csv"
        if not matrix_path.exists():
            raise FileNotFoundError(f"Feature matrix not found: {matrix_path}")
        
        if "feature_matrix" in self._cache:
            return self._cache["feature_matrix"]
        
        rows = []
        with open(matrix_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric strings to floats where appropriate
                processed_row = {}
                for key, value in row.items():
                    try:
                        processed_row[key] = float(value)
                    except (ValueError, TypeError):
                        processed_row[key] = value
                rows.append(processed_row)
        
        self._cache["feature_matrix"] = rows
        return rows

    def load_per_trace_scores(self) -> List[Dict[str, Any]]:
        """
        Load the per-trace compressibility scores CSV.
        
        Returns:
            List of dictionaries containing trace scores.
        """
        scores_path = self.config.data_processed_path / "per_trace_scores.csv"
        if not scores_path.exists():
            raise FileNotFoundError(f"Per-trace scores not found: {scores_path}")
        
        if "per_trace_scores" in self._cache:
            return self._cache["per_trace_scores"]
        
        rows = []
        with open(scores_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                processed_row = {}
                for key, value in row.items():
                    try:
                        processed_row[key] = float(value)
                    except (ValueError, TypeError):
                        processed_row[key] = value
                rows.append(processed_row)
        
        self._cache["per_trace_scores"] = rows
        return rows

    def load_accuracy_deltas(self) -> List[Dict[str, Any]]:
        """
        Load the accuracy deltas CSV.
        
        Returns:
            List of dictionaries containing baseline and compressed accuracy deltas.
        """
        deltas_path = self.config.data_processed_path / "accuracy_deltas.csv"
        if not deltas_path.exists():
            raise FileNotFoundError(f"Accuracy deltas not found: {deltas_path}")
        
        if "accuracy_deltas" in self._cache:
            return self._cache["accuracy_deltas"]
        
        rows = []
        with open(deltas_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                processed_row = {}
                for key, value in row.items():
                    try:
                        processed_row[key] = float(value)
                    except (ValueError, TypeError):
                        processed_row[key] = value
                rows.append(processed_row)
        
        self._cache["accuracy_deltas"] = rows
        return rows