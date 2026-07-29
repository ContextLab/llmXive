"""
FR-007 Implementation for Visualizations.

This module provides utilities to overlay associational warnings on generated plots
or append them to the metadata of visualization files.
"""
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from utils.fr007_warnings import ASSOCIATIONAL_WARNING_TEXT
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Metadata key for storing warnings in plot JSON sidecars
WARNING_METADATA_KEY = "associational_warning"

def attach_warning_to_plot_metadata(plot_path: Path) -> None:
    """
    Creates or updates a JSON sidecar file for a plot (e.g., scatter.png -> scatter.json)
    containing the FR-007 warning.
    
    This ensures the warning travels with the visualization artifact.
    """
    if not plot_path.exists():
        logger.warning(f"Plot file not found: {plot_path}")
        return

    # Derive sidecar path
    sidecar_path = plot_path.with_suffix('.json')
    warning_data = {
        WARNING_METADATA_KEY: ASSOCIATIONAL_WARNING_TEXT,
        "fr007_injected_at": datetime.utcnow().isoformat(),
        "source_plot": plot_path.name
    }

    # Load existing sidecar if present
    existing_data = {}
    if sidecar_path.exists():
        try:
            with open(sidecar_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Existing sidecar {sidecar_path} is invalid JSON. Overwriting.")

    existing_data.update(warning_data)

    with open(sidecar_path, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2)

    logger.info(f"FR-007 Warning attached to metadata sidecar: {sidecar_path}")

def inject_warning_into_plot_json(plot_json_path: Path) -> None:
    """
    If a plot is stored as a JSON object (e.g., plotly), inject the warning directly.
    """
    if not plot_json_path.exists():
        logger.warning(f"Plot JSON file not found: {plot_json_path}")
        return

    try:
        with open(plot_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in {plot_json_path}")
        return

    if 'annotations' not in data:
        data['annotations'] = []
    
    # Add the warning as a text annotation in the plot itself if possible
    # (Assumes plotly-like structure with text annotations)
    warning_annotation = {
        "text": ASSOCIATIONAL_WARNING_TEXT,
        "showarrow": False,
        "x": 0.01,
        "y": 0.01,
        "xref": "paper",
        "yref": "paper",
        "align": "left",
        "verticalalign": "bottom",
        "font": {"size": 10, "color": "red", "family": "Arial"},
        "bgcolor": "rgba(255, 255, 255, 0.8)",
        "borderpad": 4,
        "bordercolor": "red"
    }
    
    # Check if already present to avoid duplicates
    if not any(a.get('text') == ASSOCIATIONAL_WARNING_TEXT for a in data['annotations']):
        data['annotations'].append(warning_annotation)
    
    # Also store in metadata
    data['fr007_warning'] = ASSOCIATIONAL_WARNING_TEXT
    data['fr007_injected_at'] = datetime.utcnow().isoformat()

    with open(plot_json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    
    logger.info(f"FR-007 Warning injected into plot JSON: {plot_json_path}")

def main():
    """
    Entry point to process visualization outputs in data/outputs/
    """
    base_dir = Path(__file__).parent.parent.parent
    outputs_dir = base_dir / "data" / "outputs"

    if not outputs_dir.exists():
        logger.warning(f"Outputs directory not found: {outputs_dir}")
        return

    # Process common plot extensions
    plot_extensions = ['.png', '.jpg', '.jpeg', '.pdf', '.svg']
    json_extensions = ['.json'] # For plotly/interactive plots

    for ext in plot_extensions:
        for plot_file in outputs_dir.glob(f"*{ext}"):
            attach_warning_to_plot_metadata(plot_file)

    for ext in json_extensions:
        for json_file in outputs_dir.glob(f"*{ext}"):
            inject_warning_into_plot_json(json_file)

    logger.info("FR-007 Visualization warnings processed.")

if __name__ == "__main__":
    main()
