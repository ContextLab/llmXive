import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
import pandas as pd

from src.utils.io import ensure_directory, set_global_seed
from src.analysis.power import calculate_min_sample_size

logger = logging.getLogger(__name__)


def load_required_n(state_dir: Path) -> int:
    """
    Load the required sample size N from the power analysis state file.
    
    Args:
        state_dir: Path to the state directory.
        
    Returns:
        The required minimum sample size (int).
        
    Raises:
        FileNotFoundError: If the power analysis file does not exist.
        ValueError: If the required N is not found in the file.
    """
    power_file = state_dir / "power_analysis.yaml"
    if not power_file.exists():
        raise FileNotFoundError(f"Power analysis file not found: {power_file}")
    
    with open(power_file, 'r') as f:
        data = yaml.safe_load(f)
    
    required_n = data.get('required_sample_size')
    if required_n is None:
        raise ValueError("Required sample size 'required_sample_size' not found in power analysis file.")
    
    return int(required_n)


def load_actual_n(data_path: Path) -> int:
    """
    Load the actual sample size N from the processed features file.
    
    Args:
        data_path: Path to the processed features CSV file.
        
    Returns:
        The actual number of rows (int).
        
    Raises:
        FileNotFoundError: If the data file does not exist.
        ValueError: If the file is empty or cannot be read.
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Processed data file not found: {data_path}")
    
    try:
        df = pd.read_csv(data_path)
        actual_n = len(df)
        if actual_n == 0:
            raise ValueError("Processed data file is empty.")
        return actual_n
    except Exception as e:
        raise ValueError(f"Failed to read processed data file: {e}")


def verify_sample_size(
    required_n: int,
    actual_n: int
) -> Dict[str, Any]:
    """
    Compare actual N against required N and determine status.
    
    Args:
        required_n: The minimum sample size required for the study.
        actual_n: The actual sample size available in the dataset.
        
    Returns:
        A dictionary containing the verification results.
    """
    is_sufficient = actual_n >= required_n
    status = "PASS" if is_sufficient else "WARNING"
    
    result = {
        "required_sample_size": required_n,
        "actual_sample_size": actual_n,
        "is_sufficient": is_sufficient,
        "status": status,
        "message": (
            f"Sample size verification {'PASSED' if is_sufficient else 'FAILED'}. "
            f"Actual N ({actual_n}) {'meets' if is_sufficient else 'does not meet'} "
            f"the required N ({required_n})."
        )
    }
    
    if not is_sufficient:
        result["warning"] = (
            "Power Limitation Warning: The actual sample size is smaller than "
            "the required sample size calculated for the desired power (0.80). "
            "Statistical results may have lower power than intended."
        )
        
    return result


def save_verification_report(
    result: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Save the verification report to a YAML file.
    
    Args:
        result: The verification result dictionary.
        output_path: Path where the report should be saved.
    """
    ensure_directory(output_path.parent)
    
    report = {
        "task_id": "T022",
        "verification_status": result["status"],
        "details": result,
        "timestamp": None  # Will be set by main if needed, or left null for reproducibility
    }
    
    with open(output_path, 'w') as f:
        yaml.dump(report, f, default_flow_style=False, sort_keys=False)
        
    logger.info(f"Verification report saved to {output_path}")


def run_verification(
    data_path: Path,
    state_dir: Path,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run the full verification workflow: load required N, load actual N, compare, and save.
    
    Args:
        data_path: Path to the processed features CSV file.
        state_dir: Path to the state directory containing power_analysis.yaml.
        output_path: Optional path for the verification report. Defaults to state_dir/verification.yaml.
        
    Returns:
        The verification result dictionary.
        
    Raises:
        FileNotFoundError: If required input files are missing.
        ValueError: If data is invalid.
    """
    if output_path is None:
        output_path = state_dir / "verification.yaml"
        
    logger.info(f"Starting sample size verification...")
    logger.info(f"  - Data path: {data_path}")
    logger.info(f"  - State dir: {state_dir}")
    
    # Load required N
    required_n = load_required_n(state_dir)
    logger.info(f"  - Required N from power analysis: {required_n}")
    
    # Load actual N
    actual_n = load_actual_n(data_path)
    logger.info(f"  - Actual N from dataset: {actual_n}")
    
    # Verify
    result = verify_sample_size(required_n, actual_n)
    logger.info(f"  - Status: {result['status']}")
    logger.info(f"  - Message: {result['message']}")
    
    # Save
    save_verification_report(result, output_path)
    
    return result


def main() -> int:
    """
    Main entry point for the verification script.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    set_global_seed(42)
    
    # Default paths relative to project root
    project_root = Path(__file__).resolve().parents[2]
    data_path = project_root / "data" / "processed" / "features.csv"
    state_dir = project_root / "state"
    output_path = state_dir / "verification.yaml"
    
    try:
        result = run_verification(data_path, state_dir, output_path)
        
        if result["status"] == "WARNING":
            logger.warning(result["warning"])
            return 0  # Still success, but with a warning
        else:
            return 0
            
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
