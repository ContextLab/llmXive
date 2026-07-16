import os
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import shutil

# Import existing utilities
from code.utils.logger import get_logger
from code.utils.config import get_path, get_data_path

logger = get_logger(__name__)

def load_json_safe(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Safely load a JSON file. Returns None if file does not exist or is invalid.
    """
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"JSON file not found: {file_path}")
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return None

def load_csv_safe(file_path: str) -> Optional[list]:
    """
    Safely load a CSV file as a list of dicts (using csv module to avoid pandas dependency if not needed).
    Returns None if file does not exist.
    """
    import csv
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"CSV file not found: {file_path}")
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception as e:
        logger.error(f"Error reading CSV {file_path}: {e}")
        return None

def ensure_figures_directory(figures_dir: Path) -> None:
    """
    Ensure the figures directory exists.
    """
    if not figures_dir.exists():
        figures_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created figures directory: {figures_dir}")

def move_figures(source_dir: Path, dest_dir: Path, pattern: str = "*.png") -> int:
    """
    Move figure files from source to destination.
    Returns the count of files moved.
    """
    if not source_dir.exists():
        logger.warning(f"Source figures directory does not exist: {source_dir}")
        return 0

    ensure_figures_directory(dest_dir)
    moved_count = 0
    for file_path in source_dir.glob(pattern):
        dest_path = dest_dir / file_path.name
        shutil.move(str(file_path), str(dest_path))
        moved_count += 1
        logger.info(f"Moved figure: {file_path.name} -> {dest_path}")
    return moved_count

def aggregate_results(stability_results: Optional[Dict], 
                      plausibility_results: Optional[Dict],
                      summary_table: Optional[Dict],
                      figures_moved: int) -> Dict[str, Any]:
    """
    Aggregate all feature analysis results into a single dictionary.
    """
    return {
        "feature_stability": stability_results,
        "physical_plausibility": plausibility_results,
        "feature_summary": summary_table,
        "figures_saved": figures_moved,
        "status": "complete"
    }

def save_final_outputs(
    stability_results: Optional[Dict],
    plausibility_results: Optional[Dict],
    summary_table: Optional[Dict],
    figures_src_dir: Path,
    figures_dest_dir: Path
) -> Dict[str, Any]:
    """
    Main orchestration function to save all feature analysis outputs.
    
    1. Ensures destination directories exist.
    2. Moves generated figures from temporary/working dir to final figures dir.
    3. Aggregates stability, plausibility, and summary data.
    4. Writes the aggregated JSON to `data/processed/feature_analysis.json`.
    
    Returns the saved dictionary.
    """
    # 1. Ensure directories exist
    ensure_figures_directory(figures_dest_dir)
    
    # 2. Move figures
    moved_count = move_figures(figures_src_dir, figures_dest_dir)
    logger.info(f"Moved {moved_count} figures to {figures_dest_dir}")
    
    # 3. Aggregate
    final_data = aggregate_results(
        stability_results,
        plausibility_results,
        summary_table,
        moved_count
    )
    
    # 4. Save JSON
    output_json_path = get_data_path("processed/feature_analysis.json")
    output_path = Path(output_json_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=2, default=str)
    
    logger.info(f"Saved feature analysis results to {output_json_path}")
    return final_data

def main():
    """
    Entry point for T027: Save analysis outputs.
    Assumes T023, T024, T025, T026 have run and produced intermediate artifacts.
    """
    # Paths
    figures_src = Path("code/figures") # Assumed temp location from T024
    figures_dest = get_path("docs/paper/figures")
    
    # Load intermediate results (produced by T023, T025, T026)
    # We try to load them; if they don't exist, we pass None, 
    # but the pipeline should ensure they exist.
    stability = load_json_safe("data/processed/feature_stability_results.json")
    plausibility = load_json_safe("data/processed/physical_plausibility_results.json")
    summary = load_json_safe("data/processed/feature_summary_table.json")
    
    # Save final outputs
    save_final_outputs(
        stability_results=stability,
        plausibility_results=plausibility,
        summary_table=summary,
        figures_src_dir=figures_src,
        figures_dest_dir=Path(figures_dest)
    )
    
    logger.info("T027 completed: Feature analysis outputs saved.")

if __name__ == "__main__":
    main()