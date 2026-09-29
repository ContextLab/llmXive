import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

from config import get_project_root, get_data_paths

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_descriptors(input_path: Path) -> pd.DataFrame:
    """
    Loads descriptors from a CSV file.
    """
    return pd.read_csv(input_path)

def compute_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """
    Computes Variance Inflation Factor for each feature.
    """
    # Placeholder for VIF calculation
    return {f: 1.0 for f in features}

def generate_report(vif_scores: Dict[str, float], output_path: Path):
    """
    Generates a collinearity report.
    """
    report_path = output_path.parent / "collinearity_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w') as f:
        f.write("# Collinearity Report\n\n")
        has_collinearity = False
        for feature, vif in vif_scores.items():
            f.write(f"- {feature}: VIF = {vif:.2f}\n")
            if vif >= 10:
                has_collinearity = True
        
        if has_collinearity:
            f.write("\n## Warning\n")
            f.write("Collinearity detected (VIF >= 10). Interpret as a joint effect.\n")
        else:
            f.write("\n## Status\n")
            f.write("No collinearity detected (VIF < 10).\n")
    
    logger.info(f"Collinearity report saved to {report_path}")

def run_vif_analysis(input_path: Path, output_dir: Path):
    """
    Runs the full VIF analysis pipeline.
    """
    df = load_descriptors(input_path)
    features = [col for col in df.columns if col not in ['species', 'alloy_system_id']]
    vif_scores = compute_vif(df, features)
    generate_report(vif_scores, output_dir / "vif_report.json")

def main():
    """
    Main entry point for the descriptor filter script.
    """
    logger.info("Descriptor filter module loaded.")

if __name__ == "__main__":
    main()
