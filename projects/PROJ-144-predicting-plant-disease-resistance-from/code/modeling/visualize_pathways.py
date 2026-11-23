import os
import sys
import json
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
from utils.constants import RESULTS_DIR

def load_json_file(filepath):
    """Load a JSON file and return its contents."""
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json_file(filepath, data):
    """Save data to a JSON file."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def aggregate_pathway_scores(pathway_data):
    """
    Aggregate pathway scores from pathway analysis data.
    
    Args:
        pathway_data: Dictionary containing pathway analysis results
        
    Returns:
        DataFrame with aggregated pathway scores
    """
    if not pathway_data or 'pathway_mappings' not in pathway_data:
        return pd.DataFrame()
    
    mappings = pathway_data['pathway_mappings']
    if not mappings:
        return pd.DataFrame()
    
    # Count occurrences of each pathway
    pathway_counts = {}
    for item in mappings:
        if 'pathway' in item and item['pathway']:
            pathway = item['pathway']
            pathway_counts[pathway] = pathway_counts.get(pathway, 0) + 1
    
    # Create DataFrame
    df = pd.DataFrame([
        {'pathway': pathway, 'count': count}
        for pathway, count in pathway_counts.items()
    ])
    
    return df.sort_values('count', ascending=False)

def plot_pathway_importance(df, output_path):
    """
    Create a bar plot of pathway importance.
    
    Args:
        df: DataFrame with pathway counts
        output_path: Path to save the plot
    """
    if df.empty:
        # Create an empty plot with a message
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'No pathway data available', 
               transform=ax.transAxes, ha='center', va='center', fontsize=14)
        ax.set_title('Pathway Importance Analysis')
        ax.set_xlabel('Pathway')
        ax.set_ylabel('Count')
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()
        return
    
    # Create bar plot
    fig, ax = plt.subplots(figsize=(12, 7))
    colors = plt.cm.viridis(pd.cut(df['count'], bins=5).codes)
    bars = ax.bar(df['pathway'], df['count'], color=colors)
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45, ha='right')
    ax.set_title('Top Pathways Identified in Plant Disease Resistance Study', fontsize=14, fontweight='bold')
    ax.set_xlabel('Pathway', fontsize=12)
    ax.set_ylabel('Number of Associated Metabolites', fontsize=12)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{int(height)}',
                   xy=(bar.get_x() + bar.get_width() / 2, height),
                   xytext=(0, 3),
                   textcoords="offset points",
                   ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

def main():
    """
    Main function to generate pathway visualization.
    Reads pathway analysis data and creates a bar plot.
    """
    # Define paths
    input_path = Path(RESULTS_DIR) / "pathway_analysis.json"
    output_dir = Path(RESULTS_DIR) / "plots"
    output_path = output_dir / "pathway_barplot.png"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load pathway analysis data
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        print("Please ensure T027 has been completed successfully.")
        sys.exit(1)
    
    try:
        pathway_data = load_json_file(input_path)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {input_path}: {e}")
        sys.exit(1)
    
    # Aggregate pathway scores
    df = aggregate_pathway_scores(pathway_data)
    
    # Generate plot
    plot_pathway_importance(df, output_path)
    
    # Log success
    print(f"Visualization successfully generated: {output_path}")
    
    # Save metadata about the plot
    plot_metadata = {
        "input_file": str(input_path),
        "output_file": str(output_path),
        "num_pathways": len(df) if not df.empty else 0,
        "total_metabolites_mapped": pathway_data.get("mapping_success_rate", 0) if "mapping_success_rate" in pathway_data else 0
    }
    
    metadata_path = output_dir / "pathway_plot_metadata.json"
    save_json_file(metadata_path, plot_metadata)
    print(f"Plot metadata saved to: {metadata_path}")

if __name__ == "__main__":
    main()