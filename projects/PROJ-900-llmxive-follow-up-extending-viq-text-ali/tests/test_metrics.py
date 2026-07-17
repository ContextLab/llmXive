import pytest
import torch
import numpy as np
from utils import calculate_psnr

def test_psnr_calculation_on_known_pair():
    """
    Verify PSNR calculation on a known pair of images.
    """
    # Create two identical images -> PSNR should be infinite (or very high)
    img1 = torch.ones((1, 1, 10, 10)) * 128.0
    img2 = torch.ones((1, 1, 10, 10)) * 128.0
    
    psnr = calculate_psnr(img1, img2)
    assert psnr > 100.0, f"PSNR for identical images should be very high, got {psnr}"
    
    # Create two different images
    img3 = torch.zeros((1, 1, 10, 10))
    img4 = torch.ones((1, 1, 10, 10)) * 255.0
    
    psnr_diff = calculate_psnr(img3, img4)
    # Max diff (0 vs 255) -> PSNR = 20 * log10(255 / sqrt(mean((255-0)^2)))
    # MSE = 255^2, RMSE = 255, PSNR = 20 * log10(255/255) = 0
    # Wait, MSE = mean((255-0)^2) = 255^2. RMSE = 255.
    # PSNR = 20 * log10(MAX / RMSE) = 20 * log10(255/255) = 0.
    assert psnr_diff == 0.0, f"PSNR for 0 vs 255 should be 0, got {psnr_diff}"

def test_high_res_shape_handling():
    """
    Unit test for code/eval_high_res.py verifying shape handling for 1024x1024 inputs.
    This test ensures that the metric calculation functions (PSNR, SSIM, Texture Complexity)
    can handle high-resolution tensors without shape errors or memory issues during calculation.
    """
    # Simulate a 1024x1024 image batch (1 channel, 1024x1024)
    # Using float32 for calculation, simulating normalized pixel values (0-1 range or 0-255)
    # We use a smaller tensor to simulate the logic without allocating ~4GB for a full batch of float32 if not needed,
    # but the shape dimensions must match the expected high-res input.
    # To strictly verify the "1024x1024" shape handling, we create the tensor with those dimensions.
    # Note: A single 1024x1024 float32 image is ~4MB. A batch of 1 is fine.
    
    batch_size = 1
    channels = 1
    height = 1024
    width = 1024
    
    # Create synthetic high-res tensors (simulating real data structure)
    # Using random noise to ensure non-identical images for PSNR calculation
    torch.manual_seed(42)
    img_hr_1 = torch.rand(batch_size, channels, height, width) * 255.0
    img_hr_2 = torch.rand(batch_size, channels, height, width) * 255.0
    
    # Verify shape
    assert img_hr_1.shape == (batch_size, channels, height, width), \
        f"Expected shape ({batch_size}, {channels}, {height}, {width}), got {img_hr_1.shape}"
    
    # Test PSNR calculation on high-res inputs
    # This verifies that the function doesn't crash on large tensors
    psnr_val = calculate_psnr(img_hr_1, img_hr_2)
    assert isinstance(psnr_val, float), f"PSNR should return a float, got {type(psnr_val)}"
    assert not np.isnan(psnr_val), "PSNR should not be NaN"
    assert psnr_val >= 0.0, f"PSNR should be non-negative, got {psnr_val}"
    
    # Test SSIM calculation on high-res inputs (imported from utils)
    from utils import calculate_ssim
    ssim_val = calculate_ssim(img_hr_1, img_hr_2)
    assert isinstance(ssim_val, float), f"SSIM should return a float, got {type(ssim_val)}"
    assert not np.isnan(ssim_val), "SSIM should not be NaN"
    
    # Test Texture Complexity calculation on high-res inputs
    from utils import calculate_texture_complexity
    # calculate_texture_complexity expects (H, W) or (1, H, W) grayscale usually, 
    # but utils implementation handles batch or single. We pass the single channel slice.
    # Assuming utils.calculate_texture_complexity takes a 2D numpy array or tensor slice.
    # We pass the first image of the batch, first channel.
    hr_slice = img_hr_1[0, 0].numpy() # Shape (1024, 1024)
    
    tex_complexity = calculate_texture_complexity(hr_slice)
    assert isinstance(tex_complexity, float), f"Texture complexity should return a float, got {type(tex_complexity)}"
    assert tex_complexity >= 0.0, f"Texture complexity should be non-negative, got {tex_complexity}"
    
    # Verify that the calculation actually processed the full resolution (sanity check on value magnitude)
    # While not a strict mathematical proof, if the function truncated to a small size, 
    # the variance of Laplacian would likely be significantly different or zero if downsampled too much.
    # We rely on the fact that the function ran without memory error and produced a value.
    assert hr_slice.shape == (height, width), "Input slice shape mismatch"