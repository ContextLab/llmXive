"""
Unit tests for vector validation functionality.

Tests for T016: Add validation to ensure output vectors match model hidden 
dimension and are L2-normalized.
"""
import pytest
import torch
import numpy as np
import tempfile
import os
import csv
import json
from pathlib import Path

from validate_vectors import (
    validate_vector_dimension,
    validate_l2_normalization,
    validate_vector_batch,
    validate_csv_vectors,
    VectorValidationError,
    run_baseline_validation
)
from config import ModelConfig, OutputPaths

class TestValidateVectorDimension:
    """Tests for dimension validation."""
    
    def test_correct_dimension(self):
        """Test that correct dimensions pass validation."""
        vector = torch.randn(768)
        is_valid, error = validate_vector_dimension(vector, 768, "test_pair", 0)
        assert is_valid is True
        assert error == ""
    
    def test_wrong_dimension(self):
        """Test that wrong dimensions fail validation."""
        vector = torch.randn(512)
        is_valid, error = validate_vector_dimension(vector, 768, "test_pair", 0)
        assert is_valid is False
        assert "Dimension mismatch" in error
        assert "expected 768" in error
        assert "got 512" in error
    
    def test_2d_tensor(self):
        """Test dimension check with 2D tensor (batch dimension)."""
        vector = torch.randn(1, 768)
        is_valid, error = validate_vector_dimension(vector, 768, "test_pair", 0)
        assert is_valid is True
        assert error == ""

class TestValidateL2Normalization:
    """Tests for L2 normalization validation."""
    
    def test_perfect_normalization(self):
        """Test that perfectly normalized vectors pass."""
        vector = torch.randn(768)
        vector = vector / torch.norm(vector)
        is_valid, error = validate_l2_normalization(vector, tolerance=1e-5, pair_id="test", index=0)
        assert is_valid is True
        assert error == ""
    
    def test_slightly_normalized(self):
        """Test that slightly off-normalized vectors pass within tolerance."""
        vector = torch.randn(768)
        vector = vector / torch.norm(vector)
        # Add small perturbation
        vector = vector * 1.000001
        is_valid, error = validate_l2_normalization(vector, tolerance=1e-5, pair_id="test", index=0)
        assert is_valid is True
    
    def test_not_normalized(self):
        """Test that non-normalized vectors fail."""
        vector = torch.randn(768) * 2.0  # Not unit length
        is_valid, error = validate_l2_normalization(vector, tolerance=1e-5, pair_id="test", index=0)
        assert is_valid is False
        assert "L2 normalization failed" in error
    
    def test_scalar_value(self):
        """Test that scalar values are rejected."""
        vector = torch.tensor(1.0)
        is_valid, error = validate_l2_normalization(vector, tolerance=1e-5, pair_id="test", index=0)
        assert is_valid is False
        assert "Scalar value detected" in error

class TestValidateVectorBatch:
    """Tests for batch validation."""
    
    def test_all_valid(self):
        """Test batch where all vectors are valid."""
        vectors = [torch.randn(768) / torch.norm(torch.randn(768)) for _ in range(10)]
        pair_ids = [f"pair_{i}" for i in range(10)]
        
        results = validate_vector_batch(vectors, pair_ids, expected_dim=768)
        
        assert results["total_count"] == 10
        assert results["passed_count"] == 10
        assert results["failed_count"] == 0
        assert len(results["dimension_errors"]) == 0
        assert len(results["normalization_errors"]) == 0
    
    def test_mixed_validity(self):
        """Test batch with mixed valid/invalid vectors."""
        vectors = []
        pair_ids = []
        
        # Add valid vectors
        for i in range(5):
            v = torch.randn(768)
            v = v / torch.norm(v)
            vectors.append(v)
            pair_ids.append(f"valid_{i}")
        
        # Add invalid dimension
        vectors.append(torch.randn(512))
        pair_ids.append("bad_dim")
        
        # Add invalid normalization
        v = torch.randn(768)
        vectors.append(v * 2.0)
        pair_ids.append("bad_norm")
        
        results = validate_vector_batch(vectors, pair_ids, expected_dim=768)
        
        assert results["total_count"] == 7
        assert results["passed_count"] == 5
        assert results["failed_count"] == 2
        assert len(results["dimension_errors"]) == 1
        assert len(results["normalization_errors"]) == 1
    
    def test_length_mismatch(self):
        """Test that length mismatch raises error."""
        vectors = [torch.randn(768)]
        pair_ids = ["pair1", "pair2"]
        
        with pytest.raises(ValueError, match="Length mismatch"):
            validate_vector_batch(vectors, pair_ids, expected_dim=768)

class TestValidateCSVVectors:
    """Tests for CSV-based vector validation."""
    
    def test_valid_csv(self):
        """Test validation of a valid CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            writer = csv.writer(f)
            writer.writerow(['pair_id', 'task_type', 'vector', 'vector_dim'])
            
            # Write a valid normalized vector
            vector = torch.randn(768)
            vector = vector / torch.norm(vector)
            vector_str = "[" + ",".join(f"{x:.6f}" for x in vector.tolist()) + "]"
            writer.writerow(['pair1', 'task1', vector_str, 768])
            
            csv_path = f.name
        
        try:
            model_config = ModelConfig(
                model_name="test",
                hidden_size=768,
                max_length=512
            )
            output_paths = OutputPaths(
                raw_dir="data/raw",
                processed_dir="data/processed",
                figures_dir="figures",
                pairing_config="data/processed/pairing_config.json",
                validity_log="data/processed/validity_log.csv"
            )
            
            results = validate_csv_vectors(csv_path, model_config, output_paths)
            
            assert results["total_count"] == 1
            assert results["passed_count"] == 1
            assert results["failed_count"] == 0
            assert results["pass_rate"] == 1.0
        finally:
            os.unlink(csv_path)
    
    def test_invalid_dimension_csv(self):
        """Test validation catches dimension mismatch in CSV."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            writer = csv.writer(f)
            writer.writerow(['pair_id', 'task_type', 'vector', 'vector_dim'])
            
            # Write a vector with wrong dimension
            vector = torch.randn(512)
            vector_str = "[" + ",".join(f"{x:.6f}" for x in vector.tolist()) + "]"
            writer.writerow(['pair1', 'task1', vector_str, 512])
            
            csv_path = f.name
        
        try:
            model_config = ModelConfig(
                model_name="test",
                hidden_size=768,
                max_length=512
            )
            output_paths = OutputPaths(
                raw_dir="data/raw",
                processed_dir="data/processed",
                figures_dir="figures",
                pairing_config="data/processed/pairing_config.json",
                validity_log="data/processed/validity_log.csv"
            )
            
            results = validate_csv_vectors(csv_path, model_config, output_paths)
            
            assert results["total_count"] == 1
            assert results["passed_count"] == 0
            assert results["failed_count"] == 1
            assert len(results["errors"]) == 1
            assert "Dimension mismatch" in results["errors"][0]
        finally:
            os.unlink(csv_path)
    
    def test_invalid_normalization_csv(self):
        """Test validation catches non-normalized vectors in CSV."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            writer = csv.writer(f)
            writer.writerow(['pair_id', 'task_type', 'vector', 'vector_dim'])
            
            # Write a non-normalized vector
            vector = torch.randn(768) * 2.0
            vector_str = "[" + ",".join(f"{x:.6f}" for x in vector.tolist()) + "]"
            writer.writerow(['pair1', 'task1', vector_str, 768])
            
            csv_path = f.name
        
        try:
            model_config = ModelConfig(
                model_name="test",
                hidden_size=768,
                max_length=512
            )
            output_paths = OutputPaths(
                raw_dir="data/raw",
                processed_dir="data/processed",
                figures_dir="figures",
                pairing_config="data/processed/pairing_config.json",
                validity_log="data/processed/validity_log.csv"
            )
            
            results = validate_csv_vectors(csv_path, model_config, output_paths)
            
            assert results["total_count"] == 1
            assert results["passed_count"] == 0
            assert results["failed_count"] == 1
            assert len(results["errors"]) == 1
            assert "L2 normalization failed" in results["errors"][0]
        finally:
            os.unlink(csv_path)
    
    def test_file_not_found(self):
        """Test that missing file raises error."""
        model_config = ModelConfig(
            model_name="test",
            hidden_size=768,
            max_length=512
        )
        output_paths = OutputPaths(
            raw_dir="data/raw",
            processed_dir="data/processed",
            figures_dir="figures",
            pairing_config="data/processed/pairing_config.json",
            validity_log="data/processed/validity_log.csv"
        )
        
        with pytest.raises(FileNotFoundError):
            validate_csv_vectors("nonexistent.csv", model_config, output_paths)

class TestRunBaselineValidation:
    """Tests for the full baseline validation workflow."""
    
    def test_successful_validation(self):
        """Test successful validation workflow."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            writer = csv.writer(f)
            writer.writerow(['pair_id', 'task_type', 'vector', 'vector_dim'])
            
            # Write valid vectors
            for i in range(5):
                vector = torch.randn(768)
                vector = vector / torch.norm(vector)
                vector_str = "[" + ",".join(f"{x:.6f}" for x in vector.tolist()) + "]"
                writer.writerow([f'pair{i}', 'task1', vector_str, 768])
            
            csv_path = f.name
        
        try:
            model_config = ModelConfig(
                model_name="test",
                hidden_size=768,
                max_length=512
            )
            output_paths = OutputPaths(
                raw_dir="data/raw",
                processed_dir="data/processed",
                figures_dir="figures",
                pairing_config="data/processed/pairing_config.json",
                validity_log="data/processed/validity_log.csv"
            )
            
            is_valid = run_baseline_validation(csv_path, model_config, output_paths)
            
            assert is_valid is True
        finally:
            os.unlink(csv_path)
    
    def test_failed_validation(self):
        """Test failed validation workflow."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            writer = csv.writer(f)
            writer.writerow(['pair_id', 'task_type', 'vector', 'vector_dim'])
            
            # Write invalid vector
            vector = torch.randn(768) * 2.0
            vector_str = "[" + ",".join(f"{x:.6f}" for x in vector.tolist()) + "]"
            writer.writerow(['pair1', 'task1', vector_str, 768])
            
            csv_path = f.name
        
        try:
            model_config = ModelConfig(
                model_name="test",
                hidden_size=768,
                max_length=512
            )
            output_paths = OutputPaths(
                raw_dir="data/raw",
                processed_dir="data/processed",
                figures_dir="figures",
                pairing_config="data/processed/pairing_config.json",
                validity_log="data/processed/validity_log.csv"
            )
            
            is_valid = run_baseline_validation(csv_path, model_config, output_paths)
            
            assert is_valid is False
        finally:
            os.unlink(csv_path)