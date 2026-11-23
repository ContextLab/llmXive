import pytest
import numpy as np
from PIL import Image
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.services.scoring import (
    estimate_memory_usage,
    dynamic_batch_adjustment,
    resize_image,
    process_fidelity_batch,
    calculate_logic_scores_batch,
    TARGET_RAM_GB
)

class TestMemoryEstimation:
    def test_estimate_memory_usage_formula(self):
        """Test that memory estimation follows the formula: RAM_est = model_size_gb * 1.2 + batch_size * image_size_mb"""
        # image_size_mb = 512 * 512 * 3 * 4 bytes / (1024 * 1024) = ~3.0 MB
        expected_image_size_mb = (512 * 512 * 3 * 4) / (1024 * 1024)
        
        model_size_gb = 1.5
        batch_size = 10
        
        estimated = estimate_memory_usage(batch_size, model_size_gb)
        
        expected_ram = model_size_gb * 1.2 + batch_size * expected_image_size_mb / (1024 * 1024)
        
        # Allow small floating point differences
        assert abs(estimated - expected_ram) < 0.01

    def test_dynamic_batch_adjustment_reduces_batch(self):
        """Test that batch size is reduced when memory exceeds target"""
        # With a very small target, batch size should be reduced
        initial_batch = 100
        target_ram = 0.1  # Very small target (GB)
        
        safe_batch = dynamic_batch_adjustment(
            initial_batch_size=initial_batch,
            model_size_gb=1.5,
            target_ram_gb=target_ram
        )
        
        # Should reduce batch size to fit within target
        assert safe_batch < initial_batch
        assert safe_batch >= 1

    def test_dynamic_batch_adjustment_returns_initial_when_fits(self):
        """Test that batch size remains unchanged when it fits within target"""
        initial_batch = 4
        target_ram = 10.0  # Large target (GB)
        
        safe_batch = dynamic_batch_adjustment(
            initial_batch_size=initial_batch,
            model_size_gb=1.5,
            target_ram_gb=target_ram
        )
        
        # Should keep initial batch size
        assert safe_batch == initial_batch

class TestBatchProcessing:
    def test_resize_image_dimensions(self):
        """Test that resize_image produces correct dimensions"""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            # Create a test image
            test_img = Image.new("RGB", (1024, 768), color="red")
            test_img.save(f.name)
            
            resized = resize_image(Path(f.name), size=512)
            assert resized.size == (512, 512)
            
            os.unlink(f.name)

    def test_process_fidelity_batch_empty(self):
        """Test that process_fidelity_batch handles empty lists"""
        result = process_fidelity_batch([], [])
        assert result == []

    def test_calculate_logic_scores_batch_empty(self):
        """Test that calculate_logic_scores_batch handles empty lists"""
        result = calculate_logic_scores_batch([], [])
        assert result == []

    def test_calculate_logic_scores_batch_single(self):
        """Test logic score calculation with single pair"""
        instructions = ["Test instruction"]
        descriptions = ["Test description"]
        
        scores = calculate_logic_scores_batch(instructions, descriptions)
        
        assert len(scores) == 1
        assert isinstance(scores[0], float)

class TestSafetyBuffer:
    def test_target_ram_uses_safety_buffer(self):
        """Verify that TARGET_RAM_GB accounts for the 0.5GB safety buffer"""
        # MAX_RAM_GB = 7.0, SAFETY_BUFFER_GB = 0.5
        # TARGET_RAM_GB should be 6.5
        assert TARGET_RAM_GB == 6.5