import sys
import os
from pathlib import Path
import logging
from src.validate_metrics import validate_schema_and_metrics, DataIntegrityError
from src.config import get_memory_limit_bytes

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    if len(sys.argv) < 2:
        print("Usage: python run_validation_pipeline.py <input_csv_path> [output_csv_path]")
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    
    if not input_path.exists():
        logging.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    try:
        # Check memory limit
        limit = get_memory_limit_bytes()
        logging.info(f"Memory limit set to {limit / (1024*1024):.2f} MB")
        
        import pandas as pd
        df = pd.read_csv(input_path)
        logging.info(f"Loaded {len(df)} rows from {input_path}")
        
        validated_df = validate_schema_and_metrics(df, output_path)
        logging.info("Validation successful.")
        
    except DataIntegrityError as e:
        logging.error(f"Data Integrity Error: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
