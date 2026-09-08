import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
from src.lib import config
from src.services.analysis import run_full_analysis

logger = logging.getLogger(__name__)

def load_analysis_data() -> pd.DataFrame:
    """Load the final analysis dataset."""
    path = Path(config.get_data_path()) / "processed" / "final_analysis_dataset.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found at {path}")
    return pd.read_parquet(path)

def run_statistical_analysis(df: pd.DataFrame, correction_method: str = "bh") -> Dict[str, Any]:
    """Run statistical analysis on the dataset."""
    return run_full_analysis(df, correction_method=correction_method)

def save_metrics(metrics: Dict[str, Any], output_path: str) -> None:
    """Save metrics to JSON."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {output_path}")

def main():
    logging.basicConfig(level=logging.INFO)
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--correction-method", default="bh", choices=["bonferroni", "bh"])
    args = parser.parse_args()
    
    df = load_analysis_data()
    metrics = run_statistical_analysis(df, args.correction_method)
    
    output_path = Path(config.get_artifacts_path()) / "results" / "statistical_metrics.json"
    save_metrics(metrics, str(output_path))

if __name__ == "__main__":
    import argparse
    main()
