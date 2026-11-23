"""
Descriptor Leakage Audit Module (T066).

Extends the data leakage audit (T045) to check for descriptor leakage.
Ensures that no descriptor values in the test set are derived from 
the test set's target variables (e.g., if a descriptor is calculated 
using target data).

Dependencies: T014ba-1, T014bb-1, T014bc-1, T045
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Set, List, Tuple
import pandas as pd

# Import existing entities and utilities
from models.audit import ensure_dirs as ensure_audit_dirs, load_split_data
from data.descriptors import calculate_descriptors_batch

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Known target columns that must NOT be used to derive descriptors
TARGET_COLUMNS = {
    'langmuir_capacity', 
    'henry_constant', 
    'isotherm_type', 
    'adsorption_volume'
}

# Known descriptor columns (calculated by descriptors.py)
DESCRIPTOR_COLUMNS = {
    'molecular_weight',
    'polar_surface_area',
    'polarizability',
    'kinetic_diameter',
    'lj_epsilon',
    'quadrupole_moment',
    'vdw_volume',
    'descriptor_hash'
}

class DescriptorLeakageError(Exception):
    """Raised when descriptor leakage is detected."""
    pass

def ensure_dirs(base_path: Optional[Path] = None) -> Path:
    """Ensure the audit directory exists."""
    if base_path is None:
        base_path = Path.cwd()
    audit_dir = base_path / "data" / "validation"
    audit_dir.mkdir(parents=True, exist_ok=True)
    return audit_dir

def load_split_data(data_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load train and test splits from the data directory.
    Expects data to be in a format produced by the training pipeline.
    """
    train_path = data_dir / "train_split.csv"
    test_path = data_dir / "test_split.csv"
    
    if not train_path.exists():
        # Try to find any split files
        train_files = list(data_dir.glob("*train*.csv"))
        if train_files:
            train_path = train_files[0]
        else:
            raise FileNotFoundError(f"Training data not found in {data_dir}")
    
    if not test_path.exists():
        test_files = list(data_dir.glob("*test*.csv"))
        if test_files:
            test_path = test_files[0]
        else:
            raise FileNotFoundError(f"Test data not found in {data_dir}")
    
    logger.info(f"Loading training data from {train_path}")
    logger.info(f"Loading test data from {test_path}")
    
    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)
    
    return train_df, test_df

def check_descriptor_leakage(
    train_df: pd.DataFrame, 
    test_df: pd.DataFrame,
    descriptor_columns: Set[str],
    target_columns: Set[str]
) -> Dict[str, Any]:
    """
    Check for descriptor leakage in the test set.
    
    Leakage occurs if:
    1. A descriptor column in the test set contains values that are 
       directly derived from target variables (e.g., if a descriptor 
       was calculated using target data).
    2. There is a suspicious correlation between descriptors and targets 
       that suggests data leakage in the calculation process.
    
    Returns a report with leakage findings.
    """
    report = {
        "status": "passed",
        "leakage_detected": False,
        "findings": [],
        "details": {
            "train_descriptors": [],
            "test_descriptors": [],
            "suspicious_correlations": [],
            "validation_checks": []
        }
    }
    
    # Check 1: Verify descriptor columns exist in both sets
    train_desc_cols = set(train_df.columns) & descriptor_columns
    test_desc_cols = set(test_df.columns) & descriptor_columns
    
    report["details"]["train_descriptors"] = sorted(list(train_desc_cols))
    report["details"]["test_descriptors"] = sorted(list(test_desc_cols))
    
    missing_in_test = train_desc_cols - test_desc_cols
    if missing_in_test:
        report["findings"].append(
            f"Descriptor columns missing in test set: {missing_in_test}"
        )
    
    # Check 2: Verify no target columns are in descriptor columns
    # This would indicate a calculation error where targets were used
    # to compute descriptors
    for desc_col in descriptor_columns:
        if desc_col in target_columns:
            report["findings"].append(
                f"CRITICAL: Descriptor column '{desc_col}' is also a target column. "
                "This indicates a calculation error."
            )
            report["status"] = "failed"
            report["leakage_detected"] = True
    
    # Check 3: Analyze statistical properties for suspicious patterns
    # If descriptors were calculated using target data, we might see
    # perfect correlations or identical values across different targets
    if len(test_df) > 10 and len(test_desc_cols) > 0:
        test_desc_df = test_df[list(test_desc_cols)]
        test_target_df = test_df[list(target_columns & set(test_df.columns))]
        
        if not test_target_df.empty:
            # Calculate correlations between descriptors and targets
            for desc_col in test_desc_cols:
                for target_col in test_target_df.columns:
                    if desc_col in test_desc_df.columns and target_col in test_target_df.columns:
                        if test_desc_df[desc_col].std() > 0 and test_target_df[target_col].std() > 0:
                            correlation = test_desc_df[desc_col].corr(test_target_df[target_col])
                            if abs(correlation) > 0.99:
                                report["findings"].append(
                                    f"Suspicious correlation ({correlation:.4f}) between "
                                    f"descriptor '{desc_col}' and target '{target_col}'. "
                                    "This may indicate leakage."
                                )
                                report["details"]["suspicious_correlations"].append({
                                    "descriptor": desc_col,
                                    "target": target_col,
                                    "correlation": float(correlation)
                                })
    
    # Check 4: Verify that descriptor calculations are independent of targets
    # by checking if the same molecular structure produces the same descriptors
    # regardless of the target value (if we have duplicate structures)
    if 'adsorbent_structure_id' in test_df.columns:
        structure_groups = test_df.groupby('adsorbent_structure_id')
        duplicate_structures = [gid for gid, group in structure_groups if len(group) > 1]
        
        for structure_id in duplicate_structures[:10]:  # Check first 10 duplicates
            group = structure_groups.get_group(structure_id)
            if len(group) > 1:
                # Check if descriptors are consistent across the same structure
                for desc_col in test_desc_cols:
                    if desc_col in group.columns:
                        desc_values = group[desc_col].unique()
                        if len(desc_values) > 1:
                            # Descriptors should be identical for the same structure
                            # unless there's calculation noise or leakage
                            variance = group[desc_col].var()
                            if variance > 0.001:  # Threshold for numerical precision
                                report["findings"].append(
                                    f"Descriptor '{desc_col}' varies for the same structure "
                                    f"'{structure_id}' (variance={variance:.6f}). "
                                    "This may indicate calculation inconsistency or leakage."
                                )
    
    # Final determination
    if report["findings"]:
        report["status"] = "warning"
        if any("CRITICAL" in f or "leakage" in f.lower() for f in report["findings"]):
            report["status"] = "failed"
            report["leakage_detected"] = True
    
    return report

def write_leakage_report(report: Dict[str, Any], output_path: Path) -> None:
    """Write the leakage report to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Descriptor leakage report written to {output_path}")

def run_descriptor_audit_pipeline(
    data_dir: Path,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run the complete descriptor leakage audit pipeline.
    
    Args:
        data_dir: Directory containing train/test splits
        output_dir: Directory to write the report (defaults to data_dir/validation)
        
    Returns:
        The audit report dictionary
    """
    if output_dir is None:
        output_dir = ensure_dirs(data_dir)
    else:
        output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting descriptor leakage audit (T066)")
    
    try:
        # Load the data
        train_df, test_df = load_split_data(data_dir)
        logger.info(f"Loaded {len(train_df)} training and {len(test_df)} test samples")
        
        # Perform the leakage check
        report = check_descriptor_leakage(
            train_df, 
            test_df, 
            DESCRIPTOR_COLUMNS, 
            TARGET_COLUMNS
        )
        
        # Write the report
        report_path = output_dir / "descriptor_leakage_report.json"
        write_leakage_report(report, report_path)
        
        # If leakage is detected, raise an error
        if report["leakage_detected"]:
            raise DescriptorLeakageError(
                f"Descriptor leakage detected: {report['findings']}"
            )
        
        logger.info("Descriptor leakage audit completed successfully")
        return report
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        raise
    except DescriptorLeakageError as e:
        logger.error(f"Descriptor leakage detected: {e}")
        raise
    except Exception as e:
        logger.error(f"Audit failed with unexpected error: {e}")
        raise

def main():
    """Main entry point for the descriptor leakage audit."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run descriptor leakage audit (T066)"
    )
    parser.add_argument(
        "--data-dir", 
        type=Path, 
        default=Path("data/processed"),
        help="Directory containing train/test splits"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory to write the report"
    )
    
    args = parser.parse_args()
    
    try:
        report = run_descriptor_audit_pipeline(args.data_dir, args.output_dir)
        print(json.dumps(report, indent=2))
        sys.exit(0)
    except Exception as e:
        print(f"Audit failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()