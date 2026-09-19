import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_data(csv_path: str) -> pd.DataFrame:
    """
    Load network metrics from a CSV file.

    Args:
        csv_path: Path to the CSV file containing network metrics.

    Returns:
        DataFrame containing the network metrics.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If the CSV file is empty or has incorrect columns.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Network metrics file not found: {csv_path}")

    df = pd.read_csv(path)

    if df.empty:
        raise ValueError(f"Network metrics file is empty: {csv_path}")

    required_columns = ['id', 'class', 'N', 'clustering', 'path_length']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {csv_path}: {missing_cols}")

    logger.info(f"Loaded {len(df)} networks from {csv_path}")
    return df

def get_predictor_count(df: pd.DataFrame) -> int:
    """
    Count the number of predictor variables (topological metrics).

    Args:
        df: DataFrame containing network metrics.

    Returns:
        Number of predictor variables.
    """
    # Define predictor columns based on typical network metrics
    # excluding identifiers and the target (if any)
    predictor_cols = ['clustering', 'path_length', 'average_degree', 'density', 'transitivity']
    present_cols = [col for col in predictor_cols if col in df.columns]
    return len(present_cols) if present_cols else len([c for c in df.columns if c not in ['id', 'class', 'N']])

def check_power_limitation(df: pd.DataFrame, min_samples_per_class: int = 10, num_classes: int = 5) -> Dict[str, Any]:
    """
    Check if the dataset size meets the power limitation requirements.

    Spec FR-001 mandates at least 50 samples total (10 per class * 5 classes).

    Args:
        df: DataFrame containing network metrics.
        min_samples_per_class: Minimum required samples per class.
        num_classes: Expected number of topological classes.

    Returns:
        Dictionary with power analysis results:
        - 'valid': bool, True if requirements are met
        - 'total_samples': int
        - 'samples_per_class': dict, count per class
        - 'missing_classes': list, classes with insufficient samples
        - 'message': str, human-readable summary
    """
    total_samples = len(df)
    required_total = min_samples_per_class * num_classes

    # Count samples per class
    if 'class' in df.columns:
        class_counts = df['class'].value_counts().to_dict()
        classes_present = list(class_counts.keys())
        missing_classes = [f"Class '{c}'" for c in classes_present if class_counts.get(c, 0) < min_samples_per_class]
    else:
        class_counts = {}
        missing_classes = ["Class column missing"]

    # Determine validity
    is_valid = total_samples >= required_total and len(missing_classes) == 0

    result = {
        'valid': is_valid,
        'total_samples': total_samples,
        'required_total': required_total,
        'samples_per_class': class_counts,
        'missing_classes': missing_classes,
        'message': f"Total samples: {total_samples}/{required_total}"
    }

    if is_valid:
        result['message'] += " - Power requirement MET."
    else:
        reasons = []
        if total_samples < required_total:
            reasons.append(f"Total sample size ({total_samples}) is below required ({required_total})")
        if missing_classes:
            reasons.append(f"Insufficient samples in: {', '.join(missing_classes)}")
        result['message'] += f" - Power requirement FAILED: {'; '.join(reasons)}"

    return result

def write_warning_message(result: Dict[str, Any], output_path: str) -> None:
    """
    Write a specific warning message to a file if power requirements are not met.

    Args:
        result: Dictionary from check_power_limitation containing analysis results.
        output_path: Path to the output text file.
    """
    if result['valid']:
        logger.info("Power requirement met. No warning file generated.")
        return

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "POWER LIMITATION WARNING",
        "=" * 50,
        "",
        f"Status: FAILED",
        f"Reason: Dataset size is insufficient for statistical power.",
        "",
        f"Required Total Samples: {result['required_total']}",
        f"Actual Total Samples: {result['total_samples']}",
        "",
        "Detailed Issues:"
    ]

    if result['total_samples'] < result['required_total']:
        lines.append(f"- Total sample size ({result['total_samples']}) is below the minimum required ({result['required_total']}).")

    if result['missing_classes']:
        lines.append(f"- Insufficient samples per class (min {result['samples_per_class']} per class):")
        for cls in result['missing_classes']:
            lines.append(f"  * {cls}")

    lines.extend([
        "",
        "Action Required:",
        "  Halting execution of simulation tasks (T021b) as mandated by Spec FR-001.",
        "  Please generate additional network samples to meet the power requirement.",
        "",
        "Timestamp: " + str(pd.Timestamp.now())
    ])

    content = "\n".join(lines)
    path.write_text(content)
    logger.warning(f"Power warning written to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Check power limitation for network simulation.")
    parser.add_argument(
        '--input',
        type=str,
        default='data/raw/networks.csv',
        help='Path to the network metrics CSV file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/analysis/power_warning.txt',
        help='Path to the output warning file (only created if check fails)'
    )
    parser.add_argument(
        '--min-samples',
        type=int,
        default=10,
        help='Minimum samples required per class'
    )
    parser.add_argument(
        '--num-classes',
        type=int,
        default=5,
        help='Number of expected topological classes'
    )

    args = parser.parse_args()

    try:
        logger.info(f"Loading data from {args.input}")
        df = load_data(args.input)

        logger.info("Checking power limitation")
        result = check_power_limitation(df, args.min_samples, args.num_classes)

        logger.info(result['message'])

        if not result['valid']:
            write_warning_message(result, args.output)
            logger.error("Power requirement not met. Halting execution.")
            sys.exit(1)
        else:
            logger.info("Power requirement satisfied. Proceeding.")
            sys.exit(0)

    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
