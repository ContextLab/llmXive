"""
Script to generate a small test dataset for T017c (Data Gap Validation).
Creates data/raw/test_n.csv with exactly 29 rows to trigger the <30 threshold in T017b.
"""
import os
import sys
import logging
import pandas as pd
from pathlib import Path

# Add parent directory to path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_test_dataset(output_path: str, num_rows: int = 29) -> None:
    """
    Generate a test dataset with specific compositions repeated cyclically.
    
    Args:
        output_path: Full path to the output CSV file.
        num_rows: Number of rows to generate (default 29 to test <30 threshold).
    """
    logger.info(f"Generating test dataset with {num_rows} rows...")
    
    # Fixed list of valid compositions as per task requirements
    compositions = [
        'Al2O3', 'ZrO2', 'SiC', 'Si3N4', 'MgO', 
        'TiC', 'HfC', 'B4C', 'WC', 'AlN'
    ]
    
    # Generate data rows
    data = []
    for i in range(num_rows):
        comp = compositions[i % len(compositions)]
        
        # Create representative but varied data
        # Weibull modulus: float between 5.0 and 25.0
        weibull = 5.0 + (i * 2.0) % 20.0
        
        # Sample count: int >= 30 (valid per T018f-1)
        # This ensures the <30 check is on TOTAL ROWS, not individual sample counts
        sample_count = 30 + (i % 50)
        
        # Sintering temp: float between 1000.0 and 2000.0
        sintering_temp = 1000.0 + (i * 30.0) % 1000.0
        
        # Primary anion/cation group: Derived from composition
        # For simplicity, we map based on the primary anion
        if 'O' in comp:
            primary_group = 'O-Metal'
        elif 'C' in comp:
            primary_group = 'C-Metal'
        elif 'N' in comp:
            primary_group = 'N-Metal'
        else:
            primary_group = 'Unknown'
        
        data.append({
            'composition': comp,
            'weibull_modulus': round(weibull, 2),
            'sample_count': sample_count,
            'sintering_temp': round(sintering_temp, 1),
            'primary_anion_cation_group': primary_group
        })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    
    logger.info(f"Successfully generated {len(df)} rows at {output_path}")
    logger.info(f"Columns: {list(df.columns)}")
    logger.info(f"Sample data:\n{df.head()}")

def main():
    """Main entry point for the script."""
    # Define output path relative to project root
    project_root = Path(__file__).parent.parent.parent
    output_path = project_root / "data" / "raw" / "test_n.csv"
    
    # Generate 29 rows to trigger the <30 threshold in T017b
    generate_test_dataset(str(output_path), num_rows=29)
    
    logger.info("Test dataset generation complete.")

if __name__ == "__main__":
    main()
