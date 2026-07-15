import os
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd

def write_p_values_raw(data: List[Dict], filepath: str):
    """Write p-values to CSV."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['test_type', 'n', 'effect_size', 'alpha', 'p_value'])
        if os.path.getsize(filepath) == 0:
            writer.writeheader()
        writer.writerows(data)

def load_p_values_raw(filepath: str) -> pd.DataFrame:
    """Load p-values from CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    return pd.read_csv(filepath)

def load_p_values_raw_safe(filepath: str) -> pd.DataFrame:
    """Load p-values safely, returning empty DF if not found."""
    try:
        return load_p_values_raw(filepath)
    except FileNotFoundError:
        return pd.DataFrame()

if __name__ == '__main__':
    print("Output Writer Module")
