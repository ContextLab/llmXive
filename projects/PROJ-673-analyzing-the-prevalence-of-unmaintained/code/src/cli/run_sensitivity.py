import argparse
import logging
from pathlib import Path
from src.analysis.sensitivity_analysis import run_sensitivity_analysis
from src.config.settings import get_config

def main():
    parser = argparse.ArgumentParser(description='Run sensitivity analysis pipeline.')
    parser.add_argument('--input', type=str, default='data/processed/dependencies_raw.csv',
                        help='Input CSV file path')
    parser.add_argument('--output', type=str, default='data/processed/sensitivity_analysis.json',
                        help='Output JSON file path')
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    config = get_config()
    base = getattr(config, 'UNMAINTAINED_THRESHOLD_BASE', 180)
    delta = getattr(config, 'UNMAINTAINED_THRESHOLD_DELTA', 90)
    
    # Define the sweep range: 90 to 270 with step 10
    start = base - delta
    end = base + delta
    threshold_range = list(range(start, end + 1, 10))
    
    logging.info(f"Running sensitivity analysis with threshold range: {threshold_range}")
    
    try:
        result = run_sensitivity_analysis(
            input_path=args.input,
            output_path=args.output,
            threshold_range=threshold_range
        )
        
        logging.info(f"Success. Output written to {args.output}")
        logging.info(f"Thresholds analyzed: {len(result['threshold_sweep'])}")
        
    except FileNotFoundError as e:
        logging.error(f"Input file not found: {e}")
        raise
    except Exception as e:
        logging.error(f"Analysis failed: {e}")
        raise

if __name__ == '__main__':
    main()
