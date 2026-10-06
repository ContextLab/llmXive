import os
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import shutil
import pandas as pd

# Import existing utilities from the project API surface
from utils.logger import get_logger
from utils.config import get_path, get_data_path, get_code_path

# Ensure logger is configured
logger = get_logger(__name__)

def load_json_safe(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Safely load a JSON file. Returns None if file doesn't exist or is invalid.
    """
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"JSON file not found: {file_path}")
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error loading JSON file {file_path}: {e}")
        return None

def load_csv_safe(file_path: str) -> Optional[pd.DataFrame]:
    """
    Safely load a CSV file. Returns None if file doesn't exist or is invalid.
    """
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"CSV file not found: {file_path}")
        return None
    try:
        return pd.read_csv(path)
    except Exception as e:
        logger.error(f"Error loading CSV file {file_path}: {e}")
        return None

def ensure_figures_directory(figures_dir: Path) -> None:
    """
    Ensure the figures directory exists.
    """
    if not figures_dir.exists():
        figures_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created figures directory: {figures_dir}")

def move_figures(source_pattern: str, target_dir: Path) -> int:
    """
    Move generated figure files from source to target directory.
    Returns the count of moved files.
    """
    source_path = Path(source_pattern)
    # If source_pattern is a directory
    if source_path.is_dir():
        files = list(source_path.glob("*.png")) + list(source_path.glob("*.jpg")) + list(source_path.glob("*.svg"))
    else:
        # Assume it's a glob pattern relative to data/processed
        base_dir = source_path.parent
        pattern = source_path.name
        files = list(base_dir.glob(pattern))
    
    count = 0
    for file_path in files:
        if file_path.suffix.lower() in ['.png', '.jpg', '.svg']:
            target_file = target_dir / file_path.name
            shutil.move(str(file_path), str(target_file))
            logger.info(f"Moved figure: {file_path} -> {target_file}")
            count += 1
    return count

def aggregate_results(
    stability_results: Optional[Dict[str, Any]],
    plausibility_results: Optional[Dict[str, Any]],
    summary_df: Optional[pd.DataFrame],
    figures_moved: int
) -> Dict[str, Any]:
    """
    Aggregate all feature analysis results into a single dictionary.
    """
    result = {
        "status": "completed",
        "timestamp": pd.Timestamp.now().isoformat(),
        "figures_generated": figures_moved,
        "stability_analysis": stability_results or {"error": "Results not found"},
        "physical_plausibility": plausibility_results or {"error": "Results not found"},
        "feature_summary": {}
    }
    
    if summary_df is not None and not summary_df.empty:
        # Convert DataFrame to list of dicts for JSON serialization
        result["feature_summary"] = summary_df.to_dict(orient='records')
        result["feature_summary_count"] = len(summary_df)
    
    return result

def save_final_outputs(
    aggregated_data: Dict[str, Any],
    output_json_path: str,
    figures_target_dir: str
) -> None:
    """
    Save the aggregated results to JSON and ensure figures are in place.
    """
    # Ensure target directories exist
    output_path = Path(output_json_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(aggregated_data, f, indent=2, default=str)
    logger.info(f"Saved feature analysis results to: {output_json_path}")
    
    # Ensure figures directory exists (figures should have been moved by move_figures)
    figures_dir = Path(figures_target_dir)
    ensure_figures_directory(figures_dir)
    logger.info(f"Ensured figures directory exists: {figures_target_dir}")

def main():
    """
    Main entry point for T027: Save analysis outputs to data/processed/feature_analysis.json 
    and docs/paper/figures/.
    
    Dependencies:
    - T023: Feature stability analysis (data/processed/feature_stability.json)
    - T024: Partial dependence plots (generated in data/processed/ or similar)
    - T025: Physical plausibility check (data/processed/physical_plausibility.json)
    - T026: Feature interpretation summary (data/processed/feature_interpretation_summary.csv)
    """
    logger.info("Starting T027: Save analysis outputs")
    
    # Define paths based on project structure
    data_path = get_data_path()
    processed_path = data_path / "processed"
    figures_source = processed_path  # Figures are typically generated here by T024
    figures_target = Path("docs/paper/figures")
    stability_file = processed_path / "feature_stability.json"
    plausibility_file = processed_path / "physical_plausibility.json"
    summary_file = processed_path / "feature_interpretation_summary.csv"
    output_json = processed_path / "feature_analysis.json"
    
    # Load inputs from previous tasks
    logger.info(f"Loading stability results from: {stability_file}")
    stability_results = load_json_safe(str(stability_file))
    
    logger.info(f"Loading physical plausibility results from: {plausibility_file}")
    plausibility_results = load_json_safe(str(plausibility_file))
    
    logger.info(f"Loading feature summary table from: {summary_file}")
    summary_df = load_csv_safe(str(summary_file))
    
    # Move figures from source to target directory
    logger.info(f"Moving figures from {figures_source} to {figures_target}")
    figures_moved = move_figures(str(figures_source), Path(figures_target))
    logger.info(f"Moved {figures_moved} figure files.")
    
    # Aggregate all results
    aggregated_data = aggregate_results(
        stability_results=stability_results,
        plausibility_results=plausibility_results,
        summary_df=summary_df,
        figures_moved=figures_moved
    )
    
    # Save final outputs
    save_final_outputs(
        aggregated_data=aggregated_data,
        output_json_path=str(output_json),
        figures_target_dir=str(figures_target)
    )
    
    logger.info("T027 completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())