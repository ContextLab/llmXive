import os
import sys
import logging
import json
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats

# Add parent to path for imports if running as script
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models.utils import benjamini_hochberg_fdr, run_permutation_test_early_stop, save_permutation_results
from src.lib.config import SEED, PERMUTATIONS

logger = logging.getLogger(__name__)

def fit_species_year_gamm(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Fit a Unified Spatial Model for each species-year combination.
    Model: phenology_metric ~ s(temp) + s(precip) + s(effort) + (1 + temp | species) + GP_spatial
    
    For this implementation, we use a simplified linear regression as a proxy.
    In a full implementation, this would use pyGAM or similar.
    """
    results = []
    
    for (species, year), group in df.groupby(["species", "year"]):
        if len(group) < 10:
            continue
        
        # Simplified model: linear regression
        X = group[["median_arrival"]].values
        y = group["first_arrival"].values
        
        if len(X) == 0 or len(y) == 0:
            continue
        
        # Calculate correlation as a proxy for the coefficient
        try:
            corr = np.corrcoef(X.flatten(), y)[0, 1]
            if np.isnan(corr):
                corr = 0.0
            
            results.append({
                "species": species,
                "year": year,
                "coefficient": float(corr),
                "p_value": 0.0,  # Placeholder
                "n_obs": len(group)
            })
        except Exception as e:
            logger.warning(f"Failed to fit model for {species}-{year}: {e}")
    
    return results

def run_permutation_test_gamm(df: pd.DataFrame, output_path: Path) -> List[Dict[str, Any]]:
    """
    Run permutation test for GAMM coefficients.
    """
    permutation_results = []
    
    for (species, year), group in df.groupby(["species", "year"]):
        if len(group) < 10:
            continue
        
        X = group["median_arrival"].values
        y = group["first_arrival"].values
        
        if len(X) == 0 or len(y) == 0:
            continue
        
        # Run permutation test
        result = run_permutation_test_early_stop(y, X, n_shuffles=1000, seed=SEED)
        
        permutation_results.append({
            "species": species,
            "year": year,
            "coefficient": "median_arrival",
            "p_value": result["p_value"],
            "n_shuffles": result["n_shuffles"],
            "early_stop_flag": result["early_stop_flag"],
            "final_p_value": result["p_value"]
        })
    
    # Save results
    save_permutation_results(permutation_results, output_path)
    return permutation_results

def apply_fdr_correction(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Apply Benjamini-Hochberg FDR correction to all species-climate coefficients."""
    p_values = [r["p_value"] for r in results]
    significant, adjusted_p_values = benjamini_hochberg_fdr(p_values)
    
    for i, result in enumerate(results):
        result["adjusted_p_value"] = adjusted_p_values[i]
        result["is_significant"] = significant[i]
    
    return results

def run_gamm_pipeline(data_dir: Path = None, output_dir: Path = None) -> None:
    """Main GAMM pipeline entry point."""
    if data_dir is None:
        data_dir = project_root / "data" / "interim"
    if output_dir is None:
        output_dir = project_root / "data" / "processed"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load processed data
    phenology_path = data_dir / "phenology_metrics.csv"
    if not phenology_path.exists():
        logger.error("Phenology data not found. Run preprocessing pipeline first.")
        return
    
    df = pd.read_csv(phenology_path)
    
    # Fit models
    model_results = fit_species_year_gamm(df)
    
    # Run permutation tests
    permutation_path = output_dir / "permutation_results.json"
    permutation_results = run_permutation_test_gamm(df, permutation_path)
    
    # Apply FDR correction
    corrected_results = apply_fdr_correction(permutation_results)
    
    # Save final results
    with open(output_dir / "gamm_results.json", 'w') as f:
        json.dump(corrected_results, f, indent=2)
    
    logger.info(f"GAMM pipeline complete. Results saved to {output_dir}")
