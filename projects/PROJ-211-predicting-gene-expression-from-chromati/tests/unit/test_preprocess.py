import pytest
import pandas as pd
import numpy as np
import os
import tempfile
import json
from preprocess import (
    DependencyError,
    load_data,
    save_data,
    filter_genes_zero_expression,
    impute_missing_values,
    identify_housekeeping_genes,
    identify_cell_type_specific_genes
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def create_test_csv(path, data, columns):
    df = pd.DataFrame(data, columns=columns)
    df.to_csv(path, index=False)
    return path

def test_filter_genes_zero_expression():
    """Test that genes with zero expression in all samples are filtered out."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.csv")
        output_path = os.path.join(tmpdir, "output.csv")
        
        # Create data: Gene A has expression, Gene B is all zeros
        data = [
            {"Gene": "Gene_A", "Sample1": 10, "Sample2": 20},
            {"Gene": "Gene_B", "Sample1": 0, "Sample2": 0},
            {"Gene": "Gene_C", "Sample1": 5, "Sample2": 0}
        ]
        create_test_csv(input_path, data, ["Gene", "Sample1", "Sample2"])
        
        filter_genes_zero_expression(input_path, output_path)
        
        result = pd.read_csv(output_path)
        
        assert len(result) == 2, "Expected 2 genes (A and C)"
        assert "Gene_B" not in result["Gene"].values

def test_impute_missing_values():
    """Test that missing values are imputed with column median."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.csv")
        output_path = os.path.join(tmpdir, "output.csv")
        
        # Create data with NaN
        data = [
            {"Gene": "Gene_A", "Sample1": 10.0, "Sample2": np.nan},
            {"Gene": "Gene_B", "Sample1": 20.0, "Sample2": 30.0},
            {"Gene": "Gene_C", "Sample1": 30.0, "Sample2": 40.0}
        ]
        create_test_csv(input_path, data, ["Gene", "Sample1", "Sample2"])
        
        impute_missing_values(input_path, output_path)
        
        result = pd.read_csv(output_path)
        
        # Median of Sample1 (10, 20, 30) is 20. Median of Sample2 (30, 40) is 35.
        # Gene_A Sample2 should be 35.0
        gene_a_row = result[result["Gene"] == "Gene_A"]
        assert np.isclose(gene_a_row["Sample2"].values[0], 35.0), "Imputation failed"

def test_identify_housekeeping_genes():
    """Test housekeeping gene identification based on CV < 0.2."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.csv")
        output_path = os.path.join(tmpdir, "output.csv")
        
        # Gene A: Low variation (Mean=100, Std~10 -> CV=0.1)
        # Gene B: High variation (Mean=50, Std~40 -> CV=0.8)
        # Gene C: Moderate variation (Mean=100, Std~30 -> CV=0.3)
        data = [
            {"Gene": "Gene_A", "S1": 90, "S2": 100, "S3": 110}, # CV ~ 0.1
            {"Gene": "Gene_B", "S1": 10, "S2": 50, "S3": 90},   # CV ~ 0.8
            {"Gene": "Gene_C", "S1": 70, "S2": 100, "S3": 130}  # CV ~ 0.3
        ]
        create_test_csv(input_path, data, ["Gene", "S1", "S2", "S3"])
        
        identify_housekeeping_genes(input_path, output_path, cv_threshold=0.2)
        
        result = pd.read_csv(output_path)
        
        assert len(result) == 1, f"Expected 1 housekeeping gene, got {len(result)}"
        assert result["Gene"].iloc[0] == "Gene_A"

def test_identify_cell_type_specific_genes():
    """Test cell-type-specific gene identification based on CV > 0.5."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.csv")
        output_path = os.path.join(tmpdir, "output.csv")
        
        # Gene A: Low CV (0.1)
        # Gene B: High CV (0.8)
        data = [
            {"Gene": "Gene_A", "S1": 100, "S2": 100, "S3": 100},
            {"Gene": "Gene_B", "S1": 10, "S2": 50, "S3": 90}
        ]
        create_test_csv(input_path, data, ["Gene", "S1", "S2", "S3"])
        
        identify_cell_type_specific_genes(input_path, output_path, cv_threshold=0.5)
        
        result = pd.read_csv(output_path)
        
        assert len(result) == 1, f"Expected 1 cell-type-specific gene, got {len(result)}"
        assert result["Gene"].iloc[0] == "Gene_B"

def test_dependency_error_on_blocked_input():
    """Test that DependencyError is raised when input is blocked."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.csv")
        blocked_path = f"{input_path}.blocked"
        output_path = os.path.join(tmpdir, "output.csv")
        
        # Create blocked marker
        with open(blocked_path, 'w') as f:
            json.dump({"status": "blocked", "reason": "Test reason"}, f)
        
        with pytest.raises(DependencyError) as excinfo:
            identify_housekeeping_genes(input_path, output_path)
        
        assert "blocked" in str(excinfo.value).lower()
