import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Constants
SPEC_DIR = Path(__file__).parent.parent / "specs" / "001-predict-voc-profiles"
DATA_DIR = Path(__file__).parent.parent / "data"
RESULTS_DIR = DATA_DIR / "results"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = DATA_DIR / "models"

# Known Terpene Synthase (TPS) families for Arabidopsis thaliana
# Based on literature (e.g., Tholl et al., 2005; Chen et al., 2011)
# These are the standard TPS subfamilies found in Arabidopsis
KNOWN_TPS_FAMILIES = {
    "TPSa", "TPSb", "TPSc", "TPSd", "TPSe", "TPSf", "TPSg", "TPSh", "TPSi"
}

def load_model_and_feature_importance(model_path: Path = None, importance_path: Path = None) -> Tuple[Dict, pd.DataFrame]:
    """
    Load the trained model and feature importance data.
    
    Args:
        model_path: Path to the trained model pickle file.
        importance_path: Path to the feature importance JSON file (from T028/T030).
        
    Returns:
        Tuple of (model, feature_importance_df)
    """
    if model_path is None:
        model_path = MODELS_DIR / "random_forest.pkl"
    if importance_path is None:
        importance_path = RESULTS_DIR / "feature_importance_pvalues.json"
        
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    if not importance_path.exists():
        raise FileNotFoundError(f"Feature importance file not found: {importance_path}")
        
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
        
    with open(importance_path, 'r') as f:
        importance_data = json.load(f)
        
    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(importance_data)
    return model, df

def load_pathway_mapping(mapping_path: Path = None) -> Dict[str, str]:
    """
    Load the gene-to-pathway mapping used in T016.
    This mapping links individual genes to their pathway/family (e.g., TPSa, TPSb).
    
    Args:
        mapping_path: Path to the gene-pathway mapping file.
        
    Returns:
        Dictionary mapping gene names to pathway/family names.
    """
    if mapping_path is None:
        # Expected location based on T016 output
        mapping_path = SPEC_DIR / "gene_pathway_mapping.json"
        
    if not mapping_path.exists():
        # If the specific mapping file doesn't exist, try to infer from aggregated features
        # This is a fallback for when we only have aggregated pathway features
        return {}
        
    with open(mapping_path, 'r') as f:
        return json.load(f)

def calculate_overlap_statistics(feature_importance_df: pd.DataFrame, 
                                 gene_to_pathway: Dict[str, str],
                                 top_n: int = 20) -> Dict:
    """
    Calculate overlap statistics between top important features and known TPS families.
    
    This implements FR-008: Validate that top predictive features overlap with 
    known terpene synthase gene families.
    
    Args:
        feature_importance_df: DataFrame with 'feature', 'importance', 'p_value', 'p_value_corrected'.
        gene_to_pathway: Mapping of gene names to pathway/family names.
        top_n: Number of top features to analyze.
        
    Returns:
        Dictionary containing overlap statistics.
    """
    # Sort by corrected p-value (most significant first) or importance
    # Using corrected p-value as primary sort, then importance
    sorted_df = feature_importance_df.sort_values(
        by=['p_value_corrected', 'importance'], 
        ascending=[True, False]
    )
    
    top_features = sorted_df.head(top_n)
    
    # Identify which top features belong to known TPS families
    tps_hits = []
    non_tps_hits = []
    
    for _, row in top_features.iterrows():
        feature_name = row['feature']
        # Extract gene name if feature is "pathway_gene" format, or use as is
        # Assuming features might be named like "TPSa_Gene1" or just "Gene1"
        gene_name = feature_name.split('_')[-1] if '_' in feature_name else feature_name
        
        pathway = gene_to_pathway.get(gene_name, None)
        
        if pathway and pathway in KNOWN_TPS_FAMILIES:
            tps_hits.append({
                'feature': feature_name,
                'pathway': pathway,
                'importance': row['importance'],
                'p_value': row['p_value'],
                'p_value_corrected': row['p_value_corrected']
            })
        else:
            non_tps_hits.append({
                'feature': feature_name,
                'pathway': pathway,
                'importance': row['importance'],
                'p_value': row['p_value'],
                'p_value_corrected': row['p_value_corrected']
            })
    
    # Calculate statistics
    total_top = len(top_features)
    tps_count = len(tps_hits)
    non_tps_count = len(non_tps_hits)
    
    overlap_percentage = (tps_count / total_top * 100) if total_top > 0 else 0
    
    # Enrichment analysis: Compare observed vs expected
    # Expected: proportion of TPS families in the entire feature set
    all_features = feature_importance_df['feature'].tolist()
    all_genes = [f.split('_')[-1] if '_' in f else f for f in all_features]
    all_pathways = [gene_to_pathway.get(g, None) for g in all_genes]
    total_tps_in_set = sum(1 for p in all_pathways if p in KNOWN_TPS_FAMILIES)
    expected_percentage = (total_tps_in_set / len(all_pathways) * 100) if all_pathways else 0
    
    enrichment_ratio = (overlap_percentage / expected_percentage) if expected_percentage > 0 else float('inf')
    
    # Fisher's exact test approximation (simplified)
    # Contingency table:
    #                In Top N    Not in Top N
    # TPS Family        a           b
    # Not TPS Family    c           d
    a = tps_count
    c = total_tps_in_set - tps_count
    b = non_tps_count
    d = len(all_pathways) - total_tps_in_set - non_tps_count
    
    # Avoid division by zero
    if (a + b) == 0 or (c + d) == 0 or (a + c) == 0 or (b + d) == 0:
        odds_ratio = float('inf') if a > 0 and c == 0 else 0
    else:
        odds_ratio = (a * d) / (b * c) if (b * c) > 0 else float('inf')
    
    return {
        'top_n': top_n,
        'total_top_features': total_top,
        'tps_hits_count': tps_count,
        'non_tps_hits_count': non_tps_count,
        'overlap_percentage': round(overlap_percentage, 2),
        'expected_percentage': round(expected_percentage, 2),
        'enrichment_ratio': round(enrichment_ratio, 2) if enrichment_ratio != float('inf') else "Inf",
        'odds_ratio': round(odds_ratio, 2) if odds_ratio != float('inf') else "Inf",
        'tps_hits': tps_hits,
        'non_tps_hits': non_tps_hits,
        'known_tps_families': list(KNOWN_TPS_FAMILIES)
    }

def generate_overlap_report(stats: Dict, output_path: Path = None) -> Path:
    """
    Generate a JSON report with overlap statistics.
    
    Args:
        stats: Statistics dictionary from calculate_overlap_statistics.
        output_path: Path for the output JSON file.
        
    Returns:
        Path to the generated report.
    """
    if output_path is None:
        output_path = RESULTS_DIR / "overlap_statistics.json"
        
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Add metadata
    report = {
        'analysis_type': 'TPS Family Overlap Analysis',
        'description': 'Overlap between top predictive features and known terpene synthase families',
        'reference_families': list(KNOWN_TPS_FAMILIES),
        'statistics': stats,
        'disclaimer': 'Findings are associational due to observational data. Overlap does not imply causation.'
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    return output_path

def main():
    """Main entry point for overlap analysis."""
    print("Starting TPS family overlap analysis...")
    
    # Ensure directories exist
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load data
        print("Loading model and feature importance...")
        model, importance_df = load_model_and_feature_importance()
        
        print("Loading gene-pathway mapping...")
        gene_to_pathway = load_pathway_mapping()
        
        if not gene_to_pathway:
            print("Warning: No gene-pathway mapping found. Using feature names directly.")
            # Create a dummy mapping if none exists (features might already be pathways)
            for feat in importance_df['feature']:
                # Check if feature name starts with a known TPS family
                for family in KNOWN_TPS_FAMILIES:
                    if feat.startswith(family):
                        gene_to_pathway[feat] = family
                        break
                else:
                    gene_to_pathway[feat] = "Unknown"
        
        # Calculate statistics
        print("Calculating overlap statistics...")
        stats = calculate_overlap_statistics(importance_df, gene_to_pathway)
        
        # Generate report
        print("Generating overlap report...")
        report_path = generate_overlap_report(stats)
        
        print(f"Overlap analysis complete. Report saved to: {report_path}")
        print(f"Top {stats['top_n']} features: {stats['tps_hits_count']} overlap with known TPS families ({stats['overlap_percentage']}%)")
        
    except Exception as e:
        print(f"Error during overlap analysis: {e}")
        raise

if __name__ == "__main__":
    main()
