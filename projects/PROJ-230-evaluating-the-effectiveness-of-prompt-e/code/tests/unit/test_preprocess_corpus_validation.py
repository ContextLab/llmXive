import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path
from src.ingestion.preprocess_corpus import process_and_save_corpus
from src.ingestion.validate_dataset import is_valid_entry, validate_and_filter_dataset

class TestPreprocessCorpusValidation:
    
    def test_is_valid_entry_missing_code(self):
        """Test that entries with missing code are flagged invalid."""
        entry = {"python_code": None, "javascript_code": "console.log('hi')"}
        assert not is_valid_entry(entry)

        entry = {"python_code": "print('hi')", "javascript_code": None}
        assert not is_valid_entry(entry)

        entry = {"python_code": "", "javascript_code": "console.log('hi')"}
        assert not is_valid_entry(entry)

    def test_is_valid_entry_non_string_type(self):
        """Test that entries with non-string code are flagged invalid."""
        entry = {"python_code": 123, "javascript_code": "console.log('hi')"}
        assert not is_valid_entry(entry)

        entry = {"python_code": "print('hi')", "javascript_code": 456}
        assert not is_valid_entry(entry)

        entry = {"python_code": ["print('hi')"], "javascript_code": "console.log('hi')"}
        assert not is_valid_entry(entry)

    def test_is_valid_entry_valid(self):
        """Test that valid entries pass."""
        entry = {"python_code": "print('hi')", "javascript_code": "console.log('hi')"}
        assert is_valid_entry(entry)

    def test_validate_and_filter_dataset(self):
        """Test the filtering logic on a DataFrame."""
        data = [
            {"python_code": "a", "javascript_code": "b"}, # Valid
            {"python_code": None, "javascript_code": "b"}, # Invalid
            {"python_code": "c", "javascript_code": 123}, # Invalid
            {"python_code": "d", "javascript_code": "e"}, # Valid
        ]
        df = pd.DataFrame(data)
        
        valid_df, count, reasons = validate_and_filter_dataset(df)
        
        assert len(valid_df) == 2
        assert count == 2
        assert len(reasons) == 2

    def test_process_and_save_corpus_excludes_invalid(self):
        """Integration test: process_and_save_corpus must exclude invalid entries and write log."""
        data = [
            {"python_code": "valid_py_1", "javascript_code": "valid_js_1"},
            {"python_code": None, "javascript_code": "valid_js_2"},
            {"python_code": "valid_py_3", "javascript_code": 123},
            {"python_code": "", "javascript_code": "valid_js_4"},
            {"python_code": "valid_py_5", "javascript_code": "valid_js_5"},
        ]
        df = pd.DataFrame(data)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_csv = Path(tmpdir) / "corpus.csv"
            exclusion_log = Path(tmpdir) / "exclusion_log.txt"
            
            result_df = process_and_save_corpus(
                raw_dataset=df,
                output_path=output_csv,
                raw_cache_path=Path(tmpdir) / "raw",
                exclusion_log_path=exclusion_log,
                memory_limit_gb=7.0
            )

            # Assertions
            assert output_csv.exists(), "Output CSV not created"
            assert exclusion_log.exists(), "Exclusion log not created"

            # Check result
            assert len(result_df) == 2, f"Expected 2 valid rows, got {len(result_df)}"
            
            # Check exclusion log content
            log_content = exclusion_log.read_text()
            assert "3" in log_content, "Exclusion log should mention 3 excluded entries"
            assert "excluded" in log_content.lower() or "Invalid" in log_content

            # Verify CSV content
            saved_df = pd.read_csv(output_csv)
            assert len(saved_df) == 2
            # Check specific valid rows
            assert "valid_py_1" in saved_df["python_code"].values
            assert "valid_py_5" in saved_df["python_code"].values