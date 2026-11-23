import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import from existing API surface
from utils.logger import get_logger

def load_feature_stability_results() -> Optional[Dict[str, Any]]:
    """
    Load the feature stability analysis results from T023.
    
    Returns:
        Dict containing feature stability metrics, or None if file not found.
    """
    logger = get_logger()
    file_path = Path("data/processed/feature_stability_results.json")
    
    if not file_path.exists():
        logger.warning(f"Feature stability results file not found: {file_path}")
        return None
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse feature stability results: {e}")
        return None

def load_physical_plausibility_results() -> Optional[Dict[str, Any]]:
    """
    Load the physical plausibility check results from T025.
    
    Returns:
        Dict containing physical plausibility check, or None if file not found.
    """
    logger = get_logger()
    file_path = Path("data/processed/physical_plausibility.json")
    
    if not file_path.exists():
        logger.warning(f"Physical plausibility results file not found: {file_path}")
        return None
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse physical plausibility results: {e}")
        return None

def generate_summary_table(
    stability_results: Optional[Dict[str, Any]] = None,
    plausibility_results: Optional[Dict[str, Any]] = None
) -> pd.DataFrame:
    """
    Generate the feature interpretation summary table.
    
    This function maps features to their hypothesized chemical interpretation
    based on the stability analysis and physical plausibility checks.
    
    Args:
        stability_results: Results from T023 feature stability analysis.
        plausibility_results: Results from T025 physical plausibility check.
        
    Returns:
        DataFrame with columns: feature_name, chemical_interpretation, hypothesis
    """
    logger = get_logger()
    
    # Define the mapping of features to chemical interpretations and hypotheses
    # This is based on the domain knowledge of halide binding chemistry
    feature_interpretations = {
        'charge_density': {
            'chemical_interpretation': 'Electrostatic attraction strength between host cation and halide anion',
            'hypothesis': 'Higher positive charge density increases binding affinity via Coulombic attraction (SC-007)'
        },
        'cavity_volume': {
            'chemical_interpretation': 'Steric fit of halide anion within host binding pocket',
            'hypothesis': 'Smaller cavity volume enhances affinity for smaller halides (F⁻) but reduces it for larger halides (I⁻) due to steric hindrance'
        },
        'hydrogen_bond_donor_count': {
            'chemical_interpretation': 'Number of hydrogen bond donors available for halide interaction',
            'hypothesis': 'More H-bond donors increase binding affinity, particularly for harder halides (F⁻, Cl⁻)'
        },
        'hydrogen_bond_acceptor_count': {
            'chemical_interpretation': 'Number of hydrogen bond acceptors in the host structure',
            'hypothesis': 'H-bond acceptors may compete with halide binding or modulate host flexibility'
        },
        'molecular_weight': {
            'chemical_interpretation': 'Overall size and complexity of the host molecule',
            'hypothesis': 'Larger hosts may provide more binding sites but could suffer from entropic penalties'
        },
        'logP': {
            'chemical_interpretation': 'Hydrophobicity of the host molecule',
            'hypothesis': 'Higher logP may enhance binding in non-polar solvents but reduce solubility'
        },
        'polarizability': {
            'chemical_interpretation': 'Ability of host electron cloud to distort in response to halide',
            'hypothesis': 'Higher polarizability favors binding to softer halides (Br⁻, I⁻) via dispersion forces'
        },
        'num_rotatable_bonds': {
            'chemical_interpretation': 'Flexibility of the host molecule',
            'hypothesis': 'Fewer rotatable bonds (rigid hosts) may enhance binding via reduced entropic penalty'
        },
        'aromatic_ring_count': {
            'chemical_interpretation': 'Number of aromatic rings in the host structure',
            'hypothesis': 'Aromatic rings may contribute to halide-π interactions, especially with larger halides'
        }
    }
    
    # Determine which features are "top" features based on stability results
    top_features = []
    if stability_results and 'top_features' in stability_results:
        top_features = stability_results['top_features']
    elif stability_results and 'features' in stability_results:
        # Fallback: use all features if top_features not explicitly defined
        top_features = list(stability_results['features'].keys())
    
    # If no stability results, use a default set of expected features
    if not top_features:
        top_features = list(feature_interpretations.keys())
    
    # Build the summary table
    rows = []
    for feature_name in top_features:
        if feature_name in feature_interpretations:
            interpretation = feature_interpretations[feature_name]
        else:
            # Default interpretation for unknown features
            interpretation = {
                'chemical_interpretation': f'Chemical descriptor related to {feature_name}',
                'hypothesis': f'Feature {feature_name} may influence binding affinity through unspecified mechanisms'
            }
        
        # Add stability information to the hypothesis if available
        if stability_results and 'features' in stability_results:
            feat_data = stability_results['features'].get(feature_name, {})
            cv = feat_data.get('coefficient_of_variation')
            is_stable = feat_data.get('is_stable', True)
            
            if cv is not None:
                stability_note = f" (CV={cv:.3f}, {'stable' if is_stable else 'unstable'})"
                interpretation['hypothesis'] += stability_note
        
        # Add plausibility information if this is the top feature
        if plausibility_results and feature_name == plausibility_results.get('top_feature'):
            is_plausible = plausibility_results.get('is_plausible', True)
            reasoning = plausibility_results.get('reasoning', '')
            if not is_plausible:
                interpretation['hypothesis'] += f" [WARNING: {reasoning}]"
            else:
                interpretation['hypothesis'] += f" [VERIFIED: {reasoning}]"
        
        rows.append({
            'feature_name': feature_name,
            'chemical_interpretation': interpretation['chemical_interpretation'],
            'hypothesis': interpretation['hypothesis']
        })
    
    # Sort by feature name for consistent output
    df = pd.DataFrame(rows)
    df = df.sort_values('feature_name').reset_index(drop=True)
    
    logger.info(f"Generated feature interpretation summary with {len(df)} features")
    return df

def save_summary_table(df: pd.DataFrame, output_path: str = "data/processed/feature_interpretation_summary.csv") -> None:
    """
    Save the feature interpretation summary table to a CSV file.
    
    Args:
        df: The summary DataFrame to save.
        output_path: Path where the CSV will be written.
    """
    logger = get_logger()
    output_file = Path(output_path)
    
    # Ensure the output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_file, index=False)
    logger.info(f"Saved feature interpretation summary to {output_file}")

def main() -> None:
    """
    Main entry point for T026: Generate feature interpretation summary table.
    
    This task depends on:
    - T023: Feature stability analysis (data/processed/feature_stability_results.json)
    - T025: Physical plausibility check (data/processed/physical_plausibility.json)
    
    Output:
    - data/processed/feature_interpretation_summary.csv
    """
    logger = get_logger()
    logger.info("Starting T026: Generate feature interpretation summary table")
    
    # Load prerequisite results
    stability_results = load_feature_stability_results()
    plausibility_results = load_physical_plausibility_results()
    
    if stability_results is None:
        logger.error("Cannot proceed: T023 (feature stability) results not found. Aborting.")
        return
    
    if plausibility_results is None:
        logger.warning("T025 (physical plausibility) results not found. Proceeding without plausibility checks.")
    
    # Generate the summary table
    summary_df = generate_summary_table(stability_results, plausibility_results)
    
    # Save the summary table
    output_path = "data/processed/feature_interpretation_summary.csv"
    save_summary_table(summary_df, output_path)
    
    # Log success
    logger.info("T026 completed successfully. Output: data/processed/feature_interpretation_summary.csv")

if __name__ == "__main__":
    main()