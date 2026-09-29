"""
Script to generate the test dataset for data gap validation (T017c).
Creates data/raw/test_n.csv with exactly 29 rows to trigger the
data availability check in T017b.
"""
import os
import sys
import logging
import pandas as pd
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from config import initialize_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_test_dataset(output_path: Path) -> pd.DataFrame:
    """
    Generate a test dataset with exactly 29 rows.
    
    Args:
        output_path: Path to save the CSV file.
        
    Returns:
        The generated DataFrame.
    """
    logger.info(f"Generating test dataset with 29 rows at {output_path}")
    
    # Fixed list of valid compositions
    compositions = [
        'Al2O3', 'ZrO2', 'SiC', 'Si3N4', 'MgO', 
        'TiC', 'HfC', 'B4C', 'WC', 'AlN'
    ]
    
    # Generate 29 rows by cycling through compositions
    data = {
        'composition': [],
        'weibull_modulus': [],
        'sample_count': [],
        'sintering_temp': [],
        'primary_anion_cation_group': []
    }
    
    # Define realistic values for each composition
    composition_params = {
        'Al2O3': {'weibull': 12.5, 'sample_count': 35, 'temp': 1600.0, 'group': 'O-Al'},
        'ZrO2': {'weibull': 8.2, 'sample_count': 32, 'temp': 1450.0, 'group': 'O-Zr'},
        'SiC': {'weibull': 15.0, 'sample_count': 40, 'temp': 2000.0, 'group': 'C-Si'},
        'Si3N4': {'weibull': 10.5, 'sample_count': 38, 'temp': 1800.0, 'group': 'N-Si'},
        'MgO': {'weibull': 6.8, 'sample_count': 30, 'temp': 1900.0, 'group': 'O-Mg'},
        'TiC': {'weibull': 11.2, 'sample_count': 33, 'temp': 2100.0, 'group': 'C-Ti'},
        'HfC': {'weibull': 9.5, 'sample_count': 31, 'temp': 2300.0, 'group': 'C-Hf'},
        'B4C': {'weibull': 14.0, 'sample_count': 36, 'temp': 2200.0, 'group': 'C-B'},
        'WC': {'weibull': 7.5, 'sample_count': 34, 'temp': 1400.0, 'group': 'C-W'},
        'AlN': {'weibull': 13.0, 'sample_count': 39, 'temp': 1750.0, 'group': 'N-Al'}
    }
    
    # Create 29 rows
    for i in range(29):
        comp = compositions[i % len(compositions)]
        params = composition_params[comp]
        
        data['composition'].append(comp)
        data['weibull_modulus'].append(params['weibull'] + (i * 0.1))  # Small variation
        data['sample_count'].append(params['sample_count'])
        data['sintering_temp'].append(params['temp'] + (i * 5))  # Small variation
        data['primary_anion_cation_group'].append(params['group'])
    
    df = pd.DataFrame(data)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Successfully saved {len(df)} rows to {output_path}")
    
    return df

def main():
    """Main entry point for the script."""
    # Initialize configuration
    initialize_config()
    
    # Define output path
    output_path = Path("data/raw/test_n.csv")
    
    try:
        # Generate the dataset
        df = generate_test_dataset(output_path)
        
        # Verify the row count
        assert len(df) == 29, f"Expected 29 rows, got {len(df)}"
        assert list(df.columns) == [
            'composition', 'weibull_modulus', 'sample_count', 
            'sintering_temp', 'primary_anion_cation_group'
        ], "Column mismatch"
        
        logger.info("Test dataset generation completed successfully.")
        logger.info(f"File location: {output_path.absolute()}")
        
    except Exception as e:
        logger.error(f"Failed to generate test dataset: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
