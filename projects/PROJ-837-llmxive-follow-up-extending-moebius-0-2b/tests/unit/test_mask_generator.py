import pytest
from PIL import Image
import numpy as np

from code.data.mask_generator import generate_mask

def test_generate_mask_simple():
    img = Image.new("RGB", (100, 100), color="white")
    mask, metrics = generate_mask(img, complexity=1)
    
    assert isinstance(mask, Image.Image)
    assert mask.mode == "L"
    assert "gradient_variance" in metrics
    assert "texture_entropy" in metrics
    assert metrics["gradient_variance"] >= 0

def test_generate_mask_complex():
    img = Image.new("RGB", (100, 100), color="white")
    mask, metrics = generate_mask(img, complexity=5)
    
    assert isinstance(mask, Image.Image)
    assert mask.mode == "L"
    # Complex masks should have different metrics than simple ones
    assert metrics["texture_entropy"] > 0
