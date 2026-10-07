import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import pandas as pd
import numpy as np

# Mendeleev is required for element properties
try:
    from mendeleev import element
except ImportError:
    raise ImportError("mendeleev package is required. Install with: pip install mendeleev==0.31.0")

from resource_monitor import resource_monitor, ResourceLimitExceeded

def setup_logging():
    """Configure logging for the descriptors module."""
    project_root = get_project_root()
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / "descriptors.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def get_project_root():
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent

def get_element_properties(symbol: str) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Get atomic radius, electronegativity, and valence electrons for an element.
    Returns (radius, electronegativity, VEC).
    """
    try:
        el = element(symbol)
        radius = el.atomic_radius
        electronegativity = el.electronegativity
        # VEC is often valence electrons; using group number or specific valence config
        # Mendeleev 'valence_electrons' might vary by oxidation state, using group number as proxy for simple VEC
        vec = el.group
        return radius, electronegativity, float(vec)
    except Exception:
        return None, None, None

def parse_composition(composition_str: str) -> Dict[str, float]:
    """
    Parse a composition string like 'Fe50Ni50' into {'Fe': 0.5, 'Ni': 0.5}.
    Assumes format: ElementSymbolNumber...
    """
    import re
    if not composition_str:
        return {}
    
    # Regex to match Element and Number
    pattern = re.compile(r'([A-Z][a-z]?)(\d+(?:\.\d+)?)')
    matches = pattern.findall(composition_str)
    
    comp = {}
    total = 0.0
    for symbol, count in matches:
        val = float(count)
        comp[symbol] = val
        total += val
    
    # Normalize to fractions
    if total > 0:
        comp = {k: v/total for k, v in comp.items()}
    return comp

def calculate_weighted_mean_radius(composition_str: str, logger: logging.Logger) -> Optional[float]:
    """
    Calculate weighted mean radius for diagnostic logging.
    """
    comp = parse_composition(composition_str)
    if not comp:
        return None
    
    total_radius = 0.0
    total_weight = 0.0
    
    for symbol, weight in comp.items():
        radius, _, _ = get_element_properties(symbol)
        if radius is not None:
            total_radius += radius * weight
            total_weight += weight
        else:
            logger.warning(f"Unknown element {symbol} in composition {composition_str}")
    
    if total_weight == 0:
        return None
    return total_radius

def calculate_radius_mismatch(composition_str: str) -> float:
    """
    Calculate atomic radius mismatch (delta_r).
    Formula: sqrt(sum(ci * (1 - ri/r_bar)^2))
    """
    comp = parse_composition(composition_str)
    if not comp:
        return 0.0
    
    radii = []
    weights = []
    for symbol, weight in comp.items():
        radius, _, _ = get_element_properties(symbol)
        if radius is not None:
            radii.append(radius)
            weights.append(weight)
    
    if not radii:
        return 0.0
    
    r_bar = sum(r * w for r, w in zip(radii, weights))
    if r_bar == 0:
        return 0.0
    
    delta = 0.0
    for r, w in zip(radii, weights):
        delta += w * ((1 - r / r_bar) ** 2)
    
    return np.sqrt(delta)

def calculate_electronegativity_difference(composition_str: str) -> float:
    """
    Calculate electronegativity difference (delta_chi).
    Formula: sqrt(sum(ci * (chi_i - chi_bar)^2))
    """
    comp = parse_composition(composition_str)
    if not comp:
        return 0.0
    
    chis = []
    weights = []
    for symbol, weight in comp.items():
        _, chi, _ = get_element_properties(symbol)
        if chi is not None:
            chis.append(chi)
            weights.append(weight)
    
    if not chis:
        return 0.0
    
    chi_bar = sum(c * w for c, w in zip(chis, weights))
    delta = 0.0
    for c, w in zip(chis, weights):
        delta += w * ((c - chi_bar) ** 2)
    
    return np.sqrt(delta)

def calculate_vec(composition_str: str) -> float:
    """
    Calculate average Valence Electron Concentration (VEC).
    Formula: sum(ci * VEC_i)
    """
    comp = parse_composition(composition_str)
    if not comp:
        return 0.0
    
    vecs = []
    weights = []
    for symbol, weight in comp.items():
        _, _, vec = get_element_properties(symbol)
        if vec is not None:
            vecs.append(vec)
            weights.append(weight)
    
    if not vecs:
        return 0.0
    
    return sum(v * w for v, w in zip(vecs, weights))

def compute_descriptors(df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """
    Compute descriptors for the dataframe.
    """
    logger.info("Computing descriptors...")
    
    # Apply calculations
    df['radius_mismatch'] = df['composition'].apply(calculate_radius_mismatch)
    df['electronegativity_diff'] = df['composition'].apply(calculate_electronegativity_difference)
    df['VEC'] = df['composition'].apply(calculate_vec)
    
    # Diagnostic: weighted mean radius (for logging only, not model)
    logger.info("Calculating weighted mean radius for diagnostic...")
    weighted_radii = df['composition'].apply(lambda x: calculate_weighted_mean_radius(x, logger))
    avg_weighted_radius = weighted_radii.dropna().mean()
    
    if not np.isnan(avg_weighted_radius):
        logger.info(f"Average weighted mean radius: {avg_weighted_radius:.4f} Angstrom")
    else:
        logger.warning("Could not calculate average weighted mean radius.")
    
    return df, avg_weighted_radius

def save_diagnostic_log(avg_radius: float, project_root: Path):
    """Save diagnostic log to JSON."""
    diag = {"weighted_mean_radius": float(avg_radius) if not np.isnan(avg_radius) else 0.0}
    path = project_root / "data" / "processed" / "diagnostic_log.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(diag, f, indent=2)
    
    # Archive to artifacts
    archive_path = project_root / "artifacts" / "reports" / "diagnostic_log.json"
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copy(path, archive_path)
    logging.getLogger(__name__).info(f"Diagnostic log saved and archived to {archive_path}")

def save_descriptors(df: pd.DataFrame, project_root: Path):
    """Save computed descriptors to CSV, dropping diagnostic-only columns."""
    # Drop 'weighted_mean_radius' if it exists in the df (it shouldn't, but be safe)
    if 'weighted_mean_radius' in df.columns:
        df = df.drop(columns=['weighted_mean_radius'])
    
    output_path = project_root / "data" / "processed" / "descriptors.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logging.getLogger(__name__).info(f"Descriptors saved to {output_path}")

@resource_monitor(runtime_limit_h=2.0, memory_limit_gb=7.0)
def run_descriptors():
    """Main descriptors pipeline."""
    logger = setup_logging()
    project_root = get_project_root()
    
    input_path = project_root / "data" / "processed" / "cleaned_mg.csv"
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    df, avg_radius = compute_descriptors(df, logger)
    
    save_descriptors(df, project_root)
    save_diagnostic_log(avg_radius, project_root)
    
    logger.info("Descriptors pipeline complete.")

def main():
    run_descriptors()

if __name__ == "__main__":
    main()
