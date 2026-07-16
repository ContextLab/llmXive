import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional

from utils.logger import get_logger
from utils.config import get_data_path, get_code_path

logger = get_logger(__name__)

# Mapping of feature names to chemical hypotheses based on domain knowledge
# and typical receptor-halide interaction physics.
FEATURE_HYPOTHESES: Dict[str, str] = {
    "charge_density": "Higher local positive charge density on the binding cavity enhances electrostatic attraction to anions (F⁻ > Cl⁻ > Br⁻ > I⁻).",
    "cavity_volume": "Optimal cavity volume matches the ionic radius of the halide; too large reduces contact, too small causes steric clash.",
    "hydrogen_bond_donor_count": "Increased H-bond donors stabilize the halide via directional electrostatic interactions, particularly effective for smaller, harder halides (F⁻).",
    "molecular_weight": "Heavier hosts may have more polarizable electron clouds, potentially stabilizing larger, softer halides (I⁻) via dispersion forces.",
    "topological_polar_surface_area": "Higher TPSA indicates more polar surface area, correlating with stronger solvation competition and potentially lower affinity in polar solvents.",
    "num_rotatable_bonds": "Fewer rotatable bonds (rigid hosts) pre-organize the binding site, reducing entropic penalty upon halide binding.",
    "ecfp_fingerprint_bits": "Specific substructural motifs (captured by ECFP bits) may define the binding pocket geometry or electronic environment favorable for specific halides."
}

def load_feature_stability_results() -> Optional[Dict[str, Any]]:
    """
    Load the feature stability analysis results from T023.
    Expected file: data/processed/feature_stability_results.json
    """
    data_path = get_data_path()
    file_path = data_path / "processed" / "feature_stability_results.json"
    
    if not file_path.exists():
        logger.warning(f"Feature stability results file not found: {file_path}")
        return None

    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse feature stability results JSON: {e}")
        return None

def load_physical_plausibility_results() -> Optional[Dict[str, Any]]:
    """
    Load the physical plausibility check results from T025.
    Expected file: data/processed/physical_plausibility_results.json
    """
    data_path = get_data_path()
    file_path = data_path / "processed" / "physical_plausibility_results.json"
    
    if not file_path.exists():
        logger.warning(f"Physical plausibility results file not found: {file_path}")
        return None

    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse physical plausibility results JSON: {e}")
        return None

def generate_summary_table(
    stability_results: Optional[Dict[str, Any]],
    plausibility_results: Optional[Dict[str, Any]]
) -> pd.DataFrame:
    """
    Generate a summary table mapping features to chemical hypotheses.
    
    Columns:
    - feature_name: The name of the descriptor.
    - rank: Rank based on stability (lower CV = better).
    - cv_score: Coefficient of variation (stability metric).
    - hypothesis: The chemical hypothesis explaining the feature's role.
    - physical_status: 'Plausible', 'Implausible', or 'Unknown' based on T025.
    - stability_flag: 'Stable' (CV < 0.3) or 'Unstable' (CV >= 0.3).
    """
    if stability_results is None and plausibility_results is None:
        logger.error("No data available to generate summary table.")
        return pd.DataFrame()

    # Extract features and stability metrics
    features_data = []
    
    if stability_results and "feature_cv" in stability_results:
        # Sort by CV ascending (most stable first)
        sorted_features = sorted(
            stability_results["feature_cv"].items(), 
            key=lambda x: x[1]
        )
        
        for rank, (feature, cv) in enumerate(sorted_features, start=1):
            hypothesis = FEATURE_HYPOTHESES.get(feature, "No specific hypothesis defined.")
            
            # Determine physical status
            physical_status = "Unknown"
            if plausibility_results and "top_feature" in plausibility_results:
                if feature == plausibility_results["top_feature"]:
                    physical_status = "Plausible" if plausibility_results.get("is_plausible", False) else "Implausible"
                elif feature in plausibility_results.get("checked_features", []):
                    # If we have specific status for this feature
                    status_map = plausibility_results.get("feature_status", {})
                    physical_status = status_map.get(feature, "Unknown")
            
            stability_flag = "Stable" if cv < 0.3 else "Unstable"
            
            features_data.append({
                "feature_name": feature,
                "rank": rank,
                "cv_score": cv,
                "hypothesis": hypothesis,
                "physical_status": physical_status,
                "stability_flag": stability_flag
            })
    
    df = pd.DataFrame(features_data)
    
    if df.empty:
        logger.warning("No features found in stability results to generate table.")
    
    return df

def save_summary_table(df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """
    Save the summary table to a CSV file.
    Default path: data/processed/feature_summary.csv
    """
    if output_path is None:
        data_path = get_data_path()
        output_path = data_path / "processed" / "feature_summary.csv"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Feature summary table saved to: {output_path}")
    return output_path

def main():
    """
    Main entry point for T026: Generate feature interpretation summary table.
    Dependencies: T023 (Stability), T025 (Physical Plausibility)
    """
    logger.info("Starting T026: Generating feature interpretation summary table.")
    
    # Load dependencies
    stability_results = load_feature_stability_results()
    plausibility_results = load_physical_plausibility_results()
    
    # Generate table
    summary_df = generate_summary_table(stability_results, plausibility_results)
    
    if summary_df.empty:
        logger.error("Failed to generate summary table. Missing required data.")
        # Even if empty, we create an empty file to signify the task ran, 
        # but log the failure.
        save_summary_table(summary_df)
        return 1
    
    # Save output
    save_summary_table(summary_df)
    
    # Also save a JSON version for programmatic access if needed
    data_path = get_data_path()
    json_path = data_path / "processed" / "feature_summary.json"
    summary_df.to_json(json_path, orient='records', indent=2)
    logger.info(f"Feature summary JSON saved to: {json_path}")
    
    logger.info("T026 completed successfully.")
    return 0

if __name__ == "__main__":
    exit(main())