"""
Create test dataset for data gap validation (T017c).
Generates data/raw/test_n.csv with exactly 29 rows.
"""
import os
import sys
import logging
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import initialize_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/test_data.log')
    ]
)
logger = logging.getLogger(__name__)

def generate_test_dataset(num_rows: int = 29, output_path: str = 'data/raw/test_n.csv'):
    """
    Generate a test dataset with specific compositions to trigger data gap validation.
    
    Args:
        num_rows: Number of rows to generate (default 29 to trigger < 30 condition)
        output_path: Path to save the CSV file
    
    Returns:
        Path to the generated file
    """
    # Initialize config to ensure directories exist
    initialize_config()
    
    # Fixed list of valid compositions as per T017c
    compositions = ['Al2O3', 'ZrO2', 'SiC', 'Si3N4', 'MgO', 'TiC', 'HfC', 'B4C', 'WC', 'AlN']
    
    # Generate data
    data = {
        'composition': [],
        'weibull_modulus': [],
        'sample_count': [],
        'sintering_temp': [],
        'primary_anion_cation_group': []
    }
    
    for i in range(num_rows):
        comp = compositions[i % len(compositions)]
        data['composition'].append(comp)
        data['weibull_modulus'].append(10.0 + (i % 5))  # Values between 10 and 14
        data['sample_count'].append(35)  # Valid sample count >= 30
        data['sintering_temp'].append(1500.0 + (i % 100))
        
        # Simple mapping for primary_anion_cation_group based on composition
        if 'O' in comp:
            data['primary_anion_cation_group'].append('O-Metal')
        elif 'N' in comp:
            data['primary_anion_cation_group'].append('N-Metal')
        elif 'C' in comp:
            data['primary_anion_cation_group'].append('C-Metal')
        else:
            data['primary_anion_cation_group'].append('Unknown')
    
    df = pd.DataFrame(data)
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_file, index=False)
    logger.info(f"Generated test dataset with {num_rows} rows: {output_file}")
    
    return output_file

def main():
    """Main entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Generate test dataset for data gap validation")
    parser.add_argument('--rows', type=int, default=29, help="Number of rows to generate")
    parser.add_argument('--output', type=str, default='data/raw/test_n.csv', help="Output file path")
    args = parser.parse_args()

    try:
        result = generate_test_dataset(args.rows, args.output)
        logger.info(f"Test dataset created successfully at {result}")
        return 0
    except Exception as e:
        logger.error(f"Failed to generate test dataset: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())