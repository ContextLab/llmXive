import logging
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from utils import get_logger, get_project_paths

def calculate_cohen_d(group1: List[float], group2: List[float]) -> float:
    """
    Calculate Cohen's d effect size between two groups.
    """
    if not group1 or not group2:
        return 0.0
    
    n1, n2 = len(group1), len(group2)
    mean1, mean2 = sum(group1) / n1, sum(group2) / n2
    
    var1 = sum((x - mean1) ** 2 for x in group1) / (n1 - 1) if n1 > 1 else 0
    var2 = sum((x - mean2) ** 2 for x in group2) / (n2 - 1) if n2 > 1 else 0
    
    pooled_std = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
    pooled_std = pooled_std ** 0.5
    
    if pooled_std == 0:
        return 0.0
        
    return (mean1 - mean2) / pooled_std

def interpret_effect_size(d: float) -> str:
    """
    Interpret Cohen's d magnitude.
    """
    abs_d = abs(d)
    if abs_d < 0.2:
        return "negligible"
    elif abs_d < 0.5:
        return "small"
    elif abs_d < 0.8:
        return "medium"
    else:
        return "large"

def check_dataset_power(n: int, alpha: float = 0.05, power_threshold: float = 0.80) -> Dict[str, Any]:
    """
    Perform a simplified power check based on sample size n.
    For a two-sample t-test with medium effect size (d=0.5), 
    n=150 per group is typically sufficient for >0.8 power.
    Here we check total n against a heuristic threshold.
    """
    # Heuristic: For medium effect size, total N ~ 128-150 is often the cutoff for 80% power
    # The task specifically requires a warning if n < 150.
    is_power_sufficient = n >= 150
    
    return {
        "n": n,
        "alpha": alpha,
        "power_threshold": power_threshold,
        "power_warning": not is_power_sufficient,
        "interpretation": "Insufficient power" if not is_power_sufficient else "Adequate power for medium effect"
    }

def run_power_analysis_from_csv(csv_path: str, logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
    """
    Read the polyester filter report CSV, count valid records, 
    and perform power analysis.
    """
    if logger is None:
        logger = get_logger(__name__)
    
    path = Path(csv_path)
    if not path.exists():
        logger.error(f"Input file not found: {csv_path}")
        raise FileNotFoundError(f"Input file not found: {csv_path}")
    
    count = 0
    try:
        with open(path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Count rows that have the expected data (excluding header)
                if row: 
                    count += 1
    except Exception as e:
        logger.error(f"Error reading CSV: {e}")
        raise
    
    logger.info(f"Read {count} records from {csv_path}")
    
    analysis_result = check_dataset_power(count)
    
    if analysis_result["power_warning"]:
        logger.warning(f"POWER WARNING: Dataset size (n={count}) is below the threshold of 150. Statistical power may be insufficient.")
    else:
        logger.info(f"Power analysis passed: n={count} meets threshold.")
        
    return analysis_result

def main():
    """
    Main entry point for T015b: Power Analysis.
    Reads data/processed/polyester_filter_report.csv and generates
    data/reports/power_analysis_report.json.
    """
    paths = get_project_paths()
    input_file = paths['data_processed'] / "polyester_filter_report.csv"
    output_file = paths['data_reports'] / "power_analysis_report.json"
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger = get_logger(__name__)
    
    try:
        result = run_power_analysis_from_csv(str(input_file), logger)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Power analysis report saved to {output_file}")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Critical error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during power analysis: {e}")
        return 1

if __name__ == "__main__":
    import sys
    # Ensure utils is in path if running as script
    sys.path.insert(0, str(Path(__file__).parent))
    from utils import setup_logging
    setup_logging()
    sys.exit(main())
