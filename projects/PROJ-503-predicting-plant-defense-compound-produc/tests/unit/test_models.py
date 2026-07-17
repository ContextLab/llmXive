"""
Unit tests for the data model classes.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from code.models import ExpressionMatrix, MetaboliteMatrix, FeatureSet, ModelArtifact


class TestExpressionMatrix:
    def setup_method(self):
        """Create a sample expression matrix for testing."""
        data = pd.DataFrame(
            {
                "sample_1": [1.0, 2.0, 3.0],
                "sample_2": [1.5, 2.5, 3.5],
                "sample_3": [1.2, 2.2, 3.2]
            },
            index=["gene_A", "gene_B", "gene_C"]
        )
        self.matrix = ExpressionMatrix(data=data)
    
    def test_initialization(self):
        assert not self.matrix.data.empty
        assert self.matrix.get_dimensions() == (3, 3)
    
    def test_get_gene_ids(self):
        genes = self.matrix.get_gene_ids()
        assert set(genes) == {"gene_A", "gene_B", "gene_C"}
    
    def test_get_sample_ids(self):
        samples = self.matrix.get_sample_ids()
        assert set(samples) == {"sample_1", "sample_2", "sample_3"}
    
    def test_filter_genes(self):
        filtered = self.matrix.filter_genes(["gene_A", "gene_B"])
        assert filtered.get_dimensions() == (2, 3)
        assert "gene_C" not in filtered.get_gene_ids()
    
    def test_filter_samples(self):
        filtered = self.matrix.filter_samples(["sample_1", "sample_2"])
        assert filtered.get_dimensions() == (3, 2)
        assert "sample_3" not in filtered.get_sample_ids()
    
    def test_to_csv_and_from_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_expr.csv"
            self.matrix.to_csv(filepath)
            loaded = ExpressionMatrix.from_csv(filepath)
            assert loaded.get_dimensions() == self.matrix.get_dimensions()
            pd.testing.assert_frame_equal(loaded.data, self.matrix.data)
    
    def test_to_dict_and_from_dict(self):
        data_dict = self.matrix.to_dict()
        loaded = ExpressionMatrix.from_dict(data_dict)
        assert loaded.get_dimensions() == self.matrix.get_dimensions()
        pd.testing.assert_frame_equal(loaded.data, self.matrix.data)


class TestMetaboliteMatrix:
    def setup_method(self):
        """Create a sample metabolite matrix for testing."""
        data = pd.DataFrame(
            {
                "sample_1": [10.0, 20.0],
                "sample_2": [12.0, 22.0],
                "sample_3": [11.0, 21.0]
            },
            index=["metabolite_X", "metabolite_Y"]
        )
        self.matrix = MetaboliteMatrix(data=data)
    
    def test_initialization(self):
        assert not self.matrix.data.empty
        assert self.matrix.get_dimensions() == (2, 3)
    
    def test_log_transform(self):
        transformed = self.matrix.log_transform()
        assert transformed.get_dimensions() == (2, 3)
        # Check that values are actually transformed (log(10+eps) ~ 2.3)
        assert transformed.data.iloc[0, 0] < 10.0
    
    def test_filter_metabolites(self):
        filtered = self.matrix.filter_metabolites(["metabolite_X"])
        assert filtered.get_dimensions() == (1, 3)
    
    def test_to_csv_and_from_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_met.csv"
            self.matrix.to_csv(filepath)
            loaded = MetaboliteMatrix.from_csv(filepath)
            assert loaded.get_dimensions() == self.matrix.get_dimensions()
            pd.testing.assert_frame_equal(loaded.data, self.matrix.data)


class TestFeatureSet:
    def setup_method(self):
        """Create a sample feature set for testing."""
        data = pd.DataFrame(
            {
                "sample_1": [1.0, 2.0],
                "sample_2": [1.5, 2.5]
            },
            index=["feature_1", "feature_2"]
        )
        feature_info = {
            "feature_1": {"pathway": "terpenoid"},
            "feature_2": {"pathway": "alkaloid"}
        }
        self.feature_set = FeatureSet(data=data, feature_info=feature_info)
    
    def test_initialization(self):
        assert not self.feature_set.data.empty
        assert self.feature_set.get_dimensions() == (2, 2)
    
    def test_get_pathway_info(self):
        info = self.feature_set.get_pathway_info("feature_1")
        assert info is not None
        assert info["pathway"] == "terpenoid"
    
    def test_filter_samples(self):
        filtered = self.feature_set.filter_samples(["sample_1"])
        assert filtered.get_dimensions() == (2, 1)


class TestModelArtifact:
    def setup_method(self):
        """Create a mock model artifact for testing."""
        # Create a simple mock model
        class MockModel:
            coef_ = np.array([0.5, -0.2])
        
        metrics = {
            "rmse": 0.5,
            "pearson_r": 0.8,
            "p_value": 0.01
        }
        self.artifact = ModelArtifact(
            model=MockModel(),
            metrics=metrics,
            feature_ids=["f1", "f2"],
            target_id="metabolite_A"
        )
    
    def test_initialization(self):
        assert self.artifact.target_id == "metabolite_A"
        assert self.artifact.get_rmse() == 0.5
        assert self.artifact.get_pearson_r() == 0.8
    
    def test_get_feature_importance(self):
        importance = self.artifact.get_feature_importance()
        assert importance is not None
        assert "f1" in importance
        assert "f2" in importance
    
    def test_save_and_load_pickle(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "model.pkl"
            self.artifact.save_pickle(filepath)
            loaded = ModelArtifact.load_pickle(filepath)
            assert loaded.target_id == self.artifact.target_id
            assert loaded.get_rmse() == self.artifact.get_rmse()
    
    def test_save_and_load_json_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "model_meta.json"
            self.artifact.save_json_metadata(filepath)
            loaded = ModelArtifact.load_json_metadata(filepath)
            assert loaded["target_id"] == self.artifact.target_id
            assert loaded["metrics"]["rmse"] == self.artifact.get_rmse()