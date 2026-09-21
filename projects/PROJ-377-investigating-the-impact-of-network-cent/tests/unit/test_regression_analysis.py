import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from code.analysis.regression import (
    load_behavioral_data,
    load_centrality_or_pca_data,
    load_mean_fd_data,
    merge_all_data,
    fit_linear_regression,
)


class TestLoadBehavioralData:
    def test_loads_correctly(self):
        """Test that behavioral data is loaded correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "subject_scores.csv"
            data = {
                'subject_id': ['sub-001', 'sub-002', 'sub-003'],
                'pre_motor_score': [10.0, 12.0, 11.0],
                'post_motor_score': [15.0, 14.0, 16.0],
                'age': [25, 30, 28],
                'sex': ['M', 'F', 'M'],
                'improvement_score': [5.0, 2.0, 5.0]
            }
            df = pd.DataFrame(data)
            df.to_csv(data_path, index=False)

            result = load_behavioral_data(str(data_path))

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 3
            assert 'improvement_score' in result.columns

    def test_handles_missing_file(self):
        """Test behavior when file is missing."""
        with pytest.raises(FileNotFoundError):
            load_behavioral_data("/nonexistent/path/subject_scores.csv")


class TestLoadCentralityOrPCAData:
    def test_loads_global_centrality(self):
        """Test loading global centrality data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "global_scores.csv"
            data = {
                'subject_id': ['sub-001', 'sub-002'],
                'global_centrality': [0.5, 0.7],
                'model_type': ['Global', 'Global']
            }
            df = pd.DataFrame(data)
            df.to_csv(data_path, index=False)

            result = load_centrality_or_pca_data(str(data_path))

            assert isinstance(result, pd.DataFrame)
            assert 'global_centrality' in result.columns

    def test_loads_pca_data(self):
        """Test loading PCA-adjusted data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "model_predictors.csv"
            data = {
                'subject_id': ['sub-001', 'sub-002'],
                'PCA_Component': [0.3, 0.8],
                'model_type': ['PCA-Adjusted', 'PCA-Adjusted']
            }
            df = pd.DataFrame(data)
            df.to_csv(data_path, index=False)

            result = load_centrality_or_pca_data(str(data_path))

            assert isinstance(result, pd.DataFrame)
            assert 'PCA_Component' in result.columns


class TestLoadMeanFDData:
    def test_loads_correctly(self):
        """Test that mean FD data is loaded correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "fd_mean.csv"
            data = {
                'subject_id': ['sub-001', 'sub-002', 'sub-003'],
                'mean_fd': [0.15, 0.20, 0.18]
            }
            df = pd.DataFrame(data)
            df.to_csv(data_path, index=False)

            result = load_mean_fd_data(str(data_path))

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 3
            assert 'mean_fd' in result.columns


class TestMergeAllData:
    def test_merges_correctly(self):
        """Test that all data is merged correctly on subject_id."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create temporary files
            behavioral_path = Path(tmpdir) / "behavioral.csv"
            centrality_path = Path(tmpdir) / "centrality.csv"
            fd_path = Path(tmpdir) / "fd.csv"

            behavioral_df = pd.DataFrame({
                'subject_id': ['sub-001', 'sub-002', 'sub-003'],
                'improvement_score': [5.0, 2.0, 5.0],
                'age': [25, 30, 28],
                'sex': ['M', 'F', 'M']
            })
            behavioral_df.to_csv(behavioral_path, index=False)

            centrality_df = pd.DataFrame({
                'subject_id': ['sub-001', 'sub-002', 'sub-003'],
                'global_centrality': [0.5, 0.7, 0.6]
            })
            centrality_df.to_csv(centrality_path, index=False)

            fd_df = pd.DataFrame({
                'subject_id': ['sub-001', 'sub-002', 'sub-003'],
                'mean_fd': [0.15, 0.20, 0.18]
            })
            fd_df.to_csv(fd_path, index=False)

            result = merge_all_data(
                str(behavioral_path),
                str(centrality_path),
                str(fd_path)
            )

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 3
            assert all(col in result.columns for col in [
                'subject_id', 'improvement_score', 'global_centrality', 'mean_fd'
            ])

    def test_handles_mismatched_subjects(self):
        """Test behavior when subjects don't match across files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            behavioral_path = Path(tmpdir) / "behavioral.csv"
            centrality_path = Path(tmpdir) / "centrality.csv"
            fd_path = Path(tmpdir) / "fd.csv"

            # Only sub-001 and sub-002 in behavioral
            behavioral_df = pd.DataFrame({
                'subject_id': ['sub-001', 'sub-002'],
                'improvement_score': [5.0, 2.0]
            })
            behavioral_df.to_csv(behavioral_path, index=False)

            # All three subjects in centrality
            centrality_df = pd.DataFrame({
                'subject_id': ['sub-001', 'sub-002', 'sub-003'],
                'global_centrality': [0.5, 0.7, 0.6]
            })
            centrality_df.to_csv(centrality_path, index=False)

            # All three subjects in FD
            fd_df = pd.DataFrame({
                'subject_id': ['sub-001', 'sub-002', 'sub-003'],
                'mean_fd': [0.15, 0.20, 0.18]
            })
            fd_df.to_csv(fd_path, index=False)

            result = merge_all_data(
                str(behavioral_path),
                str(centrality_path),
                str(fd_path)
            )

            # Should only include subjects present in all files (inner join)
            assert len(result) == 2
            assert 'sub-003' not in result['subject_id'].values

class TestFitLinearRegression:
    def test_fits_model_correctly(self):
        """Test that linear regression fits correctly."""
        # Create mock merged data
        data = {
            'subject_id': [f'sub-{i:03d}' for i in range(1, 21)],
            'improvement_score': np.random.randn(20) * 2 + 5,
            'global_centrality': np.random.randn(20) * 0.1 + 0.5,
            'age': np.random.randint(20, 40, 20),
            'sex': np.random.choice(['M', 'F'], 20),
            'mean_fd': np.random.randn(20) * 0.05 + 0.15
        }
        df = pd.DataFrame(data)

        formula = "improvement_score ~ global_centrality + age + C(sex) + mean_fd"
        model_result = fit_linear_regression(df, formula)

        assert model_result is not None
        assert hasattr(model_result, 'params')
        assert len(model_result.params) > 0

    def test_handles_categorical_variables(self):
        """Test that categorical variables are handled correctly."""
        data = {
            'subject_id': [f'sub-{i:03d}' for i in range(1, 21)],
            'improvement_score': np.random.randn(20) * 2 + 5,
            'global_centrality': np.random.randn(20) * 0.1 + 0.5,
            'sex': np.random.choice(['M', 'F'], 20)
        }
        df = pd.DataFrame(data)

        formula = "improvement_score ~ global_centrality + C(sex)"
        model_result = fit_linear_regression(df, formula)

        assert model_result is not None
        # Should have parameters for both sex categories (one as reference)
        assert len(model_result.params) >= 2
