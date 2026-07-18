"""
Unit tests for data_loader module.
"""
import os
import tempfile
import pandas as pd
import numpy as np
import pytest
from code.data_loader import (
    validate_entrainment_csv,
    validate_topology_columns,
    generate_simulated_raw_matrices,
    N_SUBJECTS,
    N_NODES,
    RANDOM_SEED
)


class TestValidateEntrainmentCSV:
    def test_file_not_found(self):
        is_valid, error, df = validate_entrainment_csv("nonexistent.csv")
        assert is_valid is False
        assert "not found" in error
        assert df is None

    def test_missing_columns(self, tmp_path):
        csv_path = tmp_path / "test.csv"
        df = pd.DataFrame({"wrong_col": [1, 2, 3]})
        df.to_csv(csv_path, index=False)
        
        is_valid, error, df_out = validate_entrainment_csv(str(csv_path))
        assert is_valid is False
        assert "Missing required columns" in error

    def test_valid_entrainment(self, tmp_path):
        csv_path = tmp_path / "test.csv"
        df = pd.DataFrame({
            "subject_id": ["sub_001", "sub_002"],
            "entrainment_metric": [0.5, 0.7]
        })
        df.to_csv(csv_path, index=False)
        
        is_valid, error, df_out = validate_entrainment_csv(str(csv_path))
        assert is_valid is True
        assert error is None
        assert len(df_out) == 2

    def test_invalid_types(self, tmp_path):
        csv_path = tmp_path / "test.csv"
        df = pd.DataFrame({
            "subject_id": [1, 2],  # Should be string
            "entrainment_metric": ["a", "b"]  # Should be numeric
        })
        df.to_csv(csv_path, index=False)
        
        is_valid, error, df_out = validate_entrainment_csv(str(csv_path))
        assert is_valid is False


class TestValidateTopologyColumns:
    def test_file_not_found(self):
        is_valid, error, df = validate_topology_columns("nonexistent.csv")
        assert is_valid is False
        assert "not found" in error
        assert df is None

    def test_missing_columns(self, tmp_path):
        csv_path = tmp_path / "test.csv"
        df = pd.DataFrame({"wrong_col": [1, 2, 3]})
        df.to_csv(csv_path, index=False)
        
        is_valid, error, df_out = validate_topology_columns(str(csv_path))
        assert is_valid is False
        assert "Missing topology columns" in error

    def test_valid_topology(self, tmp_path):
        csv_path = tmp_path / "test.csv"
        df = pd.DataFrame({
            "subject_id": ["sub_001", "sub_002"],
            "clustering_coefficient": [0.3, 0.4],
            "characteristic_path_length": [2.1, 2.3]
        })
        df.to_csv(csv_path, index=False)
        
        is_valid, error, df_out = validate_topology_columns(str(csv_path))
        assert is_valid is True
        assert error is None
        assert len(df_out) == 2


class TestGenerateSimulatedRawMatrices:
    def test_generates_correct_structure(self, tmp_path):
        output_path = tmp_path / "test_matrices.csv"
        generate_simulated_raw_matrices(str(output_path))
        
        assert os.path.exists(output_path)
        
        df = pd.read_csv(output_path)
        
        # Check number of subjects
        assert len(df) == N_SUBJECTS
        
        # Check columns
        assert "subject_id" in df.columns
        assert "matrix_data" in df.columns
        
        # Check subject_id format
        assert df["subject_id"].iloc[0] == "sub_001"
        assert df["subject_id"].iloc[-1] == f"sub_{N_SUBJECTS:03d}"
        
        # Check matrix_data structure
        matrix_str = df["matrix_data"].iloc[0]
        # The list is stored as a string in CSV, we need to evaluate it
        matrix_list = eval(matrix_str)
        
        # Expected upper triangle size: 200 * 199 / 2 = 19900
        expected_size = (N_NODES * (N_NODES - 1)) // 2
        assert len(matrix_list) == expected_size
        
        # Check that all values are floats
        assert all(isinstance(v, float) for v in matrix_list)

    def test_deterministic_output(self, tmp_path):
        output_path1 = tmp_path / "test1.csv"
        output_path2 = tmp_path / "test2.csv"
        
        generate_simulated_raw_matrices(str(output_path1))
        generate_simulated_raw_matrices(str(output_path2))
        
        df1 = pd.read_csv(output_path1)
        df2 = pd.read_csv(output_path2)
        
        # Should be identical due to fixed seed
        assert len(df1) == len(df2)
        assert df1["subject_id"].tolist() == df2["subject_id"].tolist()
        
        # Check matrix data
        matrix1 = eval(df1["matrix_data"].iloc[0])
        matrix2 = eval(df2["matrix_data"].iloc[0])
        assert matrix1 == matrix2

    def test_correlation_matrix_properties(self, tmp_path):
        output_path = tmp_path / "test_matrices.csv"
        generate_simulated_raw_matrices(str(output_path))
        
        df = pd.read_csv(output_path)
        
        # Reconstruct a correlation matrix from upper triangle to verify properties
        n = N_NODES
        matrix_str = df["matrix_data"].iloc[0]
        upper_tri = eval(matrix_str)
        
        # Reconstruct full matrix
        corr_matrix = np.zeros((n, n))
        indices = np.triu_indices(n, k=1)
        corr_matrix[indices] = upper_tri
        corr_matrix = corr_matrix + corr_matrix.T
        np.fill_diagonal(corr_matrix, 1.0)
        
        # Verify diagonal is 1
        assert np.allclose(np.diag(corr_matrix), 1.0)
        
        # Verify symmetry
        assert np.allclose(corr_matrix, corr_matrix.T)
        
        # Verify values are in [-1, 1]
        assert np.all(corr_matrix >= -1.0)
        assert np.all(corr_matrix <= 1.0)