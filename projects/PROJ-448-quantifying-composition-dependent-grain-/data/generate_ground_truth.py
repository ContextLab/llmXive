"""
Generate synthetic ground truth for pipeline validation.

This script simulates DFT segregation energies using the McLean isotherm
with injected interaction coefficients from research/synthetic_ground_truth.yaml.

IMPORTANT: This task is for regression engine validation only. It does NOT
simulate experimental APT concentrations.

Output: data/raw/generated_ground_truth.csv
"""
import os
import sys
import json
import hashlib
import logging
import pandas as pd
import numpy as np
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.config import PROJECT_ROOT, RANDOM_SEED, DATA_RAW_DIR, RESEARCH_DIR
from code.models.mclean import calculate_mclean_concentration, McLeanResult
from code.errors import ConfigurationError, ValidationError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_synthetic_config(config_path: str) -> Dict[str, Any]:
    """Load synthetic ground truth configuration."""
    if not os.path.exists(config_path):
        raise ConfigurationError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    if not config or 'interaction_coefficients' not in config:
        raise ConfigurationError("Configuration missing 'interaction_coefficients' key")
    
    return config

def generate_mc_data(
    system: str,
    bulk_conc: float,
    temperature: float,
    segregation_energy: float,
    rng: np.random.Generator
) -> Dict[str, Any]:
    """
    Generate a single data point using McLean isotherm with noise.
    
    Args:
        system: Alloy system name (e.g., 'Fe-Cr-Mo')
        bulk_conc: Bulk concentration (0.0 to 1.0)
        temperature: Temperature in Kelvin
        segregation_energy: Segregation energy in eV
        rng: Random number generator for noise
    
    Returns:
        Dictionary with generated data point
    """
    # Calculate McLean concentration
    try:
        result = calculate_mclean_concentration(
            bulk_concentration=bulk_conc,
            segregation_energy_eV=segregation_energy,
            temperature_K=temperature
        )
        conc = result.equilibrium_concentration
        saturation = result.is_saturated
    except (ValueError, RuntimeError) as e:
        logger.warning(f"McLean calculation failed for {system}: {e}")
        return None
    
    # Add small Gaussian noise to simulate measurement error
    noise = rng.normal(0, 0.005)
    conc_noisy = max(0.0, min(1.0, conc + noise))
    
    # Add noise to segregation energy
    energy_noisy = max(-1.0, min(1.0, segregation_energy + rng.normal(0, 0.01)))
    
    return {
        'system': system,
        'bulk_concentration': round(bulk_conc, 4),
        'temperature_K': temperature,
        'segregation_energy_eV': round(energy_noisy, 4),
        'equilibrium_concentration': round(conc_noisy, 4),
        'is_saturated': saturation
    }

def generate_ground_truth() -> List[Dict[str, Any]]:
    """
    Generate synthetic ground truth dataset.
    
    Returns:
        List of data points
    """
    # Load configuration
    config_path = RESEARCH_DIR / 'synthetic_ground_truth.yaml'
    config = load_synthetic_config(str(config_path))
    
    # Set random seed for reproducibility
    seed = config.get('random_seed', RANDOM_SEED)
    rng = np.random.default_rng(seed)
    
    logger.info(f"Using random seed: {seed}")
    
    # Define alloy systems to simulate
    systems = [
        'Fe-Cr-Mo', 'Fe-Cr-V', 'Fe-Mo-V', 
        'Fe-Cr-W', 'Fe-Mo-W', 'Fe-V-W'
    ]
    
    # Define temperature range
    temperatures = list(range(500, 901, 50))  # 500K to 900K in 50K steps
    
    # Define bulk concentrations
    concentrations = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30]
    
    data_points = []
    
    # Injected interaction coefficients from config
    interaction_coeffs = config.get('interaction_coefficients', {})
    
    for system in systems:
        logger.info(f"Processing system: {system}")
        
        # Determine base segregation energy based on system
        # Using a simple heuristic based on system name
        if 'Cr' in system and 'Mo' in system:
            base_energy = interaction_coeffs.get('beta_CrMo', 0.05)
        elif 'Cr' in system and 'V' in system:
            base_energy = interaction_coeffs.get('beta_CrV', 0.03)
        elif 'Mo' in system and 'V' in system:
            base_energy = interaction_coeffs.get('beta_MoV', 0.02)
        elif 'Cr' in system and 'W' in system:
            base_energy = interaction_coeffs.get('beta_CrW', 0.04)
        elif 'Mo' in system and 'W' in system:
            base_energy = interaction_coeffs.get('beta_MoW', 0.03)
        elif 'V' in system and 'W' in system:
            base_energy = interaction_coeffs.get('beta_VW', 0.02)
        else:
            base_energy = 0.02
        
        # Generate data points for this system
        for temp in temperatures:
            for conc in concentrations:
                # Add system-specific variation
                energy_variation = rng.normal(0, 0.01)
                segregation_energy = base_energy + energy_variation
                
                data_point = generate_mc_data(
                    system=system,
                    bulk_conc=conc,
                    temperature=temp,
                    segregation_energy=segregation_energy,
                    rng=rng
                )
                
                if data_point:
                    data_points.append(data_point)
    
    logger.info(f"Generated {len(data_points)} data points")
    return data_points

def save_ground_truth(data: List[Dict[str, Any]], output_path: str) -> str:
    """
    Save ground truth data to CSV and return checksum.
    
    Args:
        data: List of data points
        output_path: Path to output CSV file
    
    Returns:
        SHA256 checksum of the output file
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Convert to DataFrame and save
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    
    # Calculate checksum
    checksum = calculate_sha256(output_path)
    logger.info(f"Saved ground truth to {output_path}")
    logger.info(f"Checksum: {checksum}")
    
    return checksum

def update_manifest(checksum: str, output_path: str) -> None:
    """Update data manifest with ground truth entry."""
    manifest_path = Path(DATA_RAW_DIR) / 'data_manifest.json'
    
    # Load existing manifest or create new one
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
    else:
        manifest = {'entries': []}
    
    # Create new entry
    entry = {
        'source_type': 'generated',
        'source_id': 'generate_ground_truth.py',
        'file_path': str(output_path),
        'checksum': checksum,
        'generation_parameters': {
            'random_seed': RANDOM_SEED,
            'timestamp': datetime.now().isoformat(),
            'systems': ['Fe-Cr-Mo', 'Fe-Cr-V', 'Fe-Mo-V', 'Fe-Cr-W', 'Fe-Mo-W', 'Fe-V-W'],
            'temperature_range': [500, 900],
            'concentration_range': [0.05, 0.30]
        }
    }
    
    # Check if entry already exists
    existing = False
    for i, e in enumerate(manifest['entries']):
        if e.get('source_id') == 'generate_ground_truth.py':
            manifest['entries'][i] = entry
            existing = True
            break
    
    if not existing:
        manifest['entries'].append(entry)
    
    # Save manifest
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Updated manifest at {manifest_path}")

def main():
    """Main entry point."""
    logger.info("Starting ground truth generation...")
    
    try:
        # Generate data
        data = generate_ground_truth()
        
        if not data:
            raise RuntimeError("No data points generated")
        
        # Save to CSV
        output_path = str(Path(DATA_RAW_DIR) / 'generated_ground_truth.csv')
        checksum = save_ground_truth(data, output_path)
        
        # Update manifest
        update_manifest(checksum, output_path)
        
        logger.info("Ground truth generation completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Ground truth generation failed: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())
