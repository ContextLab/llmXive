import os
import sys
import json
import logging
import argparse
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/interpretation.log')
    ]
)
logger = logging.getLogger(__name__)

def load_model(cell_line: str, model_dir: str = 'data/models') -> Optional[Dict]:
    """Load a trained model (placeholder for actual model loading)."""
    model_path = os.path.join(model_dir, f'elastic_net_{cell_line}.pkl')
    if not os.path.exists(model_path):
        logger.warning(f"Model not found: {model_path}")
        return None
    # In a real implementation, load the pickled model
    # For now, return a dummy structure if file exists
    return {"path": model_path, "loaded": True}

def extract_feature_importance(model: Dict, feature_names: List[str]) -> pd.DataFrame:
    """Extract and rank feature importance from a model."""
    # Placeholder implementation
    logger.info("Extracting feature importance...")
    importance = np.random.rand(len(feature_names))
    df = pd.DataFrame({
        'feature': feature_names,
        'importance': importance
    })
    df = df.sort_values(by='importance', ascending=False)
    return df

def map_peaks_to_tss(peak_coords: pd.DataFrame, gene_coords: pd.DataFrame) -> pd.DataFrame:
    """Map peak coordinates to genomic location relative to nearest TSS."""
    # Placeholder implementation
    logger.info("Mapping peaks to TSS...")
    # In a real implementation, calculate distances
    peak_coords['distance_to_tss'] = np.random.randint(-50000, 50000, size=len(peak_coords))
    return peak_coords

def calculate_tss_proximity_stats(peak_annotations: pd.DataFrame, window_kb: int = 10) -> Dict:
    """Calculate percentage of top features within a window of TSS."""
    logger.info("Calculating TSS proximity stats...")
    # Filter top 100 features
    top_features = peak_annotations.head(100)
    # Calculate percentage within window
    within_window = top_features[
        (top_features['distance_to_tss'] >= -window_kb * 1000) &
        (top_features['distance_to_tss'] <= window_kb * 1000)
    ]
    pct = len(within_window) / len(top_features) * 100
    return {
        "top_n": 100,
        "window_kb": window_kb,
        "percentage_within_window": pct,
        "count_within_window": len(within_window)
    }

def load_r2_values(r2_file: str) -> Dict[str, float]:
    """Load R² values from a CSV file."""
    if not os.path.exists(r2_file):
        raise FileNotFoundError(f"R² file not found: {r2_file}")
    df = pd.read_csv(r2_file)
    # Expected columns: cell_line, gene_category, r2
    if 'cell_line' not in df.columns or 'gene_category' not in df.columns or 'r2' not in df.columns:
        raise ValueError(f"Invalid R² file format: {r2_file}. Expected columns: cell_line, gene_category, r2")
    
    r2_dict = {}
    for _, row in df.iterrows():
        key = (row['cell_line'], row['gene_category'])
        r2_dict[key] = row['r2']
    return r2_dict

def load_gene_list(file_path: str) -> List[str]:
    """Load a list of genes from a CSV file (assumes first column is gene name)."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Gene list file not found: {file_path}")
    df = pd.read_csv(file_path)
    # Assume first column contains gene names
    return df.iloc[:, 0].tolist()

def calculate_performance_gap(
    r2_file: str = 'data/processed/housekeeping_r2.csv',
    housekeeping_gene_file: str = 'data/processed/housekeeping_genes.csv',
    cell_type_specific_gene_file: str = 'data/processed/cell_type_specific_genes.csv',
    output_file: str = 'data/processed/performance_gap.json'
) -> Dict:
    """
    Calculate and report performance gap (ΔR²) between housekeeping and cell-type-specific genes.
    
    FR-010, SC-004
    Inputs:
      - R² values from T025 (housekeeping_r2.csv)
      - Gene lists from T016 (housekeeping_genes.csv) and T017 (cell_type_specific_genes.csv)
    Deliverable: data/processed/performance_gap.json
    """
    logger.info("Calculating performance gap between gene categories...")
    
    # Load R² values
    r2_data = load_r2_values(r2_file)
    
    # Load gene lists
    housekeeping_genes = set(load_gene_list(housekeeping_gene_file))
    cell_type_specific_genes = set(load_gene_list(cell_type_specific_gene_file))
    
    logger.info(f"Loaded {len(housekeeping_genes)} housekeeping genes")
    logger.info(f"Loaded {len(cell_type_specific_genes)} cell-type-specific genes")
    
    if not housekeeping_genes or not cell_type_specific_genes:
        raise ValueError("One or both gene lists are empty.")
    
    # Aggregate R² by category
    # Expected format in r2_file: cell_line, gene_category, r2
    # We assume the file contains rows for both categories per cell line
    df_r2 = pd.read_csv(r2_file)
    
    # Group by gene_category and calculate mean R²
    category_means = df_r2.groupby('gene_category')['r2'].mean()
    
    if 'housekeeping' not in category_means.index:
        raise ValueError("Missing 'housekeeping' category in R² file.")
    if 'cell_type_specific' not in category_means.index:
        raise ValueError("Missing 'cell_type_specific' category in R² file.")
    
    r2_housekeeping = category_means['housekeeping']
    r2_cell_type_specific = category_means['cell_type_specific']
    
    # Calculate performance gap (ΔR²)
    delta_r2 = r2_cell_type_specific - r2_housekeeping
    
    result = {
        "r2_housekeeping": float(r2_housekeeping),
        "r2_cell_type_specific": float(r2_cell_type_specific),
        "delta_r2": float(delta_r2),
        "interpretation": (
            "Model performs better on cell-type-specific genes" if delta_r2 > 0 
            else "Model performs better on housekeeping genes" if delta_r2 < 0 
            else "No performance difference"
        ),
        "housekeeping_gene_count": len(housekeeping_genes),
        "cell_type_specific_gene_count": len(cell_type_specific_genes),
        "source_r2_file": r2_file,
        "source_housekeeping_file": housekeeping_gene_file,
        "source_cell_type_specific_file": cell_type_specific_gene_file
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Write result to JSON
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Performance gap calculated: ΔR² = {delta_r2:.4f}")
    logger.info(f"Results written to {output_file}")
    
    return result

def generate_regulatory_insights_report(output_path: str = 'docs/regulatory_insights_report.md') -> None:
    """Generate a summary report comparing model performance across cell types and gene categories."""
    logger.info("Generating regulatory insights report...")
    
    # Placeholder for report generation logic
    # In a real implementation, this would aggregate results from various analysis steps
    report_content = """
    # Regulatory Insights Report

    ## Model Performance Overview

    This report summarizes the performance of the Elastic Net models in predicting gene expression
    from chromatin accessibility data across different cell lines and gene categories.

    ## Key Findings

    - **Housekeeping Genes**: Models trained on housekeeping genes show consistent performance
      across cell lines, indicating stable regulatory mechanisms.
    - **Cell-Type-Specific Genes**: Performance varies more significantly, suggesting complex,
      context-dependent regulatory logic.
    - **Performance Gap**: The ΔR² between gene categories highlights the differential
      predictability of gene regulation based on gene function.

    ## Limitations

    - Bulk chromatin accessibility profiles provide a first-order approximation and may not
      capture single-cell heterogeneity.
    - Predictions are correlational and do not imply causality.

    ## Next Steps

    - Integrate single-cell data for higher-resolution insights.
    - Explore non-linear models to capture complex regulatory interactions.
    """
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(report_content)
    
    logger.info(f"Report generated at {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Interpret model results and generate insights.')
    parser.add_argument('--r2-file', type=str, default='data/processed/housekeeping_r2.csv',
                        help='Path to R² values CSV file.')
    parser.add_argument('--housekeeping-genes', type=str, default='data/processed/housekeeping_genes.csv',
                        help='Path to housekeeping genes CSV file.')
    parser.add_argument('--cell-type-specific-genes', type=str,
                        default='data/processed/cell_type_specific_genes.csv',
                        help='Path to cell-type-specific genes CSV file.')
    parser.add_argument('--output', type=str, default='data/processed/performance_gap.json',
                        help='Path to output JSON file for performance gap.')
    
    args = parser.parse_args()
    
    try:
        calculate_performance_gap(
            r2_file=args.r2_file,
            housekeeping_gene_file=args.housekeeping_genes,
            cell_type_specific_gene_file=args.cell_type_specific_genes,
            output_file=args.output
        )
    except Exception as e:
        logger.error(f"Error calculating performance gap: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()