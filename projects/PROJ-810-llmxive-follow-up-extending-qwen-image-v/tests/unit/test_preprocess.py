import json
import os
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np
from PIL import Image

from data.preprocess import (
    load_raw_dataset,
    extract_ground_truth_labels,
    derive_heuristic_labels,
    run_extraction
)


class TestLoadRawDataset:
    """Tests for load_raw_dataset function."""

    def test_load_parquet_file_exists(self):
        """Test loading a valid parquet file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a sample parquet file
            sample_df = pd.DataFrame({
                'image_path': ['img1.jpg', 'img2.jpg'],
                'bbox_x_min': [10, 20],
                'bbox_y_min': [15, 25],
                'bbox_width': [100, 120],
                'bbox_height': [80, 90],
                'modality_label': ['text', 'image']
            })
            parquet_path = Path(tmpdir) / 'sample.parquet'
            sample_df.to_parquet(parquet_path)

            # Test loading
            result = load_raw_dataset(str(parquet_path))
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 2
            assert 'modality_label' in result.columns

    def test_load_parquet_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            non_existent_path = Path(tmpdir) / 'non_existent.parquet'
            with pytest.raises(FileNotFoundError):
                load_raw_dataset(str(non_existent_path))

    def test_load_empty_parquet(self):
        """Test loading an empty parquet file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_df = pd.DataFrame(columns=[
                'image_path', 'bbox_x_min', 'bbox_y_min',
                'bbox_width', 'bbox_height', 'modality_label'
            ])
            parquet_path = Path(tmpdir) / 'empty.parquet'
            empty_df.to_parquet(parquet_path)

            result = load_raw_dataset(str(parquet_path))
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 0


class TestExtractGroundTruthLabels:
    """Tests for extract_ground_truth_labels function."""

    def test_extract_labels_basic(self):
        """Test basic extraction of ground truth labels."""
        df = pd.DataFrame({
            'image_id': ['img1', 'img2'],
            'bbox_x_min': [10, 20],
            'bbox_y_min': [15, 25],
            'bbox_width': [100, 120],
            'bbox_height': [80, 90],
            'modality_label': ['text', 'image']
        })

        result = extract_ground_truth_labels(df)

        assert isinstance(result, pd.DataFrame)
        assert 'image_id' in result.columns
        assert 'x_min' in result.columns
        assert 'y_min' in result.columns
        assert 'x_max' in result.columns
        assert 'y_max' in result.columns
        assert 'modality' in result.columns

        # Verify coordinate conversion
        assert result.loc[0, 'x_max'] == 110  # 10 + 100
        assert result.loc[0, 'y_max'] == 95   # 15 + 80
        assert result.loc[1, 'x_max'] == 140  # 20 + 120
        assert result.loc[1, 'y_max'] == 115  # 25 + 90

    def test_extract_labels_missing_columns(self):
        """Test that KeyError is raised for missing required columns."""
        df = pd.DataFrame({
            'image_id': ['img1'],
            'bbox_x_min': [10]
            # Missing other required columns
        })

        with pytest.raises(KeyError):
            extract_ground_truth_labels(df)

    def test_extract_labels_invalid_modality(self):
        """Test handling of invalid modality labels."""
        df = pd.DataFrame({
            'image_id': ['img1'],
            'bbox_x_min': [10],
            'bbox_y_min': [15],
            'bbox_width': [100],
            'bbox_height': [80],
            'modality_label': ['invalid']
        })

        result = extract_ground_truth_labels(df)
        assert result.loc[0, 'modality'] == 'unknown'

    def test_extract_labels_negative_coordinates(self):
        """Test handling of negative coordinates."""
        df = pd.DataFrame({
            'image_id': ['img1'],
            'bbox_x_min': [-10],
            'bbox_y_min': [-15],
            'bbox_width': [100],
            'bbox_height': [80],
            'modality_label': ['text']
        })

        result = extract_ground_truth_labels(df)
        # Should still compute correctly
        assert result.loc[0, 'x_max'] == 90
        assert result.loc[0, 'y_max'] == 65


class TestDeriveHeuristicLabels:
    """Tests for derive_heuristic_labels function."""

    def test_heuristic_labels_basic(self):
        """Test basic heuristic label derivation."""
        df = pd.DataFrame({
            'image_id': ['img1', 'img2', 'img3'],
            'x_min': [10, 50, 100],
            'y_min': [15, 60, 120],
            'x_max': [110, 150, 200],
            'y_max': [95, 140, 200],
            'modality': ['text', 'image', 'unknown']
        })

        result = derive_heuristic_labels(df)

        assert isinstance(result, pd.DataFrame)
        assert 'heuristic_modality' in result.columns

        # Text regions should be identified
        assert result.loc[0, 'heuristic_modality'] == 'text'

    def test_heuristic_labels_area_threshold(self):
        """Test that small regions are filtered out."""
        df = pd.DataFrame({
            'image_id': ['img1', 'img2'],
            'x_min': [10, 100],
            'y_min': [15, 100],
            'x_max': [15, 150],  # Very small width
            'y_max': [20, 110],  # Very small height
            'modality': ['text', 'text']
        })

        result = derive_heuristic_labels(df)
        # Should filter out very small regions
        assert len(result) <= 2

    def test_heuristic_labels_empty_input(self):
        """Test handling of empty dataframe."""
        df = pd.DataFrame(columns=[
            'image_id', 'x_min', 'y_min', 'x_max', 'y_max', 'modality'
        ])

        result = derive_heuristic_labels(df)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0


class TestRunExtraction:
    """Tests for run_extraction function."""

    def test_run_extraction_full_pipeline(self):
        """Test the full extraction pipeline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create sample input data
            input_df = pd.DataFrame({
                'image_path': ['img1.jpg', 'img2.jpg'],
                'bbox_x_min': [10, 20],
                'bbox_y_min': [15, 25],
                'bbox_width': [100, 120],
                'bbox_height': [80, 90],
                'modality_label': ['text', 'image']
            })

            input_path = Path(tmpdir) / 'input.parquet'
            input_df.to_parquet(input_path)

            output_path = Path(tmpdir) / 'output.parquet'

            # Run extraction
            run_extraction(str(input_path), str(output_path))

            # Verify output exists
            assert output_path.exists()

            # Verify output content
            output_df = pd.read_parquet(output_path)
            assert isinstance(output_df, pd.DataFrame)
            assert 'modality' in output_df.columns
            assert 'x_max' in output_df.columns

    def test_run_extraction_invalid_input_path(self):
        """Test that appropriate error is raised for invalid input."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'output.parquet'

            with pytest.raises(FileNotFoundError):
                run_extraction('non_existent.parquet', str(output_path))

    def test_run_extraction_output_directory_creation(self):
        """Test that output directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create input data
            input_df = pd.DataFrame({
                'image_path': ['img1.jpg'],
                'bbox_x_min': [10],
                'bbox_y_min': [15],
                'bbox_width': [100],
                'bbox_height': [80],
                'modality_label': ['text']
            })

            input_path = Path(tmpdir) / 'input.parquet'
            input_df.to_parquet(input_path)

            # Create output path in non-existent subdirectory
            output_path = Path(tmpdir) / 'subdir' / 'output.parquet'

            # Should create directory and file
            run_extraction(str(input_path), str(output_path))

            assert output_path.exists()