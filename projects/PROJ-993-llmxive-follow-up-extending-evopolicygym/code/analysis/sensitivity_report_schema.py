"""
Schema definition and validation for the sensitivity_report.csv artifact.

This module defines the structure, types, and validation logic for the
sensitivity report generated during the dynamic shift analysis (User Story 1).

Columns:
  - env_id (str): Identifier of the environment.
  - shift_step (int): The step number at which the dynamic shift occurred.
  - pre_shift_score (float): Average score obtained before the shift.
  - post_shift_score (float): Average score obtained after the shift.
  - drop_rate (float): Ratio of performance drop (0.0 to 1.0).
  - p_value (float): Statistical significance of the performance drop.
"""

import csv
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

# Constants for file paths
SENSITIVITY_REPORT_PATH = "data/sensitivity_report.csv"

@dataclass
class SensitivityReportRow:
    """
    Represents a single row in the sensitivity_report.csv.

    Attributes:
        env_id (str): Unique identifier for the environment (e.g., 'CartPole-v1').
        shift_step (int): The step index where the environment dynamics changed.
        pre_shift_score (float): Mean reward accumulated before the shift step.
        post_shift_score (float): Mean reward accumulated after the shift step.
        drop_rate (float): Calculated as (pre - post) / pre, clamped to [0.0, 1.0].
        p_value (float): P-value from a statistical test (e.g., t-test) comparing pre/post scores.
    """
    env_id: str
    shift_step: int
    pre_shift_score: float
    post_shift_score: float
    drop_rate: float
    p_value: float

    def __post_init__(self):
        """Validate ranges and types after initialization."""
        if not isinstance(self.env_id, str) or not self.env_id:
            raise ValueError("env_id must be a non-empty string.")
        if not isinstance(self.shift_step, int):
            raise ValueError("shift_step must be an integer.")
        if not isinstance(self.pre_shift_score, (int, float)):
            raise ValueError("pre_shift_score must be a number.")
        if not isinstance(self.post_shift_score, (int, float)):
            raise ValueError("post_shift_score must be a number.")
        
        # Validate drop_rate is within [0.0, 1.0]
        if not 0.0 <= self.drop_rate <= 1.0:
            raise ValueError(f"drop_rate must be between 0.0 and 1.0, got {self.drop_rate}")
        
        # Validate p_value is within [0.0, 1.0]
        if not 0.0 <= self.p_value <= 1.0:
            raise ValueError(f"p_value must be between 0.0 and 1.0, got {self.p_value}")

def validate_row(data: Dict[str, Any]) -> bool:
    """
    Validates a dictionary against the SensitivityReportRow schema.
    
    Args:
        data: Dictionary containing row data.
        
    Returns:
        True if valid, raises ValueError otherwise.
    """
    required_fields = ['env_id', 'shift_step', 'pre_shift_score', 'post_shift_score', 'drop_rate', 'p_value']
    
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    
    # Type checks
    if not isinstance(data['env_id'], str):
        raise ValueError("env_id must be a string")
    if not isinstance(data['shift_step'], int):
        raise ValueError("shift_step must be an integer")
    if not isinstance(data['pre_shift_score'], (int, float)):
        raise ValueError("pre_shift_score must be a number")
    if not isinstance(data['post_shift_score'], (int, float)):
        raise ValueError("post_shift_score must be a number")
    if not isinstance(data['drop_rate'], (int, float)):
        raise ValueError("drop_rate must be a number")
    if not isinstance(data['p_value'], (int, float)):
        raise ValueError("p_value must be a number")
        
    return True

def write_header_only(filepath: str = SENSITIVITY_REPORT_PATH) -> None:
    """
    Creates the CSV file with headers only. Used when no environments are discovered.
    """
    headers = ['env_id', 'shift_step', 'pre_shift_score', 'post_shift_score', 'drop_rate', 'p_value']
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)

def write_sensitivity_report(rows: List[SensitivityReportRow], filepath: str = SENSITIVITY_REPORT_PATH) -> None:
    """
    Writes a list of SensitivityReportRow objects to the CSV file.
    
    Args:
        rows: List of row objects to write.
        filepath: Path to the output CSV file.
    """
    headers = ['env_id', 'shift_step', 'pre_shift_score', 'post_shift_score', 'drop_rate', 'p_value']
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in rows:
            writer.writerow([
                row.env_id,
                row.shift_step,
                row.pre_shift_score,
                row.post_shift_score,
                row.drop_rate,
                row.p_value
            ])

def read_sensitivity_report(filepath: str = SENSITIVITY_REPORT_PATH) -> List[Dict[str, Any]]:
    """
    Reads the sensitivity report CSV and returns a list of dictionaries.
    
    Args:
        filepath: Path to the CSV file.
        
    Returns:
        List of dictionaries representing the rows.
    """
    if not os.path.exists(filepath):
        return []
        
    rows = []
    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert types back to appropriate Python types
            row['shift_step'] = int(row['shift_step'])
            row['pre_shift_score'] = float(row['pre_shift_score'])
            row['post_shift_score'] = float(row['post_shift_score'])
            row['drop_rate'] = float(row['drop_rate'])
            row['p_value'] = float(row['p_value'])
            rows.append(row)
    return rows