"""
Unit tests for code/data/validate.py
"""
import json
import os
import tempfile
import csv
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
from data.validate import load_manifest, validate_image_exists, run_validation, INVALID_RATIO_THRESHOLD
from utils.config import get_project_root

class TestLoadManifest:
    def test_load_valid_manifest(self, tmp_path):
        """Test loading a valid CSV manifest."""
        manifest_path = tmp_path / "test_manifest.csv"
        with open(manifest_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['filename', 'yield_strength'])
            writer.writeheader()
            writer.writerow({'filename': 'img1.png', 'yield_strength': '250.5'})
            writer.writerow({'filename': 'img2.png', 'yield_strength': '300.0'})
        
        rows, errors = load_manifest(manifest_path)
        
        assert len(rows) == 2
        assert rows[0]['filename'] == 'img1.png'
        assert float(rows[0]['yield_strength']) == 250.5
        assert len(errors) == 0

    def test_load_missing_columns(self, tmp_path):
        """Test loading a manifest missing required columns."""
        manifest_path = tmp_path / "bad_manifest.csv"
        with open(manifest_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['filename'])
            writer.writeheader()
            writer.writerow({'filename': 'img1.png'})
        
        rows, errors = load_manifest(manifest_path)
        
        assert len(rows) == 0
        assert len(errors) == 1
        assert 'Missing required columns' in errors[0]

    def test_load_missing_file(self, tmp_path):
        """Test loading a non-existent file."""
        rows, errors = load_manifest(tmp_path / "nonexistent.csv")
        assert len(rows) == 0
        assert len(errors) == 1
        assert 'not found' in errors[0]

    def test_load_invalid_numeric(self, tmp_path):
        """Test loading a manifest with non-numeric strength."""
        manifest_path = tmp_path / "bad_numeric.csv"
        with open(manifest_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['filename', 'yield_strength'])
            writer.writeheader()
            writer.writerow({'filename': 'img1.png', 'yield_strength': 'not_a_number'})
        
        rows, errors = load_manifest(manifest_path)
        assert len(rows) == 0
        assert len(errors) == 1
        assert 'non-numeric' in errors[0]

class TestValidateImageExists:
    def test_image_exists(self, tmp_path):
        """Test valid image path."""
        img = tmp_path / "test.png"
        img.touch()
        assert validate_image_exists(img, tmp_path / "manifest.csv", 1) is True

    def test_image_missing(self, tmp_path):
        """Test missing image path."""
        assert validate_image_exists(tmp_path / "missing.png", tmp_path / "manifest.csv", 1) is False

class TestRunValidation:
    @patch('data.validate.get_results_dir')
    @patch('data.validate.get_processed_dir')
    @patch('data.validate.get_project_root')
    def test_validation_passes(self, mock_root, mock_processed, mock_results, tmp_path):
        """Test validation passing when all images exist."""
        # Setup paths
        root = tmp_path / "project"
        processed = tmp_path / "processed"
        results = tmp_path / "results"
        
        mock_root.return_value = root
        mock_processed.return_value = processed
        mock_results.return_value = results
        
        root.mkdir(parents=True)
        processed.mkdir(parents=True)
        results.mkdir(parents=True)
        
        # Create dummy images
        img_dir = processed / "train"
        img_dir.mkdir(parents=True)
        (img_dir / "img1.png").touch()
        
        # Create manifest
        manifest = processed / "train_manifest.csv"
        with open(manifest, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['filename', 'yield_strength'])
            writer.writeheader()
            writer.writerow({'filename': 'img1.png', 'yield_strength': '250.0'})
        
        # Mock logger
        mock_logger = MagicMock()
        
        report = run_validation(mock_logger)
        
        assert report['total_pairs'] == 1
        assert report['invalid_pairs'] == 0
        assert report['status'] == 'passed'
        
        # Verify output file creation
        assert (results / "validation_report.json").exists()

    @patch('data.validate.get_results_dir')
    @patch('data.validate.get_processed_dir')
    @patch('data.validate.get_project_root')
    def test_validation_fails_missing_images(self, mock_root, mock_processed, mock_results, tmp_path):
        """Test validation failing when images are missing."""
        root = tmp_path / "project"
        processed = tmp_path / "processed"
        results = tmp_path / "results"
        
        mock_root.return_value = root
        mock_processed.return_value = processed
        mock_results.return_value = results
        
        root.mkdir(parents=True)
        processed.mkdir(parents=True)
        results.mkdir(parents=True)
        
        # Create manifest referencing missing image
        manifest = processed / "train_manifest.csv"
        with open(manifest, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['filename', 'yield_strength'])
            writer.writeheader()
            writer.writerow({'filename': 'missing.png', 'yield_strength': '250.0'})
        
        mock_logger = MagicMock()
        
        report = run_validation(mock_logger)
        
        assert report['total_pairs'] == 1
        assert report['invalid_pairs'] == 1
        assert report['status'] == 'failed'
        assert report['invalid_ratio'] == 1.0