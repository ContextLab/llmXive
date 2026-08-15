"""
T031: Filter and rank top 5 interaction terms contributing to model variance.

Reads SHAP values and feature names from data/artifacts/shap_analysis.npy
and data/processed/solubility_features.csv (to identify interaction columns).
Outputs updated ranking to data/artifacts/shap_ranking.json.

Dependency: T030 must be completed.
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.constants import DATA_DIR

def load_shap_values():
    """Load SHAP values from the artifact file."""
    shap_path = DATA_DIR / "artifacts" / "shap_values.npy"
    if not shap_path.exists():
        raise FileNotFoundError(f"SHAP values file not found at {shap_path}")
    return np.load(shap_path)

def load_feature_names():
    """Load feature names from the processed dataset."""
    features_path = DATA_DIR / "processed" / "solubility_features.csv"
    if not features_path.exists():
        raise FileNotFoundError(f"Features file not found at {features_path}")
    
    df = pd.read_csv(features_path)
    # Identify interaction terms: columns containing 'interaction' or specific patterns
    # Based on T016, interaction terms are explicitly generated
    interaction_cols = [col for col in df.columns if 'interaction' in col.lower()]
    
    # If no explicit 'interaction' column name, look for generated pairs (e.g., x1*x2)
    if not interaction_cols:
        # Heuristic: look for columns with '*' or specific naming conventions used in T016
        interaction_cols = [col for col in df.columns if '*' in col or ('_x_' in col and 'fp' not in col)]
    
    # Fallback: if still none, assume the last N columns are interaction terms (common pattern)
    # But we prefer explicit identification
    if not interaction_cols:
        # Check for columns that are not standard descriptors or fingerprints
        standard_cols = ['solute_fp', 'solvent_desc', 'logS', 'mixture_composition']
        interaction_cols = [col for col in df.columns 
                          if col not in standard_cols 
                          and not any(x in col for x in ['fp', 'molecular_weight', 'logP', 'tpsa'])]
        
    return interaction_cols

def load_existing_ranking():
    """Load the existing SHAP ranking from T030."""
    ranking_path = DATA_DIR / "artifacts" / "shap_ranking.json"
    if not ranking_path.exists():
        # Create empty structure if T030 didn't run or file missing
        return {
            "feature_importance": [],
            "top_features": [],
            "interaction_terms": []
        }
    
    with open(ranking_path, 'r') as f:
        return json.load(f)

def identify_interaction_terms_from_shap(shap_values, feature_names):
    """
    Map SHAP values to feature names and identify interaction terms.
    Returns a list of (feature_name, mean_abs_shap) for interaction terms only.
    """
    if len(feature_names) != shap_values.shape[1]:
        # Fallback: assume order matches and we need to slice
        # This shouldn't happen if data is consistent
        raise ValueError(f"Feature name count ({len(feature_names)}) doesn't match SHAP columns ({shap_values.shape[1]})")
    
    interaction_features = []
    
    # Calculate mean absolute SHAP value for each feature
    mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
    
    for i, (feat_name, shap_val) in enumerate(zip(feature_names, mean_abs_shap)):
        # Identify if this is an interaction term based on naming
        # T016 generates terms like "solvent_A_x_solvent_B" or similar
        if any(keyword in feat_name.lower() for keyword in ['interaction', 'mix', 'x_', '*']):
            interaction_features.append({
                "feature_name": feat_name,
                "mean_abs_shap": float(shap_val),
                "rank": 0  # Will be updated later
            })
    
    return interaction_features

def filter_and_rank_top5(interaction_features, top_n=5):
    """
    Filter interaction terms and rank by contribution to variance (mean abs SHAP).
    Returns top N terms.
    """
    # Sort by mean absolute SHAP value descending
    sorted_features = sorted(
        interaction_features, 
        key=lambda x: x['mean_abs_shap'], 
        reverse=True
    )
    
    # Take top N
    top_terms = sorted_features[:top_n]
    
    # Assign ranks
    for idx, term in enumerate(top_terms):
        term['rank'] = idx + 1
    
    return top_terms

def main():
    """Main execution for T031."""
    print("Starting T031: Filter and rank top 5 interaction terms")
    
    try:
        # Load data
        shap_values = load_shap_values()
        interaction_feature_names = load_feature_names()
        existing_ranking = load_existing_ranking()
        
        # Identify which columns in SHAP correspond to interaction terms
        # We need to map feature names to SHAP columns
        # Load the full feature list to get mapping
        features_df = pd.read_csv(DATA_DIR / "processed" / "solubility_features.csv")
        all_feature_names = list(features_df.columns)
        
        # Filter for interaction terms only
        interaction_terms_data = []
        for i, name in enumerate(all_feature_names):
            if any(keyword in name.lower() for keyword in ['interaction', 'mix', 'x_', '*']):
                if i < shap_values.shape[1]:
                    mean_abs = float(np.mean(np.abs(shap_values[:, i])))
                    interaction_terms_data.append({
                        "feature_name": name,
                        "mean_abs_shap": mean_abs
                    })
        
        # If no interaction terms found by name, check the last few columns (common pattern)
        if not interaction_terms_data:
            print("Warning: No interaction terms found by name. Checking last 10 columns as fallback.")
            for i in range(max(0, len(all_feature_names) - 10), len(all_feature_names)):
                name = all_feature_names[i]
                mean_abs = float(np.mean(np.abs(shap_values[:, i])))
                interaction_terms_data.append({
                    "feature_name": name,
                    "mean_abs_shap": mean_abs
                })
        
        # Sort and rank
        sorted_terms = sorted(interaction_terms_data, key=lambda x: x['mean_abs_shap'], reverse=True)
        top_5 = sorted_terms[:5]
        
        for idx, term in enumerate(top_5):
            term['rank'] = idx + 1
        
        # Update ranking structure
        existing_ranking['interaction_terms'] = top_5
        existing_ranking['total_interaction_terms_found'] = len(interaction_terms_data)
        
        # Save updated ranking
        output_path = DATA_DIR / "artifacts" / "shap_ranking.json"
        with open(output_path, 'w') as f:
            json.dump(existing_ranking, f, indent=2)
        
        print(f"Successfully ranked {len(top_5)} top interaction terms.")
        print(f"Output written to: {output_path}")
        
        # Print summary
        print("\nTop 5 Interaction Terms by Variance Contribution:")
        for term in top_5:
            print(f"  {term['rank']}. {term['feature_name']}: {term['mean_abs_shap']:.6f}")
        
        return 0
        
    except Exception as e:
        print(f"ERROR: T031 failed - {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
