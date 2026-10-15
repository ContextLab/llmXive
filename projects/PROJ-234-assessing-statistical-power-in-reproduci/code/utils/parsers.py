import re
from typing import Tuple, Optional
from .exceptions import DataFetchError

def extract_sample_size(text: str) -> Optional[int]:
    """
    Extracts sample size from text using regex r"N\s*=\s*(\d+)".
    Returns int if found, else None.
    """
    if not text:
        return None
    
    match = re.search(r"N\s*=\s*(\d+)", text)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None

def extract_effect_size(text: str) -> Tuple[Optional[float], Optional[str], Optional[Tuple[int, int]]]:
    """
    Extracts effect size from text.
    Supports Cohen's d and F-statistics.
    Returns: (value, metric_type, optional_dof_tuple)
    """
    if not text:
        return None, None, None

    # 1. Try Cohen's d: "Cohen's d = 0.5" or "d = 0.5"
    d_match = re.search(r"(?:Cohen's\s*d|d)\s*=\s*([+-]?\d*\.?\d+)", text, re.IGNORECASE)
    if d_match:
        try:
            return float(d_match.group(1)), "Cohen's d", None
        except ValueError:
            pass

    # 2. Try F-statistic: "F(2, 145) = 4.5"
    f_match = re.search(r"F\s*\(([^,]+),\s*([^)]+)\)\s*=\s*([+-]?\d*\.?\d+)", text)
    if f_match:
        try:
            df1 = int(f_match.group(1).strip())
            df2 = int(f_match.group(2).strip())
            val = float(f_match.group(3))
            return val, "F", (df1, df2)
        except ValueError:
            pass

    return None, None, None
