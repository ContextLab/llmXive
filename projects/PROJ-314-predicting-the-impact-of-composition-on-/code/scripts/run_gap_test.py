"""
Run the data gap test using the test dataset.
This script verifies that the pipeline halts with sys.exit(1) when N < 30.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/gap_test.log')
    ]
)
logger = logging.getLogger(__name__)

def create_small_sample_dataset(output_path: str = "data/raw/test_n.csv", n_rows: int = 29):
    """
    Create a small sample dataset for testing the data gap protocol.
    
    Args:
        output_path: Path to save the CSV file
        n_rows: Number of rows (default 29 to trigger data gap)
    """
    import pandas as pd
    
    # Fixed list of valid compositions
    compositions = [
        'Al2O3', 'ZrO2', 'SiC', 'Si3N4', 'MgO', 'TiC', 
        'HfC', 'B4C', 'WC', 'AlN'
    ]
    
    data = {
        'composition': [],
        'weibull_modulus': [],
        'sample_count': [],
        'sintering_temp': [],
        'primary_anion_cation_group': []
    }
    
    for i in range(n_rows):
        comp = compositions[i % len(compositions)]
        
        # Simple heuristic for anion/cation group
        if 'O' in comp:
            group = f"O-{comp.split('O')[0].strip()}"
        elif 'N' in comp:
            group = f"N-{comp.split('N')[0].strip()}"
        elif 'C' in comp:
            group = f"C-{comp.split('C')[0].strip()}"
        else:
            group = "Unknown"
        
        data['composition'].append(comp)
        data['weibull_modulus'].append(5.0 + (i % 5) * 2.0)
        data['sample_count'].append(35)
        data['sintering_temp'].append(1500.0 + (i % 10) * 50.0)
        data['primary_anion_cation_group'].append(group)
    
    df = pd.DataFrame(data)
    
    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Created small sample dataset with {len(df)} rows at {output_path}")
    return df

def main():
    """Main entry point for the gap test."""
    parser = argparse.ArgumentParser(description="Run data gap validation test")
    parser.add_argument("--n", type=int, default=29, help="Number of rows (default 29)")
    parser.add_argument("--dataset", default="data/raw/test_n.csv", help="Path to test dataset")
    args = parser.parse_args()
    
    logger.info(f"Starting data gap test with N={args.n}")
    
    # Create test dataset if it doesn't exist
    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        logger.info("Test dataset not found, creating...")
        create_small_sample_dataset(args.dataset, args.n)
    else:
        logger.info(f"Using existing dataset at {args.dataset}")
    
    # Verify dataset size
    import pandas as pd
    df = pd.read_csv(args.dataset)
    logger.info(f"Dataset contains {len(df)} rows")
    
    if len(df) != args.n:
        logger.warning(f"Dataset has {len(df)} rows, expected {args.n}")
    
    # Run the ingestion pipeline (which should trigger data gap check)
    try:
        from ingestion import main as run_ingestion
        
        # Set environment to use test dataset
        os.environ['TEST_DATASET_PATH'] = args.dataset
        
        # Run ingestion - this should exit with code 1 if N < 30
        logger.info("Running ingestion pipeline...")
        run_ingestion()
        
        # If we reach here, the pipeline did not exit (unexpected for N < 30)
        logger.error("Pipeline completed without exiting (expected exit code 1 for N < 30)")
        sys.exit(1)
        
    except SystemExit as e:
        if e.code == 1:
            logger.info("Pipeline correctly exited with code 1 (data gap detected)")
            
            # Verify report was generated
            report_path = Path("data/reports/data_availability_report.json")
            if report_path.exists():
                logger.info(f"Data availability report generated at {report_path}")
                with open(report_path, 'r') as f:
                    report = json.load(f)
                logger.info(f"Report content: {json.dumps(report, indent=2)}")
                sys.exit(0)
            else:
                logger.error("Data availability report not found")
                sys.exit(1)
        else:
            logger.error(f"Pipeline exited with unexpected code: {e.code}")
            sys.exit(e.code)
    except Exception as e:
        logger.error(f"Pipeline failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
