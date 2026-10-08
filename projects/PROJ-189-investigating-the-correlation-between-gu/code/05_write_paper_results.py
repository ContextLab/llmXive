"""
Module to write the Results section of the paper draft based on analysis artifacts.

This module implements task T043b:
- Reads correlation results from data/processed/correlation_results.csv
- Reads model significance verification from data/processed/significance_verification.json
- Reads memory logs from data/processed/memory_log.txt (optional context)
- Updates docs/paper_draft.md with a formatted Results section
"""

import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))

from utils.logging import setup_logging, get_logger

# Constants for paths
CORRELATION_RESULTS_PATH = "data/processed/correlation_results.csv"
SIGNIFICANCE_VERIFICATION_PATH = "data/processed/significance_verification.json"
MEMORY_LOG_PATH = "data/processed/memory_log.txt"
PAPER_DRAFT_PATH = "docs/paper_draft.md"
OUTPUT_RESULTS_PATH = "data/processed/results_section_content.md"

def load_correlation_results(logger: logging.Logger) -> pd.DataFrame:
    """Load the correlation results CSV."""
    path = Path(CORRELATION_RESULTS_PATH)
    if not path.exists():
        logger.error(f"Correlation results file not found: {path}")
        raise FileNotFoundError(f"Missing required artifact: {path}")
    
    logger.info(f"Loading correlation results from {path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} correlation pairs")
    return df

def load_significance_verification(logger: logging.Logger) -> dict:
    """Load the model significance verification JSON."""
    path = Path(SIGNIFICANCE_VERIFICATION_PATH)
    if not path.exists():
        logger.warning(f"Significance verification file not found: {path}")
        # Return a default structure if missing, but log warning
        return {
            "threshold": None,
            "r_squared": None,
            "status": "unknown",
            "message": "Verification data missing"
        }
    
    logger.info(f"Loading significance verification from {path}")
    with open(path, 'r') as f:
        data = json.load(f)
    return data

def load_memory_log(logger: logging.Logger) -> str:
    """Load the memory log text file."""
    path = Path(MEMORY_LOG_PATH)
    if not path.exists():
        logger.warning(f"Memory log file not found: {path}")
        return ""
    
    with open(path, 'r') as f:
        return f.read()

def format_correlation_table(df: pd.DataFrame, logger: logging.Logger) -> str:
    """Format the top significant correlations for the paper."""
    if df.empty:
        return "No significant correlations were found (adj-p < 0.05)."
    
    # Sort by absolute rho value descending
    df_sorted = df.sort_values(by="rho", key=abs, ascending=False)
    
    # Select top 10 for display
    top_n = min(10, len(df_sorted))
    top_df = df_sorted.head(top_n)
    
    lines = []
    lines.append("### Significant Genus-Cognitive Score Associations")
    lines.append("")
    lines.append("| Genus | Spearman's Rho | P-value | Adj. P-value (FDR) | Interpretation |")
    lines.append("|-------|----------------|---------|--------------------|----------------|")
    
    for _, row in top_df.iterrows():
        genus = row.get('genus', 'Unknown')
        rho = f"{row['rho']:.4f}"
        p_val = f"{row['p_value']:.4g}"
        adj_p = f"{row['adj_p_value']:.4g}"
        interp = row.get('interpretation', 'Associational')
        lines.append(f"| {genus} | {rho} | {p_val} | {adj_p} | {interp} |")
    
    lines.append("")
    lines.append(f"**Total significant pairs:** {len(df)} (adj-p < 0.05)")
    return "\n".join(lines)

def format_model_significance(verification_data: dict, logger: logging.Logger) -> str:
    """Format the model significance verification results."""
    lines = []
    lines.append("### Predictive Model Significance")
    lines.append("")
    
    status = verification_data.get("status", "unknown")
    r_squared = verification_data.get("r_squared")
    threshold = verification_data.get("threshold")
    
    if r_squared is not None and threshold is not None:
        lines.append(f"- **Hold-out R² Score:** {r_squared:.4f}")
        lines.append(f"- **Permutation Null Threshold (95th percentile):** {threshold:.4f}")
        lines.append("")
        
        if status == "pass":
            lines.append(f"> **Conclusion:** The model's R² ({r_squared:.4f}) exceeds the permutation null threshold ({threshold:.4f}), indicating that the predictive performance is statistically significant and not due to random chance.")
        else:
            lines.append(f"> **Conclusion:** The model's R² ({r_squared:.4f}) did not exceed the permutation null threshold ({threshold:.4f}). The predictive performance may not be statistically significant.")
    else:
        lines.append("> **Note:** Model significance verification data is incomplete or missing.")
    
    lines.append("")
    return "\n".join(lines)

def generate_results_section(correlation_df: pd.DataFrame, 
                             verification_data: dict, 
                             logger: logging.Logger) -> str:
    """Generate the full Results section markdown content."""
    sections = []
    
    # Header
    sections.append("## Results")
    sections.append("")
    
    # Correlation Analysis
    sections.append("### Correlation Analysis")
    sections.append("")
    sections.append("Spearman rank correlations were computed between CLR-transformed genus-level relative abundances and cognitive test scores, with Benjamini-Hochberg FDR correction applied (α = 0.05).")
    sections.append("")
    sections.append(format_correlation_table(correlation_df, logger))
    
    # Predictive Modeling
    sections.append("### Predictive Modeling")
    sections.append("")
    sections.append("A Random Forest regressor with 5-fold cross-validation was trained to predict cognitive scores from microbial features. Model significance was assessed against a permutation null distribution (1000 shuffles).")
    sections.append("")
    sections.append(format_model_significance(verification_data, logger))
    
    # Summary
    sections.append("### Summary")
    sections.append("")
    significant_count = len(correlation_df)
    sections.append(f"Analysis identified **{significant_count}** genus-cognitive score pairs with significant associations (adj-p < 0.05). The predictive model demonstrated {'significant' if verification_data.get('status') == 'pass' else 'non-significant'} performance relative to the permutation null distribution.")
    sections.append("")
    
    return "\n".join(sections)

def update_paper_draft(results_content: str, logger: logging.Logger) -> None:
    """Update the paper draft with the new Results section."""
    path = Path(PAPER_DRAFT_PATH)
    if not path.exists():
        logger.error(f"Paper draft not found: {path}")
        raise FileNotFoundError(f"Missing paper draft: {path}")
    
    logger.info(f"Updating paper draft at {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the Results section marker or insert before Discussion
    # Strategy: Replace existing "## Results" section or insert if missing
    lines = content.split('\n')
    new_lines = []
    in_results_section = False
    results_written = False
    skip_until_next_header = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check for Results header
        if line.strip().startswith("## Results"):
            in_results_section = True
            skip_until_next_header = True
            # Write our new results content
            new_lines.append(line) # Keep the header
            new_lines.append(results_content)
            new_lines.append("") # Spacer
            results_written = True
            # Skip original results content until next ## header
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("## "):
                i += 1
            continue
        
        # Check for Discussion header (if Results was missing)
        if not results_written and line.strip().startswith("## Discussion"):
            # Insert Results section before Discussion
            new_lines.append(results_content)
            new_lines.append("")
            results_written = True
        
        if not skip_until_next_header:
            new_lines.append(line)
        
        # Stop skipping if we hit a new ## header (and we are skipping)
        if skip_until_next_header and line.strip().startswith("## "):
            skip_until_next_header = False
            in_results_section = False
        
        i += 1
    
    # If Results section was not found and Discussion was not found, append at end
    if not results_written:
        new_lines.append("\n## Results")
        new_lines.append(results_content)
    
    updated_content = '\n'.join(new_lines)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    logger.info("Paper draft updated successfully")

def save_results_section_content(results_content: str, logger: logging.Logger) -> None:
    """Save the generated results section to a standalone file."""
    path = Path(OUTPUT_RESULTS_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(results_content)
    
    logger.info(f"Results section content saved to {path}")

def main():
    """Main entry point for T043b."""
    # Setup logging
    logger = setup_logging(module_name="write_paper_results")
    logger.info("Starting Results section generation (T043b)")
    
    try:
        # 1. Load data
        correlation_df = load_correlation_results(logger)
        verification_data = load_significance_verification(logger)
        # memory_log = load_memory_log(logger) # Optional, not strictly needed for text generation
        
        # 2. Generate Results section
        results_content = generate_results_section(correlation_df, verification_data, logger)
        
        # 3. Save standalone content (for review)
        save_results_section_content(results_content, logger)
        
        # 4. Update paper draft
        update_paper_draft(results_content, logger)
        
        logger.info("Task T043b completed successfully")
        print("Results section generated and paper draft updated.")
        
    except Exception as e:
        logger.error(f"Error during Results section generation: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()