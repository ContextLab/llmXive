import os
import sys
import json
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Add project root to path if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.constants import RESULTS_DIR

def load_json_file(file_path: Path) -> dict:
    """Load a JSON file and return its contents."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)

def aggregate_pathway_scores(pathway_data: list) -> pd.DataFrame:
    """
    Aggregate pathway data to calculate frequency and importance scores.
    
    Args:
        pathway_data: List of dictionaries containing pathway analysis results
        
    Returns:
        DataFrame with aggregated pathway statistics
    """
    if not pathway_data:
        raise ValueError("No pathway data provided for aggregation")
    
    df = pd.DataFrame(pathway_data)
    
    # Ensure required columns exist
    required_cols = ['pathway_name', 'metabolite_id']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Calculate frequency (count of metabolites per pathway)
    frequency = df.groupby('pathway_name').size().reset_index(name='frequency')
    
    # Calculate importance score (average intensity or weight if available)
    # If 'importance' or 'score' column exists, use it; otherwise default to 1
    if 'importance' in df.columns:
        importance = df.groupby('pathway_name')['importance'].mean().reset_index(name='importance_score')
    elif 'score' in df.columns:
        importance = df.groupby('pathway_name')['score'].mean().reset_index(name='importance_score')
    else:
        # Default importance score based on frequency
        importance = frequency.copy()
        importance['importance_score'] = importance['frequency']
    
    # Merge frequency and importance
    result = frequency.merge(importance, on='pathway_name')
    
    # Sort by importance score descending
    result = result.sort_values('importance_score', ascending=False).reset_index(drop=True)
    
    return result

def plot_pathway_importance(df: pd.DataFrame, output_path: Path, top_n: int = 15):
    """
    Create a bar plot of top pathways by importance score.
    
    Args:
        df: Aggregated pathway DataFrame
        output_path: Path to save the plot
        top_n: Number of top pathways to display
    """
    if df.empty:
        raise ValueError("Cannot plot empty DataFrame")
    
    # Select top N pathways
    top_df = df.head(top_n).copy()
    
    # Create figure with high resolution
    plt.figure(figsize=(14, 8), dpi=300)
    
    # Create bar plot
    ax = sns.barplot(
        data=top_df,
        x='importance_score',
        y='pathway_name',
        hue='frequency',
        palette='viridis',
        legend=False,
        edgecolor='black',
        linewidth=1.2
    )
    
    # Customize plot
    plt.title('Top Pathways by Importance Score', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Importance Score', fontsize=12, labelpad=10)
    plt.ylabel('Pathway', fontsize=12, labelpad=10)
    
    # Add value labels on bars
    for i, (idx, row) in enumerate(top_df.iterrows()):
        ax.text(
            row['importance_score'] + 0.1,
            i,
            f"{row['importance_score']:.2f}",
            va='center',
            fontsize=10,
            fontweight='bold'
        )
    
    # Improve layout
    plt.tight_layout()
    
    # Save with high resolution
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()

def main():
    """Main function to execute pathway visualization."""
    # Define paths
    input_path = RESULTS_DIR / "pathway_analysis.json"
    output_path = RESULTS_DIR / "pathway_barplot.png"
    
    print(f"Loading pathway analysis from: {input_path}")
    
    # Load data
    try:
        data = load_json_file(input_path)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure T027 has completed and generated results/pathway_analysis.json")
        sys.exit(1)
    
    # Handle different data structures
    if isinstance(data, dict):
        # Check if data is wrapped in a key
        if 'pathways' in data:
            pathway_data = data['pathways']
        elif 'results' in data:
            pathway_data = data['results']
        else:
            # Assume the dict itself contains the pathway entries
            pathway_data = list(data.values()) if any(isinstance(v, list) for v in data.values()) else [data]
    elif isinstance(data, list):
        pathway_data = data
    else:
        raise ValueError(f"Unexpected data structure: {type(data)}")
    
    if not pathway_data:
        print("Error: No pathway data found in the input file")
        sys.exit(1)
    
    print(f"Processing {len(pathway_data)} pathway entries")
    
    # Aggregate data
    try:
        aggregated_df = aggregate_pathway_scores(pathway_data)
        print(f"Aggregated data for {len(aggregated_df)} unique pathways")
    except Exception as e:
        print(f"Error aggregating pathway data: {e}")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate plot
    try:
        print(f"Generating visualization: {output_path}")
        plot_pathway_importance(aggregated_df, output_path)
        print(f"Successfully saved visualization to: {output_path}")
    except Exception as e:
        print(f"Error generating plot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()