"""
Feature Interpretation Summary Generator (T026)

Generates a summary table mapping machine learning features to chemical hypotheses
based on the stability analysis (T023) and physical plausibility checks (T025).

This script must run after T023 and T025.
"""

import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import from project utils
from code.utils.logger import get_logger
from code.utils.config import get_data_path, get_path

logger = get_logger(__name__)

# Mapping of feature names to chemical hypotheses based on domain knowledge
FEATURE_HYPOTHESES = {
    "charge_density": (
        "Higher charge density on the host binding pocket increases electrostatic "
        "attraction to anions (F⁻ > Cl⁻ > Br⁻ > I⁻), leading to higher binding affinity."
    ),
    "cavity_volume": (
        "Optimal cavity volume matches the ionic radius of the halide. Too small "
        "causes steric repulsion; too large reduces van der Waals contact and "
        "electrostatic field strength."
    ),
    "hydrogen_bond_donor_count": (
        "Increased number of hydrogen bond donors (e.g., NH, OH groups) enhances "
        "specific halide recognition via directional H-bonding, particularly for "
        "smaller, harder anions like F⁻."
    ),
    "polarizability": (
        "Host polarizability modulates dispersion forces with larger, softer "
        "anions (I⁻, Br⁻). Higher polarizability may favor softer anions."
    ),
    "molecular_weight": (
        "Molecular weight acts as a proxy for scaffold size. Correlation may "
        "indicate size-dependent steric constraints rather than a direct chemical "
        "mechanism."
    ),
    "logP": (
        "Lipophilicity (logP) influences solvation effects. Higher logP may "
        "disfavor binding in polar solvents (acetonitrile) due to desolvation "
        "penalties, or favor binding in non-polar solvents."
    ),
    "aromatic_ring_count": (
        "Aromatic rings provide pi-holes or quadrupole moments that can interact "
        "with anions (anion-pi interactions). Higher count may stabilize larger "
        "anions."
    ),
    "formal_charge": (
        "Net formal charge on the host (e.g., cationic receptors) strongly "
        "enhances affinity via Coulombic attraction. Neutral hosts rely on "
        "weaker interactions."
    ),
    "homo_energy": (
        "HOMO energy relates to electron-donating capability. May correlate with "
        "charge transfer interactions in specific host-guest complexes."
    ),
    "lumo_energy": (
        "LUMO energy relates to electron-accepting capability. Lower LUMO may "
        "facilitate charge transfer from the anion to the host."
    )
}

# Default hypotheses for unknown features
DEFAULT_HYPOTHESIS = (
    "Feature correlates with binding affinity. Specific chemical mechanism "
    "requires further investigation or domain-specific literature review."
)

def load_feature_stability_results() -> Optional[Dict[str, Any]]:
    """
    Load the feature stability analysis results from T023.
    Expected path: data/processed/feature_stability.json
    """
    path = get_data_path() / "processed" / "feature_stability.json"
    if not path.exists():
        logger.warning(f"Feature stability results not found at {path}. "
                       "Ensure T023 has run successfully.")
        return None

    with open(path, 'r') as f:
        return json.load(f)

def load_physical_plausibility_results() -> Optional[Dict[str, Any]]:
    """
    Load the physical plausibility check results from T025.
    Expected path: data/processed/physical_plausibility.json
    """
    path = get_data_path() / "processed" / "physical_plausibility.json"
    if not path.exists():
        logger.warning(f"Physical plausibility results not found at {path}. "
                       "Ensure T025 has run successfully.")
        return None

    with open(path, 'r') as f:
        return json.load(f)

def generate_summary_table(
    stability_data: Dict[str, Any],
    plausibility_data: Dict[str, Any]
) -> pd.DataFrame:
    """
    Generate a summary DataFrame mapping features to chemical hypotheses.
    """
    records = []

    # Extract top features from stability analysis
    # Expected structure: {"top_features": [{"feature": name, "cv": val, "rank": int}, ...]}
    top_features = stability_data.get("top_features", [])

    # Create a lookup for plausibility results
    # Expected structure: {"top_feature": name, "plausible": bool, "reason": str}
    top_feature_name = plausibility_data.get("top_feature")
    is_top_plausible = plausibility_data.get("plausible", True)
    plausibility_reason = plausibility_data.get("reason", "N/A")

    for idx, feat_info in enumerate(top_features):
        feature_name = feat_info.get("feature")
        cv = feat_info.get("cv")
        rank = feat_info.get("rank")
        stability_label = "Stable" if cv < 0.3 else "Unstable"

        # Retrieve hypothesis
        hypothesis = FEATURE_HYPOTHESES.get(feature_name, DEFAULT_HYPOTHESIS)

        # Determine physical plausibility flag for this feature
        # If this is the top feature, use the specific plausibility result
        # Otherwise, assume plausible unless known otherwise
        phys_flag = "Unknown"
        if feature_name == top_feature_name:
            phys_flag = "Plausible" if is_top_plausible else "Implausible"
        else:
            # For non-top features, we don't have specific checks in T025
            # but we can infer if the hypothesis aligns with general principles
            # For now, mark as 'Not Checked' to be safe
            phys_flag = "Not Checked"

        records.append({
            "Rank": rank,
            "Feature": feature_name,
            "Stability (CV)": cv,
            "Stability Status": stability_label,
            "Physical Plausibility": phys_flag,
            "Chemical Hypothesis": hypothesis,
            "Plausibility Note": plausibility_reason if phys_flag != "Not Checked" else "-"
        })

    df = pd.DataFrame(records)
    # Sort by rank
    df = df.sort_values(by="Rank").reset_index(drop=True)
    return df

def save_summary_table(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the summary table as CSV and JSON.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save CSV
    csv_path = output_path.with_suffix('.csv')
    df.to_csv(csv_path, index=False)
    logger.info(f"Saved feature summary table to {csv_path}")

    # Save JSON for programmatic access
    json_path = output_path.with_suffix('.json')
    summary_dict = {
        "generated_at": pd.Timestamp.now().isoformat(),
        "total_features_analyzed": len(df),
        "stable_features_count": len(df[df["Stability Status"] == "Stable"]),
        "implausible_features_count": len(df[df["Physical Plausibility"] == "Implausible"]),
        "summary": df.to_dict(orient="records")
    }
    with open(json_path, 'w') as f:
        json.dump(summary_dict, f, indent=2)
    logger.info(f"Saved feature summary JSON to {json_path}")

def main():
    """
    Main entry point for T026.
    """
    logger.info("Starting Feature Interpretation Summary Generation (T026)...")

    # Load dependencies
    stability_data = load_feature_stability_results()
    plausibility_data = load_physical_plausibility_results()

    if not stability_data or not plausibility_data:
        logger.error("Missing required input data. Ensure T023 and T025 have completed.")
        raise FileNotFoundError("Required input files (feature_stability.json, physical_plausibility.json) not found.")

    # Generate table
    df = generate_summary_table(stability_data, plausibility_data)

    # Define output path
    output_dir = get_data_path() / "processed"
    output_file = output_dir / "feature_summary_table"

    # Save results
    save_summary_table(df, output_file)

    logger.info("T026 completed successfully.")
    print(df.to_string(index=False))

if __name__ == "__main__":
    main()