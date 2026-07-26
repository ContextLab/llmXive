"""
Unit tests for the data model classes.
"""
import pytest
import pandas as pd
import numpy as np
import json
import tempfile
import os

from code.models.expression_matrix import ExpressionMatrix
from code.models.metabolite_matrix import MetaboliteMatrix
from code.models.feature_set import FeatureSet
from code.models.model_artifact import ModelArtifact


class TestExpressionMatrix:
    def test_init_empty(self):
        mat = ExpressionMatrix()
        assert len(mat.data) == 0
        assert list(mat.data.columns) == ['gene_id', 'sample_id', 'value']

    def test_init_with_data(self):
        df = pd.DataFrame({
            'gene_id': ['G1', 'G2'],
            'sample_id': ['S1', 'S1'],
            'value': [10.5, 20.0]
        })
        mat = ExpressionMatrix(df)
        assert len(mat) == 2
        assert 'G1' in mat.get_unique_genes()
        assert 'S1' in mat.get_unique_samples()

    def test_invalid_columns(self):
        df = pd.DataFrame({'wrong': [1]})
        with pytest.raises(ValueError):
            ExpressionMatrix(df)

    def test_save_and_load(self):
        df = pd.DataFrame({
            'gene_id': ['G1'],
            'sample_id': ['S1'],
            'value': [5.0]
        })
        mat = ExpressionMatrix(df)
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            fname = f.name
        try:
            mat.save(fname)
            mat2 = ExpressionMatrix.load(fname)
            assert len(mat2) == 1
            assert mat2.data.iloc[0]['gene_id'] == 'G1'
        finally:
            os.remove(fname)

    def test_filter_by_samples(self):
        df = pd.DataFrame({
            'gene_id': ['G1', 'G2'],
            'sample_id': ['S1', 'S2'],
            'value': [1.0, 2.0]
        })
        mat = ExpressionMatrix(df)
        filtered = mat.filter_by_samples(['S1'])
        assert len(filtered) == 1
        assert filtered.data.iloc[0]['sample_id'] == 'S1'

    def test_to_pivot(self):
        df = pd.DataFrame({
            'gene_id': ['G1', 'G1'],
            'sample_id': ['S1', 'S2'],
            'value': [10.0, 20.0]
        })
        mat = ExpressionMatrix(df)
        pivot = mat.to_pivot()
        assert pivot.loc['G1', 'S1'] == 10.0
        assert pivot.loc['G1', 'S2'] == 20.0


class TestMetaboliteMatrix:
    def test_init_empty(self):
        mat = MetaboliteMatrix()
        assert len(mat.data) == 0
        assert list(mat.data.columns) == ['metabolite_id', 'sample_id', 'value']

    def test_init_with_data(self):
        df = pd.DataFrame({
            'metabolite_id': ['M1', 'M2'],
            'sample_id': ['S1', 'S1'],
            'value': [5.5, 6.0]
        })
        mat = MetaboliteMatrix(df)
        assert len(mat) == 2
        assert 'M1' in mat.get_unique_metabolites()

    def test_save_and_load(self):
        df = pd.DataFrame({
            'metabolite_id': ['M1'],
            'sample_id': ['S1'],
            'value': [3.0]
        })
        mat = MetaboliteMatrix(df)
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            fname = f.name
        try:
            mat.save(fname)
            mat2 = MetaboliteMatrix.load(fname)
            assert len(mat2) == 1
        finally:
            os.remove(fname)


class TestFeatureSet:
    def test_init(self):
        fs = FeatureSet(gene_ids=['G1', 'G2'])
        assert 'G1' in fs.gene_ids
        assert len(fs) == 2

    def test_add_remove(self):
        fs = FeatureSet()
        fs.add_gene('G1')
        assert fs.contains('G1')
        fs.remove_gene('G1')
        assert not fs.contains('G1')

    def test_save_and_load(self):
        fs = FeatureSet(gene_ids=['G1', 'G2'], metadata={'source': 'test'})
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            fname = f.name
        try:
            fs.save(fname)
            with open(fname, 'r') as f:
                data = json.load(f)
            assert 'G1' in data['gene_ids']
            assert data['metadata']['source'] == 'test'
        finally:
            os.remove(fname)

    def test_set_operations(self):
        fs1 = FeatureSet(['G1', 'G2'])
        fs2 = FeatureSet(['G2', 'G3'])
        assert fs1.intersect(fs2).to_list() == ['G2']
        assert set(fs1.union(fs2).to_list()) == {'G1', 'G2', 'G3'}
        assert fs1.difference(fs2).to_list() == ['G1']


class TestModelArtifact:
    def test_init(self):
        # Mock model object
        class MockModel:
            pass
        model = MockModel()
        artifact = ModelArtifact(model=model, metrics={'rmse': 0.5})
        assert artifact.metrics['rmse'] == 0.5
        assert artifact.model is model

    def test_save_and_load(self):
        class MockModel:
            pass
        model = MockModel()
        artifact = ModelArtifact(
            model=model,
            coefficients=np.array([1.0, 2.0]),
            metrics={'r2': 0.9}
        )
        with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
            fname = f.name
        try:
            artifact.save(fname)
            loaded = ModelArtifact.load(fname)
            assert loaded.metrics['r2'] == 0.9
            np.testing.assert_array_equal(loaded.coefficients, [1.0, 2.0])
        finally:
            os.remove(fname)