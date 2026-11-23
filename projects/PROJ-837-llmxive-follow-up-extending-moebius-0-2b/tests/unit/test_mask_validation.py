import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.mask_generator import generate_mask
from PIL import Image

class TestMaskValidation:
    def test_mask_gradient_variance_calculation(self):
        """Test that gradient variance is calculated correctly"""
        img = Image.new('RGB', (64, 64), color='white')
        mask, metrics = generate_mask(img)
        
        assert 'gradient_variance' in metrics
        assert metrics['gradient_variance'] >= 0

    def test_mask_texture_entropy_calculation(self):
        """Test that texture entropy is calculated correctly"""
        img = Image.new('RGB', (64, 64), color='white')
        mask, metrics = generate_mask(img)
        
        assert 'texture_entropy' in metrics
        assert metrics['texture_entropy'] >= 0

    def test_mask_area_ratio_bounds(self):
        """Test that area ratio is within valid bounds"""
        img = Image.new('RGB', (64, 64), color='white')
        mask, metrics = generate_mask(img)
        
        assert 0 <= metrics['area_ratio'] <= 1

    def test_mask_complexity_correlation(self):
        """Test that complexity metrics vary with mask shape"""
        img = Image.new('RGB', (64, 64), color='white')
        
        masks = []
        metrics_list = []
        
        for _ in range(5):
            m, metrics = generate_mask(img)
            masks.append(np.array(m))
            metrics_list.append(metrics)
        
        # Verify metrics are not all identical
        variances = [m['gradient_variance'] for m in metrics_list]
        entropies = [m['texture_entropy'] for m in metrics_list]
        
        assert len(set(variances)) > 1 or len(set(entropies)) > 1

    def test_mask_binary_property(self):
        """Test that mask values are strictly binary"""
        img = Image.new('RGB', (128, 128), color='white')
        mask, _ = generate_mask(img)
        mask_np = np.array(mask)
        
        unique_values = np.unique(mask_np)
        assert all(v in [0, 1] for v in unique_values)

    def test_mask_not_trivial(self):
        """Test that mask is not all zeros or all ones"""
        img = Image.new('RGB', (64, 64), color='white')
        
        # Generate multiple masks to ensure we don't hit edge case
        for _ in range(10):
            mask, metrics = generate_mask(img)
            mask_np = np.array(mask)
            mean_val = np.mean(mask_np)
            
            # Should have some masked and some unmasked pixels
            if 0.05 < mean_val < 0.95:
                break
        else:
            pytest.fail("Could not generate non-trivial mask after 10 attempts")
