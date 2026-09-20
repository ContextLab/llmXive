import os
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import random
import argparse
from pathlib import Path
import logging

# Import existing config and logger utilities
try:
    from utils.config import get_config_dict, set_seed as config_set_seed
    from utils.logger import get_logger
except ImportError:
    # Fallback for direct execution if path is not set up, 
    # though the prompt implies running within the project structure.
    # We will assume the imports work as per the API surface.
    pass

# --- Configuration & Constants ---
# These parameters define the physics of the synthetic microstructure generation.
# They align with the K_IC formula defined in research.md Section 3.2.

# Base fracture toughness (MPa√m) for a theoretical zero-grain-size, zero-precipitate alloy
BASE_K_IC = 25.0 

# Hall-Petch coefficient (strength increases as grain size decreases)
# Negative alpha because smaller grains (lower value) -> higher strength -> higher K_IC
ALPHA_GRAIN = 150.0 

# Precipitate strengthening coefficient
# Positive beta because more precipitates (higher density) -> higher K_IC
BETA_PRECIP = 0.5

# Noise standard deviation for synthetic scatter
NOISE_STD = 2.0

# Image dimensions
IMAGE_SIZE = 128
MIN_GRAIN_SIZE_PX = 4  # Nyquist limit enforcement (T055)
MAX_GRAIN_SIZE_PX = 40

def set_seed(seed):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    if 'torch' in globals():
        import torch
        torch.manual_seed(seed)

def generate_grain_structure(draw, num_grains, img_w, img_h):
    """
    Generates a Voronoi-like grain structure using random seed points and 
    filling polygons. This mimics polycrystalline microstructures.
    
    Returns a list of grain dictionaries with properties.
    """
    grains = []
    seed_points = []
    
    # Generate seed points ensuring they are within bounds
    for i in range(num_grains):
        x = random.uniform(0, img_w)
        y = random.uniform(0, img_h)
        seed_points.append((x, y))
    
    # Simple Voronoi approximation: assign each pixel to nearest seed
    # For performance in pure PIL, we draw convex hulls or simplified polygons
    # representing the "territory" of each seed. 
    # A more robust approach for pure PIL without scipy:
    # 1. Create a blank image.
    # 2. For each seed, define a radius based on local density.
    # 3. Draw filled circles/ellipses that overlap, then use a "nearest" logic?
    # Actually, for synthetic microstructure, a "blob" approach with random centers
    # and radii, then smoothing, is often sufficient for texture analysis.
    # Let's use a "Random Polygon" approach for clearer grain boundaries.
    
    # We will construct the image by drawing random polygons that tile the space roughly.
    # Since exact Voronoi is complex without scipy, we simulate grain boundaries
    # by drawing random lines and filling regions.
    
    # Alternative: Generate a set of random convex polygons that cover the image.
    # We'll use a simpler "growth" simulation: start with seeds, grow them until they hit.
    
    # Implementation: Voronoi via distance transform approximation is hard in PIL.
    # Let's use a "Randomized Polygon Tiling" strategy.
    # 1. Create a grid of points.
    # 2. Perturb them.
    # 3. Draw lines between neighbors to form cells.
    
    # Simpler approach for texture:
    # Draw random ellipses/circles with different orientations and colors,
    # then apply a filter to blend boundaries, creating a "grainy" look.
    
    # Let's go with a "Random Grain" approach:
    # Generate N random centers. For each, generate a random radius and orientation.
    # Draw filled polygons.
    
    # To ensure coverage, we'll use a grid-based perturbation.
    grid_size = int(np.ceil(np.sqrt(num_grains)))
    cell_w = img_w / grid_size
    cell_h = img_h / grid_size
    
    drawn_grains = []
    
    for i in range(num_grains):
        cx = (i % grid_size) * cell_w + cell_w / 2 + random.uniform(-cell_w/4, cell_w/4)
        cy = (i // grid_size) * cell_h + cell_h / 2 + random.uniform(-cell_h/4, cell_h/4)
        
        # Random radius, ensuring minimum size
        r_x = random.uniform(MIN_GRAIN_SIZE_PX, MAX_GRAIN_SIZE_PX)
        r_y = random.uniform(MIN_GRAIN_SIZE_PX, MAX_GRAIN_SIZE_PX)
        angle = random.uniform(0, 2 * np.pi)
        
        # Generate polygon points for an ellipse
        points = []
        for theta in np.linspace(0, 2 * np.pi, 12):
            px = cx + r_x * np.cos(theta) * np.cos(angle) - r_y * np.sin(theta) * np.sin(angle)
            py = cy + r_x * np.cos(theta) * np.sin(angle) + r_y * np.sin(theta) * np.cos(angle)
            points.append((px, py))
        
        # Random grayscale intensity for the grain (0-255)
        intensity = random.randint(50, 200)
        
        # Draw the polygon
        draw.polygon(points, fill=intensity, outline=intensity-10)
        
        # Store grain properties for metadata
        drawn_grains.append({
            "center": (cx, cy),
            "radius_x": r_x,
            "radius_y": r_y,
            "intensity": intensity,
            "area": np.pi * r_x * r_y
        })
    
    return drawn_grains

def calculate_physics_informed_k_ic(grains, precipitate_density, alloy_family):
    """
    Calculates K_IC based on the formula in research.md Section 3.2:
    K_IC = base_value + alpha * (1/grain_size_avg) + beta * precipitate_density + noise
    
    Note: The prompt formula says "alpha * grain_size", but physically, 
    Hall-Petch implies strength increases as grain size decreases.
    We will interpret "grain_size" in the formula as the inverse (1/d) or 
    adjust the sign of alpha to reflect physical reality if alpha is negative.
    However, the prompt explicitly wrote: `K_IC = base_value + alpha * grain_size + beta * precipitate_density + noise`.
    If we strictly follow the prompt's formula, larger grains = higher K_IC.
    We will implement the formula *exactly as described in the prompt text* 
    but use a negative alpha to simulate the physical reality if the prompt implies 
    the standard Hall-Petch relationship (where alpha is usually negative in K_IC = K0 - k*d^-0.5).
    
    Let's stick to the prompt's variable names but ensure physical plausibility:
    We will calculate average grain size (d).
    K_IC = base_value + (alpha * d) + (beta * precipitate_density) + noise
    
    To make it physically meaningful (smaller grains -> stronger), we set alpha to a negative value.
    """
    if not grains:
        avg_grain_size = 20.0 # Default
    else:
        avg_grain_size = np.mean([g['radius_x'] for g in grains])
    
    # Ensure grain size is not too small to avoid division by zero or extreme values if inverted
    # But here we use it linearly.
    
    # Formula: K_IC = base_value + alpha * grain_size + beta * precipitate_density + noise
    # We use the constants defined at the top.
    # To simulate physics: smaller grains -> higher toughness.
    # So if grain_size increases, K_IC should decrease.
    # Thus alpha should be negative.
    
    # Let's adjust the constants to match the "physics-informed" requirement:
    # We will use the constants defined at the top, but ensure alpha is negative.
    # If the user defined alpha as positive in the prompt, we must negate it here
    # to satisfy the "physics-informed" requirement.
    
    # Re-reading the prompt: "K_IC = base_value + alpha * grain_size + beta * precipitate_density + noise"
    # It doesn't specify the sign of alpha. We choose the sign to make it physical.
    # Physical: Smaller grains = Higher K_IC.
    # So: K_IC = Base - |alpha| * grain_size + ...
    
    effective_alpha = -1.0 * ALPHA_GRAIN # Negative to reflect Hall-Petch
    
    # Alloy family modifier
    family_modifier = 0.0
    if alloy_family == 'steel':
        family_modifier = 10.0
    elif alloy_family == 'Al':
        family_modifier = 5.0
    elif alloy_family == 'Ti':
        family_modifier = 8.0
    
    noise = np.random.normal(0, NOISE_STD)
    
    k_ic = BASE_K_IC + (effective_alpha * avg_grain_size) + (BETA_PRECIP * precipitate_density) + family_modifier + noise
    
    # Clamp to physical range (typical K_IC for metals is 20-200 MPa√m)
    k_ic = max(20.0, min(200.0, k_ic))
    
    return k_ic

def generate_sample_metadata(grain_props, precip_density, k_ic, alloy_family, seed):
    """Generates metadata dictionary for a single sample."""
    # Sample preparation metadata (T053a)
    # These are synthetic values derived from generator parameters
    magnification_calibration = 1.0 / (np.mean([g['radius_x'] for g in grain_props]) * 0.1) # Arbitrary scale
    section_thickness = random.uniform(10, 50) # microns
    surface_prep_protocol = "Polished and etched"
    
    return {
        "image_id": f"sample_{seed:05d}",
        "alloy_family": alloy_family,
        "k_ic": round(k_ic, 4),
        "num_grains": len(grain_props),
        "avg_grain_size_px": round(np.mean([g['radius_x'] for g in grain_props]), 2),
        "precipitate_density": round(precip_density, 4),
        "magnification_calibration": round(magnification_calibration, 4),
        "section_thickness": round(section_thickness, 2),
        "surface_prep_protocol": surface_prep_protocol,
        "seed": seed
    }

def generate_dataset(num_images=2000, output_dir='data/raw', seed=42):
    """
    Generates a synthetic dataset of microstructure images and metadata.
    Produces >= 2000 images with physics-informed K_IC values.
    """
    set_seed(seed)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    metadata_list = []
    
    alloy_families = ['steel', 'Al', 'Ti']
    
    logger = get_logger()
    logger.info(f"Starting synthetic generation of {num_images} images...")
    
    for i in range(num_images):
        # Random alloy family
        alloy = random.choice(alloy_families)
        
        # Random number of grains (affects texture)
        num_grains = random.randint(20, 100)
        
        # Create image
        img = Image.new('L', (IMAGE_SIZE, IMAGE_SIZE), color=0)
        draw = ImageDraw.Draw(img)
        
        # Generate grain structure
        grains = generate_grain_structure(draw, num_grains, IMAGE_SIZE, IMAGE_SIZE)
        
        # Add grain boundaries (edges)
        # Draw lines between grains? Or just rely on the intensity difference.
        # Let's apply a slight blur to soften boundaries and simulate optical limits
        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        # Random precipitate density (0.0 to 1.0)
        precip_density = random.uniform(0.0, 1.0)
        
        # Add precipitates (small dots)
        for _ in range(int(precip_density * 500)):
            px = random.randint(0, IMAGE_SIZE-1)
            py = random.randint(0, IMAGE_SIZE-1)
            # Dark dots
            draw.point((px, py), fill=random.randint(0, 50))
        
        # Calculate K_IC
        k_ic = calculate_physics_informed_k_ic(grains, precip_density, alloy)
        
        # Generate metadata
        meta = generate_sample_metadata(grains, precip_density, k_ic, alloy, i)
        metadata_list.append(meta)
        
        # Save image
        filename = f"sample_{i:05d}.png"
        img.save(output_path / filename)
        
        if (i + 1) % 500 == 0:
            logger.info(f"Generated {i+1} images...")
    
    # Save metadata
    metadata_file = output_path / "metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata_list, f, indent=2)
    
    logger.info(f"Generation complete. Saved {num_images} images to {output_path}")
    logger.info(f"Metadata saved to {metadata_file}")
    
    return num_images

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic microstructure dataset")
    parser.add_argument('--num_images', type=int, default=2000, help='Number of images to generate')
    parser.add_argument('--output_dir', type=str, default='data/raw', help='Output directory')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    
    args = parser.parse_args()
    
    generate_dataset(num_images=args.num_images, output_dir=args.output_dir, seed=args.seed)

if __name__ == "__main__":
    main()
