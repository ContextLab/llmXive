"""
Unit tests for the UMAP visualization module.
"""
import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path if necessary
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.viz.plots import (
    load_umap_embedding,
    load_resistance_labels,
    generate_umap_scatter_plot,
    run_umap_viz_pipeline
)
from src.config import get_data_processed_path


class TestLoadUmEmbedding:
    """Tests for load_umap_embedding function."""

    def test_load_umap_embedding_success(self, tmp_path):
        """Test successful loading of UMAP embedding."""
        # Create a mock embedding file
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        embedding_file = processed_dir / "umap_embedding.csv"
        
        mock_data = pd.DataFrame({
            'InChIKey': ['key1', 'key2', 'key3'],
            'umap_1': [0.1, 0.2, 0.3],
            'umap_2': [0.4, 0.5, 0.6]
        })
        mock_data.to_csv(embedding_file, index=False)
        
        with patch('src.viz.plots.get_data_processed_path', return_value=processed_dir):
            result = load_umap_embedding()
            
        assert isinstance(result, pd.DataFrame)
        assert 'umap_1' in result.columns
        assert 'umap_2' in result.columns
        assert len(result) == 3

    def test_load_umap_embedding_file_not_found(self, tmp_path):
        """Test error when embedding file does not exist."""
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        with patch('src.viz.plots.get_data_processed_path', return_value=processed_dir):
            with pytest.raises(FileNotFoundError):
                load_umap_embedding()

    def test_load_umap_embedding_missing_columns(self, tmp_path):
        """Test error when required columns are missing."""
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        embedding_file = processed_dir / "umap_embedding.csv"
        
        mock_data = pd.DataFrame({
            'InChIKey': ['key1', 'key2'],
            'other_col': [1, 2]
        })
        mock_data.to_csv(embedding_file, index=False)
        
        with patch('src.viz.plots.get_data_processed_path', return_value=processed_dir):
            with pytest.raises(ValueError):
                load_umap_embedding()


class TestLoadResistanceLabels:
    """Tests for load_resistance_labels function."""

    def test_load_resistance_labels_success(self, tmp_path):
        """Test successful loading of resistance labels."""
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        descriptors_file = processed_dir / "descriptors.csv"
        
        mock_data = pd.DataFrame({
            'InChIKey': ['key1', 'key2', 'key3'],
            'resistance_label': ['High', 'Low', 'High'],
            'descriptor1': [1.0, 2.0, 3.0]
        })
        mock_data.to_csv(descriptors_file, index=False)
        
        with patch('src.viz.plots.get_data_processed_path', return_value=processed_dir):
            result = load_resistance_labels()
            
        assert isinstance(result, pd.DataFrame)
        assert 'InChIKey' in result.columns
        assert 'resistance_label' in result.columns
        assert len(result) == 3

    def test_load_resistance_labels_no_file(self, tmp_path):
        """Test returning None when descriptors file does not exist."""
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        with patch('src.viz.plots.get_data_processed_path', return_value=processed_dir):
            result = load_resistance_labels()
            
        assert result is None

    def test_load_resistance_labels_no_label_column(self, tmp_path):
        """Test returning None when no resistance label column found."""
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        descriptors_file = processed_dir / "descriptors.csv"
        
        mock_data = pd.DataFrame({
            'InChIKey': ['key1', 'key2'],
            'other_col': [1.0, 2.0]
        })
        mock_data.to_csv(descriptors_file, index=False)
        
        with patch('src.viz.plots.get_data_processed_path', return_value=processed_dir):
            result = load_resistance_labels()
            
        assert result is None


class TestGenerateUmEmbeddingScatterPlot:
    """Tests for generate_umap_scatter_plot function."""

    def test_generate_plot_with_labels(self, tmp_path):
        """Test generating plot with resistance labels."""
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        output_file = processed_dir / "test_plot.png"
        
        embedding_df = pd.DataFrame({
            'InChIKey': ['key1', 'key2', 'key3'],
            'umap_1': [0.1, 0.2, 0.3],
            'umap_2': [0.4, 0.5, 0.6]
        })
        
        labels_df = pd.DataFrame({
            'InChIKey': ['key1', 'key2', 'key3'],
            'resistance_label': ['High', 'Low', 'High']
        })
        
        result_path = generate_umap_scatter_plot(
            embedding_df, 
            labels_df, 
            output_path=output_file
        )
        
        assert result_path.exists()
        assert result_path == output_file

    def test_generate_plot_without_labels(self, tmp_path):
        """Test generating plot without resistance labels."""
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        output_file = processed_dir / "test_plot.png"
        
        embedding_df = pd.DataFrame({
            'InChIKey': ['key1', 'key2', 'key3'],
            'umap_1': [0.1, 0.2, 0.3],
            'umap_2': [0.4, 0.5, 0.6]
        })
        
        result_path = generate_umap_scatter_plot(
            embedding_df, 
            labels_df=None, 
            output_path=output_file
        )
        
        assert result_path.exists()
        assert result_path == output_file

    def test_generate_plot_creates_directory(self, tmp_path):
        """Test that output directory is created if it doesn't exist."""
        processed_dir = tmp_path / "data" / "processed" / "subdir"
        output_file = processed_dir / "test_plot.png"
        
        embedding_df = pd.DataFrame({
            'InChIKey': ['key1'],
            'umap_1': [0.1],
            'umap_2': [0.2]
        })
        
        result_path = generate_umap_scatter_plot(
            embedding_df, 
            labels_df=None, 
            output_path=output_file
        )
        
        assert result_path.exists()
        assert processed_dir.exists()


class TestRunUmEmbeddingVizPipeline:
    """Tests for run_umap_viz_pipeline function."""

    @patch('src.viz.plots.load_umap_embedding')
    @patch('src.viz.plots.load_resistance_labels')
    @patch('src.viz.plots.generate_umap_scatter_plot')
    def test_run_pipeline_calls_functions(self, mock_gen, mock_load_labels, mock_load_emb, tmp_path):
        """Test that pipeline calls the correct functions."""
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        mock_load_emb.return_value = pd.DataFrame({'umap_1': [1], 'umap_2': [2]})
        mock_load_labels.return_value = None
        mock_gen.return_value = processed_dir / "umap_scatter.png"
        
        with patch('src.viz.plots.get_data_processed_path', return_value=processed_dir):
            result = run_umap_viz_pipeline()
            
        mock_load_emb.assert_called_once()
        mock_load_labels.assert_called_once()
        mock_gen.assert_called_once()
        assert result == processed_dir / "umap_scatter.png"