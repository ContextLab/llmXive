"""
Unit tests for artifact injection logic.
"""
import numpy as np
from code.synthetic.artifacts import inject_noise, clip_saturation
from code.config import NOISE_SEED

def test_noise_injection_sigma():
    """
    Assert that injected noise matches target sigma within tolerance.
    (FR-002)
    """
    # Create a flat image (zero mean for simplicity in noise check)
    image = np.zeros((100, 100), dtype=np.float64)
    target_sigma = 0.1
    
    np.random.seed(NOISE_SEED)
    noisy_image = inject_noise(image, target_sigma)
    
    # Calculate actual std of the difference (the noise)
    actual_noise = noisy_image - image
    actual_sigma = np.std(actual_noise)
    
    # Check within 5% tolerance
    assert abs(actual_sigma - target_sigma) / target_sigma < 0.05

def test_saturation_clipping():
    """
    Assert that the correct fraction of brightest pixels are clipped.
    (FR-003)
    
    We generate a synthetic image with a known distribution of values.
    We then apply saturation clipping at a specific threshold.
    We verify that:
    1. The number of clipped pixels matches the theoretical expectation
       (or is within a small tolerance due to floating point edge cases).
    2. The clipped pixels are exactly at the saturation threshold.
    3. Unclipped pixels remain unchanged.
    """
    # Use a deterministic seed for reproducibility
    rng = np.random.default_rng(42)
    
    # Create an image with values ranging from 0 to 100
    # We want to control exactly how many pixels will be clipped
    # by creating a known distribution.
    image_size = 1000
    saturation_threshold = 50.0
    saturation_fraction = 0.2  # We want 20% of pixels to be >= 50.0
    
    # Create an array where exactly 20% of values are >= 50.0
    # We do this by creating a sorted array and setting the top 20%
    values = np.linspace(0, 99, image_size)  # 0 to 99
    expected_clipped_count = int(image_size * saturation_fraction)
    
    # Ensure the top 20% are >= 50.0
    # The 80th percentile index
    split_idx = image_size - expected_clipped_count
    values[split_idx:] = np.linspace(saturation_threshold, 99, expected_clipped_count)
    
    # Shuffle to make it look like a real image
    rng.shuffle(values)
    image = values.reshape((int(np.sqrt(image_size)), int(np.sqrt(image_size))))
    
    # Count expected clipped pixels (>= threshold)
    expected_clipped = np.sum(image >= saturation_threshold)
    
    # Apply saturation clipping
    clipped_image = clip_saturation(image, saturation_threshold)
    
    # Count actual clipped pixels
    # A pixel is "clipped" if it was >= threshold and is now exactly threshold
    # Or simply if it is at the threshold and we know it was originally higher
    # A robust check: count pixels at threshold that *could* have been clipped
    # But the simplest check from the task description: "correct fraction of brightest pixels are clipped"
    # This implies the number of pixels at the saturation limit should match the number of pixels
    # that exceeded the limit in the original image.
    
    # However, `clip_saturation` sets values > threshold to threshold.
    # So in the result, all values > threshold become threshold.
    # We need to count how many pixels in the ORIGINAL image were > threshold.
    original_exceeded = np.sum(image > saturation_threshold)
    
    # In the clipped image, these pixels are now exactly at threshold.
    # But there might be original pixels that were exactly at threshold too.
    # So we check:
    # 1. No pixel in clipped_image is > threshold
    assert np.all(clipped_image <= saturation_threshold), "Clipping failed: some pixels exceed threshold"
    
    # 2. The number of pixels that are *exactly* at the threshold in the result
    #    should be at least the number that exceeded it.
    #    (It could be more if there were original pixels exactly at threshold)
    result_at_threshold = np.sum(clipped_image == saturation_threshold)
    assert result_at_threshold >= original_exceeded, \
        f"Not enough pixels at threshold. Expected >= {original_exceeded}, got {result_at_threshold}"
    
    # 3. Verify the specific "fraction" logic requested:
    #    The task says "asserting that the correct fraction of brightest pixels are clipped".
    #    Let's verify the fraction of pixels that were clipped relative to the total.
    #    We define "clipped" as pixels where original > threshold and result == threshold.
    #    Since we can't easily mask "original > threshold" without storing the mask,
    #    we rely on the fact that `clip_saturation` modifies the array in place or returns a new one.
    #    Let's assume it returns a new one or we can compare.
    
    # Re-run with a mask to be precise about the "fraction"
    mask_original_exceeded = image > saturation_threshold
    mask_clipped_in_result = clipped_image == saturation_threshold
    
    # The intersection: pixels that exceeded AND are now at threshold
    # Note: If a pixel was exactly at threshold, it stays at threshold.
    # So the set of pixels at threshold in result = (original > threshold) U (original == threshold)
    # The set of pixels that were CLIPPED is (original > threshold)
    
    # We can verify the count of clipped pixels by checking the difference
    # between the original and the clipped image.
    diff = clipped_image - image
    # Pixels that were clipped will have diff < 0 (specifically, threshold - original_value)
    # Pixels that were not clipped will have diff == 0
    actual_clipped_pixels = np.sum(diff < 0)
    
    # Calculate the fraction
    actual_fraction = actual_clipped_pixels / image.size
    expected_fraction = saturation_fraction
    
    # Assert the fraction is correct (allowing for integer rounding in split_idx)
    # The split_idx calculation: int(image_size * 0.2) = 200.
    # So expected_clipped is exactly 200.
    # 200 / 1000 = 0.2.
    assert np.isclose(actual_fraction, expected_fraction, atol=1e-5), \
        f"Clipped fraction mismatch. Expected {expected_fraction}, got {actual_fraction} ({actual_clipped_pixels} pixels)"
    
    # Additional check: Verify that the values of the clipped pixels are set to the threshold
    clipped_values = clipped_image[diff < 0]
    assert np.all(clipped_values == saturation_threshold), \
        "Clipped pixels are not set to the saturation threshold"