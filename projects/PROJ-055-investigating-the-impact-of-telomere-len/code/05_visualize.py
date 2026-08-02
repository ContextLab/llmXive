"""
Visualization module for the Telomere-Lifespan Impact study.

This module generates plots for the association analysis and moderator effects.
Specifically, it creates the grouped scatter plot with regression lines for
Migratory vs Resident species (FR-007).
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Ensure imports from sibling modules match the API surface
# We assume 04_model_pglS.py and 06_moderator.py have run before this.

def load_processed_data() -> pd.DataFrame:
    """
    Load the merged processed data from the pipeline.
    
    Returns:
        pd.DataFrame: The merged dataset containing species, telomere_length_kb,
                      lifespan, migration_status, and body_mass_g.
                      
    Raises:
        FileNotFoundError: If the processed data file does not exist.
    """
    data_path = Path("data/processed/merged_data.csv")
    if not data_path.exists():
        raise FileNotFoundError(
            f"Processed data not found at {data_path}. "
            "Please run the data ingestion pipeline (T014-T017) first."
        )
    
    df = pd.read_csv(data_path)
    
    # Validate expected columns exist
    required_cols = ['species', 'telomere_length_kb', 'lifespan', 'migration_status']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in merged data: {missing}")
        
    return df

def load_moderator_results() -> Optional[Dict[str, Any]]:
    """
    Load the moderator analysis results to determine if the interaction effect
    was statistically significant (for plot annotation).
    
    Returns:
        Dict or None: The interaction statistics if available, else None.
    """
    results_path = Path("results/moderator_analysis_results.csv")
    if not results_path.exists():
        logging.warning(f"Moderator results not found at {results_path}. "
                        "Plot will be generated without significance annotation.")
        return None
        
    try:
        # The moderator analysis saves a summary. We look for the interaction term.
        # Assuming the format from T034: species, coefficient, se, p_value, ...
        # or a summary row for the interaction.
        # Let's try to read the interaction stats specifically if saved, 
        # or just read the file to check existence.
        df = pd.read_csv(results_path)
        
        # We expect a row or column indicating the interaction term stats.
        # If the file contains the full model summary, we might need to parse.
        # For T035, we just need to know if we should annotate the plot.
        # Let's assume a specific column 'term' exists if it's a summary, 
        # or we just check if the file is non-empty.
        
        # Simplified: If the file exists and has content, we assume the model ran.
        # We will try to extract the interaction p-value if a 'term' column exists.
        if 'term' in df.columns:
            interaction_row = df[df['term'].str.contains('interaction', case=False, na=False)]
            if not interaction_row.empty:
                return interaction_row.iloc[0].to_dict()
        
        return {'status': 'model_ran'}
    except Exception as e:
        logging.warning(f"Could not parse moderator results: {e}")
        return None

def plot_moderator_scatter(
    data: pd.DataFrame,
    output_path: str,
    moderator_stats: Optional[Dict[str, Any]] = None
) -> None:
    """
    Generate a grouped scatter plot with separate regression lines for 
    "Migratory" and "Resident" species.
    
    This fulfills FR-007: Visualize the interaction effect of migration status
    on the telomere-lifespan relationship.
    
    Args:
        data: The merged dataframe.
        output_path: Path to save the plot (e.g., 'results/moderator_plot.png').
        moderator_stats: Optional dictionary containing interaction stats for annotation.
    """
    # Ensure output directory exists
    out_dir = Path(output_path).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Filter for valid data points (remove NaNs in key columns)
    plot_data = data.dropna(subset=['telomere_length_kb', 'lifespan', 'migration_status'])
    
    if plot_data.empty:
        raise ValueError("No valid data points found for plotting after dropping NaNs.")
        
    # Set the visual style
    sns.set_theme(context="talk", style="whitegrid", font="sans-serif")
    
    plt.figure(figsize=(12, 8))
    
    # Create the scatter plot with regression lines per group
    # x: telomere_length_kb, y: lifespan, hue: migration_status
    sns.lmplot(
        data=plot_data,
        x='telomere_length_kb',
        y='lifespan',
        hue='migration_status',
        palette={'Migratory': '#2c7bb6', 'Resident': '#d7191c'}, # Blue for Migratory, Red for Resident
        markers=['o', 's'],
        height=8,
        aspect=1.5,
        scatter_kws={'alpha': 0.6, 's': 60, 'edgecolors': 'w', 'linewidths': 1},
        line_kws={'linewidth': 2}
    )
    
    plt.title(
        "Telomere Length vs Lifespan by Migration Status",
        fontsize=16,
        pad=20
    )
    plt.xlabel("Telomere Length (kb)", fontsize=14)
    plt.ylabel("Maximum Lifespan (years)", fontsize=14)
    plt.legend(title="Migration Status", title_fontsize=12, fontsize=11)
    
    # Add annotation if moderator stats are available and significant
    if moderator_stats:
        # Try to find a p-value in the stats
        p_val = moderator_stats.get('p_value') or moderator_stats.get('interaction_p_value')
        if p_val is not None:
            annotation_text = f"Interaction p-value: {p_val:.3f}"
            if p_val < 0.05:
                annotation_text += " (Significant)"
            
            plt.figtext(
                0.98, 0.02, annotation_text,
                ha='right', va='bottom',
                fontsize=11,
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            )
    
    # Save the plot
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logging.info(f"Moderator scatter plot saved to {output_path}")

def main():
    """
    Main entry point for generating the moderator visualization.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Loading processed data...")
        df = load_processed_data()
        
        logger.info("Loading moderator analysis results...")
        stats = load_moderator_results()
        
        output_file = "results/moderator_plot.png"
        logger.info(f"Generating moderator plot: {output_file}")
        
        plot_moderator_scatter(df, output_file, stats)
        
        logger.info("Task T035 completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during visualization: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
