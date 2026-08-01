"""
Module to generate the curated markdown report of top perovskite candidates.

This task (T041) reads the full ranked list of candidates from `results/screening_full.csv`,
selects the top N candidates based on predicted decomposition energy, and generates
a human-readable Markdown report at `results/screening_candidates.md`.

The report includes:
- A summary of the screening process.
- A table of the top candidates with key descriptors (formula, t, mu, delta_X, predicted_energy).
- Highlighting of thermodynamically stable candidates (predicted_energy < -0.1 eV/atom).
- Notes on Out-of-Distribution (OOD) flags.
"""

import os
import sys
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import logging utilities from the project's utils
from utils.logging_config import get_logger, log_pipeline_event

# Configure logger
logger = get_logger(__name__)

# Constants
RESULTS_DIR = Path("results")
FULL_RANKED_FILE = RESULTS_DIR / "screening_full.csv"
CANDIDATE_REPORT_FILE = RESULTS_DIR / "screening_candidates.md"
TOP_N_CANDIDATES = 20
STABILITY_THRESHOLD = -0.1  # eV/atom


def load_ranked_candidates(file_path: Path) -> pd.DataFrame:
    """
    Load the full ranked list of candidates from a CSV file.
    
    Args:
        file_path: Path to the CSV file containing ranked candidates.
        
    Returns:
        A pandas DataFrame containing the candidate data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or missing required columns.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Ranked candidates file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    
    required_columns = ['formula', 'predicted_decomposition_energy', 'tolerance_factor', 
                        'octahedral_factor', 'electronegativity_diff', 'is_ood']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {file_path}: {missing_cols}")
        
    if df.empty:
        raise ValueError(f"Ranked candidates file {file_path} is empty.")
        
    logger.info(f"Loaded {len(df)} ranked candidates from {file_path}")
    return df


def select_top_candidates(df: pd.DataFrame, n: int = TOP_N_CANDIDATES) -> pd.DataFrame:
    """
    Select the top N candidates based on predicted decomposition energy (ascending).
    
    Args:
        df: DataFrame containing all ranked candidates.
        n: Number of top candidates to select.
        
    Returns:
        A DataFrame containing the top N candidates.
    """
    # Ensure the dataframe is sorted by predicted energy (ascending)
    # The input should already be sorted, but we ensure it here.
    df_sorted = df.sort_values(by='predicted_decomposition_energy', ascending=True)
    top_candidates = df_sorted.head(n).copy()
    
    logger.info(f"Selected top {n} candidates for the report.")
    return top_candidates


def generate_markdown_report(candidates: pd.DataFrame, total_screened: int) -> str:
    """
    Generate a Markdown report string for the top candidates.
    
    Args:
        candidates: DataFrame containing the top candidates.
        total_screened: Total number of candidates screened.
        
    Returns:
        A string containing the Markdown formatted report.
    """
    lines = []
    lines.append("# Top Perovskite Stability Candidates")
    lines.append("")
    lines.append("## Screening Summary")
    lines.append(f"- **Total Candidates Screened**: {total_screened}")
    lines.append(f"- **Candidates in Report**: {len(candidates)}")
    lines.append(f"- **Stability Threshold**: < {STABILITY_THRESHOLD} eV/atom")
    lines.append("")
    
    # Check for stable candidates
    stable_count = (candidates['predicted_decomposition_energy'] < STABILITY_THRESHOLD).sum()
    lines.append(f"**Note**: {stable_count} candidate(s) in this list are predicted to be thermodynamically stable (energy < {STABILITY_THRESHOLD} eV/atom).")
    lines.append("")
    
    # Table Header
    lines.append("## Top Candidates")
    lines.append("")
    lines.append("| # | Formula | Predicted Energy (eV/atom) | Tolerance Factor (t) | Octahedral Factor (μ) | ΔElectronegativity | OOD Flag |")
    lines.append("|:---:|:---|:---:|:---:|:---:|:---:|:---:|")
    
    # Table Rows
    for idx, row in candidates.iterrows():
        rank = idx + 1
        formula = row['formula']
        energy = row['predicted_decomposition_energy']
        t = row['tolerance_factor']
        mu = row['octahedral_factor']
        delta_x = row['electronegativity_diff']
        is_ood = "Yes" if row['is_ood'] else "No"
        
        # Highlight stable candidates
        if energy < STABILITY_THRESHOLD:
            energy_str = f"**{energy:.4f}**"
        else:
            energy_str = f"{energy:.4f}"
            
        lines.append(f"| {rank} | {formula} | {energy_str} | {t:.4f} | {mu:.4f} | {delta_x:.4f} | {is_ood} |")
        
    lines.append("")
    lines.append("## Methodology")
    lines.append("- Candidates were generated via combinatorial enumeration of A, B, and X sites.")
    lines.append("- Geometric feasibility was filtered using the Goldschmidt tolerance factor (0.8 ≤ t ≤ 1.1).")
    lines.append("- Stability was predicted using a RandomForestRegressor trained on Materials Project/OQMD data.")
    lines.append("- Candidates are sorted by predicted decomposition energy (lower is more stable).")
    lines.append("")
    lines.append("---")
    lines.append(f"*Report generated by T041 on {pd.Timestamp.now()}*")
    
    return "\n".join(lines)


def save_report(report_content: str, output_path: Path) -> None:
    """
    Save the generated Markdown report to a file.
    
    Args:
        report_content: The Markdown string content.
        output_path: Path to save the report.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    logger.info(f"Saved candidate report to {output_path}")


def main() -> None:
    """
    Main entry point for generating the candidate report.
    """
    log_pipeline_event("Starting T041: Generate Candidates Report")
    
    try:
        # 1. Load the full ranked list
        df_full = load_ranked_candidates(FULL_RANKED_FILE)
        total_screened = len(df_full)
        
        # 2. Select top candidates
        df_top = select_top_candidates(df_full, n=TOP_N_CANDIDATES)
        
        # 3. Generate the report
        report_md = generate_markdown_report(df_top, total_screened)
        
        # 4. Save the report
        save_report(report_md, CANDIDATE_REPORT_FILE)
        
        logger.info("T041 completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Failed to load data: {e}")
        raise
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during report generation: {e}")
        raise
    
    log_pipeline_event("T041 finished")

if __name__ == "__main__":
    main()