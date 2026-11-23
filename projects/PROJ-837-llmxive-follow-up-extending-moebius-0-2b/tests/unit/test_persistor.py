import pytest
import os
import sys
from pathlib import Path
import tempfile
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.persistor import (
    compute_image_hash, 
    persist_masked_images,
    persist_scores
)
from PIL import Image

class TestPersistor:
    def test_compute_image_hash_consistency(self):
        """Test that image hash is consistent"""
        img = Image.new('RGB', (64, 64), color='red')
        
        hash1 = compute_image_hash(img)
        hash2 = compute_image_hash(img)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length

    def test_compute_image_hash_different_images(self):
        """Test that different images have different hashes"""
        img1 = Image.new('RGB', (64, 64), color='red')
        img2 = Image.new('RGB', (64, 64), color='blue')
        
        hash1 = compute_image_hash(img1)
        hash2 = compute_image_hash(img2)
        
        assert hash1 != hash2

    def test_persist_masked_images(self):
        """Test saving masked images to disk"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "output")
            
            # Create test images
            images = []
            for i in range(3):
                img = Image.new('RGB', (32, 32), color=(i*50, 0, 0))
                images.append(img)
            
            image_ids = [f"img_{i}" for i in range(3)]
            
            result = persist_masked_images(
                images, 
                image_ids, 
                output_dir
            )
            
            assert result is True
            assert os.path.exists(output_dir)
            
            # Check files were created
            files = os.listdir(output_dir)
            assert len(files) == 3
            assert all(f.endswith('.png') for f in files)

    def test_persist_scores(self):
        """Test saving scores to CSV"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scores_path = os.path.join(tmpdir, "scores.csv")
            
            scores = [
                {'image_id': 'img1', 'score': 3.5, 'mode': 'CI'},
                {'image_id': 'img2', 'score': 4.2, 'mode': 'CI'}
            ]
            
            result = persist_scores(scores, scores_path)
            
            assert result is True
            assert os.path.exists(scores_path)
            
            # Verify content
            with open(scores_path, 'r') as f:
                import csv
                reader = csv.DictReader(f)
                rows = list(reader)
                
                assert len(rows) == 2
                assert rows[0]['image_id'] == 'img1'
                assert float(rows[0]['score']) == 3.5

    def test_persist_masked_images_empty_list(self):
        """Test saving empty list of images"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = persist_masked_images([], [], tmpdir)
            assert result is True

    def test_persist_scores_empty_list(self):
        """Test saving empty list of scores"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scores_path = os.path.join(tmpdir, "scores.csv")
            result = persist_scores([], scores_path)
            assert result is True
            assert os.path.exists(scores_path)
