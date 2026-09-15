"""
Script to generate test data for data gap validation (T017c).
Creates data/raw/test_n.csv with exactly 29 rows to verify T017b halts correctly.
"""
import os
import sys
import logging
import pandas as pd
from pathlib import Path
from config import initialize_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_test_dataset(output_path: str, num_rows: int = 29) -> None:
    """
    Generate a test dataset with exactly num_rows rows.
    
    Args:
        output_path: Path to save the CSV file.
        num_rows: Number of rows to generate (default 29).
    """
    # Fixed list of valid compositions as per task specification
    compositions = [
        'Al2O3', 'ZrO2', 'SiC', 'Si3N4', 'MgO', 
        'TiC', 'HfC', 'B4C', 'WC', 'AlN'
    ]
    
    # Generate data by cycling through compositions
    data = []
    for i in range(num_rows):
        composition = compositions[i % len(compositions)]
        
        # Generate realistic but deterministic values
        # Weibull modulus typically ranges from 5 to 30 for ceramics
        weibull_modulus = 10.0 + (i * 0.5) % 15.0
        
        # Sample count must be valid (>= 30) but total rows < 30 triggers the gap
        sample_count = 30 + (i % 20)
        
        # Sintering temperature in Celsius
        sintering_temp = 1200.0 + (i * 50.0) % 800.0
        
        # Primary anion/cation group (derived from composition)
        # For simplicity, we use a mapping based on the primary cation
        group_mapping = {
            'Al2O3': 'O-Al',
            'ZrO2': 'O-Zr',
            'SiC': 'C-Si',
            'Si3N4': 'N-Si',
            'MgO': 'O-Mg',
            'TiC': 'C-Ti',
            'HfC': 'C-Hf',
            'B4C': 'C-B',
            'WC': 'C-W',
            'AlN': 'N-Al'
        }
        primary_anion_cation_group = group_mapping.get(composition, 'Unknown')
        
        data.append({
            'composition': composition,
            'weibull_modulus': round(weibull_modulus, 2),
            'sample_count': sample_count,
            'sintering_temp': round(sintering_temp, 1),
            'primary_anion_cation_group': primary_anion_cation_group
        })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Generated test dataset with {len(df)} rows at {output_path}")
    logger.info(f"Columns: {list(df.columns)}")
    logger.info(f"Row count: {len(df)} (expected: {num_rows})")
    
    # Verify row count
    if len(df) != num_rows:
        raise ValueError(f"Expected {num_rows} rows but generated {len(df)}")
    
    logger.info("Test dataset generation completed successfully.")

def main():
    """Main entry point for the script."""
    # Initialize configuration
    initialize_config()
    
    # Define output path
    project_root = Path(__file__).parent.parent.parent
    output_path = project_root / "data" / "raw" / "test_n.csv"
    
    # Generate the dataset with exactly 29 rows
    generate_test_dataset(str(output_path), num_rows=29)
    
    logger.info(f"Successfully created {output_path} with 29 rows for T017c verification.")

if __name__ == "__main__":
    main()