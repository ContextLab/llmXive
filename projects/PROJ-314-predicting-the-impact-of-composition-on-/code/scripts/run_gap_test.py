import os
import sys
import json
import argparse
from pathlib import Path
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def create_small_sample_dataset(output_path: Path, num_rows: int = 29):
    """
    Create a small sample dataset with exactly num_rows where sample_count >= 30.
    Used to verify T017 halts when total row count < 30.
    """
    if output_dir is None:
        output_dir = DATA_RAW_DIR
    
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "combined_raw.csv"
    
    log.info(f"Creating small sample dataset with {num_rows} rows at {output_path}")
    
    data = {
        'composition': [f'Al2O3_{i}' for i in range(num_rows)],
        'weibull_modulus': [5.0 + (i % 3) for i in range(num_rows)],
        'sample_count': [30 + i for i in range(num_rows)], # All >= 30
        'sintering_temp': [1500 + (i % 100) for i in range(num_rows)]
    }
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    print(f"Created test dataset with {num_rows} rows at {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Run T017 Gap Test")
    parser.add_argument('--rows', type=int, default=29, help="Number of rows to generate")
    parser.add_argument('--output', type=str, default='data/raw/test_n29.csv', help="Output path")
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    create_small_sample_dataset(output_path, args.rows)
    print(f"Test data generated. Run 'python code/ingestion.py --load-test {output_path}' to test T017.")

if __name__ == "__main__":
    main()