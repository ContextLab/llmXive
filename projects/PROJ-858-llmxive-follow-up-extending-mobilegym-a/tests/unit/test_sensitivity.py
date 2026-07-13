import pytest
import json
import os
import sys
from pathlib import Path
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis.sensitivity import (
    calculate_vector_scalar,
    compute_pearson_correlation,
    align_data,
    analyze_sensitivity
)

class TestCalculateVectorScalar:
    def test_all_ones(self):
        vector = [1, 1, 1, 1]
        assert calculate_vector_scalar(vector) == 4.0

    def test_all_zeros(self):
        vector = [0, 0, 0, 0]
        assert calculate_vector_scalar(vector) == 0.0

    def test_mixed(self):
        vector = [1, 0, 1, 0, 1]
        assert calculate_vector_scalar(vector) == 3.0

    def test_invalid_vector(self):
        with pytest.raises(ValueError):
            calculate_vector_scalar([1, 2, 0, 1])

class TestPearsonCorrelation:
    def test_perfect_positive(self):
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        r = compute_pearson_correlation(x, y)
        assert abs(r - 1.0) < 1e-6

    def test_perfect_negative(self):
        x = [1, 2, 3, 4, 5]
        y = [10, 8, 6, 4, 2]
        r = compute_pearson_correlation(x, y)
        assert abs(r - (-1.0)) < 1e-6

    def test_no_correlation(self):
        # Random-ish data with no clear correlation
        x = [1, 2, 3, 4, 5]
        y = [5, 1, 4, 2, 3]
        r = compute_pearson_correlation(x, y)
        # Should be close to 0
        assert abs(r) < 0.2

    def test_insufficient_data(self):
        with pytest.raises(ValueError):
            compute_pearson_correlation([1], [2])

class TestAlignData:
    def test_basic_alignment(self):
        coverage = [
            {"task_id": "A", "vector": [1, 1, 0]},
            {"task_id": "B", "vector": [0, 1, 1]},
            {"task_id": "C", "vector": [1, 0, 1]}
        ]
        validation = [
            {"task_id": "A", "success_rate": 0.8},
            {"task_id": "B", "success_rate": 0.5},
            {"task_id": "C", "success_rate": 0.6}
        ]
        
        scalars, rates = align_data(coverage, validation)
        
        assert len(scalars) == 3
        assert len(rates) == 3
        
        # Check specific values
        assert 2.0 in scalars  # A and C have sum 2
        assert 0.8 in rates

    def test_missing_task(self):
        coverage = [
            {"task_id": "A", "vector": [1, 1, 0]},
            {"task_id": "B", "vector": [0, 1, 1]}
        ]
        validation = [
            {"task_id": "A", "success_rate": 0.8}
            # B is missing
        ]
        
        scalars, rates = align_data(coverage, validation)
        
        assert len(scalars) == 1
        assert len(rates) == 1
        assert scalars[0] == 2.0

class TestSensitivityAnalysis:
    def test_end_to_end_with_temp_files(self, tmp_path):
        # Create temporary files
        coverage_file = tmp_path / "coverage.json"
        validation_file = tmp_path / "validation.json"
        output_file = tmp_path / "report.json"
        
        # Write test data
        coverage_data = [
            {"task_id": "t1", "vector": [1, 1, 1]},
            {"task_id": "t2", "vector": [0, 0, 0]},
            {"task_id": "t3", "vector": [1, 0, 1]}
        ]
        validation_data = [
            {"task_id": "t1", "success_rate": 0.9},
            {"task_id": "t2", "success_rate": 0.1},
            {"task_id": "t3", "success_rate": 0.5}
        ]
        
        with open(coverage_file, 'w') as f:
            json.dump(coverage_data, f)
        with open(validation_file, 'w') as f:
            json.dump(validation_data, f)
        
        # Run analysis
        results = analyze_sensitivity(
            str(coverage_file),
            str(validation_file),
            str(output_file)
        )
        
        # Verify output file exists
        assert output_file.exists()
        
        # Verify results structure
        assert "pearson_r" in results
        assert "status" in results
        assert "message" in results
        
        # With this data (perfect correlation between count and rate), r should be 1.0
        assert abs(results["pearson_r"] - 1.0) < 1e-6
        assert results["status"] == "VALIDATED"