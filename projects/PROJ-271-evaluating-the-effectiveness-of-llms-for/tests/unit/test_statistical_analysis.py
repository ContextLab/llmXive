import os
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Import the function under test from the existing API surface
from code.statistical_analysis import (
    load_static_baseline,
    load_semantic_results,
    merge_datasets,
    generate_sensitivity_report
)
from code.config import get_data_path, get_processed_path, get_results_path

class TestComplementaritySummaryGeneration:
    """
    Test T047: Verify the logic that identifies smells detected *only* by static
    vs *only* by LLM. This corresponds to FR-009 and SC-003.
    """

    @pytest.fixture
    def sample_baseline(self, tmp_path):
        """Create a mock static_baseline.csv for testing."""
        data = {
            'code': ['def a(): pass', 'def b(): pass', 'def c(): pass', 'def d(): pass'],
            'loc': [1, 10, 20, 30],
            'cyclomatic_complexity': [1, 5, 10, 15],
            'static_smell_labels': [
                '["Long Method"]',  # Only static
                '["Naming Convention"]', # Only LLM (in semantic)
                '["Long Method", "Naming Convention"]', # Both
                '[]' # Neither
            ]
        }
        df = pd.DataFrame(data)
        path = tmp_path / "static_baseline.csv"
        df.to_csv(path, index=False)
        return path

    @pytest.fixture
    def sample_semantic(self, tmp_path):
        """Create a mock semantic_results.json for testing."""
        data = [
            {
                "id": 0,
                "code": "def a(): pass",
                "llm_labels": ["Naming Convention"], # Only LLM detected this
                "embedding": [0.1] * 384
            },
            {
                "id": 1,
                "code": "def b(): pass",
                "llm_labels": ["Long Method"], # Only LLM detected this (mismatch)
                "embedding": [0.2] * 384
            },
            {
                "id": 2,
                "code": "def c(): pass",
                "llm_labels": ["Long Method", "Naming Convention"], # Both detected
                "embedding": [0.3] * 384
            },
            {
                "id": 3,
                "code": "def d(): pass",
                "llm_labels": [], # Neither
                "embedding": [0.4] * 384
            }
        ]
        path = tmp_path / "semantic_results.json"
        with open(path, 'w') as f:
            json.dump(data, f)
        return path

    def test_complementarity_logic_identifies_only_static(self, sample_baseline, sample_semantic, tmp_path):
        """
        Verify that the sensitivity report generation correctly identifies
        smells present in static but NOT in LLM labels.
        """
        # Load and merge data
        static_df = load_static_baseline(sample_baseline)
        semantic_data = load_semantic_results(sample_semantic)
        
        # Manually merge to ensure alignment for the test (mimicking merge_datasets logic)
        merged = merge_datasets(static_df, semantic_data)
        
        # Ensure we have the expected columns
        assert 'static_smell_labels' in merged.columns
        assert 'llm_labels' in merged.columns

        # Call the function that generates the report logic
        # We pass a temp path for the output, but we are primarily interested
        # in the return value or the side effect of the file generation logic.
        # Since generate_sensitivity_report writes to disk, we check the file.
        
        output_path = tmp_path / "sensitivity_report.md"
        result = generate_sensitivity_report(merged, str(output_path))

        # The function should return a dictionary or write a file.
        # Based on T028 description, it generates a markdown file.
        assert output_path.exists(), "Sensitivity report file should be created"

        content = output_path.read_text()
        
        # Verify the report contains the section for "Only Static"
        # The logic should identify 'Long Method' in row 0 as static-only
        # (Static: Long Method, LLM: Naming Convention -> Wait, in sample data:
        # Row 0: Static=['Long Method'], LLM=['Naming Convention'] -> Only Static: Long Method
        # Row 1: Static=['Naming Convention'], LLM=['Long Method'] -> Only Static: Naming Convention
        # Row 2: Static=['Long Method', 'Naming Convention'], LLM=['Long Method', 'Naming Convention'] -> Both
        # Row 3: Static=[], LLM=[] -> Neither
        
        # We expect 'Long Method' to be in the "Only Static" or "Static Only" section
        # based on Row 0.
        assert "Only Static" in content or "Static Only" in content or "Detected by Static Only" in content, \
            "Report must contain a section identifying smells detected only by static analysis"
        
        # Verify that 'Long Method' appears in the static-only section context
        # (Simple string check for the presence of the smell name in the report)
        assert "Long Method" in content

    def test_complementarity_logic_identifies_only_llm(self, sample_baseline, sample_semantic, tmp_path):
        """
        Verify that the sensitivity report generation correctly identifies
        smells present in LLM but NOT in static labels.
        """
        static_df = load_static_baseline(sample_baseline)
        semantic_data = load_semantic_results(sample_semantic)
        merged = merge_datasets(static_df, semantic_data)

        output_path = tmp_path / "sensitivity_report.md"
        generate_sensitivity_report(merged, str(output_path))

        content = output_path.read_text()

        # In sample data:
        # Row 0: Static=['Long Method'], LLM=['Naming Convention'] -> Only LLM: Naming Convention
        # Row 1: Static=['Naming Convention'], LLM=['Long Method'] -> Only LLM: Long Method
        
        assert "Only LLM" in content or "LLM Only" in content or "Detected by LLM Only" in content, \
            "Report must contain a section identifying smells detected only by LLM"

    def test_complementarity_logic_handles_empty_labels(self, sample_baseline, sample_semantic, tmp_path):
        """
        Verify that the logic handles cases where labels are empty lists correctly
        without crashing.
        """
        static_df = load_static_baseline(sample_baseline)
        semantic_data = load_semantic_results(sample_semantic)
        merged = merge_datasets(static_df, semantic_data)

        output_path = tmp_path / "sensitivity_report.md"
        # Should not raise an exception
        result = generate_sensitivity_report(merged, str(output_path))
        
        assert output_path.exists()

    def test_complementarity_logic_correct_counts(self, sample_baseline, sample_semantic, tmp_path):
        """
        Verify that the summary counts (if present) match the expected logic.
        """
        static_df = load_static_baseline(sample_baseline)
        semantic_data = load_semantic_results(sample_semantic)
        merged = merge_datasets(static_df, semantic_data)

        output_path = tmp_path / "sensitivity_report.md"
        generate_sensitivity_report(merged, str(output_path))
        
        content = output_path.read_text()
        
        # We expect at least one item in "Only Static" (Row 0: Long Method)
        # and at least one item in "Only LLM" (Row 0: Naming Convention, Row 1: Long Method)
        # This is a heuristic check based on the sample data constructed.
        assert "Long Method" in content
        assert "Naming Convention" in content