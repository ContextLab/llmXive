"""
Script to test the data gap validation logic (T017).
This script creates a small sample dataset and runs the validation.
"""
import os
import sys
import json
import argparse
from pathlib import Path
import pandas as pd
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ingestion import validate_data_gap, DATA_RAW_DIR, DATA_REPORTS_DIR, MIN_VALID_ENTRIES

def create_small_sample_dataset(num_rows: int = 29, output_dir: Path = None):
    """
    Creates a small sample dataset with exactly num_rows entries.
    """
    if output_dir is None:
        output_dir = DATA_RAW_DIR
    
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "combined_raw.csv"
    
    log.info(f"Creating small sample dataset with {num_rows} rows at {output_path}")
    
    data = {
        'composition': [f'Ceramic_{i}' for i in range(num_rows)],
        'weibull_modulus': [10.0 + (i * 0.5) for i in range(num_rows)],
        'sample_count': [50] * num_rows,
        'primary_anion_cation_group': ['O-Al'] * num_rows
    }
    
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    
    log.info(f"Dataset created successfully: {output_path}")
    return output_path

def main():
    parser = argparse.ArgumentParser(description="Test data gap validation (T017)")
    parser.add_argument('--rows', type=int, default=29, help='Number of rows in test dataset')
    parser.add_argument('--output-dir', type=str, default=None, help='Output directory for test data')
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir) if args.output_dir else DATA_RAW_DIR
    
    # Create test dataset
    create_small_sample_dataset(args.rows, output_dir)
    
    # Run validation
    log.info("Running data gap validation...")
    passed, df = validate_data_gap()
    
    if passed:
        log.info("Validation PASSED (unexpected for small sample)")
        sys.exit(0)
    else:
        log.info("Validation FAILED as expected (data gap detected)")
        # Check if report was generated
        report_path = DATA_REPORTS_DIR / "data_availability_report.json"
        if report_path.exists():
            log.info(f"Report generated: {report_path}")
            with open(report_path, 'r') as f:
                report = json.load(f)
            log.info(f"Report content: {json.dumps(report, indent=2)}")
        else:
            log.error("Report was NOT generated!")
            sys.exit(1)

if __name__ == "__main__":
    main()