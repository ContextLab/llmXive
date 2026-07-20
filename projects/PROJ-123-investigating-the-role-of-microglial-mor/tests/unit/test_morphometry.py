import pytest
import numpy as np
from code.morphometry import (
    calculate_soma_area_and_length,
    denoise_and_subtract,
    skeletonize_and_count,
    process_microglia_image,
    handle_empty_fields
)
from code.synthetic_data import generate_microglia_cell

def test_empty_field_detection():
    """Test that empty fields are correctly identified."""
    empty_img = np.zeros((50, 50))
    assert handle_empty_fields(empty_img) is True
    
    noise_img = np.random.rand(50, 50) * 1e-7
    assert handle_empty_fields(noise_img) is True

def test_soma_area_and_length_calculation():
    """Test soma area and total length calculation on synthetic data."""
    # Generate a synthetic microglia cell with known properties
    # We use a high pixel size to make the geometry clear
    img, _ = generate_microglia_cell(seed=42, soma_radius=10, num_processes=5, 
                                     process_length=50, pixel_size=1.0)
    
    # Preprocess
    denoised = denoise_and_subtract(img)
    
    # Skeletonize
    branch_points, skeleton = skeletonize_and_count(denoised)
    
    # Calculate metrics
    soma_area, total_length = calculate_soma_area_and_length(denoised, skeleton, pixel_size_um=1.0)
    
    # Assertions
    # Soma area should be positive and reasonable (pi * r^2 approx)
    assert soma_area > 0, "Soma area must be positive"
    assert soma_area < 10000, "Soma area seems too large"
    
    # Total length should be positive
    assert total_length > 0, "Total length must be positive"
    
    # Check that branch points are non-negative
    assert branch_points >= 0, "Branch points cannot be negative"

def test_process_microglia_image_full_pipeline():
    """Test the full processing pipeline on synthetic data."""
    img, _ = generate_microglia_cell(seed=123, soma_radius=8, num_processes=4, 
                                     process_length=40, pixel_size=0.5)
    
    result = process_microglia_image(img, pixel_size_um=0.5)
    
    assert result["valid"] is True
    assert "branch_points" in result
    assert "soma_area" in result
    assert "total_length" in result
    assert "sholl_intersections" in result
    
    # Check types
    assert isinstance(result["branch_points"], int)
    assert isinstance(result["soma_area"], float)
    assert isinstance(result["total_length"], float)
    assert isinstance(result["sholl_intersections"], dict)

def test_soma_area_consistency():
    """Test that soma area is consistent for similar inputs."""
    # Generate two similar cells
    img1, _ = generate_microglia_cell(seed=10, soma_radius=10, num_processes=3, process_length=30, pixel_size=1.0)
    img2, _ = generate_microglia_cell(seed=10, soma_radius=10, num_processes=3, process_length=30, pixel_size=1.0)
    
    denoised1 = denoise_and_subtract(img1)
    _, skeleton1 = skeletonize_and_count(denoised1)
    area1, _ = calculate_soma_area_and_length(denoised1, skeleton1, pixel_size_um=1.0)
    
    denoised2 = denoise_and_subtract(img2)
    _, skeleton2 = skeletonize_and_count(denoised2)
    area2, _ = calculate_soma_area_and_length(denoised2, skeleton2, pixel_size_um=1.0)
    
    # They should be very close (within 5% due to noise/sampling)
    diff = abs(area1 - area2)
    assert diff < 0.05 * max(area1, area2), f"Soma area inconsistent: {area1} vs {area2}"