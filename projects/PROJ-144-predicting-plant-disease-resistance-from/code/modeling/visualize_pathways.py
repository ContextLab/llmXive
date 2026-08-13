"""
Visualization module for pathway analysis results.
Generates bar plots of pathway frequency/importance based on aggregated pathway data.
"""
import os
import sys
import json
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.constants import RESULTS_DIR, ensure_dirs

def load_json_file(file_path: Path) -> dict:
    """Load a JSON file and return its contents as a dictionary."""
    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)

def save_json_file(file_path: Path, data: dict):
    """Save a dictionary to a JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def aggregate_pathway_scores(pathway_data: dict) -> pd.DataFrame:
    """
    Aggregate pathway data to compute frequency and importance scores.
    
    Args:
        pathway_data: Dictionary containing pathway analysis results.
                     Expected keys: 'pathway_mappings', 'narrative_report', 'framing'
    
    Returns:
        DataFrame with pathway names, frequency, and importance scores.
    """
    if 'pathway_mappings' not in pathway_data or not pathway_data['pathway_mappings']:
        # Return empty dataframe if no mappings
        return pd.DataFrame(columns=['pathway_name', 'frequency', 'importance'])

    mappings = pathway_data['pathway_mappings']
    
    # Count frequency of each pathway
    pathway_counts = {}
    pathway_importance = {}
    
    for mapping in mappings:
        pathway_name = mapping.get('pathway_name', 'Unknown')
        if pathway_name:
            pathway_counts[pathway_name] = pathway_counts.get(pathway_name, 0) + 1
            # Use metabolite importance as proxy if available, otherwise default to 1
            importance = mapping.get('metabolite_importance', 1.0)
            if pathway_name not in pathway_importance:
                pathway_importance[pathway_name] = []
            pathway_importance[pathway_name].append(importance)
    
    # Create dataframe
    data = []
    for pathway_name, count in pathway_counts.items():
        avg_importance = sum(pathway_importance[pathway_name]) / len(pathway_importance[pathway_name])
        data.append({
            'pathway_name': pathway_name,
            'frequency': count,
            'importance': avg_importance
        })
    
    df = pd.DataFrame(data)
    if not df.empty:
        df = df.sort_values(by=['frequency', 'importance'], ascending=[False, False])
    
    return df

def plot_pathway_importance(df: pd.DataFrame, output_path: Path, top_n: int = 15):
    """
    Create a bar plot of pathway frequency/importance.
    
    Args:
        df: DataFrame with pathway data (pathway_name, frequency, importance)
        output_path: Path to save the plot
        top_n: Number of top pathways to display
    """
    if df.empty or len(df) == 0:
        # Create a placeholder plot if no data
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, 'No pathway data available', 
                horizontalalignment='center', verticalalignment='center',
                transform=plt.gca().transAxes)
        plt.title('Pathway Analysis - No Data')
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        return

    # Select top N pathways
    df_top = df.head(top_n).copy()
    
    # Create figure
    plt.figure(figsize=(12, 8))
    
    # Create bar plot with frequency on primary axis
    ax1 = plt.gca()
    sns.barplot(data=df_top, x='pathway_name', y='frequency', 
               ax=ax1, palette='viridis', edgecolor='black')
    
    ax1.set_xlabel('Pathway', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Frequency (Number of Metabolites)', fontsize=12, fontweight='bold')
    ax1.set_title('Top Pathways by Metabolite Frequency', fontsize=14, fontweight='bold')
    ax1.tick_params(axis='x', rotation=45)
    
    # Add importance as a secondary visualization (color intensity or secondary bar)
    # For clarity, we'll add importance values as text labels
    for i, row in df_top.iterrows():
        ax1.text(i, row['frequency'] + 0.1, f"Int: {row['importance']:.2f}",
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def main():
    """
    Main function to generate pathway visualization.
    
    Reads pathway analysis from results/pathway_analysis.json
    and generates results/plots/pathway_barplot.png
    """
    # Define paths
    input_path = RESULTS_DIR / "pathway_analysis.json"
    output_dir = RESULTS_DIR / "plots"
    output_path = output_dir / "pathway_barplot.png"
    
    # Ensure output directory exists
    ensure_dirs([output_dir])
    
    # Load pathway analysis data
    print(f"Loading pathway analysis from: {input_path}")
    try:
        pathway_data = load_json_file(input_path)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        # Create empty plot as fallback
        output_dir.mkdir(parents=True, exist_ok=True)
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, 'Pathway analysis data not found', 
                horizontalalignment='center', verticalalignment='center',
                transform=plt.gca().transAxes)
        plt.title('Pathway Analysis - Data Missing')
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Placeholder plot saved to: {output_path}")
        return
    
    # Aggregate pathway scores
    print("Aggregating pathway scores...")
    pathway_df = aggregate_pathway_scores(pathway_data)
    
    if pathway_df.empty:
        print("No pathway mappings found in data.")
        # Create empty plot
        output_dir.mkdir(parents=True, exist_ok=True)
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, 'No pathway mappings found', 
                horizontalalignment='center', verticalalignment='center',
                transform=plt.gca().transAxes)
        plt.title('Pathway Analysis - No Mappings')
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Empty plot saved to: {output_path}")
        return
    
    print(f"Found {len(pathway_df)} unique pathways")
    
    # Generate plot
    print(f"Generating bar plot: {output_path}")
    plot_pathway_importance(pathway_df, output_path, top_n=15)
    
    # Verify output
    if output_path.exists() and output_path.stat().st_size > 0:
        print(f"SUCCESS: Plot generated and saved to {output_path}")
        print(f"File size: {output_path.stat().st_size} bytes")
    else:
        print(f"ERROR: Failed to generate plot at {output_path}")
        sys.exit(1)

if __name__ == "__main__":
    main()
