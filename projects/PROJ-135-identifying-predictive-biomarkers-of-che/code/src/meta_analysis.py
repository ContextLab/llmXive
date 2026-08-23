import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Set, Any, Optional

# Import existing utilities from the project API surface
from src.config import get_project_root, ensure_directories
from src.utils import calculate_checksum, setup_logging

# Ensure logging is configured
setup_logging()
logger = logging.getLogger(__name__)

def load_gene_panel(panel_path: Path) -> Dict[str, Any]:
    """
    Load the gene panel JSON file.
    
    Args:
        panel_path: Path to the gene_panel.json file.
        
    Returns:
        Dictionary containing the gene panel data.
        
    Raises:
        FileNotFoundError: If the panel file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not panel_path.exists():
        raise FileNotFoundError(f"Gene panel file not found: {panel_path}")
        
    with open(panel_path, 'r') as f:
        return json.load(f)

def calculate_meta_analysis_bonferroni(panel_data: Dict[str, Any]) -> int:
    """
    Calculate m_meta: the number of genes in the final selected panel.
    
    According to FR-010, m_meta is the number of genes in the final panel
    used for meta-analysis significance correction.
    
    Args:
        panel_data: Dictionary containing the gene panel data with a 'selected' list.
        
    Returns:
        Integer count of selected genes (m_meta).
        
    Raises:
        ValueError: If the panel data is malformed or 'selected' list is empty.
    """
    if 'selected' not in panel_data:
        raise ValueError("Gene panel missing 'selected' key")
        
    selected_genes = panel_data['selected']
    
    if not isinstance(selected_genes, list):
        raise ValueError("'selected' must be a list")
        
    m_meta = len(selected_genes)
    
    if m_meta == 0:
        raise ValueError("Gene panel 'selected' list is empty; cannot calculate m_meta")
        
    return m_meta

def write_bonferroni_correction(m_meta: int, output_path: Path) -> None:
    """
    Write the Bonferroni correction parameters to a JSON file.
    
    Args:
        m_meta: The number of genes in the final panel.
        output_path: Path where the bonferroni_correction.json file will be written.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    bonferroni_data = {
        "m_meta": m_meta,
        "description": "Number of genes in final panel for meta-analysis Bonferroni correction",
        "alpha_threshold": 0.01 / m_meta if m_meta > 0 else float('inf')
    }
    
    with open(output_path, 'w') as f:
        json.dump(bonferroni_data, f, indent=2)
        
    logger.info(f"Written Bonferroni correction parameters to {output_path}")
    logger.info(f"m_meta = {m_meta}, adjusted alpha threshold = {bonferroni_data['alpha_threshold']:.6e}")

def main() -> int:
    """
    Main entry point for T024d: Calculate Meta-Analysis Bonferroni.
    
    Logic:
    1. Pre-Check: Verify results/meta_analysis/gene_panel.json exists and contains a non-empty 'selected' list.
    2. Calculate m_meta as the number of genes in the final panel.
    3. Write m_meta to results/meta_analysis/bonferroni_correction.json.
    
    Returns:
        0 on success, 1 on failure.
    """
    try:
        project_root = get_project_root()
        panel_path = project_root / "results" / "meta_analysis" / "gene_panel.json"
        output_path = project_root / "results" / "meta_analysis" / "bonferroni_correction.json"
        
        # Pre-Check: Verify gene panel exists
        if not panel_path.exists():
            logger.error(f"Pre-check failed: Gene panel file not found at {panel_path}")
            logger.error("Cannot proceed with Bonferroni calculation without a valid gene panel.")
            return 1
        
        # Load gene panel
        logger.info(f"Loading gene panel from {panel_path}")
        panel_data = load_gene_panel(panel_path)
        
        # Verify non-empty selected list
        if 'selected' not in panel_data or not panel_data['selected']:
            logger.error("Pre-check failed: Gene panel 'selected' list is empty or missing.")
            logger.error("Cannot calculate m_meta without selected genes.")
            return 1
        
        # Calculate m_meta
        logger.info("Calculating m_meta (number of genes in final panel)...")
        m_meta = calculate_meta_analysis_bonferroni(panel_data)
        
        # Write output
        logger.info(f"Writing Bonferroni correction results to {output_path}")
        write_bonferroni_correction(m_meta, output_path)
        
        # Verify output file was created
        if not output_path.exists():
            logger.error("Failed to write output file: {output_path}")
            return 1
        
        logger.info("T024d completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in gene panel: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during Bonferroni calculation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
