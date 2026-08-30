import os
import sys
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Any
from pathlib import Path

def load_calibration_report():
    report_path = Path("results/calibration_report.csv")
    if not report_path.exists():
        raise FileNotFoundError(f"Calibration report not found: {report_path}")
    return pd.read_csv(report_path)

def rank_methods_by_ece(df: pd.DataFrame) -> List[str]:
    return df.sort_values('ece')['method'].tolist()

def rank_methods_by_interval_score(df: pd.DataFrame) -> List[str]:
    return df.sort_values('interval_score')['method'].tolist()

def determine_best_method(df: pd.DataFrame) -> str:
    # Best method is the one with the lowest ECE
    return df.loc[df['ece'].idxmin(), 'method']

def generate_ranking_report(df: pd.DataFrame):
    ece_rank = rank_methods_by_ece(df)
    is_rank = rank_methods_by_interval_score(df)
    best = determine_best_method(df)
    
    report = {
        'ece_ranking': ece_rank,
        'interval_score_ranking': is_rank,
        'best_method': best
    }
    
    report_path = Path("results/ranking_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

def main():
    df = load_calibration_report()
    generate_ranking_report(df)
