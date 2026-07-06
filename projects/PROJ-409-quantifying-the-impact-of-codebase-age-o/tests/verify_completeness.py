import csv
import sys
import logging
from pathlib import Path
from typing import List, Optional

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger

logger = get_logger(__name__)

TARGET_COMPLETENESS_RATE = 0.95

def calculate_completeness_rate(file_path: Path) -> Optional[float]:
    """
    Calculate the data completeness rate for the inference results.
    
    A data point is considered 'valid' if:
    - The row exists
    - `perplexity` is not null/empty/NaN
    - `functional_correctness_rate` is not null/empty/NaN
    
    Completeness = (Valid Rows) / (Total Rows with Snippet ID)
    
    Args:
        file_path: Path to the inference results CSV
        
    Returns:
        The completeness rate (0.0 to 1.0) or None if file missing/empty
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return None

    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                logger.error("File is empty or has no header.")
                return None

            total_rows = 0
            valid_rows = 0

            for row in reader:
                # Skip rows without a snippet_id (invalid extraction)
                if not row.get('snippet_id') or row.get('snippet_id').strip() == '':
                    continue
                
                total_rows += 1

                # Check if metrics are valid
                pplx = row.get('perplexity', '').strip()
                correct = row.get('functional_correctness_rate', '').strip()

                is_valid_pplx = pplx and pplx.lower() != 'nan' and pplx != ''
                is_valid_correct = correct and correct.lower() != 'nan' and correct != ''

                if is_valid_pplx and is_valid_correct:
                    valid_rows += 1

            if total_rows == 0:
                logger.warning("No valid snippet rows found in file.")
                return 0.0

            rate = valid_rows / total_rows
            logger.info(f"Completeness calculation: {valid_rows}/{total_rows} = {rate:.2%}")
            return rate

    except Exception as e:
        logger.error(f"Error calculating completeness: {e}")
        return None

def main():
    """
    Main entry point to verify data completeness rate.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    data_results_dir = project_root / 'data' / 'results'
    inference_output_path = data_results_dir / 'inference_results.csv'

    rate = calculate_completeness_rate(inference_output_path)

    if rate is None:
        logger.error("❌ T019.2 Verification FAILED: Could not calculate completeness (file missing or error).")
        sys.exit(1)

    if rate >= TARGET_COMPLETENESS_RATE:
        logger.info(f"✅ T019.2 Verification PASSED: Completeness rate {rate:.2%} >= {TARGET_COMPLETENESS_RATE:.2%} target.")
        sys.exit(0)
    else:
        logger.error(f"❌ T019.2 Verification FAILED: Completeness rate {rate:.2%} < {TARGET_COMPLETENESS_RATE:.2%} target.")
        sys.exit(1)

if __name__ == '__main__':
    main()