"""
Contract test for CSV output schema (T016).

This test verifies that the main pipeline script (src/cli/main.py)
produces a results.csv file with the exact schema defined in the
feature specification (FR-007).

Schema requirements:
- Must contain columns: query_id, method, ndcg_at_10, precision_at_10, recall_at_10
- Must have at least one row per retrieval method (BM25, Dual-Encoder, RAG)
- Must NOT contain throughput metrics (those go to results/throughput_report.json)
"""

import os
import csv
import json
import tempfile
import shutil
from pathlib import Path
import pytest
from typing import List, Dict, Any

# Import the main CLI module to trigger the pipeline
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.cli.main import main as cli_main
from src.data.models import RetrievalMethod


REQUIRED_COLUMNS = [
    "query_id",
    "method",
    "ndcg_at_10",
    "precision_at_10",
    "recall_at_10"
]

REQUIRED_METHODS = [
    RetrievalMethod.BM25.value,
    RetrievalMethod.DUAL_ENCODER.value,
    RetrievalMethod.RAG.value
]

THROUGHPUT_FILE = "results/throughput_report.json"
RESULTS_CSV = "results/results.csv"


class TestCSVOutputSchema:
    """Contract tests for results.csv output schema."""
    
    def test_results_csv_exists(self, project_root):
        """Verify that results.csv is created after pipeline execution."""
        # Run the pipeline
        cli_main()
        
        results_path = Path(project_root) / RESULTS_CSV
        assert results_path.exists(), f"results.csv not found at {results_path}"
    
    def test_results_csv_has_required_columns(self, project_root):
        """Verify that results.csv contains all required columns."""
        # Run the pipeline
        cli_main()
        
        results_path = Path(project_root) / RESULTS_CSV
        
        with open(results_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            assert headers is not None, "CSV file is empty or has no headers"
            
            for col in REQUIRED_COLUMNS:
                assert col in headers, f"Required column '{col}' missing from CSV. Found: {headers}"
    
    def test_results_csv_has_required_methods(self, project_root):
        """Verify that results.csv contains rows for all required retrieval methods."""
        # Run the pipeline
        cli_main()
        
        results_path = Path(project_root) / RESULTS_CSV
        
        methods_found = set()
        
        with open(results_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                methods_found.add(row['method'])
        
        for method in REQUIRED_METHODS:
            assert method in methods_found, (
                f"Required method '{method}' missing from results.csv. "
                f"Found methods: {methods_found}"
            )
    
    def test_results_csv_numeric_columns_valid(self, project_root):
        """Verify that numeric columns contain valid float values."""
        # Run the pipeline
        cli_main()
        
        results_path = Path(project_root) / RESULTS_CSV
        
        numeric_cols = ["ndcg_at_10", "precision_at_10", "recall_at_10"]
        
        with open(results_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            row_count = 0
            
            for row in reader:
                row_count += 1
                for col in numeric_cols:
                    try:
                        value = float(row[col])
                        assert 0.0 <= value <= 1.0, (
                            f"Value {value} for {col} out of valid range [0, 1]"
                        )
                    except (ValueError, TypeError) as e:
                        pytest.fail(f"Invalid numeric value in column {col}: {row[col]} - {e}")
        
        assert row_count > 0, "No data rows found in results.csv"
    
    def test_results_csv_no_throughput_columns(self, project_root):
        """Verify that throughput metrics are NOT in results.csv (FR-007)."""
        # Run the pipeline
        cli_main()
        
        results_path = Path(project_root) / RESULTS_CSV
        
        throughput_keywords = ["throughput", "queries_per_hour", "total_time", "execution_time"]
        
        with open(results_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            
            for keyword in throughput_keywords:
                for header in headers:
                    assert keyword.lower() not in header.lower(), (
                        f"Throughput metric '{header}' found in results.csv. "
                        f"Throughput should be in {THROUGHPUT_FILE}"
                    )
    
    def test_throughput_report_separate_file(self, project_root):
        """Verify that throughput metrics are written to separate file."""
        # Run the pipeline
        cli_main()
        
        throughput_path = Path(project_root) / THROUGHPUT_FILE
        assert throughput_path.exists(), (
            f"Throughput report not found at {throughput_path}. "
            "Throughput metrics must be written to a separate JSON file."
        )
        
        with open(throughput_path, 'r', encoding='utf-8') as f:
            throughput_data = json.load(f)
        
        assert "queries_per_hour" in throughput_data, (
            "queries_per_hour missing from throughput report"
        )
        assert "total_queries" in throughput_data, (
            "total_queries missing from throughput report"
        )
        assert "total_time_seconds" in throughput_data, (
            "total_time_seconds missing from throughput report"
        )
    
    def test_results_csv_schema_completeness(self, project_root):
        """Comprehensive schema validation: all constraints together."""
        # Run the pipeline
        cli_main()
        
        results_path = Path(project_root) / RESULTS_CSV
        
        with open(results_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Check 1: At least one row per required method
        methods_in_rows = {row['method'] for row in rows}
        for method in REQUIRED_METHODS:
            assert method in methods_in_rows, f"Missing method: {method}"
        
        # Check 2: All required columns present
        headers = reader.fieldnames
        for col in REQUIRED_COLUMNS:
            assert col in headers, f"Missing column: {col}"
        
        # Check 3: No throughput columns
        for header in headers:
            assert "throughput" not in header.lower(), f"Throughput column found: {header}"
        
        # Check 4: All rows have valid data
        for row in rows:
            assert row['query_id'], "Empty query_id"
            assert row['method'], "Empty method"
            for col in ["ndcg_at_10", "precision_at_10", "recall_at_10"]:
                assert row[col], f"Empty {col}"
                try:
                    val = float(row[col])
                    assert 0.0 <= val <= 1.0
                except ValueError:
                    pytest.fail(f"Invalid numeric value in {col}: {row[col]}")