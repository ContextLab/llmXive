"""
Schema definition and validation for sensitivity_report.csv.

This module defines the structure and data types for the sensitivity report
generated during the dynamic shift analysis (US1).

Columns:
    env_id (str): Environment identifier
    shift_step (int): Step at which the dynamic shift occurs
    pre_shift_score (float): Agent performance score before shift
    post_shift_score (float): Agent performance score after shift
    drop_rate (float): Ratio of performance drop (0.0-1.0)
    p_value (float): Statistical significance of the performance drop
"""
import csv
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

# Column definitions
SENSITIVITY_REPORT_COLUMNS = [
    'env_id',
    'shift_step',
    'pre_shift_score',
    'post_shift_score',
    'drop_rate',
    'p_value'
]

# Data type expectations
COLUMN_TYPES = {
    'env_id': str,
    'shift_step': int,
    'pre_shift_score': float,
    'post_shift_score': float,
    'drop_rate': float,
    'p_value': float
}

@dataclass
class SensitivityReportRow:
    """Represents a single row in the sensitivity report."""
    env_id: str
    shift_step: int
    pre_shift_score: float
    post_shift_score: float
    drop_rate: float
    p_value: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV writing."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SensitivityReportRow':
        """Create instance from dictionary."""
        return cls(
            env_id=str(data['env_id']),
            shift_step=int(data['shift_step']),
            pre_shift_score=float(data['pre_shift_score']),
            post_shift_score=float(data['post_shift_score']),
            drop_rate=float(data['drop_rate']),
            p_value=float(data['p_value'])
        )

def validate_row(row: Dict[str, Any]) -> bool:
    """
    Validate a row of data against the schema.
    
    Args:
        row: Dictionary containing row data
        
    Returns:
        True if valid, raises ValueError if invalid
    """
    # Check all required columns present
    for col in SENSITIVITY_REPORT_COLUMNS:
        if col not in row:
            raise ValueError(f"Missing required column: {col}")
    
    # Validate data types
    for col, expected_type in COLUMN_TYPES.items():
        try:
            if expected_type == int:
                int(row[col])
            elif expected_type == float:
                float(row[col])
            elif expected_type == str:
                str(row[col])
        except (ValueError, TypeError):
            raise ValueError(f"Invalid type for {col}: expected {expected_type}, got {type(row[col])}")
    
    # Validate constraints
    drop_rate = float(row['drop_rate'])
    if not (0.0 <= drop_rate <= 1.0):
        raise ValueError(f"drop_rate must be between 0.0 and 1.0, got {drop_rate}")
    
    p_value = float(row['p_value'])
    if not (0.0 <= p_value <= 1.0):
        raise ValueError(f"p_value must be between 0.0 and 1.0, got {p_value}")
    
    return True

def write_header_only(output_path: str) -> None:
    """
    Write a CSV file with headers only (used when no environments are found).
    
    Args:
        output_path: Path to write the CSV file
    """
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=SENSITIVITY_REPORT_COLUMNS)
        writer.writeheader()

def write_sensitivity_report(rows: List[SensitivityReportRow], output_path: str) -> None:
    """
    Write sensitivity report to CSV file.
    
    Args:
        rows: List of SensitivityReportRow objects
        output_path: Path to write the CSV file
    """
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=SENSITIVITY_REPORT_COLUMNS)
        writer.writeheader()
        
        for row in rows:
            row_dict = row.to_dict()
            validate_row(row_dict)
            writer.writerow(row_dict)

def read_sensitivity_report(input_path: str) -> List[SensitivityReportRow]:
    """
    Read sensitivity report from CSV file.
    
    Args:
        input_path: Path to read the CSV file
        
    Returns:
        List of SensitivityReportRow objects
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Sensitivity report not found: {input_path}")
    
    rows = []
    with open(input_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            validate_row(row)
            rows.append(SensitivityReportRow.from_dict(row))
    
    return rows