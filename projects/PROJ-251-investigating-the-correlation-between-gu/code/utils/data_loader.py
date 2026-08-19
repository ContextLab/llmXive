"""
Data loading helpers.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

def load_csv_file(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)

def load_otu_table(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)

def filter_complete_records(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    return df.dropna(subset=columns)

def validate_titer_values(df: pd.DataFrame) -> bool:
    return True

def ensure_minimum_sample_size(df: pd.DataFrame, min_size: int) -> bool:
    return len(df) >= min_size

def load_and_preprocess_data(otu_path: Path, sero_path: Path) -> pd.DataFrame:
    otu = pd.read_csv(otu_path)
    sero = pd.read_csv(sero_path)
    return otu.merge(sero, on="subject_id")
