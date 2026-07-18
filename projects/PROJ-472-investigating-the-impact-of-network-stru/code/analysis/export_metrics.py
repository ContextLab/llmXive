import os
import sys
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any

from config import get_data_root
from utils.logger import get_logger

logger = get_logger(__name__)

def load_metrics_from_store(data_root: Path) -> pd.DataFrame:
    file = data_root / "processed" / "metrics.csv"
    if file.exists():
        return pd.read_csv(file)
    return pd.DataFrame()

def load_avalanche_fitting_results(data_root: Path) -> pd.DataFrame:
    # Placeholder
    return pd.DataFrame()

def load_qc_status(data_root: Path) -> pd.DataFrame:
    # Placeholder
    return pd.DataFrame()

def collect_subject_metrics(data_root: Path) -> pd.DataFrame:
    metrics = load_metrics_from_store(data_root)
    # Merge with other data
    return metrics

def run_export_pipeline(data_root: Path):
    """Exports final metrics."""
    df = collect_subject_metrics(data_root)
    if not df.empty:
        out_file = data_root / "results" / "exported_metrics.csv"
        df.to_csv(out_file, index=False)
        logger.info(f"Exported metrics to {out_file}")

def main():
    data_root = get_data_root()
    run_export_pipeline(data_root)

if __name__ == "__main__":
    main()